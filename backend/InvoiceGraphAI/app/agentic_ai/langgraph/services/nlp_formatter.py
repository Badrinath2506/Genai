from typing import Dict, Any
from ..models.response import IntegratedResponse, NLPResponse
from ..services.logger import logger

class NLPFormatter:
    def format_response(self, raw_response: IntegratedResponse, original_query: str) -> NLPResponse:
        """Convert raw data into natural language response"""
        try:
            logger.app_logger.debug("Formatting response with NLP")
            
            # Generate natural language summary
            nl_response = self._generate_natural_language(raw_response)
            
            # Create structured response
            structured = {
                "natural_language": nl_response,
                "structured_data": raw_response.dict(),
                "source_queries": [original_query]
            }
            
            logger.app_logger.info("Successfully formatted NLP response")
            return NLPResponse(**structured)
            
        except Exception as e:
            logger.log_error(e, "NLP formatting failed")
            raise
    
    def _generate_natural_language(self, data: IntegratedResponse) -> str:
        """Generate human-readable response from integrated data"""
        parts = []
        
        # Handle circuit responses
        if data.circuits:
            if len(data.circuits) == 1:
                circuit = data.circuits[0]
                parts.append(f"I found circuit {circuit.circuit_id} for account {circuit.account_name}.")
            else:
                parts.append(f"I found {len(data.circuits)} matching circuits.")
        
        # Handle invoice responses
        if data.invoices:
            if len(data.invoices) == 1:
                invoice = data.invoices[0]
                parts.append(f"I found invoice {invoice.invoice_number} for {invoice.account_name} amounting {invoice.amount} {invoice.currency}.")
            else:
                parts.append(f"I found {len(data.invoices)} matching invoices.")
        
        # Handle related invoices
        if data.related_invoices and data.circuits:
            if len(data.related_invoices) == 1:
                parts.append(f"The related invoice is {data.related_invoices[0].invoice_number}.")
            else:
                parts.append(f"There are {len(data.related_invoices)} related invoices.")
        
        # Handle related circuits
        if data.related_circuits and data.invoices:
            if len(data.related_circuits) == 1:
                parts.append(f"The invoice is associated with circuit {data.related_circuits[0].circuit_id}.")
            else:
                parts.append(f"The invoices are associated with {len(data.related_circuits)} circuits.")
        
        if not parts:
            return "No matching data found for your query."
        
        return " ".join(parts)

nlp_formatter = NLPFormatter()