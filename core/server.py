import logging
import asyncio
from datetime import datetime
from typing import Callable, Optional

import gradio as gr
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.models import AgentCard, JSONRPCResponse, InternalError, SendTaskRequest, SendTaskResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class A2ABaseServer:
    def __init__(self, agent_card: AgentCard, process_task_fn: Callable):
        self.agent_card = agent_card
        self.process_task_fn = process_task_fn
        self.app = FastAPI(title=agent_card.name)
        self.logs = []

        # A2A Discovery Endpoint
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            return self.agent_card.model_dump()

        # A2A JSON-RPC Endpoint
        @self.app.post("/")
        async def handle_rpc(request: Request):
            body = await request.json()
            method = body.get("method", "Unknown")
            logger.info(f"[{self.agent_card.name}] Received Request: {body}")
            self.add_log(f"Incoming Request ({method})", f"Payload: {body}")

            try:
                if body.get("method") == "tasks/send":
                    req = SendTaskRequest.model_validate(body)
                    result = await self.process_task_fn(req)
                    response_payload = jsonable_encoder(result.model_dump(exclude_none=True))
                    self.add_log("Outgoing Response", f"Payload: {response_payload}")
                    return JSONResponse(content=response_payload)
                else:
                    raise ValueError(f"Method {body.get('method')} not supported")
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                error_resp = JSONRPCResponse(
                    id=body.get("id"),
                    error=InternalError(data=str(e))
                )
                error_payload = jsonable_encoder(error_resp.model_dump())
                self.add_log("Error Response", f"Payload: {error_payload}")
                return JSONResponse(content=error_payload, status_code=400)

    def add_log(self, title: str, content: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_log = f"[{timestamp}] === {title} ===\n{content}\n" + ("-" * 40)
        self.logs.append(formatted_log)
        if len(self.logs) > 50:
            self.logs.pop(0)

    def create_gradio_interface(self):
        with gr.Blocks(title=f"{self.agent_card.name} UI") as demo:
            gr.Markdown(f"# {self.agent_card.name}")
            gr.Markdown(f"**Description:** {self.agent_card.description}")
            gr.Markdown(f"**A2A Endpoint:** `{self.agent_card.url}`")

            with gr.Row():
                with gr.Column():
                    log_output = gr.TextArea(
                        label="Transaction Logs (Auto-updating)", interactive=False, lines=25
                    )
                    timer = gr.Timer(1)

            def get_logs():
                return "\n".join(reversed(self.logs))

            timer.tick(get_logs, outputs=log_output)
            demo.load(get_logs, outputs=log_output)

        return demo

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        import uvicorn
        demo = self.create_gradio_interface()
        self.app = gr.mount_gradio_app(self.app, demo, path="/ui")

        print(f"\n{self.agent_card.name} started!")
        print(f"A2A Endpoint : http://{host}:{port}/")
        print(f"Gradio UI    : http://{host}:{port}/ui\n")

        uvicorn.run(self.app, host=host, port=port)
