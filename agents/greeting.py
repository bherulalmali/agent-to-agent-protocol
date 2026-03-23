import httpx
import asyncio
from typing import Optional
from core.models import (
    AgentCard, Task, TaskStatus, TaskState, SendTaskRequest, SendTaskResponse,
    Message, TextPart, SendTaskParams
)
from core.server import A2ABaseServer
from config.settings import GREETING_PORT, TELL_TIME_URL

# The identity of our agent
agent_card = AgentCard(
    name="GreetingAgent",
    description="I create poetic greetings. I depend on TellTimeAgent for the time.",
    url=f"http://localhost:{GREETING_PORT}/",
    capabilities=["greeting", "poetry"]
)

class GreetingAgent:
    def __init__(self):
        self.server: Optional[A2ABaseServer] = None
        self.tell_time_url = TELL_TIME_URL

    async def call_tell_time(self, session_id: str) -> str:
        """Helper to call TellTimeAgent via A2A JSON-RPC."""
        request_body = SendTaskRequest(
            method="tasks/send",
            params=SendTaskParams(
                sessionId=session_id,
                message=Message(role="user", parts=[TextPart(text="What time is it?")])
            )
        )
        
        if self.server:
            self.server.add_log("📤 Requesting Time (A2A Request)", 
                                f"Target: {self.tell_time_url}\nPayload: {request_body.model_dump()}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.tell_time_url, json=request_body.model_dump(), timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if self.server:
                        self.server.add_log("📥 Time Received (A2A Response)", f"Payload: {data}")
                    
                    history = data["result"]["history"]
                    return history[-1]["parts"][0]["text"]
                else:
                    err_msg = f"Error from TellTimeAgent: {response.status_code}"
                    if self.server:
                        self.server.add_log("❌ A2A Error", err_msg)
                    return err_msg
            except Exception as e:
                err_msg = f"Failed to connect to TellTimeAgent: {e}"
                if self.server:
                    self.server.add_log("❌ Connection Error", err_msg)
                return err_msg

    # Implementation of the business logic
    async def process_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # 1. Start the task
        task = Task(
            sessionId=request.params.sessionId,
            status=TaskStatus(state=TaskState.IN_PROGRESS),
            history=[request.params.message]
        )
        
        # 2. Call TellTimeAgent
        time_str = await self.call_tell_time(request.params.sessionId)
        
        # 3. Generate poetic greeting
        response_text = f"Greetings, traveler! The stars align and the clocks whisper that {time_str}. May your day be as graceful as the passing hours."
        
        # 4. Complete the task
        task.history.append(Message(role="agent", parts=[TextPart(text=response_text)]))
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        if self.server:
            self.server.add_log("📤 Poetic Greeting Created", response_text)
            
        return SendTaskResponse(id=request.id, result=task)

if __name__ == "__main__":
    agent = GreetingAgent()
    server = A2ABaseServer(agent_card, agent.process_task)
    agent.server = server
    server.run(port=GREETING_PORT)
