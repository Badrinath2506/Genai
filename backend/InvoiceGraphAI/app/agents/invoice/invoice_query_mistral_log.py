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
from typing import Optional, Dict, List, Any
import sys
import json
import os
from pathlib import Path

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
persist_dir = r"C:\Badri\IPC\GenAIPOC\genai_app\vector_stores\invoice_vector_store\chroma\chroma.sqlite3"
ollama_api_url = "http://localhost:11434/api/generate"
ollama_model = "mistral"
chunk_size = 5
warning_threshold = 200

# Configure logging properly
def configure_logging():
    """Configure robust logging with file rotation and proper paths"""
    logger = logging.getLogger("invoice_api")
    logger.setLevel(logging.DEBUG)
    
    # Create log directory in a reliable location
    log_dir = Path(os.environ.get('TEMP', '.')) / "invoice_logs"
    try:
        log_dir.mkdir(exist_ok=True, mode=0o777)
    except Exception as e:
        logger.warning(f"Could not create log directory: {e}")
        log_dir = Path('.')  # Fallback to current directory

    log_file = log_dir / "invoice_query.log"
    
    # Clear previous log handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler with rotation (10MB per file, keep 3 backups)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Configure third-party loggers
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured. Log file: {log_file}")
    return logger

logger = configure_logging()

# Pydantic models (unchanged)
class QueryRequest(BaseModel):
    query: str
    include_details: Optional[bool] = True
    max_results: Optional[int] = 100

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

# Database initialization with error handling
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

# [Rest of your existing code remains the same...]

if __name__ == "__main__":
    try:
        import uvicorn
        logger.info("Starting Invoice Query API server")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)