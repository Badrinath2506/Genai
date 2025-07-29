import chromadb
import asyncio
import aiohttp
import logging
import re
import traceback
from collections import defaultdict
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import genai_app.config.config_path as circuitConfig
from typing import Optional, Dict, List, Any
import sys
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

# Initialize FastAPI app
app = FastAPI(title="Invoice Query Engine API",
              description="API for querying invoice data with natural language processing")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIG
persist_dir =  r"C:\Badri\IPC\GenAIPOC\genai_app\vector_stores\invoice_vector_store\chroma\chroma.sqlite3"
log_file_path = r"C:\Badri\IPC\GenAIPOC\genai_app\agents\invoice_agent\query\logs"

# HuggingFace Model Configuration
HF_MODEL_NAME = "google/flan-t5-large"  # Default model, can be changed to any suitable model
HF_MODEL_CACHE_DIR = "./model_cache"
MAX_MODEL_INPUT_LENGTH = 1024  # For most models
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Configure logging (same as before)
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)

def configure_logging():
    logger = logging.getLogger("invoice_api")
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    
    return logger

logger = configure_logging()

# Pydantic models (same as before)
class QueryRequest(BaseModel):
    query: str
    include_details: Optional[bool] = True
    max_results: Optional[int] = 100
    model_name: Optional[str] = None  # Allow model selection per request

class InvoiceItem(BaseModel):
    invoice_number: str
    customer_name: str
    date: str
    amount: float
    currency: str

class QueryResponse(BaseModel):
    success: bool
    count: int
    total_amount: Optional[Dict[str, float]] = None
    invoices: Optional[List[InvoiceItem]] = None
    summary: str
    error: Optional[str] = None
    error_details: Optional[str] = None
    model_used: Optional[str] = None

# Model Loader with caching
class HuggingFaceModel:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.models = {}
            cls._instance.tokenizers = {}
        return cls._instance
    
    def get_model(self, model_name: str = HF_MODEL_NAME):
        if model_name not in self.models:
            try:
                logger.info(f"Loading model: {model_name}")
                
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir=HF_MODEL_CACHE_DIR
                )
                
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    cache_dir=HF_MODEL_CACHE_DIR,
                    device_map="auto" if DEVICE == "cuda" else None,
                    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
                )
                
                self.tokenizers[model_name] = tokenizer
                self.models[model_name] = model
                logger.info(f"Successfully loaded model: {model_name}")
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}", exc_info=True)
                raise RuntimeError(f"Model loading failed: {str(e)}")
        
        return self.models[model_name], self.tokenizers[model_name]

# Initialize model
try:
    hf_model = HuggingFaceModel()
    default_model, default_tokenizer = hf_model.get_model()
    logger.info(f"Default model loaded: {HF_MODEL_NAME} on {DEVICE}")
except Exception as e:
    logger.critical("Failed to initialize model", exc_info=True)
    sys.exit(1)

# Database initialization (same as before)
def initialize_database():
    try:
        logger.info("Initializing ChromaDB client")
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        collection = chroma_client.get_or_create_collection(name="invoice_collection")
        logger.info("Database initialized successfully")
        return collection
    except Exception as e:
        logger.critical(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise RuntimeError(f"Database initialization failed: {str(e)}")

try:
    collection = initialize_database()
except Exception as e:
    logger.error("Application cannot start without database connection")
    sys.exit(1)

# Prompt Builder (updated for better model compatibility)
def build_prompt(context: str, user_query: str) -> str:
    return f"""
INVOICE QUERY TASK:
Answer the user's question about invoices based EXACTLY on the provided records.
Only use information from the records below.

USER QUESTION: {user_query}

INVOICE RECORDS:
{context}

INSTRUCTIONS:
1. If asked for counts, respond with just the number and context.
2. If asked for details, provide a clear table with Invoice Number, Customer Name, Date, Amount, Currency.
3. Never invent information not present in the records.
4. For date ranges, be precise about what's included.

RESPONSE:
"""

# Query HuggingFace Model
async def query_huggingface(
    prompt: str,
    model_name: str = HF_MODEL_NAME,
    max_length: int = 200,
    temperature: float = 0.7
) -> str:
    try:
        model, tokenizer = hf_model.get_model(model_name)
        
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_MODEL_INPUT_LENGTH
        ).to(DEVICE)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.debug(f"HF Model response: {response}")
        return response.strip()
    
    except Exception as e:
        logger.error(f"Error querying HuggingFace model: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Model query failed: {str(e)}"
        )

# Main query processing (updated for HF)
async def process_invoice_query(
    user_query: str,
    include_details: bool = True,
    model_name: str = HF_MODEL_NAME
) -> Dict[str, Any]:
    logger.info(f"Processing query with model {model_name}: '{user_query}'")
    response_data = {
        "success": False,
        "count": 0,
        "summary": "Error processing query",
        "error": None,
        "error_details": None,
        "model_used": model_name
    }

    try:
        # [Previous filtering code remains the same until the detailed processing part]
        
        if include_details and not count_mode:
            try:
                all_rows = []
                for i, (chunk_docs, chunk_metas) in enumerate(chunk_results(filtered_docs, filtered_metas, chunk_size)):
                    logger.info(f"Processing chunk {i+1} with model {model_name}")

                    context = "\n".join(
                        f"| {meta.get('invoice_number')} | {meta.get('customer')} | {meta.get('date')} | {meta.get('amount')} | {meta.get('currency')} |"
                        for meta in chunk_metas
                    )

                    prompt = build_prompt(context, user_query)
                    
                    # Use HF model instead of Mistral
                    chunk_response = await query_huggingface(prompt, model_name)
                    
                    # Process response
                    lines = chunk_response.strip().splitlines()
                    valid_chunk_rows = [
                        line.strip() for line in lines
                        if line.startswith("|") and line.count("|") >= 4 
                        and "Invoice Number" not in line and "---" not in line
                    ]

                    all_rows.extend(valid_chunk_rows)
                    logger.debug(f"Processed {len(valid_chunk_rows)} valid rows from chunk")

                if all_rows:
                    response_data["invoices"] = invoice_items
            except Exception as e:
                logger.error(f"Error processing detailed results: {str(e)}", exc_info=True)
                response_data["error"] = "Error processing detailed results"
                response_data["error_details"] = str(e)

        return response_data

    except Exception as e:
        logger.critical(f"Unexpected error in process_invoice_query: {str(e)}", exc_info=True)
        response_data.update({
            "error": "Unexpected processing error",
            "error_details": str(e)
        })
        return response_data

# API Endpoints (updated to support model selection)
@app.post("/query", response_model=QueryResponse)
async def query_invoices(request: QueryRequest):
    """
    Process natural language queries about invoices.
    Optionally specify a HuggingFace model name.
    """
    try:
        model_name = request.model_name or HF_MODEL_NAME
        logger.info(f"Starting query processing with model {model_name}")
        
        result = await process_invoice_query(
            request.query, 
            request.include_details,
            model_name
        )
        
        if request.max_results and "invoices" in result and result["invoices"]:
            result["invoices"] = result["invoices"][:request.max_results]
            original_count = result["count"]
            result["count"] = len(result["invoices"])
            result["summary"] = f"{result['summary']} Showing {len(result['invoices'])} of {original_count} matching invoices."
        
        logger.info(f"Query completed successfully with model {model_name}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "details": str(e)
            }
        )

# Additional endpoint for model management
@app.get("/models/available")
async def list_available_models():
    """List recommended models for this application"""
    return {
        "recommended_models": [
            "google/flan-t5-large",  # Good balance of size and capability
            "google/flan-t5-xl",     # More capable version
            "google/flan-ul2",       # Even larger, more powerful
            "bigscience/bloomz-7b1",  # Alternative model
            "facebook/bart-large-cnn" # Good for summarization
        ],
        "current_model": HF_MODEL_NAME,
        "device": DEVICE
    }

@app.post("/models/switch")
async def switch_model(new_model: str):
    """Switch to a different HuggingFace model"""
    try:
        logger.info(f"Attempting to switch to model: {new_model}")
        model, tokenizer = hf_model.get_model(new_model)
        global HF_MODEL_NAME
        HF_MODEL_NAME = new_model
        logger.info(f"Successfully switched to model: {new_model}")
        return {
            "success": True,
            "new_model": new_model,
            "device": DEVICE
        }
    except Exception as e:
        logger.error(f"Model switch failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Could not load model {new_model}: {str(e)}"
        )

# Health check with model status
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verify database connection
        collection.count()
        
        # Verify model
        model, tokenizer = hf_model.get_model()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "model": {
                "name": HF_MODEL_NAME,
                "status": "loaded",
                "device": DEVICE
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "service": "database" if "database" in str(e).lower() else "model"
            }
        )

if __name__ == "__main__":
    try:
        import uvicorn
        logger.info(f"Starting Invoice Query API server with model {HF_MODEL_NAME}")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)