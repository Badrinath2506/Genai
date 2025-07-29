# AGENT MOCKAPIS 
http://localhost:9002/docs 

## INVOICE
-- uvicorn agents.mockapis.invoice_mock_query_api:app --reload
-- uvicorn agents.mockapis.invoice_mock_query_api:app --port 8001 --host 0.0.0.0 --reload
# AGENTIC 
## Autogen
--  uvicorn agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0 --reload
--  uvicorn agentic_ai.autogen.main1:app --reload --port 9002

## Langgraph 
-- uvicorn agentic_ai.langgraph.main:app --reload --port 9003 --reload



# EXECUTE 
-- pip install python-json-logger 
-- pip install httpx
-- conda deactivate
-- pip install fastapi uvicorn httpx python-dotenv python-json-logger