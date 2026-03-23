# Agent-to-Agent (A2A) Protocol — POC_A2A

A proof-of-concept demonstrating the **Agent-to-Agent (A2A) protocol**, where multiple AI agents built on different frameworks communicate with each other over a standardized JSON-RPC 2.0 interface.

---

## What is A2A?

The A2A (Agent-to-Agent) protocol is a communication standard that allows AI agents — regardless of the underlying framework — to discover and call each other over HTTP. Each agent exposes:

- A **discovery endpoint** at `/.well-known/agent.json` that advertises its capabilities (an "Agent Card")
- A **task endpoint** at `/` that accepts JSON-RPC 2.0 requests

This POC shows that an agent built with plain Python, Google ADK, or LangGraph can all interoperate seamlessly as long as they speak the A2A protocol.

---

## Architecture

```
Client (Gradio Chat UI — Port 8080)
        |
        | A2A JSON-RPC
        v
OrchestratorAgent (Port 8003)
  - Uses Gemini LLM to decide which agent to call
        |
        |-- routes to --> TellTimeAgent (Port 8001)
        |                 - Returns the current system time
        |
        `-- routes to --> GreetingAgent (Port 8002)
                          - Calls TellTimeAgent internally
                          - Returns a poetic greeting with the time
```

### Agent Variants

This POC includes two sets of agent implementations to demonstrate cross-framework interoperability:

| Folder | Agent | Framework |
|---|---|---|
| `agents/` | TellTimeAgent, GreetingAgent, OrchestratorAgent | Plain Python |
| `agents/variants/adk/` | TellTimeAgent | Google ADK |
| `agents/variants/langgraph/` | GreetingAgent | LangGraph + Gemini |

All variants expose the same A2A interface, so the Orchestrator can call any of them without modification.

---

## Project Structure

```
POC_A2A/
├── agents/
│   ├── tell_time.py             # TellTimeAgent — returns current system time (Port 8001)
│   ├── greeting.py              # GreetingAgent — poetic greeting, calls TellTimeAgent (Port 8002)
│   ├── orchestrator.py          # OrchestratorAgent — LLM-based router (Port 8003)
│   └── variants/
│       ├── adk/
│       │   └── agent.py         # TellTimeAgent implemented with Google ADK
│       └── langgraph/
│           └── agent.py         # GreetingAgent implemented with LangGraph
│
├── client/
│   └── app.py                   # Gradio chat UI that talks to the Orchestrator (Port 8080)
│
├── config/
│   ├── settings.py              # Centralized config: ports, URLs, API keys
│   └── agent_registry.json      # Agent base URLs the Orchestrator discovers at startup
│
├── core/
│   ├── models.py                # Pydantic models: AgentCard, Task, Message, JSON-RPC types
│   └── server.py                # Reusable FastAPI + Gradio server base class
│
├── scripts/
│   └── check_models.py          # Utility to verify Gemini API key and list available models
│
├── utilities/
│   └── discovery.py             # Fetches Agent Cards from the registry
│
├── tests/                       # Test suite
├── .env.example                 # Template — copy to .env and fill in your API key
├── .gitignore
├── Makefile                     # Shortcut commands: make run-tell-time, make run-all, etc.
├── pyproject.toml               # Project metadata
├── requirements.txt             # Pinned dependencies
└── README.md
```

---

## Prerequisites

**Python 3.11 or 3.13** is required (tested on Python 3.13).

### Step 1 — Create and activate a virtual environment

```bash
cd /path/to/a2a_samples-main

python3 -m venv POC_A2A/venv
source POC_A2A/venv/bin/activate      # macOS / Linux
# POC_A2A\venv\Scripts\activate       # Windows
```

### Step 2 — Install all dependencies

A `requirements.txt` with fully pinned versions is included:

```bash
pip install -r POC_A2A/requirements.txt
```

This installs everything needed for all three agent variants (plain Python, Google ADK, LangGraph).

### Step 3 — Set your Google API Key

Copy the example env file and fill in your key:

```bash
cp POC_A2A/.env.example POC_A2A/.env
# then edit POC_A2A/.env and set GOOGLE_API_KEY=your_key_here
```

Get a free API key at https://aistudio.google.com/app/apikey.

All ports and URLs can also be overridden in `.env` — see `.env.example` for all options.

---

## Running the POC

All commands must be run from the **project root** (`a2a_samples-main/`) with the venv active, so that `POC_A2A.*` package imports resolve correctly.

```bash
cd /path/to/a2a_samples-main
source POC_A2A/venv/bin/activate
```

Then open **4 terminals** (all from `a2a_samples-main/` with the venv active) and start in order:

### Terminal 1 — TellTimeAgent (Port 8001)

```bash
python -m POC_A2A.agents.tell_time
```

Expected output:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Terminal 2 — GreetingAgent (Port 8002)

```bash
python -m POC_A2A.agents.greeting
```

Expected output:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Terminal 3 — OrchestratorAgent (Port 8003)

```bash
python -m POC_A2A.agents.orchestrator
```

Expected output — watch for agent discovery:
```
INFO: GOOGLE_API_KEY loaded successfully (starts with AIza...)
INFO: HTTP Request: GET http://localhost:8001/.well-known/agent.json "HTTP/1.1 200 OK"
INFO: Discovered agent: TellTimeAgent at http://localhost:8001/
INFO: HTTP Request: GET http://localhost:8002/.well-known/agent.json "HTTP/1.1 200 OK"
INFO: Discovered agent: GreetingAgent at http://localhost:8002/
INFO: Orchestrator initialized with 2 agents.
INFO: Uvicorn running on http://0.0.0.0:8003
```

### Terminal 4 — Client UI (Port 8080)

```bash
python -m POC_A2A.client.app
```

Expected output:
```
Running on local URL:  http://127.0.0.1:8080
```

> **Start order matters**: TellTimeAgent (1) → GreetingAgent (2) → OrchestratorAgent (3) → Client (4).
> The Orchestrator hits `/.well-known/agent.json` on each agent at startup to build its routing table.

### Shortcut — run everything with Make

From inside `POC_A2A/`:

```bash
make run-tell-time     # Terminal 1
make run-greeting      # Terminal 2
make run-orchestrator  # Terminal 3
make run-client        # Terminal 4

# Or start all four in one shot (agents in background, client in foreground):
make run-all
```

---

## Accessing the UIs

| Service | URL | Description |
|---|---|---|
| TellTimeAgent | http://localhost:8001/ui | Live A2A transaction logs |
| GreetingAgent | http://localhost:8002/ui | Live A2A transaction logs |
| OrchestratorAgent | http://localhost:8003/ui | LLM routing decisions + logs |
| Chat Client | http://localhost:8080 | End-user chat interface |

Each agent's `/ui` page auto-refreshes every second and shows all incoming requests and outgoing responses in real time.

---

## A2A Demonstration — UI

1. Open **http://localhost:8080** in your browser.
2. Type a message and hit Enter. The client sends a JSON-RPC request to the Orchestrator.
3. Open **http://localhost:8003/ui** in another tab — you'll see the Orchestrator's LLM routing decision and the outgoing A2A delegation request in real time.
4. Open **http://localhost:8001/ui** or **http://localhost:8002/ui** to watch the receiving agent's logs update as it processes the delegated task.

Suggested demo flow (open all 4 tabs side by side):

| Step | Action | What to observe |
|---|---|---|
| 1 | Send `"What time is it?"` | Orchestrator UI shows Gemini decision: `TellTimeAgent`. TellTimeAgent UI shows the incoming request and time response. |
| 2 | Send `"Give me a poetic greeting"` | Orchestrator routes to GreetingAgent. GreetingAgent UI shows it making a secondary A2A call to TellTimeAgent, then composing the reply. |
| 3 | Send `"What day is today?"` | Orchestrator routes to TellTimeAgent — see the full chain in 3 browser tabs simultaneously. |

---

## A2A Demonstration — Terminal

You can also drive the entire system directly with `curl` without the UI client.

### 1. Verify Agent Discovery

Each agent advertises itself at `/.well-known/agent.json`:

```bash
curl http://localhost:8001/.well-known/agent.json
```
```json
{"name": "TellTimeAgent", "description": "I provide the current system time.", "url": "http://localhost:8001/", "capabilities": ["time", "current_time"]}
```

### 2. Call TellTimeAgent directly

```bash
curl -s -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "t1",
    "method": "tasks/send",
    "params": {
      "sessionId": "demo-session",
      "message": {"role": "user", "parts": [{"text": "What time is it?"}]}
    }
  }' | python3 -m json.tool
```

Expected response:
```json
{
  "result": {
    "status": {"state": "COMPLETED"},
    "history": [
      {"role": "user",  "parts": [{"text": "What time is it?"}]},
      {"role": "agent", "parts": [{"text": "The current time is: 2026-03-21 18:29:47"}]}
    ]
  }
}
```

### 3. Call GreetingAgent directly (agent-to-agent chain)

GreetingAgent internally calls TellTimeAgent via A2A before responding:

```bash
curl -s -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "t2",
    "method": "tasks/send",
    "params": {
      "sessionId": "demo-session",
      "message": {"role": "user", "parts": [{"text": "Say hello to me"}]}
    }
  }' | python3 -m json.tool
```

### 4. Route via Orchestrator — time query

```bash
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "t3",
    "method": "tasks/send",
    "params": {
      "sessionId": "demo-session",
      "message": {"role": "user", "parts": [{"text": "What is the current time?"}]}
    }
  }' | python3 -m json.tool
```

Watch the Orchestrator terminal — it will log:
```
INFO: [OrchestratorAgent] Received Request: ...
INFO: Attempting to use model: gemini-1.5-flash
```

### 5. Route via Orchestrator — greeting query

```bash
curl -s -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "t4",
    "method": "tasks/send",
    "params": {
      "sessionId": "demo-session",
      "message": {"role": "user", "parts": [{"text": "Give me a poetic greeting"}]}
    }
  }' | python3 -m json.tool
```

This triggers the full 3-hop chain: **curl → Orchestrator → GreetingAgent → TellTimeAgent**.

---

## How A2A Works in This POC

### 1. Agent Discovery

At startup, the Orchestrator reads `agent_registry.json` (a list of base URLs) and fetches each agent's card from `/.well-known/agent.json`:

```json
{
  "name": "TellTimeAgent",
  "description": "I provide the current system time.",
  "url": "http://localhost:8001/",
  "capabilities": ["time", "current_time"]
}
```

### 2. Task Request (JSON-RPC 2.0)

All agent-to-agent calls follow the `tasks/send` method:

```json
{
  "jsonrpc": "2.0",
  "id": "abc123",
  "method": "tasks/send",
  "params": {
    "sessionId": "session-uuid",
    "message": {
      "role": "user",
      "parts": [{ "text": "What time is it?" }]
    }
  }
}
```

### 3. Task Response

```json
{
  "jsonrpc": "2.0",
  "id": "abc123",
  "result": {
    "id": "task-uuid",
    "sessionId": "session-uuid",
    "status": { "state": "COMPLETED" },
    "history": [
      { "role": "user",  "parts": [{ "text": "What time is it?" }] },
      { "role": "agent", "parts": [{ "text": "The current time is: 2026-03-21 14:30:00" }] }
    ]
  }
}
```

---

## Cross-Framework Interoperability

A key demonstration of this POC is that **framework doesn't matter** — only the protocol does.

- **`agents/variants/adk/agent.py`** — TellTimeAgent built with **Google ADK**, using an `LlmAgent` backed by Gemini.
- **`agents/variants/langgraph/agent.py`** — GreetingAgent built with **LangGraph**, using a `StateGraph` with conditional edges to optionally skip the time lookup.

Both expose identical A2A endpoints. Swap either into the registry and the rest of the system works without any changes.

---

## Key Design Decisions

- **`A2ABaseServer`** (`core/server.py`) — a reusable FastAPI + Gradio base that any agent can use. Handles routing, validation, error responses, and the live log UI in one place.
- **`AgentCard`** — a Pydantic model that is both served at `/.well-known/agent.json` and used internally to represent discovered agents.
- **`config/settings.py`** — all ports, URLs, and the API key are loaded from environment variables. Override any value in `.env` without touching code.
- **File-based registry** (`config/agent_registry.json`) — kept intentionally simple for the POC. In production this would be a service registry or DNS-based discovery.
