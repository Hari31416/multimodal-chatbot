from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union


class HealthResponse(BaseModel):
    status: str


class ChatRequest(BaseModel):
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
    answer: str
    artifacts: Optional[Any] = None
