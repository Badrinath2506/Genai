from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from agentic_ai.autogen.models.query_models import QueryRequest
from agentic_ai.autogen.agents.query_agent import QueryDecisionAgent
from agentic_ai.autogen.agents.nlp_processor import NLPProcessor
from agentic_ai.autogen.utils.logger import logger

query_agent = QueryDecisionAgent()
nlp_processor = NLPProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    logger.info("Starting Circuit & Invoice Query System")
    yield
    # Optional: shutdown code here

app = FastAPI(
    title="Circuit & Invoice Query System",
    description="Intelligent query system for circuit and invoice data with agentic behavior",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/query")
async def handle_query(user_query: QueryRequest):
    try:

        import pdb;pdb.set_trace();
        
        logger.log_prompt(user_query.prompt, user_query.session_id)

        extraction = await query_agent.extract_entities(user_query.prompt)
        # Pass original prompt for intent decisions if needed
        query_circuit, query_invoice = await query_agent.decide_query_targets(extraction)

        query_response = await query_agent.execute_queries(
            query_circuit,
            query_invoice,
            extraction.entities,
            extraction.is_count_query
        )

        nl_response = await nlp_processor.process_response(query_response)

        logger.log_response(user_query.prompt, nl_response, user_query.session_id)

        return JSONResponse(content=nl_response)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your query")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentic_ai.autogen.main:app", host="0.0.0.0", port=9002, reload=True)
