from typing import Any, Literal, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# --- JSON-RPC Models ---

class JSONRPCMessage(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[str] = Field(default_factory=lambda: uuid4().hex)

class JSONRPCRequest(JSONRPCMessage):
    method: str
    params: Optional[dict[str, Any]] = None

class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

class JSONRPCResponse(JSONRPCMessage):
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None

class InternalError(JSONRPCError):
    code: int = -32603
    message: str = "Internal error"

# --- A2A Models ---

class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    capabilities: List[str] = []

class TextPart(BaseModel):
    text: str

class Message(BaseModel):
    role: str
    parts: List[TextPart]

class TaskState(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskStatus(BaseModel):
    state: TaskState
    timestamp: datetime = Field(default_factory=datetime.now)

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sessionId: str
    status: TaskStatus
    history: List[Message] = []

class SendTaskParams(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sessionId: str
    message: Message

class SendTaskRequest(JSONRPCRequest):
    method: str = "tasks/send"
    params: SendTaskParams

class SendTaskResponse(JSONRPCResponse):
    result: Optional[Task] = None
