from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union, Dict


class HealthResponse(BaseModel):
    status: str


class StartNewChatResponse(BaseModel):
    sessionId: str


class AllSessionsResponse(BaseModel):
    sessionIds: List[str]
    titles: List[str] = Field(
        default_factory=list,
        description="Optional titles for each session, if available",
    )


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


class OneChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


class AllChatResponse(BaseModel):
    sessionId: str
    messages: List[OneChatMessage]


class UploadCSVResponse(BaseModel):
    sessionId: str
    columns: List[str]
    headPreview: List[List[Any]]


class AnalyzeRequest(BaseModel):
    sessionId: str
    message: str


class AnalyzeResponse(BaseModel):
    reply: str
    code: Optional[str]
    artifact: Optional[str]
    artifact_is_mime_type: bool
    code_execution_failed: Optional[bool] = False


class AnalysisResponseModalChatbot(BaseModel):
    explanation: str = Field(
        ..., description="2-4 sentence description of your analysis approach"
    )
    code: Optional[str] = Field(
        ..., description="Python code that performs the analysis"
    )
    plot: Optional[str] = Field(
        ...,
        description="Either 'plot_created' if visualization made, or 'no_plot' if not",
    )


class SessionInfo(BaseModel):
    session_id: str
    created_at: float
    last_accessed: float
    title: Optional[str] = "Working Session"


class DeleteSessionResponse(BaseModel):
    message: str = "Session deleted successfully"
