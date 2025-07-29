@echo off
cd ..
call .\invoicegraphai_env\Scripts\activate
python -m uvicorn agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0