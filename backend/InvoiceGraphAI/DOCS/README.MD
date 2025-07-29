# create env 
-- python -m venv invoicegraphai_env
-- .\invoicegraphai_env\Scripts\activate
-- pip install -r requirements.txt
pip install python-json-logger

# Using PM2 for Windows
-- npm install pm2 -g
-- pm2 delete all
-- pm2 start servers.config.js
'''
servers.config.js

module.exports = {
  apps: [
    {
      name: "invoice-api",
      script: "uvicorn",
      args: "agents.mockapis.invoice_mock_query_api:app --port 8000 --host 0.0.0.0",
      interpreter: "python"
    },
    {
      name: "circuit-api",
      script: "uvicorn",
      args: "agents.mockapis.circuit_mock_query_api:app --port 8001 --host 0.0.0.0",
      interpreter: "python"
    },
    {
      name: "agentic-ai",
      script: "uvicorn",
      args: "agentic_ai.autogen.agents.main:app --port 9002 --host 0.0.0.0",
      interpreter: "python"
    }
  ]
}

'''