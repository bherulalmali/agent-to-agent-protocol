PYTHON := venv/bin/python
PIP    := venv/bin/pip

.PHONY: help install check-models run-tell-time run-greeting run-orchestrator run-client run-all

help:
	@echo ""
	@echo "  A2A Protocol POC — available commands"
	@echo ""
	@echo "  make install          Install all dependencies into venv"
	@echo "  make check-models     Verify Gemini API key and list available models"
	@echo "  make run-tell-time    Start TellTimeAgent  (port 8001)"
	@echo "  make run-greeting     Start GreetingAgent  (port 8002)"
	@echo "  make run-orchestrator Start OrchestratorAgent (port 8003)"
	@echo "  make run-client       Start Gradio chat client (port 8080)"
	@echo "  make run-all          Start all four services (agents in background, client in foreground)"
	@echo ""

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

check-models:
	$(PYTHON) -m scripts.check_models

run-tell-time:
	$(PYTHON) -m agents.tell_time

run-greeting:
	$(PYTHON) -m agents.greeting

run-orchestrator:
	$(PYTHON) -m agents.orchestrator

run-client:
	$(PYTHON) -m client.app

run-all:
	@echo "Starting all A2A agents..."
	$(PYTHON) -m agents.tell_time    &
	$(PYTHON) -m agents.greeting     &
	$(PYTHON) -m agents.orchestrator &
	$(PYTHON) -m client.app
