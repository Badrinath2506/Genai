import chromadb
import asyncio
import aiohttp
import logging
import re
from collections import defaultdict
from datetime import datetime
import genai_app.config.config_path as circuitConfig

# CONFIG
persist_dir = r"E:\Badri_NewVM\deployment\GenAIWorkSpace\GenAIPOC\genai_app\vector_stores\invoice_vector_store\chroma\chroma.sqlite3" #circuitConfig.VECTOR_DB_INVOICE_CHROMA_QUERY_FOLDER_PATH

ollama_api_url = "http://localhost:11434/api/generate"
ollama_model = "mistral"
chunk_size = 5
warning_threshold = 200

log_file_path = circuitConfig.LOG_PATH_INVOICE_LOGFILE

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file_path, filemode='a')
logger = logging.getLogger("invoice_query_circuit")


# INIT DB
chroma_client = chromadb.PersistentClient(path=persist_dir)
collection = chroma_client.get_or_create_collection(name="invoice_collection")

# QUERY TYPE CHECKER
def is_count_only_query(user_query: str) -> bool:
    return any(kw in user_query.lower() for kw in ["count", "how many", "number of invoices"])

# PROMPT BUILDER
def build_prompt(context: str, user_query: str) -> str:
    return f"""You are InvoiceGPT, an intelligent assistant that helps users query structured invoice data.

You are provided with a list of invoice records. Each record includes:
- Invoice Number
- Bill Type
- Bill UCN
- Account Number
- Account Name
- Bill ID
- Bill Start Da   
- Currency Rate
- Date End
- Circuit ID
- Account ID
- Carrier Circuit Type ID
- Bandwidth ID
- Channel
- Channel Bank
- Channel Bank2
- CCT Type ID Customer
- Service ID
- Alternate UCN
- UCN aCode
- UCN FULL
- Project ID
- Company ID Customer
- UCN No

---

### Instructions:
1. Carefully read the user's question and understand whether they are asking for:
   - A **count** of matching invoices only, OR
   - A **summary with count** and a **detailed list of matching invoices**

2. If the user is asking only for a count (e.g., for a specific customer, billing account, or year):
   - Respond with a single sentence like:  
     **"There are 8 invoices for customer 'XYZ' in 2022."**

3. If the user asks for invoice **details**, **list**, or provides a **date range**:
   - First respond with a summary:  
     **"There are 12 matching invoices between Jan 2022 and Dec 2023."**
   - Then provide a Markdown table of matching records with columns:  
     | Invoice Number | Customer Name | Date | Amount | Currency |

4. Do **not invent** any invoices. Only use those listed in the next section.

5. If no matching records exist, say:  
   **"No matching invoices found."**

---

### Invoice Records:
{context}

---

### User Question:
{user_query}

---

### Your Response:
"""

# CALL MISTRAL API
async def query_mistral(prompt, api_url=ollama_api_url, model=ollama_model):
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        logger.info("Sending prompt to Mistral...")
        async with session.post(api_url, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result.get("response", "").strip()
            logger.error(f"Mistral API error: HTTP {resp.status}")
            return ""

# SPLIT RESULTS INTO CHUNKS
def chunk_results(documents, metadatas, chunk_size):
    for i in range(0, len(documents), chunk_size):
        yield documents[i:i+chunk_size], metadatas[i:i+chunk_size]

# MAIN QUERY HANDLER
async def query_chroma_with_mistral(user_query: str):
    count_mode = is_count_only_query(user_query)
    logger.info(f"🔍 Detecting query type: {'count' if count_mode else 'list'}")

    results = collection.get(include=['documents', 'metadatas'])
    documents = results['documents']
    metadatas = results['metadatas']
    
    # import pdb; pdb.set_trace()
    
    logger.info(f"Retrieved {len(documents)} documents from ChromaDB.")

    if len(documents) > warning_threshold:
        print(f"⚠️ Warning: {len(documents)} documents found. Consider refining your query for better results.")

    if not documents:
        return "⚠️ No matching invoices found."

    # SHARED FILTERS
    year_match = re.search(r"(?:year\s+)?(20\d{2})", user_query)
    
    year = year_match.group(1) if year_match else None

    month_match = re.search(r"month\s+(0?[1-9]|1[0-2])\b", user_query.lower())
    month = month_match.group(1).zfill(2) if month_match else None

    date_range_match = re.search(r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})", user_query)
    start_date = datetime.strptime(date_range_match.group(1), "%Y-%m-%d") if date_range_match else None
    end_date = datetime.strptime(date_range_match.group(2), "%Y-%m-%d") if date_range_match else None

    cust_match = re.search(r"customer\s+([a-z0-9\s&.,'-]+?)(?=\s+(?:during|in|between|issued|for|on|and|$))", user_query.lower())
    customer = cust_match.group(1).strip() if cust_match else None

    bill_match = re.search(r"billing account\s+([a-z0-9\s&.,'-]+)", user_query.lower())
    billing = bill_match.group(1).strip() if bill_match else None

    logger.info(f"🧪 Filtering for year={year}, month={month}, customer={customer}, billing={billing}, date_range={start_date} to {end_date}")

    filtered_metas = []
    filtered_docs = []
    
  
    
    for doc, meta in zip(documents, metadatas):
        date_str = meta.get("date", "")
        if not date_str:
            continue
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue

        if year and date_str[:4] != year:
            continue
        if month and date_str[5:7] != month:
            continue
        if start_date and end_date and not (start_date <= date_obj <= end_date):
            continue
        if customer and customer not in meta.get("customer", "").lower():
            continue
        if billing and billing not in meta.get("bill_account", "").lower():
            continue

        filtered_metas.append(meta)
        filtered_docs.append(doc)

    if count_mode:
        grouped_totals = defaultdict(lambda: defaultdict(float))

        for meta in filtered_metas:
            try:
                amount = float(meta.get("amount", 0))
                currency = meta.get("currency", "").upper()
                cust_name = meta.get("customer", "Unknown Customer")
                grouped_totals[cust_name][currency] += amount
            except Exception as e:
                logger.warning(f"Skipping amount parsing error: {e}")

        logger.info(f"✅ Final count of matching invoices: {len(filtered_metas)}")

        summary = f"There are {len(filtered_metas)} invoices that match your request."
        if grouped_totals:
            breakdown_lines = [""]
            for cust, currency_map in grouped_totals.items():
                breakdown_lines.append(f"Customer: {cust}")
                for currency, total in currency_map.items():
                    breakdown_lines.append(f"  Total in {currency}: {total:.2f}")
            return summary + "\n" + "\n".join(breakdown_lines)
        return summary

    # --- FULL DETAIL MODE ---
    all_rows = []

    for i, (chunk_docs, chunk_metas) in enumerate(chunk_results(filtered_docs, filtered_metas, chunk_size)):
        logger.info(f"Processing chunk {i+1}/{(len(filtered_docs) + chunk_size - 1) // chunk_size} with {len(chunk_docs)} records")

        context = "\n".join(
            f"| {meta.get('invoice_number')} | {meta.get('customer')} | {meta.get('date')} | {meta.get('amount')} | {meta.get('currency')} |"
            for meta in chunk_metas
        )

        prompt = build_prompt(context, user_query)
        chunk_response = await query_mistral(prompt)

        logger.debug(f"Mistral response (chunk {i+1}):\n{chunk_response}")

        lines = chunk_response.strip().splitlines()
        valid_chunk_rows = []
        for line in lines:
            line = line.strip()
            if line.startswith("|") and line.count("|") >= 4 and "Invoice Number" not in line and "---" not in line:
                valid_chunk_rows.append(line)

        logger.info(f"Extracted {len(valid_chunk_rows)} valid rows from chunk {i+1}")
        all_rows.extend(valid_chunk_rows)

    if all_rows:
        header = "| Invoice Number | Customer Name | Date | Amount | Currency |"
        separator = "|----------------|----------------|------|--------|----------|"
        final_output = [header, separator] + all_rows
        friendly_intro = "Here are the invoice records I found that match your query:\n\n"
        return friendly_intro + "\n".join(final_output)
    else:
        return "No relevant invoices found."

# --- INTERACTIVE ENTRYPOINT ---
if __name__ == "__main__":
    while True:
        user_input = input("🔍 Enter your invoice query (or type 'exit' to quit): ").strip().lower()
        if user_input in ['exit', 'quit', 'bye']:
            print("👋 Goodbye!")
            break

        final_response = asyncio.run(query_chroma_with_mistral(user_input))
        print("\n🧠 Final Aggregated Response:\n", final_response)
