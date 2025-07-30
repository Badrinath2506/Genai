import subprocess
import sys

servers = [
    ["uvicorn", "agents.mockapis.invoice_mock_query_api:app", "--port", "8000", "--host", "0.0.0.0", "--reload"],
    ["uvicorn", "agents.mockapis.circuit_mock_query_api:app", "--port", "8001", "--host", "0.0.0.0", "--reload"],
    ["uvicorn", "agentic_ai.autogen.main:app", "--port", "9002", "--host", "0.0.0.0", "--reload"]
]

# For Windows
if sys.platform == "win32":
    processes = []
    for server in servers:
        # CREATE_NEW_PROCESS_GROUP flag helps with Ctrl+C handling
        p = subprocess.Popen(server, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        processes.append(p)
    
    try:
        # Wait until all processes complete
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        for p in processes:
            p.terminate()