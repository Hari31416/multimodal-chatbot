"""Models for various endpoint responses to be passed to frontend."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

from .object_models import *


# health check /health
class HealthResponse(BaseModel):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )
    status: str = Field("ok", description="Health status of the service")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp in UTC"
    )


# Info about a single session /sessions/info/<session_id>
class SessionInfoResponse(SessionInfo):
    responseId: Optional[str] = Field(
        None, description="Optional response ID associated with the session"
    )  # only for session info endpoint


# all sessions info /sessions/list
class AllSessionInfoResponse(BaseModel):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )
    sessions: List[SessionInfoResponse] = Field(
        ..., description="List of all chat sessions with their details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp in UTC"
    )


# start new chat /sessions/new
class CreateNewSessionResponse(BaseModel):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )
    sessionId: str = Field(
        default_factory=different_ids_factory["session"],
        description="Newly created session ID",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp in UTC"
    )


# Delete a sessions /sessions/delete/<session_id>
class DeleteSessionResponse(BaseModel):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )
    message: str = Field(..., description="Result message of the delete operation")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp in UTC"
    )


# upload csv /upload/csv
class CSVUploadResponse(CSVArtifact):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )


# upload image /upload/image
class ImageUploadResponse(ImageArtifact):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )


# get artifacts /artifacts/<session_id>/<artifact_id>
class GetArtifactResponse(BaseModel):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )
    RootModel: Artifact
    model_config = ConfigDict(discriminator="type")


# simple chat-message /sessions/<session_id>/<message-id>
class MessageResponse(Message):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )


# complete session with messages /sessions/<session_id>
class SessionResponse(Session):
    responseId: str = Field(
        default_factory=different_ids_factory["response"],
        description="Unique response ID",
    )
