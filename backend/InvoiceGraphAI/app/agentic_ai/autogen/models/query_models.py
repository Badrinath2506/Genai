from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    prompt: str = Field(..., description="User's natural language query")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")

class EntityExtraction(BaseModel):
    entities: Dict[str, List[str]] = Field(..., description="Extracted entities from prompt")
    intent: str = Field(..., description="Detected intent of the query")
    is_count_query: bool = Field(False, description="Whether query is asking for a count")

class QueryResponse(BaseModel):
    success: bool = Field(..., description="Whether query was successful")
    response: Dict[str, Any] = Field(..., description="Formatted response data")
    related_entities: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None, 
        description="Related entities that were automatically fetched"
    )
    debug_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Debugging information for developers",
        exclude=True
    )