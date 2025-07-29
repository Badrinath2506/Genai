from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agentic_ai.autogen.agents.clients.api_client import BaseAPIClient
from agentic_ai.autogen.config import config
from agentic_ai.autogen.utils.logger import logger

class InvoiceQuery(BaseModel):
    filters: Dict[str, Any]
    count_only: bool = False

class InvoiceClient(BaseAPIClient):
    def __init__(self):
        super().__init__(config.INVOICE_API_URL)
    
    async def query_invoices(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query invoice data from mock API"""
        try:
            # Validate query
            query_model = InvoiceQuery(**query)
            
            # Make API request
            response = await self._make_request(
                "POST",
                "/query",
                {
                    "query": self._build_query_string(query_model.filters),
                    "count_only": query_model.count_only
                }
            )
            
            # Process response
            if query_model.count_only:
                return [{"count": response.get("response", "0")}]
            
            # For detailed responses, we need to parse the table format
            return self._parse_invoice_response(response.get("response", ""))
            
        except Exception as e:
            logger.error(f"Error querying invoice data: {str(e)}")
            raise
    
    def _build_query_string(self, filters: Dict[str, Any]) -> str:
        """Build a natural language query string from filters"""
        parts = []
        for field, value in filters.items():
            if field == "invoice_number":
                parts.append(f"invoice number {', '.join(value)}")
            elif field == "account_name":
                parts.append(f"account name {', '.join(value)}")
            elif field == "date":
                parts.append(f"date {', '.join(value)}")
        
        return " and ".join(parts) if parts else "Show all invoices"
    
    def _parse_invoice_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the table-formatted invoice response into structured data"""
        invoices = []
        
        if not response_text or "No matching invoices found" in response_text:
            return invoices
        
        # Split into lines and find the table data
        lines = [line.strip() for line in response_text.split("\n") if line.strip()]
        
        # Find the start of the table (after header and separator)
        try:
            table_start = 0
            for i, line in enumerate(lines):
                if line.startswith("| Invoice Number |"):
                    table_start = i + 2  # Skip header and separator
                    break
            
            # Process each table row
            for line in lines[table_start:]:
                if not line.startswith("|"):
                    continue
                
                # Split by pipe and strip whitespace
                parts = [part.strip() for part in line.split("|")[1:-1]]
                if len(parts) >= 5:
                    invoices.append({
                        "invoice_number": parts[0],
                        "account_name": parts[1],
                        "date": parts[2],
                        "amount": parts[3],
                        "currency": parts[4]
                    })
        except Exception as e:
            logger.error(f"Error parsing invoice response: {str(e)}")
            raise
        
        return invoices