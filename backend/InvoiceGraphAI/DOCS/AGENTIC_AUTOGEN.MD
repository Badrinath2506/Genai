/query_system
│   main.py                # Main application entry point
│   config.py              # Configuration settings
│   requirements.txt       # Dependencies
│
├───/agents
│   │   query_agent.py     # Main query decision agent
│   │   nlp_processor.py   # NLP response formatter
│   │
│   └───/clients
│       │   api_client.py  # Base API client
│       │   circuit_client.py
│       │   invoice_client.py
│
├───/models
│   │   query_models.py    # Pydantic models
│
├───/utils
│   │   logger.py          # Custom logger setup
│   │   helpers.py         # Utility functions
│
└───/logs
    ├───/prompts           # Prompt logs
    ├───/responses         # Query response logs
    ├───/debug             # Debug logs
    └───/errors            # Error logs



User Prompt
    │
    ▼
[Input Parser] → (Extract entities/Intent)
    │
    ▼
[Query Decision Agent] → Decide which API(s) to call
    │
    ├───▶ [Circuit API Client] → Get circuit data
    │        │
    │        └──▶ If invoice numbers found → [Invoice API Client]
    │
    └───▶ [Invoice API Client] → Get invoice data
             │
             └──▶ If circuit info needed → [Circuit API Client]
                      │
                      ▼
[NLP Response Formatter] → Generate natural language response
    │
    ▼
[Response Logger] → Log prompt + response
    │
    ▼
JSON Response to User