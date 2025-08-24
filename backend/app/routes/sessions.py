from fastapi import APIRouter, HTTPException

from app.models.response_models import (
    CreateNewSessionResponse,
    SessionInfoResponse,
    AllSessionInfoResponse,
    DeleteSessionResponse,
    MessageResponse,
    SessionResponse,
)
from app.models.object_models import Session, Message, SessionInfo
from app.services.session_assembler import session_assembler
from app.services.storage.redis_cache import redis_cache
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/new", response_model=CreateNewSessionResponse)
async def start_new_session(user_id: str):
    """Start a new chat session."""
    logger.info(f"Starting a new chat session for user: {user_id}")

    try:
        # Create a new session
        new_session = Session(userId=user_id, title="New Chat Session")

        # Save to Redis cache
        redis_cache.save_session(new_session, cascade=False)

        logger.info(f"Created new session {new_session.sessionId} for user {user_id}")
        return CreateNewSessionResponse(sessionId=new_session.sessionId, userId=user_id)

    except Exception as e:
        logger.error(f"Failed to create new session for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create new session")


@router.get("/info/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str, user_id: str):
    """Get information about a specific chat session."""
    logger.info(f"Fetching info for session: {session_id}")

    try:
        session_info = await session_assembler.get_session_summary(session_id, user_id)

        if session_info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or access denied",
            )

        return SessionInfoResponse(
            sessionId=session_info.sessionId,
            userId=session_info.userId,
            createdAt=session_info.createdAt,
            updatedAt=session_info.updatedAt,
            title=session_info.title,
            numMessages=session_info.numMessages,
            numArtifacts=session_info.numArtifacts,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch session info {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch session info")


@router.get("/list", response_model=AllSessionInfoResponse)
async def list_all_sessions(user_id: str):
    """List all chat sessions for a user."""
    logger.info(f"Listing all chat sessions for user: {user_id}")

    try:
        sessions = await session_assembler.get_all_user_sessions(user_id)

        session_responses = [
            SessionInfoResponse(
                sessionId=session.sessionId,
                userId=session.userId,
                createdAt=session.createdAt,
                updatedAt=session.updatedAt,
                title=session.title,
                numMessages=session.numMessages,
                numArtifacts=session.numArtifacts,
            )
            for session in sessions
        ]

        return AllSessionInfoResponse(sessions=session_responses)

    except Exception as e:
        logger.error(f"Failed to list sessions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")


@router.delete("/delete/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str, user_id: str):
    """Delete a specific chat session."""
    logger.info(f"Deleting session: {session_id}")

    try:
        # Delete with cascade to remove all messages and artifacts
        deleted_count = redis_cache.delete_session_with_ownership(
            session_id, user_id, cascade=True
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or access denied",
            )

        logger.info(
            f"Successfully deleted session {session_id} with {deleted_count} Redis keys"
        )
        return DeleteSessionResponse(
            message=f"Session {session_id} deleted successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.get("/{session_id}/{message_id}", response_model=MessageResponse)
async def get_message(session_id: str, message_id: str, user_id: str):
    """Get a specific message from a chat session."""
    logger.info(f"Fetching message {message_id} from session {session_id}")

    try:
        # Get message with full ownership validation
        message = redis_cache.get_message_with_full_ownership(
            message_id, session_id, user_id
        )

        if message is None:
            raise HTTPException(
                status_code=404,
                detail=f"Message {message_id} not found or access denied",
            )

        # Get artifacts for this message
        artifact_ids = redis_cache.get_artifact_ids_for_message(message_id, session_id)
        if artifact_ids:
            artifacts = []
            for artifact_id in artifact_ids:
                artifact = redis_cache.get_artifact_with_full_ownership(
                    artifact_id, message_id, session_id, user_id
                )
                if artifact:
                    artifacts.append(artifact)
            message.artifacts = artifacts
        else:
            message.artifacts = []

        return MessageResponse(
            messageId=message.messageId,
            sessionId=message.sessionId,
            role=message.role,
            timestamp=message.timestamp,
            content=message.content,
            artifacts=message.artifacts,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch message")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user_id: str):
    """Get a complete chat session with all messages and artifacts."""
    logger.info(f"Fetching complete session: {session_id}")

    try:
        # Use the optimized session assembler
        complete_session = await session_assembler.get_complete_session(
            session_id, user_id
        )

        if complete_session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or access denied",
            )

        logger.info(
            f"Successfully assembled session {session_id} with {complete_session.numMessages} messages"
        )
        return complete_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch complete session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch session")
