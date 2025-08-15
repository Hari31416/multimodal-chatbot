from pydantic import BaseModel, Field
from typing import List, Optional, Any
from fastapi import File


class HealthResponse(BaseModel):
    status: str


class StartNewChatResponse(BaseModel):
    sessionId: str


class AllSessionsResponse(BaseModel):
    sessions: List[str]


class ChatRequest(BaseModel):
    message: str
    sessionId: Optional[str] = Field(
        None, description="Optional session ID for context"
    )


class ChatRequestVision(BaseModel):
    message: str
    sessionId: Optional[str] = Field(
        None, description="Optional session ID for context"
    )


class ChatResponse(BaseModel):
    reply: str


class UploadCSVResponse(BaseModel):
    sessionId: str
    columns: List[str]
    headPreview: List[List[Any]]


class AnalyzeRequest(BaseModel):
    sessionId: str
    question: str


class AnalyzeResponse(BaseModel):
    reply: str
    artifacts: Optional[Any] = None
