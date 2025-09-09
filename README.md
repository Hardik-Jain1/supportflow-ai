```
customer-support-triage-agent/
│── README.md
│── pyproject.toml            # or requirements.txt for deps
│── .env                      # secrets, MCP configs (gitignored)
│── .gitignore
│
├── src/
│   ├── main.py                # entrypoint to start system
│   ├── config/                # configs for agents, tools, protocols
│   │   ├── settings.py
│   │   └── prompts/
│   │       ├── triage_prompt.txt
│   │       └── reply_prompt.txt
│   │
│   ├── agents/                # each agent (separate framework possible)
│   │   ├── triage_agent.py    # classify ticket
│   │   ├── kb_agent.py        # retrieve KB answers
│   │   ├── reply_agent.py     # draft response
│   │   ├── escalation_agent.py# escalate complex issues
│   │   └── action_agent.py    # refunds, Jira tasks
│   │
│   ├── tools/                 # MCP-based tools or custom tools
│   │   ├── refund_tool.py
│   │   ├── jira_tool.py
│   │   ├── email_tool.py
│   │   └── kb_search_tool.py
│   │
│   ├── flows/                 # LangGraph / CrewAI / Smolagents flows
│   │   ├── triage_flow.py
│   │   └── escalation_flow.py
│   │
│   ├── protocols/             # ACP + MCP implementations
│   │   ├── acp_handler.py
│   │   └── mcp_handler.py
│   │
│   ├── utils/                 # helpers (logging, parsers, validators)
│   │   ├── logger.py
│   │   ├── parsers.py
│   │   └── validators.py
│   │
│   └── tests/                 # pytest tests
│       ├── test_agents.py
│       ├── test_tools.py
│       └── test_flows.py
│
├── data/                      # sample tickets, KB docs, outputs
│   ├── tickets.json
│   └── kb_articles.json
│
└── docs/
    ├── architecture.md        # diagrams, ACP/MCP flow docs
    └── roadmap.md             # how we’ll evolve system
```