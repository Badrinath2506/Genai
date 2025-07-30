@echo off
START "Invoice API" cmd /k uvicorn agents.mockapis.invoice_mock_query_api:app --port 8000 --host 0.0.0.0 --reload
START "Circuit API" cmd /k uvicorn agents.mockapis.circuit_mock_query_api:app --port 8001 --host 0.0.0.0 --reload
START "Agentic AI" cmd /k uvicorn agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0 --reload