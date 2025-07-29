from typing import List, Optional
from ..models.response import IntegratedResponse, CircuitData, InvoiceData
from ..services.logger import logger

class ResponseIntegrator:
    async def integrate_responses(
        self,
        circuits: Optional[List[CircuitData]] = None,
        invoices: Optional[List[InvoiceData]] = None,
        related_invoices: Optional[List[InvoiceData]] = None,
        related_circuits: Optional[List[CircuitData]] = None
    ) -> IntegratedResponse:
        """Combine all data into a single integrated response"""
        try:
            logger.app_logger.debug("Integrating responses from multiple sources")
            
            # Create the base response
            response = IntegratedResponse()
            
            # Add direct results
            if circuits:
                response.circuits = circuits
            if invoices:
                response.invoices = invoices
            
            # Add related data if available
            if related_invoices:
                response.related_invoices = related_invoices
            elif circuits:
                # If we have circuits but no related invoices, fetch them
                response.related_invoices = await circuit_agent.get_related_invoices(circuits)
            
            if related_circuits:
                response.related_circuits = related_circuits
            elif invoices:
                # If we have invoices but no related circuits, fetch them
                response.related_circuits = await invoice_agent.get_related_circuits(invoices)
            
            logger.app_logger.info("Successfully integrated responses")
            return response
            
        except Exception as e:
            logger.log_error(e, "Response integration failed")
            raise

response_integrator = ResponseIntegrator()