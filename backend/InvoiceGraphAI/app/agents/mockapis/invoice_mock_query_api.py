import asyncio
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
    title="Mock Invoice Query API",
    description="Mock API for testing invoice queries without external dependencies",
    version="1.0.0"
)

# Configuration
class Config:
    VECTOR_DB_PATH = r"C:\Badri\IPC\InvoiceGraphAI\agents\mockapis\mock_data\invoice_data.json"
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
log_file_path = os.path.join(config.LOG_BASE_PATH, f"mock_invoice_api_{current_date}.log")

logger = logging.getLogger("mock_invoice_api")
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

# Mock data storage
mock_invoice_data = []

# Load mock data from file if exists
try:
    if os.path.exists(config.VECTOR_DB_PATH):
        with open(config.VECTOR_DB_PATH, 'r') as f:
            mock_invoice_data = json.load(f)
        logger.info(f"Loaded {len(mock_invoice_data)} mock invoice records")
    else:
        # Create some sample data if file doesn't exist
        mock_invoice_data = [
            {
                "invoice_number": "INV-2023-001",
                "account_name": "Acme Corp",
                "date": "2023-01-15",
                "amount": "1250.00",
                "currency": "USD",
                "customer": "acme corp",
                "bill_account": "acme main"
            },
            {
                "invoice_number": "INV-2023-002",
                "account_name": "Globex Inc",
                "date": "2023-02-20",
                "amount": "890.50",
                "currency": "EUR",
                "customer": "globex inc",
                "bill_account": "globex europe"
            },
            {
                "invoice_number": "INV-2023-003",
                "account_name": "Acme Corp",
                "date": "2023-03-10",
                "amount": "2100.00",
                "currency": "USD",
                "customer": "acme corp",
                "bill_account": "acme west"
            }
        ]
        logger.info("Created sample mock invoice data")
except Exception as e:
    logger.error(f"Failed to initialize mock data: {str(e)}")
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

async def mock_query_mistral(prompt: str) -> str:
    """Mock version of the Mistral query function"""
    try:
        logger.debug(f"Mock processing prompt: {prompt[:200]}...")
        
        # Extract context from prompt
        context_start = prompt.find("### Invoice Records:") + len("### Invoice Records:")
        context_end = prompt.find("### User Question:")
        context = prompt[context_start:context_end].strip()
        
        # Extract user question
        question_start = prompt.find("### User Question:") + len("### User Question:")
        question_end = prompt.find("### Your Response:")
        user_query = prompt[question_start:question_end].strip()
        
        # Count the number of invoice records in context
        invoice_count = context.count("|") // 5  # Each record has 5 pipes
        
        if is_count_only_query(user_query):
            return f"There are {invoice_count} invoices that match your request."
        else:
            if invoice_count == 0:
                return "No matching invoices found."
            
            # Reconstruct the table from context
            table_lines = [line.strip() for line in context.split("\n") if line.strip().startswith("|")]
            
            if not table_lines:
                return "No matching invoices found."
                
            header = "| Invoice Number | Customer Name | Date | Amount | Currency |"
            separator = "|----------------|----------------|------|--------|----------|"
            
            return (
                f"There are {invoice_count} matching invoices.\n\n"
                f"{header}\n"
                f"{separator}\n"
                + "\n".join(table_lines)
            )
            
    except Exception as e:
        logger.error(f"Error in mock_query_mistral: {str(e)}")
        return "An error occurred while processing your request."

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

async def process_detail_response(filtered_metas: list, user_query: str) -> str:
    try:
        all_rows = []
        for i in range(0, len(filtered_metas), config.CHUNK_SIZE):
            chunk_metas = filtered_metas[i:i+config.CHUNK_SIZE]
            logger.info(f"Processing chunk {i+1}/{(len(filtered_metas) + config.CHUNK_SIZE - 1) // config.CHUNK_SIZE}")
            
            context = "\n".join(
                f"| {meta.get('invoice_number')} | {meta.get('account_name')} | {meta.get('date')} | {meta.get('amount')} | {meta.get('currency')} |"
                for meta in chunk_metas
            )
            
            prompt = f"""You are InvoiceGPT, an intelligent assistant that helps users query structured invoice data.

### Invoice Records:
{context}

### User Question:
{user_query}

### Your Response:
"""
            chunk_response = await mock_query_mistral(prompt)
            
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
        logger.info(f"Starting mock invoice query processing for: {request.query}")
        
        count_mode = request.count_only or is_count_only_query(request.query)
        logger.info(f"Count mode: {count_mode}")

        # Get all documents from mock data
        metadatas = mock_invoice_data
        logger.info(f"Retrieved {len(metadatas)} documents from mock data")

        if len(metadatas) > config.WARNING_THRESHOLD:
            logger.warning(f"Large result set: {len(metadatas)} documents found")

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
        
        for meta in metadatas:
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

        if not filtered_metas:
            logger.info("No matching invoices found after filtering")
            return JSONResponse(
                content={"response": "No matching invoices found."},
                status_code=404
            )

        if count_mode:
            response = await process_count_response(filtered_metas)
        else:
            response = await process_detail_response(filtered_metas, request.query)

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
        # Simple mock checks
        if not isinstance(mock_invoice_data, list):
            raise Exception("Mock data not initialized properly")
            
        return JSONResponse(content={"status": "healthy"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/reset_mock_data")
async def reset_mock_data():
    """Endpoint to reset mock data (for testing)"""
    global mock_invoice_data
    try:
        if os.path.exists(config.VECTOR_DB_PATH):
            with open(config.VECTOR_DB_PATH, 'r') as f:
                mock_invoice_data = json.load(f)
        else:
            mock_invoice_data = [
                {
                    "invoice_number": "INV-2023-001",
                    "account_name": "Acme Corp",
                    "date": "2023-01-15",
                    "amount": "1250.00",
                    "currency": "USD",
                    "customer": "acme corp",
                    "bill_account": "acme main"
                },
                {
                    "invoice_number": "INV-2023-002",
                    "account_name": "Globex Inc",
                    "date": "2023-02-20",
                    "amount": "890.50",
                    "currency": "EUR",
                    "customer": "globex inc",
                    "bill_account": "globex europe"
                },
                {
                    "invoice_number": "INV-2023-003",
                    "account_name": "Acme Corp",
                    "date": "2023-03-10",
                    "amount": "2100.00",
                    "currency": "USD",
                    "customer": "acme corp",
                    "bill_account": "acme west"
                }
            ]
        return JSONResponse(content={"status": "success", "count": len(mock_invoice_data)})
    except Exception as e:
        logger.error(f"Failed to reset mock data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset mock data")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,
        access_log=False
    )