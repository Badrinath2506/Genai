import asyncio
import logging
import json
from datetime import datetime
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging.handlers
from pydantic import BaseModel
from typing import Optional, Dict, Any
from collections import defaultdict

app = FastAPI(
    title="Mock Circuit Query API",
    description="Mock API for testing circuit queries without external dependencies",
    version="1.0.0"
)

# Configuration
class Config:
    MOCK_DATA_PATH = r"C:\Badri\IPC\InvoiceGraphAI\agents\mockapis\mock_data\circuit_data.json"
    CHUNK_SIZE = 5
    WARNING_THRESHOLD = 200
    LOG_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT = 3
    LOG_BASE_PATH = "./logs"

config = Config()

# Field aliases
FIELD_ALIASES = {
    "invoice": "invoice_number",
    "invoice no": "invoice_number",
    "invoice number": "invoice_number",
    "customer": "account_name",   
    "billing account": "account_number",
    "bill account": "account_number",
    "circuit": "circuit_id",
    "circuit_id": "circuit_id",
    "network id": "circuit_id"    
}

# Ensure directories exist
os.makedirs(config.LOG_BASE_PATH, exist_ok=True)
os.makedirs(os.path.dirname(config.MOCK_DATA_PATH), exist_ok=True)

# Set up logging
current_date = datetime.now().strftime("%m%d%Y")
log_file_path = os.path.join(config.LOG_BASE_PATH, f"mock_circuit_api_{current_date}.log")

logger = logging.getLogger("mock_circuit_api")
logger.setLevel(logging.DEBUG)

# Handlers
file_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=config.LOG_MAX_SIZE,
    backupCount=config.LOG_BACKUP_COUNT
)
console_handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Mock data storage
mock_circuit_data = []

# Load or initialize mock data
try:
    if os.path.exists(config.MOCK_DATA_PATH):
        with open(config.MOCK_DATA_PATH, 'r') as f:
            mock_circuit_data = json.load(f)
        logger.info(f"Loaded {len(mock_circuit_data)} mock circuit records")
    else:
        # Sample circuit data
        mock_circuit_data = [
            {
                "invoice_number": "INV-2023-001",
                "account_name": "Acme Corp",
                "circuit_id": "CIRC-001",
                "account_number": "ACME-001",
                "date": "2023-01-15"
            },
            {
                "invoice_number": "INV-2023-002",
                "account_name": "Globex Inc",
                "circuit_id": "CIRC-002",
                "account_number": "GLOBEX-001",
                "date": "2023-02-20"
            },
            {
                "invoice_number": "INV-2023-003",
                "account_name": "Acme Corp",
                "circuit_id": "CIRC-003",
                "account_number": "ACME-002",
                "date": "2023-03-10"
            }
        ]
        logger.info("Created sample mock circuit data")
except Exception as e:
    logger.error(f"Failed to initialize mock data: {str(e)}")
    raise

# Models
class CircuitQueryRequest(BaseModel):
    query: str
    count_only: Optional[bool] = False

# Utility functions
def is_count_only_query(user_query: str) -> bool:
    result = any(kw in user_query.lower() for kw in ["count", "how many", "number of circuits"])
    logger.debug(f"is_count_only_query: {result} for query='{user_query}'")
    return result

async def mock_query_mistral(prompt: str) -> str:
    """Mock version of the Mistral query function for circuits"""
    try:
        # Extract context from prompt
        context_start = prompt.find("### Circuit Records:") + len("### Circuit Records:")
        context_end = prompt.find("### User Question:")
        context = prompt[context_start:context_end].strip()
        
        # Count the number of circuit records in context
        circuit_count = context.count("|") // 3  # Each record has 3 pipes
        
        if is_count_only_query(prompt):
            return f"There are {circuit_count} circuits that match your request."
        else:
            if circuit_count == 0:
                return "No matching circuits found."
            
            # Reconstruct the table from context
            table_lines = [line.strip() for line in context.split("\n") if line.strip().startswith("|")]
            
            header = "| Invoice Number | Customer Name | Circuit ID |"
            separator = "|----------------|---------------|------------|"
            
            return (
                f"There are {circuit_count} matching circuits.\n\n"
                f"{header}\n"
                f"{separator}\n"
                + "\n".join(table_lines)
            )
            
    except Exception as e:
        logger.error(f"Error in mock_query_mistral: {str(e)}")
        return "An error occurred while processing your circuit request."

async def parse_filters_with_llm(user_query: str) -> Dict[str, Any]:
    """Mock version of filter parsing"""
    try:
        # Simple mock parsing - in a real scenario you'd want to implement proper NLP
        filters = {}
        
        # Check for invoice number pattern
        invoice_match = re.search(r"(?:invoice|inv)\s*(?:no|num|number)?\s*([A-Z0-9-]+)", user_query, re.IGNORECASE)
        if invoice_match:
            filters["invoice_number"] = invoice_match.group(1).strip()
        
        # Check for circuit ID pattern
        circuit_match = re.search(r"(?:circuit|circ)\s*(?:id)?\s*([A-Z0-9-]+)", user_query, re.IGNORECASE)
        if circuit_match:
            filters["circuit_id"] = circuit_match.group(1).strip()
        
        # Check for customer name
        cust_match = re.search(r"(?:customer|account)\s+(?:name)?\s*([a-z0-9\s&.,'-]+)", user_query, re.IGNORECASE)
        if cust_match:
            filters["account_name"] = cust_match.group(1).strip().title()
            
        logger.debug(f"Mock parsed circuit filters: {filters}")
        return filters
        
    except Exception as e:
        logger.error(f"Error in mock parse_filters_with_llm: {str(e)}")
        return {}

def normalize_filters(raw_filters: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}
    for raw_key, value in raw_filters.items():
        key = FIELD_ALIASES.get(raw_key.strip().lower(), raw_key.strip().lower())
        if value is not None:
            normalized[key] = value
    logger.debug(f"Normalized circuit filters: {normalized}")
    return normalized

async def process_count_response(filtered_metas: list) -> str:
    try:
        summary = f"There are {len(filtered_metas)} circuits that match your request."
        logger.info(f"Generated circuit count response: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error in process_count_response: {str(e)}")
        raise

async def process_detail_response(filtered_metas: list, user_query: str) -> str:
    try:
        all_rows = []
        for i in range(0, len(filtered_metas), config.CHUNK_SIZE):
            chunk_metas = filtered_metas[i:i+config.CHUNK_SIZE]
            logger.info(f"Processing circuit chunk {i+1}/{(len(filtered_metas) + config.CHUNK_SIZE - 1) // config.CHUNK_SIZE}")
            
            context = "\n".join(
                f"| {meta.get('invoice_number')} | {meta.get('account_name')} | {meta.get('circuit_id')} |"
                for meta in chunk_metas
            )
            
            prompt = f"""You are CircuitGPT, an intelligent assistant that helps users query structured circuit data.

### Circuit Records:
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
                if line.startswith("|") and line.count("|") >= 3
                and "Invoice Number" not in line and "---" not in line
            ]
            all_rows.extend(valid_chunk_rows)

        if all_rows:
            header = "| Invoice Number | Customer Name | Circuit ID |"
            separator = "|----------------|---------------|------------|"
            final_output = [header, separator] + all_rows
            friendly_intro = f"I found {len(all_rows)} matching circuit records. Here's the detailed list:\n\n"
            return friendly_intro + "\n".join(final_output)
        return "No matching circuits found."
    except Exception as e:
        logger.error(f"Error in process_detail_response: {str(e)}")
        raise

@app.post("/query")
async def query_circuit_data(request: CircuitQueryRequest):
    """Query endpoint for circuit data"""
    try:
        start_time = datetime.now()
        logger.info(f"Starting mock circuit query processing for: {request.query}")
        
        count_mode = request.count_only or is_count_only_query(request.query)
        logger.info(f"Count mode: {count_mode}")

        # Parse and normalize filters
        raw_filters = await parse_filters_with_llm(request.query)
        if not raw_filters:
            logger.warning("No filters could be parsed from the circuit query")
            return JSONResponse(
                content={"response": "Could not extract any filters from your query. Please try rephrasing."},
                status_code=400
            )
            
        filters = normalize_filters(raw_filters)
        logger.info(f"Using circuit filters: {filters}")

        # Apply filters to mock data
        filtered_metas = []
        for meta in mock_circuit_data:
            match = True
            for k, v in filters.items():
                meta_val = str(meta.get(k, "")).lower()
                filter_val = str(v).lower()
                if filter_val not in meta_val:
                    match = False
                    break
            if match:
                filtered_metas.append(meta)

        logger.info(f"Filtered down to {len(filtered_metas)} matching circuit records")

        if not filtered_metas:
            logger.info("No matching circuits found after filtering")
            return JSONResponse(
                content={"response": "No matching circuits found."},
                status_code=404
            )

        if count_mode:
            response = await process_count_response(filtered_metas)
        else:
            response = await process_detail_response(filtered_metas, request.query)

        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Circuit query processed successfully in {processing_time:.2f} seconds")
        
        return JSONResponse(content={"response": response})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing circuit query: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing circuit query")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if not isinstance(mock_circuit_data, list):
            raise Exception("Mock data not initialized properly")
        return JSONResponse(content={"status": "healthy"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/reset_mock_data")
async def reset_mock_data():
    """Endpoint to reset mock data (for testing)"""
    global mock_circuit_data
    try:
        if os.path.exists(config.MOCK_DATA_PATH):
            with open(config.MOCK_DATA_PATH, 'r') as f:
                mock_circuit_data = json.load(f)
        else:
            mock_circuit_data = [
                {
                    "invoice_number": "INV-2023-001",
                    "account_name": "Acme Corp",
                    "circuit_id": "CIRC-001",
                    "account_number": "ACME-001",
                    "date": "2023-01-15"
                },
                {
                    "invoice_number": "INV-2023-002",
                    "account_name": "Globex Inc",
                    "circuit_id": "CIRC-002",
                    "account_number": "GLOBEX-001",
                    "date": "2023-02-20"
                },
                {
                    "invoice_number": "INV-2023-003",
                    "account_name": "Acme Corp",
                    "circuit_id": "CIRC-003",
                    "account_number": "ACME-002",
                    "date": "2023-03-10"
                }
            ]
        return JSONResponse(content={"status": "success", "count": len(mock_circuit_data)})
    except Exception as e:
        logger.error(f"Failed to reset mock data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset mock circuit data")

# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host="0.0.0.0",
#         port=8001,  # Different port than invoice API
#         log_config=None,
#         access_log=False
#     )

if __name__ == "__main__":
    uvicorn.run(
        "circuit_query_mockapi:app",  # Use module string syntax
        host="0.0.0.0",
        port=8001,
        reload=True  # Ensures changes take effect
    )