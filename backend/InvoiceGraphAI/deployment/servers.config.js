const path = require('path');
const projectRoot = path.join(__dirname, "..");

module.exports = {
  apps: [
    {
      name: "invoice-api",
      script: path.join(projectRoot, "invoicegraphai_env", "Scripts", "python.exe"),
      args: "-m uvicorn agents.mockapis.invoice_mock_query_api:app --port 8000 --host 0.0.0.0",
      cwd: projectRoot,
      interpreter: "none",
      exec_mode: "fork",
      windowsHide: true,
      autorestart: true,
      env: {
        PYTHONPATH: projectRoot
      }
    },
    {
      name: "circuit-api",
      script: path.join(projectRoot, "invoicegraphai_env", "Scripts", "python.exe"),
      args: "-m uvicorn agents.mockapis.circuit_mock_query_api:app --port 8001 --host 0.0.0.0",
      cwd: projectRoot,
      interpreter: "none",
      exec_mode: "fork",
      windowsHide: true,
      autorestart: true,
      env: {
        PYTHONPATH: projectRoot
      }
    },
    {
      name: "agentic-ai",
      script: path.join(projectRoot, "invoicegraphai_env", "Scripts", "python.exe"),
      args: "-m uvicorn agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0",
      cwd: projectRoot,
      interpreter: "none",
      exec_mode: "fork",
      windowsHide: true,
      autorestart: true,
      env: {
        PYTHONPATH: projectRoot
      }
    }
  ]
}