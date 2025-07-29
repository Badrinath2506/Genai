import re
from typing import Dict, List
from ..models.response import QueryAnalysis
from ..services.logger import logger

class QueryAnalyzer:
    def analyze(self, prompt: str) -> QueryAnalysis:
        """Determine what type of query this is and extract entities"""
        try:
            logger.log_prompt(prompt)
            
            # Normalize the prompt for analysis
            normalized = prompt.lower().strip()
            
            # Initialize analysis result
            analysis = QueryAnalysis(
                query_type="both" if "both" in normalized else "invoice",
                entities={},
                requires_related=False
            )
            
            # Check for explicit circuit queries
            circuit_keywords = ["circuit", "network id", "circuit id"]
            if any(kw in normalized for kw in circuit_keywords):
                analysis.query_type = "circuit"
            
            # Extract invoice numbers
            invoice_nos = self._extract_invoice_numbers(prompt)
            if invoice_nos:
                analysis.entities["invoice_numbers"] = invoice_nos
                # If query has invoice numbers but no circuit keywords, it's likely invoice query
                if analysis.query_type != "circuit":
                    analysis.query_type = "invoice"
                else:
                    analysis.requires_related = True
            
            # Extract circuit IDs
            circuit_ids = self._extract_circuit_ids(prompt)
            if circuit_ids:
                analysis.entities["circuit_ids"] = circuit_ids
                analysis.query_type = "circuit"
                analysis.requires_related = True
            
            # Extract customer names
            customers = self._extract_customers(prompt)
            if customers:
                analysis.entities["customers"] = customers
            
            logger.app_logger.debug(f"Query analysis: {analysis}")
            return analysis
            
        except Exception as e:
            logger.log_error(e, "Query analysis failed")
            raise
    
    def _extract_invoice_numbers(self, text: str) -> List[str]:
        """Extract invoice numbers from text"""
        pattern = r"\b(?:invoice|inv)[\s-]*(?:no|num|number)?[\s-]*([A-Z]{2,}-?\d{3,}-?\d{3,})\b"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches))  # Remove duplicates
    
    def _extract_circuit_ids(self, text: str) -> List[str]:
        """Extract circuit IDs from text"""
        pattern = r"\b(?:circuit|circ)[\s-]*(?:id)?[\s-]*([A-Z]{2,}-?\d{3,})\b"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches))
    
    def _extract_customers(self, text: str) -> List[str]:
        """Extract customer names from text"""
        pattern = r"(?:customer|account)\s+(?:name)?\s*([a-z0-9\s&.,'-]+)(?=\s+(?:circuit|invoice|for|on|$))"
        matches = re.findall(pattern, text.lower())
        return [m.strip().title() for m in set(matches)]

query_analyzer = QueryAnalyzer()