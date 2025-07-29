## Installation 
-- pip install fastapi uvicorn
--pip install chromadb

-- conda activate genaiworksapce_conda_env

## Circuit Agents
-- python -m circuit_agent.embedder.circuit_embedder
-- python -m circuit_agent.query.circuit_query_engine
-- uvicorn circuit_agent.query.query_api:app --host 0.0.0.0 --port 8090 --reload
-- uvicorn circuit_agent.query.api:app --host 0.0.0.0 --port 8090 --reload


## Invoice Agents
-- python -m invoice_agent.embedder.invoice_embedder
-- python -m invoice_agent.embedder.invoice_embedding
-- python -m invoice_agent.query.circuit_query_engine
-- uvicorn invoice_agent.query.query_api:app --host 0.0.0.0 --port 8090 --reload
