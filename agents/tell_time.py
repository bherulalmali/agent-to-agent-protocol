import asyncio
from datetime import datetime
from POC_A2A.core.models import AgentCard, Task, TaskStatus, TaskState, SendTaskRequest, SendTaskResponse, Message, TextPart
from POC_A2A.core.server import A2ABaseServer
from POC_A2A.config.settings import TELL_TIME_PORT

# The identity of our agent
agent_card = AgentCard(
    name="TellTimeAgent",
    description="I provide the current system time.",
    url=f"http://localhost:{TELL_TIME_PORT}/",
    capabilities=["time", "current_time"]
)

# Implementation of the business logic
async def process_task(request: SendTaskRequest) -> SendTaskResponse:
    # 1. Start the task
    task = Task(
        sessionId=request.params.sessionId,
        status=TaskStatus(state=TaskState.IN_PROGRESS),
        history=[request.params.message]
    )
    
    # 2. Perform the logic (get time)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_text = f"The current time is: {now}"
    
    # 3. Complete the task
    task.history.append(Message(role="agent", parts=[TextPart(text=response_text)]))
    task.status = TaskStatus(state=TaskState.COMPLETED)
    
    # Log to UI
    server.add_log("🕒 Time Lookup", response_text)
    
    return SendTaskResponse(id=request.id, result=task)

if __name__ == "__main__":
    server = A2ABaseServer(agent_card, process_task)
    server.run(port=TELL_TIME_PORT)
