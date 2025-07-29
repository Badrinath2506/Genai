from typing import Dict, Any, Optional, List
import httpx
import logging
from pydantic import BaseModel

from agentic_ai.autogen.config import config
from agentic_ai.autogen.utils.logger import logger

class BaseAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=config.API_TIMEOUT)
        self.logger = logger
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generic request method"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            self.logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == "GET":
                response = await self.client.get(url)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"API request failed with status {e.response.status_code}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error making API request: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = await self._make_request("GET", "/health")
            return response.get("status") == "healthy"
        except Exception:
            return False