from pydantic import BaseModel, Field
from typing import List, Optional, Any


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
    message: str


class AnalyzeResponse(BaseModel):
    reply: str
    code: str
    artifacts: str
    artifact_is_mime_type: bool


class AnalysisResponseModalChatbot(BaseModel):
    explanation: str = Field(
        ..., description="2-4 sentence description of your analysis approach"
    )
    code: str = Field(..., description="Python code that performs the analysis")
    plot: str = Field(
        ...,
        description="Either 'plot_created' if visualization made, or 'no_plot' if not",
    )
