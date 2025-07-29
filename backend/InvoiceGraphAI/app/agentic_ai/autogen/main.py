from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging

from agentic_ai.autogen.models.query_models import QueryRequest
from agentic_ai.autogen.agents.query_agent import QueryDecisionAgent
from agentic_ai.autogen.agents.nlp_processor import NLPProcessor
from agentic_ai.autogen.utils.logger import logger

app = FastAPI(
    title="Circuit & Invoice Query System",
    description="Intelligent query system for circuit and invoice data with agentic behavior",
    version="1.0.0"
)

class UserQuery(BaseModel):
    prompt: str
    session_id: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Circuit & Invoice Query System")

@app.post("/query")
async def handle_query(user_query: UserQuery):
    """Main query endpoint"""
    try:
        # Log the incoming prompt
        logger.log_prompt(user_query.prompt, user_query.session_id)
        
        # Initialize components
        query_agent = QueryDecisionAgent()
        nlp_processor = NLPProcessor()
        
        # Extract entities and intent
        extraction = await query_agent.extract_entities(user_query.prompt)
        
        # Decide which APIs to query
        query_circuit, query_invoice = await query_agent.decide_query_targets(extraction)
        
        # Execute queries
        query_response = await query_agent.execute_queries(
            query_circuit,
            query_invoice,
            extraction.entities,
            extraction.is_count_query
        )
        
        # Process through NLP layer
        nl_response = await nlp_processor.process_response(query_response)
        
        # Log the response
        logger.log_response(user_query.prompt, nl_response, user_query.session_id)
        
        return JSONResponse(content=nl_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your query"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # TODO: Add actual health checks for dependencies
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Module path syntax
        host="0.0.0.0",
        port=9002,
        reload=True,          # Auto-reload on code changes
        log_level="debug",   # Detailed logs
        workers=1            # Good for development
    )