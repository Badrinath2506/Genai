import httpx
from typing import Dict, Any
import json
from ..models.response import CircuitData, InvoiceData
from ..config import config
from ..services.logger import logger

class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient()
    
    async def query_circuit(self, query: str, count_only: bool = False) -> Dict[str, Any]:
        """Execute circuit query"""
        try:
            payload = {"query": query, "count_only": count_only}
            response = await self.client.post(config.CIRCUIT_API_URL, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.log_error(e, f"Circuit API query failed for: {query}")
            raise
        except Exception as e:
            logger.log_error(e, "Unexpected error in circuit query")
            raise
    
    async def query_invoice(self, query: str, count_only: bool = False) -> Dict[str, Any]:
        """Execute invoice query"""
        try:
            payload = {"query": query, "count_only": count_only}
            response = await self.client.post(config.INVOICE_API_URL, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.log_error(e, f"Invoice API query failed for: {query}")
            raise
        except Exception as e:
            logger.log_error(e, "Unexpected error in invoice query")
            raise
    
    async def close(self):
        await self.client.aclose()

api_client = APIClient()