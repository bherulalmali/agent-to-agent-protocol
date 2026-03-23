import asyncio
import httpx
import logging
from typing import TypedDict, List, Optional, Annotated

# LangGraph & LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# A2A Core Imports
from POC_A2A.config.settings import GREETING_PORT, TELL_TIME_URL
from POC_A2A.core.models import (
    AgentCard, Task, TaskStatus, TaskState, SendTaskRequest, SendTaskResponse,
    Message, TextPart, SendTaskParams
)
from POC_A2A.core.server import A2ABaseServer

logger = logging.getLogger(__name__)

# --- Models & State ---
class AgentState(TypedDict):
    query: str
    session_id: str
    time_info: Optional[str]
    allow_time_agent: bool
    response: Optional[str]

# --- Node Implementation ---
class GreetingAgentLangGraph:
    def __init__(self):
        # Using a more stable model name for LangChain
        self.model_name = "gemini-1.5-flash-latest"
        self.llm = ChatGoogleGenerativeAI(model=self.model_name)
        self.tell_time_url = TELL_TIME_URL
        self.server: Optional[A2ABaseServer] = None
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("check_preference", self.check_preference)
        workflow.add_node("call_time_agent", self.call_time_agent)
        workflow.add_node("generate_greeting", self.generate_greeting)
        
        workflow.set_entry_point("check_preference")
        
        workflow.add_conditional_edges(
            "check_preference",
            self.should_call_time,
            {
                "call": "call_time_agent",
                "skip": "generate_greeting"
            }
        )
        
        workflow.add_edge("call_time_agent", "generate_greeting")
        workflow.add_edge("generate_greeting", END)
        
        return workflow.compile()

    def check_preference(self, state: AgentState):
        query_lower = state["query"].lower()
        # Logic: skip if user mentions "don't use tell_time" or "avoid time agent"
        # Expanding keywords to be more robust (detecting 'avoid' and 'time' in sequence or proximity)
        skip_patterns = ["don't use tell_time", "avoid time agent", "avoid the time agent", 
                         "not use tell_time", "skip time", "without time"]
        allow = not any(k in query_lower for k in skip_patterns)
        
        if self.server:
            pref_status = "ALLOWED" if allow else "SKIPPED by user request"
            self.server.add_log("🧠 LangGraph Node: check_preference", f"Query: {state['query']}\nTellTime Status: {pref_status}")
            
        return {"allow_time_agent": allow}

    def should_call_time(self, state: AgentState):
        return "call" if state["allow_time_agent"] else "skip"

    async def call_time_agent(self, state: AgentState):
        if self.server:
            self.server.add_log("📤 Requesting Time (A2A)", f"Calling: {self.tell_time_url}")
            
        async with httpx.AsyncClient() as client:
            request_body = SendTaskRequest(
                method="tasks/send",
                params=SendTaskParams(
                    sessionId=state["session_id"],
                    message=Message(role="user", parts=[TextPart(text="What time is it?")])
                )
            )
            try:
                response = await client.post(self.tell_time_url, json=request_body.model_dump(), timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    time_str = data["result"]["history"][-1]["parts"][0]["text"]
                    if self.server:
                        self.server.add_log("📥 Time Received", time_str)
                    return {"time_info": time_str}
                return {"time_info": "(Time service error)"}
            except Exception as e:
                return {"time_info": f"(Connection error: {e})"}

    async def generate_greeting(self, state: AgentState):
        time_context = f"The current time is {state['time_info']}" if state['time_info'] else "No time info was provided."
        prompt = f"User said: {state['query']}. {time_context}. Generate a warm, poetic greeting. If time was skipped, apologize gracefully for not mentioning the hour."
        
        if self.server:
            self.server.add_log("🧠 LangGraph Node: generate_greeting", f"Prompt: {prompt}")
            
        try:
            res = await self.llm.ainvoke(prompt)
            return {"response": res.content}
        except Exception as e:
            logger.error(f"Error calling model: {e}")
            # Robust fallback for POC presentation
            fallback_msg = f"Greetings! I received your message: '{state['query']}'. {time_context if state['time_info'] else 'I hope your day is going well!'} (Model fallback due to: {e})"
            return {"response": fallback_msg}

    async def process_task(self, request: SendTaskRequest) -> SendTaskResponse:
        task = Task(
            sessionId=request.params.sessionId,
            status=TaskStatus(state=TaskState.IN_PROGRESS),
            history=[request.params.message]
        )
        
        initial_state = {
            "query": request.params.message.parts[0].text,
            "session_id": request.params.sessionId,
            "time_info": None,
            "allow_time_agent": True,
            "response": None
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        response_text = final_state["response"]
        
        task.history.append(Message(role="agent", parts=[TextPart(text=response_text)]))
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        if self.server:
            self.server.add_log("📤 Final Output", response_text)
            
        return SendTaskResponse(id=request.id, result=task)

agent_card = AgentCard(
    name="GreetingAgent",
    description="I create poetic greetings using LangGraph.",
    url=f"http://localhost:{GREETING_PORT}/",
    capabilities=["greeting", "langgraph"]
)

if __name__ == "__main__":
    agent = GreetingAgentLangGraph()
    server = A2ABaseServer(agent_card, agent.process_task)
    agent.server = server
    server.run(port=GREETING_PORT)
