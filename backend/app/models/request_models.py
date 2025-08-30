"""Models for various request bodies from the frontend."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


# Request with artifactid


class GetArtifactRequest(BaseModel):
    sessionId: str = Field(..., description="Session ID")
    artifactId: str = Field(..., description="Artifact ID")
    userId: Optional[str] = Field(
        None, description="Optional user ID associated with the session"
    )


# requests with sessionId


class SessionInfoRequest(BaseModel):
    sessionId: str = Field(..., description="Session ID")
    userId: Optional[str] = Field(
        None, description="Optional user ID associated with the session"
    )


class DeleteSessionRequest(SessionInfoRequest): ...


class SessionRequest(SessionInfoRequest): ...


# Requests with messageId


class MessageRequest(BaseModel):
    sessionId: str = Field(..., description="Session ID")
    messageId: str = Field(..., description="Message ID")
    userId: Optional[str] = Field(
        None, description="Optional user ID associated with the session"
    )


# For file uploads


class CSVUploadRequest(SessionInfoRequest):
    delimiter: Optional[str] = Field(
        ",", description="Delimiter used in the CSV file, default is ','"
    )
    header: Optional[bool] = Field(
        True, description="Whether the CSV file has a header row, default is True"
    )
    encoding: Optional[str] = Field(
        "utf-8", description="Encoding of the CSV file, default is 'utf-8'"
    )


class ImageUploadRequest(SessionInfoRequest):
    caption: Optional[str] = Field(
        None, description="Optional caption or description for the image"
    )
    alt_text: Optional[str] = Field(None, description="Optional alt text for the image")
