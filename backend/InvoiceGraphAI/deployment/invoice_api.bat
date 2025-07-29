@echo off
cd ..  # Move to project root
call .\invoicegraphai_env\Scripts\activate
python -m uvicorn agents.mockapis.invoice_mock_query_api:app --port 8000 --host 0.0.0.0