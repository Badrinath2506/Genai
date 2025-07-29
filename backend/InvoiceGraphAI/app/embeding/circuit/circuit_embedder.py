import os
import json
import re
import datetime
import torch
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import config.config_path as circuitConfig


# python -m genai_app.agents.circuit_agent.embedder.circuit_embedder


# --- CONFIGURATION ---
json_directory = circuitConfig.SOURCE_RAW_FOLDER_CIRCUIT_PATH
persist_dir = circuitConfig.VECTOR_DB_CIRCUIT_CHROMA_FOLDER_PATH

# --- INIT DEVICE AND MODEL ---
device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)

# --- INIT CHROMA DB ---
sqlite_persist_path = os.path.join(persist_dir, "chroma.sqlite3")
chroma_client = chromadb.PersistentClient(path=sqlite_persist_path)
collection = chroma_client.get_or_create_collection(name="invoice_collection")

# --- BATCH EMBEDDING FUNCTION ---
def batch_encode(texts, model, batch_size=32):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        embeddings.extend(batch_embeddings)
    return embeddings

# --- NORMALIZATION UTILS ---
def clean_text(value):
    if not isinstance(value, str):
        value = str(value)
    return re.sub(r'\s+', ' ', value).strip().lower()

def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def format_date(date_obj):
    if date_obj:
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    return ""

# --- INGEST FILES ---
doc_count = 0
file_count = 0
for json_file in os.listdir(json_directory):
    if json_file.endswith(".json"):
        file_count += 1
        file_path = os.path.join(json_directory, json_file)
        
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                invoice_data = json.load(f)
            except Exception as e:
                print(f"❌ Failed to parse {json_file}: {e}")
                continue
            
            if not isinstance(invoice_data, list):
                print(f"⚠️ Skipped {json_file}: expected a list of invoices")
                continue
            
            documents = []
            metadatas = []
            ids = []
            
            for i, record in enumerate(invoice_data):
                try:
                    invoice_number = clean_text(record.get("InvoiceNumber", ""))
                    bill_type = clean_text(record.get("BillType", ""))
                    bill_ucn = clean_text(record.get("BillUCN", ""))
                    account_number = clean_text(record.get("AccountNumber", ""))
                    account_name = clean_text(record.get("AccountName", ""))
                    bill_id = clean_text(record.get("BillID", ""))
                    bill_start_date = parse_date(record.get("BillStartDate", ""))
                    currency_rate = clean_text(record.get("CurrencyRate", ""))
                    date_end = parse_date(record.get("Date_End", ""))
                    circuit_id = clean_text(record.get("CircuitID", ""))
                    account_id = clean_text(record.get("AccountID", ""))
                    carrier_circuit_type_id = clean_text(record.get("CarrierCircuitTypeID", None))
                    bandwidth_id = clean_text(record.get("BandwidthID", ""))
                    channel = clean_text(record.get("Channel", None))
                    channel_bank = clean_text(record.get("ChannelBank", None))
                    channel_bank2 = clean_text(record.get("ChannelBank2", None))
                    cct_type_id_customer = clean_text(record.get("CCTTypeID_Customer", None))
                    service_id = clean_text(record.get("ServiceID", ""))
                    alternate_ucn = clean_text(record.get("AlternateUCN", ""))
                    ucn_acode = clean_text(record.get("UCN_aCode", ""))
                    ucn_full = clean_text(record.get("UCN_FULL", ""))
                    project_id = clean_text(record.get("ProjectID", ""))
                    company_id_customer = clean_text(record.get("CompanyID_Customer", ""))
                    ucn_no = clean_text(record.get("UCN_No", ""))

                    unique_id = f"{circuit_id}_{account_id}_{invoice_number}"
                    
                    # Parse and normalize date
                    date_str = record.get("BillStartDate", "")
                    date_obj = parse_date(date_str)
                    if not date_obj:
                        print(f"⚠️ Invalid date in record {i} of {json_file}: '{date_str}'")
                        continue
                    
                    year = str(date_obj.year)
                    month = date_obj.strftime("%B").lower()
                    
                    # Remove existing if already in DB
                    try:
                        collection.delete(ids=[unique_id])
                    except Exception:
                        pass # Safe to ignore if ID doesn't exist
                    
                    # Document + Metadata
                    text = f"Invoice {invoice_number} for customer {account_name} on {date_str} amounting {0} {currency_rate}."
                    metadata = {
                        "invoice_number": invoice_number,
                        "bill_type": bill_type,
                        "bill_ucn": bill_ucn,
                        "account_number": account_number,
                        "account_name": account_name,
                        "bill_id": bill_id,
                        "bill_start_date": format_date(bill_start_date),
                        "currency_rate": currency_rate,
                        "date_end": format_date(date_end),
                        "circuit_id": circuit_id,
                        "account_id": account_id,
                        "carrier_circuit_type_id": carrier_circuit_type_id,
                        "bandwidth_id": bandwidth_id,
                        "channel": channel,
                        "channel_bank": channel_bank,
                        "channel_bank2": channel_bank2,
                        "cct_type_id_customer": cct_type_id_customer,
                        "service_id": service_id,
                        "alternate_ucn": alternate_ucn,
                        "ucn_acode": ucn_acode,
                        "ucn_full": ucn_full,
                        "project_id": project_id,
                        "company_id_customer": company_id_customer,
                        "ucn_no": ucn_no,
                        "year": year,
                        "month": month
                    }
                    
                    documents.append(text)
                    metadatas.append(metadata)
                    ids.append(unique_id)
                    
                    doc_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Skipping record {i} in {json_file}: {e}")
            
            # Check for duplicate IDs
            if len(ids) != len(set(ids)):
                print(f"❌ Duplicate IDs found in {json_file}. Skipping this file.")
                continue
            
            if documents:
                embeddings = batch_encode(documents, embedding_model, batch_size=32)
                collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
                print(f"✅ Upserted {len(documents)} from {json_file}")

# --- FINALIZE ---
print(f"\n📦 Completed ingestion: {doc_count} documents from {file_count} files into ChromaDB at {persist_dir}")
print(collection.count())

