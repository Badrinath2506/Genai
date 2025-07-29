from typing import List, Dict, Optional
from ..models.response import CircuitData, InvoiceData
from ..services.api_client import api_client
from ..services.logger import logger

class CircuitAgent:
    async def query_circuits(self, query: str, invoice_numbers: Optional[List[str]] = None) -> List[CircuitData]:
        """Query circuit data with optional invoice number filter"""
        try:
            # Build the query
            if invoice_numbers:
                query_parts = [f"invoice_number:{inv}" for inv in invoice_numbers]
                full_query = " OR ".join(query_parts)
                if query.strip():
                    full_query = f"({full_query}) AND ({query})"
            else:
                full_query = query
            
            logger.app_logger.debug(f"Executing circuit query: {full_query}")
            
            # Execute query
            response = await api_client.query_circuit(full_query)
            circuits = [CircuitData(**item) for item in response.get("data", [])]
            
            logger.app_logger.info(f"Found {len(circuits)} matching circuits")
            return circuits
            
        except Exception as e:
            logger.log_error(e, "Circuit query failed")
            raise
    
    async def get_related_invoices(self, circuit_data: List[CircuitData]) -> List[InvoiceData]:
        """Get invoices related to these circuits"""
        try:
            if not circuit_data:
                return []
                
            invoice_numbers = list(set(circuit.invoice_number for circuit in circuit_data))
            query = " OR ".join(f"invoice_number:{inv}" for inv in invoice_numbers)
            
            logger.app_logger.debug(f"Fetching related invoices for circuits: {query}")
            
            response = await api_client.query_invoice(query, count_only=False)
            invoices = [InvoiceData(**item) for item in response.get("data", [])]
            
            logger.app_logger.info(f"Found {len(invoices)} related invoices")
            return invoices
            
        except Exception as e:
            logger.log_error(e, "Failed to fetch related invoices")
            raise

circuit_agent = CircuitAgent()