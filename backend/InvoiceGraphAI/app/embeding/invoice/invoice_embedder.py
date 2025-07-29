import os
import json
import re
import datetime
import torch
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import config.config_path as configPath


# --- CONFIGURATION ---
json_directory = configPath.SOURCE_RAW_FOLDER_INVOICE_PATH
persist_dir = configPath.VECTOR_DB_INVOICE_CHROMA_FOLDER_PATH

# --- INIT DEVICE AND MODEL ---
device = "cuda" if torch.cuda.is_available() else "cpu"
embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)

# --- INIT CHROMA DB ---
sqlite_persist_path = os.path.join(persist_dir, "chroma.sqlite3")
chroma_client = chromadb.PersistentClient(path=sqlite_persist_path)
collection = chroma_client.get_or_create_collection(name="invoice_collection")

# --- UTILS ---
def clean_text(value):
    if not isinstance(value, str):
        value = str(value)
    return re.sub(r'\s+', ' ', value).strip().lower()

def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

def format_date(date_obj):
    if date_obj:
        return date_obj.strftime("%Y-%m-%d")
    return ""

def batch_encode(texts, model, batch_size=32):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        embeddings.extend(batch_embeddings)
    return embeddings

# --- INGEST FILES ---
doc_count = 0
file_count = 0

for json_file in os.listdir(json_directory):
    if json_file.endswith(".json"):
        file_count += 1
        file_path = os.path.join(json_directory, json_file)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    data = list(data.values())[0].get("value", {}).get("text", [])
                    data = json.loads(data)
            except Exception as e:
                print(f"❌ Failed to parse {json_file}: {e}")
                continue

        documents = []
        metadatas = []
        ids = []

        for i, record in enumerate(data):
            try:
                # Extract and clean all fields
                fields = {
                    "invoicenumber": record.get("invoicenumber", ""),
                    "billaccount": record.get("billaccount", ""),
                    "billaddress": record.get("billaddress", ""),
                    "billaddresscity": record.get("billaddresscity", ""),
                    "billaddressstate": record.get("billaddressstate", ""),
                    "billaddresscountry": record.get("billaddresscountry", ""),
                    "billaddresszip": record.get("billaddresszip", ""),
                    "serviceadress": record.get("serviceadress", ""),
                    "shipaddresscity": record.get("shipaddresscity", ""),
                    "shipaddressstate": record.get("shipaddressstate", ""),
                    "shipaddresscountry": record.get("shipaddresscountry", ""),
                    "shipaddresszip": record.get("shipaddresszip", ""),
                    "shiptoaccount": record.get("shiptoaccount", ""),
                    "date": record.get("date", ""),
                    "invoiceamount": record.get("invoiceamount", 0),
                    "outstandingbal": record.get("outstandingbal", 0),
                    "currency": record.get("currency", ""),
                    "projectnumber": record.get("projectnumber", ""),
                    "ponumber": record.get("ponumber", ""),
                    "projecttype": record.get("projecttype", ""),
                    "partyid": record.get("partyid", ""),
                    "billtocustomername": record.get("billtocustomername", "")
                }

                date_obj = parse_date(fields["date"])
                if not date_obj:
                    print(f"⚠️ Invalid date in record {i} of {json_file}: '{fields['date']}'")
                    continue

                unique_id = f"{fields['invoicenumber']}_{fields['billaccount']}"
                collection.delete(ids=[unique_id])  # Remove if exists

                # Create document text
                text = f"Invoice {fields['invoicenumber']} for {fields['billtocustomername']} on {fields['date']} amounting {fields['invoiceamount']} {fields['currency']}."

                # Clean all fields for metadata
                metadata = {k: clean_text(v) if isinstance(v, str) else v for k, v in fields.items()}
                metadata["year"] = str(date_obj.year)
                metadata["month"] = date_obj.strftime("%B").lower()

                documents.append(text)
                metadatas.append(metadata)
                ids.append(unique_id)
                doc_count += 1

            except Exception as e:
                print(f"⚠️ Skipping record {i} in {json_file}: {e}")

        if len(ids) != len(set(ids)):
            print(f"❌ Duplicate IDs found in {json_file}. Skipping this file.")
            continue

        if documents:
            embeddings = batch_encode(documents, embedding_model)
            collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
            print(f"✅ Upserted {len(documents)} from {json_file}")

print(f"\n📦 Completed ingestion: {doc_count} documents from {file_count} files into ChromaDB at {persist_dir}")
print(collection.count())
