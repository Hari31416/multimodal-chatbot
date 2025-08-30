"""
Chat endpoints implementing the proper storage workflow.

These endpoints handle chat message creation, LLM responses, and artifact management
following the workflow described in storage_options_temp.md.
"""

from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from typing import Optional, List, Union
import pandas as pd
import io
import base64

from app.models.models import ChatRequest, ChatRequestVision
from app.models.response_models import MessageResponse, ImageArtifact, CSVArtifact
from app.models.object_models import Message
from app.services.chat.message_service import message_service
from app.services.chat.session_service import session_service
from app.services.storage.redis_cache import redis_cache
from app.services import llm
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def handle_vision_request(
    message: str,
    image_artifacts: List[ImageArtifact],
    session_id: str,
    user_id: str,
) -> MessageResponse:
    """
    Handle a vision request by decoding the image and calling the vision completion service.
    """
    try:
        response = await llm.vision_completion(
            message=message,
            image_artifacts=image_artifacts,
            session_id=session_id,
            user_id=user_id,
        )
        response = MessageResponse(**response.model_dump())
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process vision chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_data_analysis_request(
    message: str,
    df_artifact: CSVArtifact,
    image_artifacts: Optional[Union[ImageArtifact, List[ImageArtifact]]] = None,
    session_id: str = None,
    user_id: str = None,
) -> MessageResponse:
    """
    Handle a data analysis request by calling the analyze_data service.
    """
    try:
        response = await llm.analyze_data(
            message=message,
            df_artifact=df_artifact,
            image_artifacts=image_artifacts,
            session_id=session_id,
            user_id=user_id,
        )
        response = MessageResponse(**response.model_dump())
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process data analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=MessageResponse)
async def send_message(
    message: str = Form(...),
    session_id: str = Form(...),
    user_id: str = Form(...),
    artifact_ids: Optional[str] = Form(None),
):
    """
    Send a chat message and get LLM response. A single endpoint to handle text,
    vision, and data analysis requests based on provided artifact IDs.

    - If no artifact IDs are provided, it's a text-only request.
    - If image artifact IDs are provided, it's a vision request.
    - If a CSV artifact ID is provided, it's a data analysis request.
    """
    artifact_ids = artifact_ids.split(",") if artifact_ids else []
    artifacts_from_session = set(
        redis_cache.get_file_artifact_ids_for_session(session_id)
    )
    artifact_ids_final = []
    for artifact_id in artifact_ids or []:
        if artifact_id in artifacts_from_session:
            artifact_ids_final.append(artifact_id)
        else:
            logger.warning(
                f"Artifact ID {artifact_id} not found in session {session_id}. Either it doesn't exist or access is denied."
            )

    logger.debug(
        f"Artifact IDs provided: {artifact_ids}, valid artifact IDs for session {session_id}: {artifact_ids_final}"
    )
    logger.info(f"Total valid artifact IDs to attach: {len(artifact_ids_final)}")
    artifacts = await session_service._batch_fetch_artifacts(artifact_ids_final)
    artifacts = [art for _, art in artifacts.items() if art is not None]
    unique_artifact_types = set(art.type for art in artifacts)
    logger.info(f"Unique artifact types to attach: {unique_artifact_types}")

    if len(unique_artifact_types) == 1 and "image" in unique_artifact_types:
        logger.info("Handling as vision request")
        return await handle_vision_request(
            message=message,
            image_artifacts=artifacts,
            session_id=session_id,
            user_id=user_id,
        )

    if len(unique_artifact_types) == 1 and "csv" in unique_artifact_types:
        logger.info("Handling as data analysis request.")
        if len(unique_artifact_types) > 1:
            logger.warning(
                "Multiple artifact types found for data analysis request. Only CSV artifacts will be considered."
            )
        return await handle_data_analysis_request(
            message=message,
            df_artifact=artifacts[0],
            session_id=session_id,
            user_id=user_id,
        )

    if "csv" in unique_artifact_types:
        logger.info("Handling as data analysis request with image artifacts.")
        df_artifact = next((art for art in artifacts if art.type == "csv"), None)
        image_artifacts = [art for art in artifacts if art.type == "image"]
        return await handle_data_analysis_request(
            message=message,
            df_artifact=df_artifact,
            image_artifacts=image_artifacts if image_artifacts else None,
            session_id=session_id,
            user_id=user_id,
        )

    logger.info("Handling as text-only request")
    try:
        response = await llm.text_completion(
            message=message,
            session_id=session_id,
            user_id=user_id,
        )
        response = MessageResponse(**response.model_dump())
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process text chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, user_id: str):
    """
    Get chat history for a session using the optimized session assembler.
    """
    try:
        complete_session = await session_service.get_complete_session(
            session_id, user_id
        )

        if complete_session is None:
            raise HTTPException(
                status_code=404, detail="Session not found or access denied"
            )

        # Extract messages for legacy compatibility
        messages = []
        for msg in complete_session.messages:
            # Convert to legacy format
            messages.append({"role": msg.role, "content": msg.content})

        return {"sessionId": session_id, "messages": messages}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
