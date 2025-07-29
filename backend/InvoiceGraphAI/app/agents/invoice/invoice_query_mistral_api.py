import chromadb
import asyncio
import aiohttp
import logging
import re
import json
from collections import defaultdict
from datetime import datetime
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging.handlers
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Invoice Query API",
    description="API for querying invoice data using ChromaDB and Mistral",
    version="1.0.0"
)

# Configuration
class Config:
    VECTOR_DB_PATH = "./vector_stores/invoice_vector_store/chroma"
    OLLAMA_API_URL = "http://localhost:11434/api/generate"
    OLLAMA_MODEL = "mistral"
    CHUNK_SIZE = 5
    WARNING_THRESHOLD = 200
    LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT = 3
    LOG_BASE_PATH = "./logs"

config = Config()

# Ensure log directory exists
os.makedirs(config.LOG_BASE_PATH, exist_ok=True)

# Set up logging with rotation
current_date = datetime.now().strftime("%m%d%Y")
log_file_path = os.path.join(config.LOG_BASE_PATH, f"invoice_api_{current_date}.log")

logger = logging.getLogger("invoice_api")
logger.setLevel(logging.DEBUG)

# Create handlers
file_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=config.LOG_MAX_SIZE,
    backupCount=config.LOG_BACKUP_COUNT
)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize ChromaDB
try:
    chroma_client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
    collection = chroma_client.get_or_create_collection(name="invoice_collection")
    logger.info("ChromaDB client initialized successfully for invoices")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
    raise

# Models
class InvoiceQueryRequest(BaseModel):
    query: str
    count_only: Optional[bool] = False

# Utility functions
def is_count_only_query(user_query: str) -> bool:
    result = any(kw in user_query.lower() for kw in ["count", "how many", "number of invoices"])
    logger.debug(f"is_count_only_query: {result} for query='{user_query}'")
    return result

async def query_mistral(prompt: str, timeout: int = 240) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
            logger.debug(f"Sending prompt to Mistral: {payload}")
            
            async with session.post(
                config.OLLAMA_API_URL, 
                json=payload, 
                timeout=timeout
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    response = result.get("response", "").strip()
                    logger.debug(f"Received response from Mistral: {response}")
                    return response
                else:
                    error_msg = f"Mistral API error: HTTP {resp.status}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                    
    except asyncio.TimeoutError:
        error_msg = "Mistral API request timed out"
        logger.error(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Error querying Mistral API: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

def build_prompt(context: str, user_query: str) -> str:
    return f"""You are InvoiceGPT, an intelligent assistant that helps users query structured invoice data.

You are provided with a list of invoice records. Each record includes:
- Invoice Number
- Customer Name
- Date
- Amount
- Currency

---

### Instructions:
1. Carefully read the user's question and understand whether they are asking for:
   - A **count** of matching invoices only, OR
   - A **summary with count** and a **detailed list of matching invoices**

2. If the user is asking only for a count:
   - Respond with a single sentence like:  
     **"There are 8 invoices for customer 'XYZ' in 2022."**

3. If the user asks for invoice **details** or **list**:
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

async def process_count_response(filtered_metas: list) -> str:
    try:
        grouped_totals = defaultdict(lambda: defaultdict(float))
        for meta in filtered_metas:
            try:
                amount = float(meta.get("amount", 0))
                currency = meta.get("currency", "").upper()
                cust_name = meta.get("account_name", "Unknown Customer")
                grouped_totals[cust_name][currency] += amount
            except Exception as e:
                logger.warning(f"Skipping amount parsing error: {str(e)}")

        summary = f"There are {len(filtered_metas)} invoices that match your request."
        if grouped_totals:
            breakdown_lines = [""]
            for cust, currency_map in grouped_totals.items():
                breakdown_lines.append(f"Customer: {cust}")
                for currency, total in currency_map.items():
                    breakdown_lines.append(f"  Total in {currency}: {total:.2f}")
            return summary + "\n" + "\n".join(breakdown_lines)
        return summary
    except Exception as e:
        logger.error(f"Error in process_count_response: {str(e)}")
        raise

async def process_detail_response(filtered_docs: list, filtered_metas: list, user_query: str) -> str:
    try:
        all_rows = []
        for i in range(0, len(filtered_docs), config.CHUNK_SIZE):
            chunk_metas = filtered_metas[i:i+config.CHUNK_SIZE]
            logger.info(f"Processing chunk {i+1}/{(len(filtered_docs) + config.CHUNK_SIZE - 1) // config.CHUNK_SIZE}")
            
            context = "\n".join(
                f"| {meta.get('invoice_number')} | {meta.get('account_name')} | {meta.get('date')} | {meta.get('amount')} | {meta.get('currency')} |"
                for meta in chunk_metas
            )
            
            prompt = build_prompt(context, user_query)
            chunk_response = await query_mistral(prompt)
            
            lines = chunk_response.strip().splitlines()
            valid_chunk_rows = [
                line.strip()
                for line in lines
                if line.startswith("|") and line.count("|") >= 4
                and "Invoice Number" not in line and "---" not in line
            ]
            all_rows.extend(valid_chunk_rows)

        if all_rows:
            header = "| Invoice Number | Customer Name | Date | Amount | Currency |"
            separator = "|----------------|----------------|------|--------|----------|"
            final_output = [header, separator] + all_rows
            friendly_intro = f"I found {len(all_rows)} matching invoice records. Here's the detailed list:\n\n"
            return friendly_intro + "\n".join(final_output)
        return "No matching invoices found."
    except Exception as e:
        logger.error(f"Error in process_detail_response: {str(e)}")
        raise

@app.post("/query")
async def query_invoice_data(request: InvoiceQueryRequest):
    """Query endpoint for invoice data"""
    try:
        start_time = datetime.now()
        logger.info(f"Starting invoice query processing for: {request.query}")
        
        count_mode = request.count_only or is_count_only_query(request.query)
        logger.info(f"Count mode: {count_mode}")

        # Get all documents (consider adding filtering here)
        results = collection.get(include=['documents', 'metadatas'])
        documents = results['documents']
        metadatas = results['metadatas']
        logger.info(f"Retrieved {len(documents)} documents from ChromaDB")

        if len(documents) > config.WARNING_THRESHOLD:
            logger.warning(f"Large result set: {len(documents)} documents found")

        # Apply filters from query
        year_match = re.search(r"(?:year\s+)?(20\d{2})", request.query)
        year = year_match.group(1) if year_match else None

        month_match = re.search(r"month\s+(0?[1-9]|1[0-2])\b", request.query.lower())
        month = month_match.group(1).zfill(2) if month_match else None

        date_range_match = re.search(r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})", request.query)
        start_date = datetime.strptime(date_range_match.group(1), "%Y-%m-%d") if date_range_match else None
        end_date = datetime.strptime(date_range_match.group(2), "%Y-%m-%d") if date_range_match else None

        cust_match = re.search(r"customer\s+([a-z0-9\s&.,'-]+?)(?=\s+(?:during|in|between|issued|for|on|and|$))", request.query.lower())
        customer = cust_match.group(1).strip() if cust_match else None

        bill_match = re.search(r"billing account\s+([a-z0-9\s&.,'-]+)", request.query.lower())
        billing = bill_match.group(1).strip() if bill_match else None

        logger.info(f"Applying filters - year: {year}, month: {month}, customer: {customer}, billing: {billing}, date_range: {start_date} to {end_date}")

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

        if not filtered_docs:
            logger.info("No matching invoices found after filtering")
            return JSONResponse(
                content={"response": "No matching invoices found."},
                status_code=404
            )

        if count_mode:
            response = await process_count_response(filtered_metas)
        else:
            response = await process_detail_response(filtered_docs, filtered_metas, request.query)

        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Invoice query processed successfully in {processing_time:.2f} seconds")
        
        return JSONResponse(content={"response": response})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing invoice query: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing invoice query")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Simple checks
        collection.count()  # Verify ChromaDB connection
        async with aiohttp.ClientSession() as session:
            async with session.get(config.OLLAMA_API_URL.replace("/api/generate", "/api/tags")) as resp:
                if resp.status != 200:
                    raise Exception("Mistral API not reachable")
                    
        return JSONResponse(content={"status": "healthy"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,
        access_log=False
    )