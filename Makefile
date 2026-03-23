PYTHON      := venv/bin/python
PIP         := venv/bin/pip
PROJECT_ROOT := $(shell cd .. && pwd)

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
	@echo "  make run-all          Start all four services in background"
	@echo ""

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

check-models:
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.scripts.check_models

run-tell-time:
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.agents.tell_time

run-greeting:
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.agents.greeting

run-orchestrator:
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.agents.orchestrator

run-client:
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.client.app

run-all:
	@echo "Starting all A2A agents in background..."
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.agents.tell_time   &
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.agents.greeting    &
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.agents.orchestrator &
	cd $(PROJECT_ROOT) && $(PYTHON) -m POC_A2A.client.app
