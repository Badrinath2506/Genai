genai-streaming-app/
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── websocket_server.py    # WebSocket streaming logic
│   ├── sse_server.py          # SSE streaming logic
│   ├── llm_service.py         # (Optional) Mock or real Gemini model logic
│   ├── requirements.txt       # Backend dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.js
│   │   ├── components/
│   │   │   ├── WebSocketStream.jsx
│   │   │   ├── SSEStream.jsx
│   ├── package.json
│   └── vite.config.js         # If using Vite (or use CRA config)
├── README.md
