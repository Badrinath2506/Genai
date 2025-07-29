┌─────────────────┐    ┌───────────────────────┐    ┌─────────────────┐
│                 │    │                       │    │                 │
│   User Prompt   │───▶│  Agentic Decision     │───▶│  Query Router   │
│                 │    │  Engine (Strategy     │    │  (Facade)       │
└─────────────────┘    │  Pattern)             │    └────────┬────────┘
                       └───────────────────────┘             │
                                                            ▼
┌─────────────────┐    ┌───────────────────────┐    ┌─────────────────┐
│                 │    │                       │    │                 │
│   NLP Processor │◀───┤  Data Fetcher         │◀───┤  Query Handler  │
│   (Chain of     │    │  (Circuit/Invoice     │    │  (Circuit/      │
│   Responsibility)│    │  Services)            │    │  Invoice)       │
└────────┬────────┘    └───────────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌───────────────────────┐
│                 │    │                       │
│  Response       │───▶│  Logging System       │
│  Formatter      │    │  (Multi-level)        │
│                 │    │                       │
└─────────────────┘    └───────────────────────┘


project_root/
├── agents/
│   ├── decision_engine.py
│   └── nlp_processor.py
├── services/
│   ├── circuit_service.py
│   ├── invoice_service.py
│   └── query_facade.py
├── models/
│   ├── circuit.py
│   ├── invoice.py
│   └── response.py
├── logging/
│   ├── prompt_logger.py
│   ├── query_logger.py
│   └── config.py
├── utils/
│   ├── error_handler.py
│   └── helpers.py
├── main.py
└── requirements.txt