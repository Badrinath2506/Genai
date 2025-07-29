from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

from agentic_ai.autogen.models.query_models import EntityExtraction, QueryResponse
from agentic_ai.autogen.utils.logger import logger
from agentic_ai.autogen.agents.clients.circuit_client import CircuitClient
from agentic_ai.autogen.agents.clients.invoice_client import InvoiceClient


class QueryDecisionAgent:
    def __init__(self):
        self.circuit_client = CircuitClient()
        self.invoice_client = InvoiceClient()

    async def extract_entities(self, prompt: str) -> EntityExtraction:
        """Extract entities and intent from user prompt"""
        try:
            normalized_prompt = prompt.lower().strip()

            # Initialize entities dictionary
            entities = {
                "invoice_numbers": [],
                "circuit_ids": [],
                "account_names": [],
                "dates": [],
                "customers": []
            }

            # Extract invoice numbers
            invoice_matches = re.finditer(
                r"(?:invoice|inv)\s*(?:no|num|number)?\s*([A-Za-z0-9-]+)",
                prompt,
                re.IGNORECASE
            )
            entities["invoice_numbers"] = [m.group(1).upper() for m in invoice_matches]

            # Extract circuit IDs
            circuit_matches = re.finditer(
                r"(?:circuit|circ)\s*(?:id)?\s*([A-Za-z0-9-]+)",
                prompt,
                re.IGNORECASE
            )
            entities["circuit_ids"] = [m.group(1).upper() for m in circuit_matches]

            # Extract account names
            account_matches = re.finditer(
                r"(?:account|customer)\s+(?:name)?\s*([A-Za-z0-9\s&.,'-]+)",
                prompt,
                re.IGNORECASE
            )
            entities["account_names"] = [m.group(1).strip().title() for m in account_matches]

            # Extract dates - grouped correctly
            date_matches = re.finditer(
                r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b",
                prompt
            )
            for m in date_matches:
                date_str = m.group(1)
                try:
                    if '/' in date_str:
                        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                    else:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    entities["dates"].append(date_obj.strftime("%Y-%m-%d"))
                except ValueError:
                    # Skip invalid dates
                    continue

            # Detect if the query is a count query
            is_count_query = any(
                kw in normalized_prompt
                for kw in ["count", "how many", "number of", "total"]
            )

            # Detect intent properly
            if any(kw in normalized_prompt for kw in ["invoice", "billing", "payment"]):
                intent = "invoice"
            elif any(kw in normalized_prompt for kw in ["circuit", "network", "connection"]):
                intent = "circuit"
            else:
                intent = "unknown"

            return EntityExtraction(
                entities=entities,
                intent=intent,
                is_count_query=is_count_query
            )

        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise

    async def decide_query_targets(self, extraction: EntityExtraction, prompt: Optional[str] = None) -> Tuple[bool, bool]:
        """Decide whether to query circuits, invoices, or both"""

        query_circuit = False
        query_invoice = False

        # Use prompt string if provided for extra checks
        prompt_lower = prompt.lower() if prompt else ""

        if extraction.intent == "circuit":
            query_circuit = True
            # If we have invoice numbers in a circuit query, fetch invoices too
            if extraction.entities.get("invoice_numbers"):
                query_invoice = True
        elif extraction.intent == "invoice":
            query_invoice = True
            # For invoice queries, fetch circuits only if explicitly asked in prompt
            if "circuit" in extraction.entities or "with circuit" in prompt_lower:
                query_circuit = True
        else:
            # Default to both if intent is unclear
            query_circuit = True
            query_invoice = True

        return query_circuit, query_invoice

    async def execute_queries(
        self,
        query_circuit: bool,
        query_invoice: bool,
        entities: Dict[str, List[str]],
        is_count_query: bool
    ) -> QueryResponse:
        """Execute the appropriate queries based on decision"""
        try:
            circuit_results = []
            invoice_results = []
            related_entities = {}

            # Query circuits if needed
            if query_circuit:
                circuit_query = {
                    "count_only": is_count_query,
                    "filters": {}
                }

                if entities.get("circuit_ids"):
                    circuit_query["filters"]["circuit_id"] = entities["circuit_ids"]
                if entities.get("invoice_numbers"):
                    circuit_query["filters"]["invoice_number"] = entities["invoice_numbers"]
                if entities.get("account_names"):
                    circuit_query["filters"]["account_name"] = entities["account_names"]

                circuit_results = await self.circuit_client.query_circuits(circuit_query)

                # Fetch related invoices if circuits found and not a count query
                if not is_count_query and circuit_results:
                    invoice_numbers = list({
                        circuit["invoice_number"]
                        for circuit in circuit_results
                        if "invoice_number" in circuit
                    })
                    if invoice_numbers and not query_invoice:
                        invoice_query = {
                            "count_only": False,
                            "filters": {"invoice_number": invoice_numbers}
                        }
                        related_invoices = await self.invoice_client.query_invoices(invoice_query)
                        if related_invoices:
                            related_entities["invoices"] = related_invoices

            # Query invoices if needed
            if query_invoice:
                invoice_query = {
                    "count_only": is_count_query,
                    "filters": {}
                }

                if entities.get("invoice_numbers"):
                    invoice_query["filters"]["invoice_number"] = entities["invoice_numbers"]
                if entities.get("account_names"):
                    invoice_query["filters"]["account_name"] = entities["account_names"]
                if entities.get("dates"):
                    invoice_query["filters"]["date"] = entities["dates"]

                invoice_results = await self.invoice_client.query_invoices(invoice_query)

                # Fetch related circuits if invoices found and not a count query
                if not is_count_query and invoice_results:
                    invoice_numbers = list({
                        invoice["invoice_number"]
                        for invoice in invoice_results
                        if "invoice_number" in invoice
                    })
                    if invoice_numbers and not query_circuit:
                        circuit_query = {
                            "count_only": False,
                            "filters": {"invoice_number": invoice_numbers}
                        }
                        related_circuits = await self.circuit_client.query_circuits(circuit_query)
                        if related_circuits:
                            related_entities["circuits"] = related_circuits

            # Build the response dictionary
            response_data = {}
            if circuit_results:
                response_data["circuits"] = circuit_results
            if invoice_results:
                response_data["invoices"] = invoice_results

            return QueryResponse(
                success=True,
                response=response_data,
                related_entities=related_entities if related_entities else None
            )

        except Exception as e:
            logger.error(f"Error executing queries: {str(e)}")
            raise
