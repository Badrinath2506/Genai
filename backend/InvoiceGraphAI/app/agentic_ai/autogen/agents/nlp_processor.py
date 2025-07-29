from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from agentic_ai.autogen.models.query_models import QueryResponse
from agentic_ai.autogen.utils.logger import logger

class NLPProcessor:
    def __init__(self):
        self.logger = logger
    
    async def process_response(self, response: QueryResponse) -> Dict[str, Any]:
        """Convert raw API responses into natural language with JSON structure"""
        try:
            if not response.success or not response.response:
                return {
                    "status": "error",
                    "message": "No data available",
                    "data": None
                }
            
            # Initialize response structure
            nl_response = {
                "summary": "",
                "details": {},
                "related_info": {}
            }
            
            # Process main response data
            if "circuits" in response.response:
                circuits = response.response["circuits"]
                
                if isinstance(circuits, list):
                    if circuits and "count" in circuits[0]:
                        # Count response
                        nl_response["summary"] = circuits[0]["count"]
                    else:
                        # Detailed circuit response
                        nl_response["summary"] = f"Found {len(circuits)} circuit records"
                        nl_response["details"]["circuits"] = self._format_circuit_details(circuits)
                else:
                    nl_response["details"]["circuits"] = circuits
            
            if "invoices" in response.response:
                invoices = response.response["invoices"]
                
                if isinstance(invoices, list):
                    if invoices and "count" in invoices[0]:
                        # Count response
                        nl_response["summary"] = invoices[0]["count"]
                    else:
                        # Detailed invoice response
                        nl_response["summary"] = f"Found {len(invoices)} invoice records"
                        nl_response["details"]["invoices"] = self._format_invoice_details(invoices)
                else:
                    nl_response["details"]["invoices"] = invoices
            
            # Process related entities if present
            if response.related_entities:
                if "invoices" in response.related_entities:
                    related_invoices = response.related_entities["invoices"]
                    nl_response["related_info"]["invoices"] = self._format_invoice_details(related_invoices)
                    nl_response["summary"] += f" (with {len(related_invoices)} related invoices)"
                
                if "circuits" in response.related_entities:
                    related_circuits = response.related_entities["circuits"]
                    nl_response["related_info"]["circuits"] = self._format_circuit_details(related_circuits)
                    nl_response["summary"] += f" (with {len(related_circuits)} related circuits)"
            
            # If we only have a count response, make it the main message
            if "count" in nl_response.get("summary", ""):
                nl_response["message"] = nl_response.pop("summary")
            
            return {
                "status": "success",
                "response": nl_response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing NLP response: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to process response",
                "error": str(e)
            }
    
    def _format_circuit_details(self, circuits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format circuit details for response"""
        return [
            {
                "circuit_id": circuit.get("circuit_id", "N/A"),
                "invoice_number": circuit.get("invoice_number", "N/A"),
                "account_name": circuit.get("account_name", "N/A"),
                "account_number": circuit.get("account_number", "N/A"),
                "date": circuit.get("date", "N/A")
            }
            for circuit in circuits
        ]
    
    def _format_invoice_details(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format invoice details for response"""
        return [
            {
                "invoice_number": invoice.get("invoice_number", "N/A"),
                "account_name": invoice.get("account_name", "N/A"),
                "date": invoice.get("date", "N/A"),
                "amount": invoice.get("amount", "N/A"),
                "currency": invoice.get("currency", "N/A"),
                "customer": invoice.get("customer", "N/A"),
                "bill_account": invoice.get("bill_account", "N/A")
            }
            for invoice in invoices
        ]