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
      args: "agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0",
      interpreter: "python"
    }
  ]
}