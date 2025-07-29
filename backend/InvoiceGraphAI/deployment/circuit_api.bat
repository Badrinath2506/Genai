@echo off
cd ..
call .\invoicegraphai_env\Scripts\activate
python -m uvicorn agents.mockapis.circuit_mock_query_api:app --port 8001 --host 0.0.0.0