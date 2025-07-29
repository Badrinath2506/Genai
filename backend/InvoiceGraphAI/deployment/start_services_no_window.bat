@echo off
set "VENV_PYTHON=%~dp0..\invoicegraphai_env\Scripts\python.exe"
start "" /B "%VENV_Python%" -m uvicorn agents.mockapis.invoice_mock_query_api:app --port 8000 --host 0.0.0.0
start "" /B "%VENV_Python%" -m uvicorn agents.mockapis.circuit_mock_query_api:app --port 8001 --host 0.0.0.0
start "" /B "%VENV_Python%" -m uvicorn agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0
exit