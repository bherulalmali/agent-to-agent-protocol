import asyncio
import logging
from datetime import datetime
from typing import Optional

# ADK Imports
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.genai import types

# A2A Core Imports
from POC_A2A.config.settings import TELL_TIME_PORT
from POC_A2A.core.models import (
    AgentCard, Task, TaskStatus, TaskState, SendTaskRequest, SendTaskResponse,
    Message, TextPart
)
from POC_A2A.core.server import A2ABaseServer

# Set up logger
logger = logging.getLogger(__name__)

# The identity of our agent
agent_card = AgentCard(
    name="TellTimeAgent",
    description="I provide the current time using Google ADK.",
    url=f"http://localhost:{TELL_TIME_PORT}/",
    capabilities=["time", "adk"]
)

class TellTimeAgentADK:
    def __init__(self):
        self._agent = LlmAgent(
            model="gemini-1.5-flash-latest",
            name="tell_time_agent",
            description="Tells the current time",
            instruction="Reply with the current time in the format YYYY-MM-DD HH:MM:SS."
        )
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        self._user_id = "poc_user"
        self.server: Optional[A2ABaseServer] = None

    async def process_task(self, request: SendTaskRequest) -> SendTaskResponse:
        # 1. Start the task
        task = Task(
            sessionId=request.params.sessionId,
            status=TaskStatus(state=TaskState.IN_PROGRESS),
            history=[request.params.message]
        )
        
        user_query = request.params.message.parts[0].text
        session_id = request.params.sessionId
        
        if self.server:
            self.server.add_log("🧠 ADK Thinking", f"Query: {user_query}")

        # 2. Invoke ADK Logic
        try:
            # Ensure session exists in the service
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id
            )
            if session is None:
                await self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    session_id=session_id,
                    state={}
                )

            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_query)]
            )

            last_event = None
            async for event in self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                new_message=content
            ):
                last_event = event

            if last_event and last_event.content and last_event.content.parts:
                response_text = "\n".join([p.text for p in last_event.content.parts if p.text])
            else:
                response_text = f"The current time is: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        except Exception as e:
            logger.error(f"ADK Error: {e}")
            response_text = f"The current time is: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Fallback due to error: {e})"

        # 3. Complete the task
        task.history.append(Message(role="agent", parts=[TextPart(text=response_text)]))
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        if self.server:
            self.server.add_log("📤 ADK Output", response_text)
            
        return SendTaskResponse(id=request.id, result=task)

if __name__ == "__main__":
    agent = TellTimeAgentADK()
    server = A2ABaseServer(agent_card, agent.process_task)
    agent.server = server
    server.run(port=TELL_TIME_PORT)
