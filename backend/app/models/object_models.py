"""Models for various objects used in the application."""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union, Dict, Literal
from datetime import datetime
import uuid


def generate_random_id() -> str:
    """Generate a random ID."""
    return str(uuid.uuid4())


def generate_random_id_and_add_prefix(prefix: str) -> str:
    """Generate a random ID with a given prefix."""
    id_ = str(uuid.uuid4())
    return f"{prefix}_{id_}"


different_ids_factory = {
    "session": lambda: generate_random_id_and_add_prefix("session"),
    "message": lambda: generate_random_id_and_add_prefix("message"),
    "response": lambda: generate_random_id_and_add_prefix("response"),
    "artifact": lambda: generate_random_id_and_add_prefix("artifact"),
    "chat": lambda: generate_random_id_and_add_prefix("chat"),
}


class BaseArtifact(BaseModel):
    artifactId: str = Field(
        default_factory=different_ids_factory["artifact"],
        description="Unique artifact ID",
    )
    type: Literal["chart", "table", "image", "csv", "code"] = Field(
        ..., description="Type of the artifact"
    )
    data: Union[str, bytes] = Field(..., description="Data representing the artifact")
    url: Optional[str] = Field(
        None, description="URL of the uploaded artifact if applicable"
    )
    description: Optional[str] = Field(
        None, description="Optional description of the artifact"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp in UTC"
    )

    def __repr__(self) -> str:
        return f"<Artifact id={self.artifactId} type={self.type} description={self.description} data_length={len(self.data) if self.data else 0}>"


class ImageArtifact(BaseArtifact):
    type: Literal["image"] = Field("image", description="Type of the artifact")
    width: Optional[int] = Field(None, description="Width of the image")
    height: Optional[int] = Field(None, description="Height of the image")
    format: Optional[str] = Field(None, description="Format of the image")
    thumbnail_data: Optional[str] = Field(
        None, description="Base64 encoded thumbnail image data"
    )
    alt_text: Optional[str] = Field(None, description="Alt text for the image")


class CSVArtifact(BaseArtifact):
    type: Literal["csv"] = Field("csv", description="Type of the artifact")
    num_rows: Optional[int] = Field(None, description="Number of rows in the CSV")
    num_columns: Optional[int] = Field(None, description="Number of columns in the CSV")


class TextArtifact(BaseArtifact):
    type: Literal["text"] = Field("text", description="Type of the artifact")
    data: str = Field(..., description="Text data representing the artifact")
    length: Optional[int] = Field(None, description="Length of the text data")


class CodeArtifact(BaseArtifact):
    type: Literal["code"] = Field("code", description="Type of the artifact")
    data: str = Field(..., description="Code data representing the artifact")
    length: Optional[int] = Field(None, description="Length of the code data")
    language: Optional[str] = Field(
        None, description="Programming language of the code"
    )


Artifact = Union[ImageArtifact, CSVArtifact, TextArtifact, CodeArtifact]


class Message(BaseModel):
    messageId: str = Field(
        default_factory=different_ids_factory["message"],
        description="Unique message ID",
    )
    sessionId: str = Field(..., description="Session ID associated with the message")
    role: Literal["user", "assistant", "system", "tool"] = Field(
        ..., description="Role of the message sender"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Message timestamp in UTC"
    )
    content: str = Field(..., description="Content of the message")
    artifacts: Optional[List[Artifact]] = Field(
        None, description="List of artifacts associated with the message"
    )

    def __repr__(self) -> str:
        return f"<Message id={self.messageId} role={self.role} content={self.content[:20]}...> artifacts={len(self.artifacts) if self.artifacts else 0}>"


# all data required to reconstruct a session
class Session(BaseModel):
    sessionId: str = Field(
        default_factory=different_ids_factory["session"],
        description="Unique session ID",
    )
    userId: Optional[str] = Field(
        None, description="User ID associated with the session"
    )
    createdAt: datetime = Field(
        default_factory=datetime.now, description="Session creation timestamp in UTC"
    )
    updatedAt: datetime = Field(
        default_factory=datetime.now,
        description="Session last updated timestamp in UTC",
    )
    title: Optional[str] = Field(
        None, description="Optional title for the chat session"
    )
    messages: List[Message] = Field(
        default_factory=list, description="List of messages in the chat session"
    )
    numMessages: int = Field(0, description="Number of messages in the session")

    def __repr__(self) -> str:
        return f"<Session id={self.sessionId} userId={self.userId} title={self.title} numMessages={len(self.messages)}>"


# a brief session info without messages and artifacts
class SessionInfo(BaseModel):
    sessionId: str = Field(
        default_factory=different_ids_factory["session"],
        description="Unique session ID",
    )
    userId: Optional[str] = Field(
        None, description="User ID associated with the session"
    )
    createdAt: datetime = Field(
        default_factory=datetime.now, description="Session creation timestamp in UTC"
    )
    updatedAt: datetime = Field(
        default_factory=datetime.now,
        description="Session last updated timestamp in UTC",
    )
    title: Optional[str] = Field(
        None, description="Optional title for the chat session"
    )
    numMessages: int = Field(0, description="Number of messages in the session")
    numArtifacts: int = Field(0, description="Number of artifacts in the session")

    def __repr__(self) -> str:
        return f"<SessionInfo id={self.sessionId} userId={self.userId} title={self.title} numMessages={self.numMessages} numArtifacts={self.numArtifacts}>"
