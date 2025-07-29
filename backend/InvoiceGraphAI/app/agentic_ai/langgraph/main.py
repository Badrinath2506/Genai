from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from .services.api_client import api_client  # Update this import path based on your structure

from .models.response import NLPResponse
from .agents.query_analyzer import query_analyzer
from .agents.circuit_agent import circuit_agent
from .agents.invoice_agent import invoice_agent
from .services.response_integrator import response_integrator
from .services.nlp_formatter import nlp_formatter
from .services.logger import logger

app = FastAPI(
    title="Circuit & Invoice Query System",
    description="Integrated system for querying circuit and invoice data with NLP",
    version="1.0.0"
)

class UserQuery(BaseModel):
    query: str
    debug: Optional[bool] = False

@app.post("/query")
async def handle_query(request: UserQuery):
    """Main endpoint for processing user queries"""
    try:
        # Step 1: Analyze the query
        analysis = query_analyzer.analyze(request.query)
        
        # Step 2: Execute appropriate queries
        circuits, invoices = None, None
        
        if analysis.query_type in ["circuit", "both"]:
            circuits = await circuit_agent.query_circuits(
                request.query,
                analysis.entities.get("invoice_numbers")
            )
        
        if analysis.query_type in ["invoice", "both"]:
            invoices = await invoice_agent.query_invoices(
                request.query,
                analysis.entities.get("invoice_numbers")
            )
        
        # Step 3: Integrate responses
        integrated = await response_integrator.integrate_responses(
            circuits=circuits,
            invoices=invoices
        )
        
        # Step 4: Format with NLP
        formatted = nlp_formatter.format_response(integrated, request.query)
        
        # Step 5: Log the complete interaction
        logger.log_response(request.query, formatted.dict())
        
        # Return the response
        return JSONResponse(content=formatted.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(e, "Query processing failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    # Replace:
    # await api_client.close()
    # With:
    await app.state.api_client.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9003)