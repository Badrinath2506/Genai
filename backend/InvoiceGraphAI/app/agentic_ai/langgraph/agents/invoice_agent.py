from typing import List, Optional
from ..models.response import InvoiceData, CircuitData
from ..services.api_client import api_client
from ..services.logger import logger

class InvoiceAgent:
    async def query_invoices(self, query: str, invoice_numbers: Optional[List[str]] = None) -> List[InvoiceData]:
        """Query invoice data with optional invoice number filter"""
        try:
            # Build the query
            if invoice_numbers:
                query_parts = [f"invoice_number:{inv}" for inv in invoice_numbers]
                full_query = " OR ".join(query_parts)
                if query.strip():
                    full_query = f"({full_query}) AND ({query})"
            else:
                full_query = query
            
            logger.app_logger.debug(f"Executing invoice query: {full_query}")
            
            # Execute query
            response = await api_client.query_invoice(full_query)
            invoices = [InvoiceData(**item) for item in response.get("data", [])]
            
            logger.app_logger.info(f"Found {len(invoices)} matching invoices")
            return invoices
            
        except Exception as e:
            logger.log_error(e, "Invoice query failed")
            raise
    
    async def get_related_circuits(self, invoice_data: List[InvoiceData]) -> List[CircuitData]:
        """Get circuits related to these invoices"""
        try:
            if not invoice_data:
                return []
                
            invoice_numbers = list(set(invoice.invoice_number for invoice in invoice_data))
            query = " OR ".join(f"invoice_number:{inv}" for inv in invoice_numbers)
            
            logger.app_logger.debug(f"Fetching related circuits for invoices: {query}")
            
            response = await api_client.query_circuit(query, count_only=False)
            circuits = [CircuitData(**item) for item in response.get("data", [])]
            
            logger.app_logger.info(f"Found {len(circuits)} related circuits")
            return circuits
            
        except Exception as e:
            logger.log_error(e, "Failed to fetch related circuits")
            raise

invoice_agent = InvoiceAgent()