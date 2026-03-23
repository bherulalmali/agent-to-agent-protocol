import asyncio
import logging
from typing import List, Optional

import httpx
from google.genai import Client, types

from config.settings import GOOGLE_API_KEY, ORCHESTRATOR_PORT, AGENT_REGISTRY_PATH
from core.models import (
    AgentCard, Task, TaskStatus, TaskState, SendTaskRequest, SendTaskResponse,
    Message, TextPart, SendTaskParams
)
from core.server import A2ABaseServer
from utilities.discovery import discover_agents

# Set up logger
logger = logging.getLogger(__name__)

# The identity of our agent
agent_card = AgentCard(
    name="OrchestratorAgent",
    description="I route your requests to the best available agent.",
    url=f"http://localhost:{ORCHESTRATOR_PORT}/",
    capabilities=["routing", "orchestration"]
)

class Orchestrator:
    def __init__(self):
        self.agent_cards: List[AgentCard] = []
        self.server: Optional[A2ABaseServer] = None
        api_key = GOOGLE_API_KEY
        if api_key:
            logger.info(f"GOOGLE_API_KEY loaded successfully (starts with {api_key[:4]}...)")
        else:
            logger.error("GOOGLE_API_KEY NOT FOUND in environment!")
        self.client = Client(api_key=api_key)

    async def initialize(self):
        """Discover agents from registry."""
        self.agent_cards = await discover_agents(AGENT_REGISTRY_PATH)
        logging.info(f"Orchestrator initialized with {len(self.agent_cards)} agents.")

    async def delegate(self, agent: AgentCard, user_msg: str, session_id: str) -> str:
        """Call a child agent via A2A."""
        request_body = SendTaskRequest(
            method="tasks/send",
            params=SendTaskParams(
                sessionId=session_id,
                message=Message(role="user", parts=[TextPart(text=user_msg)])
            )
        )
        
        if self.server:
            self.server.add_log("📤 Delegating Task (A2A Request)", 
                                f"Target: {agent.name} ({agent.url})\nPayload: {request_body.model_dump()}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(agent.url, json=request_body.model_dump(), timeout=20.0)
                if response.status_code == 200:
                    data = response.json()
                    if self.server:
                        self.server.add_log("📥 Received A2A Response", f"From: {agent.name}\nPayload: {data}")
                    
                    history = data["result"]["history"]
                    return history[-1]["parts"][0]["text"]
                else:
                    err_msg = f"Error from {agent.name}: {response.status_code}"
                    if self.server:
                        self.server.add_log("❌ Delegation Error", err_msg)
                    return err_msg
            except Exception as e:
                err_msg = f"Failed to connect to {agent.name}: {e}"
                if self.server:
                    self.server.add_log("❌ Connection Error", err_msg)
                return err_msg

    async def process_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # 1. Start the task
        task = Task(
            sessionId=request.params.sessionId,
            status=TaskStatus(state=TaskState.IN_PROGRESS),
            history=[request.params.message]
        )
        
        user_query = request.params.message.parts[0].text
        
        # 2. Use Gemini to decide which agent to call
        agent_descriptions = "\n".join([f"- {a.name}: {a.description}" for a in self.agent_cards])
        system_prompt = f"""
        You are an orchestrator agent. You have access to the following child agents:
        {agent_descriptions}
        
        Analyze the user's query and decide which agent to call. 
        If it's about time, use TellTimeAgent.
        If it's about greetings or poetry, use GreetingAgent.
        
        Respond ONLY with the name of the agent to call. If no agent fits, respond with 'NONE'.
        """
        
        # Try a few common model names to avoid 404
        models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-flash-latest", "gemini-2.0-flash-exp"]
        response = None
        last_error = ""

        for model_name in models_to_try:
            try:
                logger.info(f"Attempting to use model: {model_name}")
                response = self.client.models.generate_content(
                    model=model_name,
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                    contents=[user_query]
                )
                if response:
                    logger.info(f"Successfully used model: {model_name}")
                    break
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                last_error = str(e)

        if response:
            target_agent_name = response.text.strip()
            if self.server:
                self.server.add_log("🧠 LLM Reasoner", f"Inquiry: '{user_query}'\nDecision: Call {target_agent_name}")
                
            target_agent = next((a for a in self.agent_cards if a.name == target_agent_name), None)
            
            if target_agent:
                # 3. Delegate
                response_text = await self.delegate(target_agent, user_query, request.params.sessionId)
            else:
                response_text = f"I decided to call {target_agent_name}, but that agent is not currently available."
        else:
            response_text = f"I'm sorry, I'm having trouble reasoning about your request. (Last error: {last_error})"

        # 4. Complete the task
        task.history.append(Message(role="agent", parts=[TextPart(text=response_text)]))
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        if self.server:
            self.server.add_log("📤 Final Output", response_text)
            
        return SendTaskResponse(id=request.id, result=task)

orchestrator = Orchestrator()

if __name__ == "__main__":
    # 1. Run initialization in a short-lived event loop
    asyncio.run(orchestrator.initialize())
    
    # 2. Start the blocking server (starts its own event loop)
    server = A2ABaseServer(agent_card, orchestrator.process_task)
    orchestrator.server = server
    server.run(port=ORCHESTRATOR_PORT)
