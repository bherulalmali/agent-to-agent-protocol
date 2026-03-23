import os
from dotenv import load_dotenv

# Explicitly load .env from the POC_A2A/ directory so it works regardless
# of which working directory the process is started from.
_POC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_POC_ROOT, ".env"))

# --- API Keys ---
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")

# --- Agent Ports ---
TELL_TIME_PORT: int = int(os.environ.get("TELL_TIME_PORT", 8001))
GREETING_PORT: int = int(os.environ.get("GREETING_PORT", 8002))
ORCHESTRATOR_PORT: int = int(os.environ.get("ORCHESTRATOR_PORT", 8003))
CLIENT_PORT: int = int(os.environ.get("CLIENT_PORT", 8080))

# --- Agent URLs ---
TELL_TIME_URL: str = os.environ.get("TELL_TIME_URL", f"http://localhost:{TELL_TIME_PORT}/")
GREETING_URL: str = os.environ.get("GREETING_URL", f"http://localhost:{GREETING_PORT}/")
ORCHESTRATOR_URL: str = os.environ.get("ORCHESTRATOR_URL", f"http://localhost:{ORCHESTRATOR_PORT}/")

# --- Registry ---
AGENT_REGISTRY_PATH: str = os.environ.get(
    "AGENT_REGISTRY_PATH",
    os.path.join(os.path.dirname(__file__), "agent_registry.json"),
)
