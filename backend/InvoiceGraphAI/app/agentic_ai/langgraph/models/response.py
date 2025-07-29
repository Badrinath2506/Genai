from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryAnalysis(BaseModel):
    query_type: str  # 'circuit', 'invoice', or 'both'
    entities: Dict[str, List[str]]
    requires_related: bool = False

class CircuitData(BaseModel):
    invoice_number: str
    account_name: str
    circuit_id: str
    account_number: str
    date: str

class InvoiceData(BaseModel):
    invoice_number: str
    account_name: str
    date: str
    amount: str
    currency: str

class IntegratedResponse(BaseModel):
    circuits: Optional[List[CircuitData]] = None
    invoices: Optional[List[InvoiceData]] = None
    related_invoices: Optional[List[InvoiceData]] = None
    related_circuits: Optional[List[CircuitData]] = None

class NLPResponse(BaseModel):
    natural_language: str
    structured_data: IntegratedResponse
    source_queries: List[str]