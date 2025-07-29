// deployment/run.js
const { exec } = require('child_process');

const commands = [
  'cd .. && .\\invoicegraphai_env\\Scripts\\activate && python -m uvicorn agents.mockapis.invoice_mock_query_api:app --port 8000 --host 0.0.0.0',
  'cd .. && .\\invoicegraphai_env\\Scripts\\activate && python -m uvicorn agents.mockapis.circuit_mock_query_api:app --port 8001 --host 0.0.0.0',
  'cd .. && .\\invoicegraphai_env\\Scripts\\activate && python -m uvicorn agentic_ai.autogen.main:app --port 9002 --host 0.0.0.0'
];

commands.forEach(cmd => {
  exec(cmd, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`Stderr: ${stderr}`);
      return;
    }
    console.log(`Stdout: ${stdout}`);
  });
});