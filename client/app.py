import httpx
import gradio as gr
import uuid
from core.models import SendTaskRequest, SendTaskParams, Message, TextPart
from config.settings import ORCHESTRATOR_URL, CLIENT_PORT

async def chat_with_orchestrator(message, history):
    session_id = str(uuid.uuid4())
    
    payload = SendTaskRequest(
        method="tasks/send",
        params=SendTaskParams(
            sessionId=session_id,
            message=Message(role="user", parts=[TextPart(text=message)])
        )
    )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(ORCHESTRATOR_URL, json=payload.model_dump(), timeout=60.0)
            if response.status_code == 200:
                data = response.json()
                bot_msg = data["result"]["history"][-1]["parts"][0]["text"]
                return bot_msg
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Failed to connect to Orchestrator: {e}"

with gr.Blocks(title="A2A POC Client") as demo:
    gr.Markdown("# 🌐 A2A Protocol POC")
    gr.Markdown("This client communicates with the **OrchestratorAgent** (Port 8003), which delegates tasks to **TellTimeAgent** (8001) or **GreetingAgent** (8002).")
    
    gr.ChatInterface(chat_with_orchestrator)

if __name__ == "__main__":
    demo.launch(server_port=CLIENT_PORT)
