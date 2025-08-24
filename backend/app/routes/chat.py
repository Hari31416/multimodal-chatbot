"""
Chat endpoints implementing the proper storage workflow.

These endpoints handle chat message creation, LLM responses, and artifact management
following the workflow described in storage_options_temp.md.
"""

from fastapi import APIRouter, HTTPException, Form
from typing import Optional

from app.models.models import ChatRequest, ChatRequestVision
from app.models.response_models import MessageResponse
from app.models.object_models import Message
from app.services.message_service import message_service
from app.services.session_assembler import session_assembler
from app.services import llm
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: str = Form(...), session_id: str = Form(...), user_id: str = Form(...)
):
    """
    Send a chat message and get LLM response.

    Follows the workflow:
    1. Create user message in cache
    2. Store message in Redis cache
    3. Add message ID to session index
    4. Update session's last updated time
    5. Get LLM response
    6. Create assistant message with any artifacts
    7. Store assistant message and update indexes
    """
    try:
        # Step 1-4: Create user message
        user_message = await message_service.create_user_message(
            session_id=session_id, user_id=user_id, content=message
        )

        if user_message is None:
            raise HTTPException(
                status_code=404, detail="Session not found or access denied"
            )

        # Step 5: Get LLM response
        try:
            llm_response = await llm.text_completion(message, session_id=session_id)
        except Exception as e:
            logger.error(f"LLM completion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate response")

        # Step 6-7: Create assistant message
        assistant_message = await message_service.create_assistant_message(
            session_id=session_id,
            user_id=user_id,
            content=llm_response,
            artifacts=None,  # TODO: Handle artifacts from LLM if any
        )

        if assistant_message is None:
            raise HTTPException(
                status_code=500, detail="Failed to save assistant response"
            )

        # Return the assistant message
        return MessageResponse(
            messageId=assistant_message.messageId,
            sessionId=assistant_message.sessionId,
            role=assistant_message.role,
            timestamp=assistant_message.timestamp,
            content=assistant_message.content,
            artifacts=assistant_message.artifacts or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send-with-vision", response_model=MessageResponse)
async def send_message_with_vision(
    message: str = Form(...),
    session_id: str = Form(...),
    user_id: str = Form(...),
    image_data: Optional[str] = Form(None, description="Base64 encoded image data"),
):
    """
    Send a chat message with optional image and get vision-enabled LLM response.
    """
    try:
        # Create user message (artifacts for images handled separately)
        user_message = await message_service.create_user_message(
            session_id=session_id, user_id=user_id, content=message
        )

        if user_message is None:
            raise HTTPException(
                status_code=404, detail="Session not found or access denied"
            )

        # Get vision LLM response
        try:
            if image_data:
                # Decode base64 image data
                import base64

                image_bytes = base64.b64decode(image_data)
                llm_response = await llm.vision_completion(
                    message=message, image_bytes=image_bytes, session_id=session_id
                )
            else:
                llm_response = await llm.text_completion(message, session_id=session_id)
        except Exception as e:
            logger.error(f"Vision LLM completion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate response")

        # Create assistant message
        assistant_message = await message_service.create_assistant_message(
            session_id=session_id,
            user_id=user_id,
            content=llm_response,
            artifacts=None,  # TODO: Handle artifacts from LLM if any
        )

        if assistant_message is None:
            raise HTTPException(
                status_code=500, detail="Failed to save assistant response"
            )

        return MessageResponse(
            messageId=assistant_message.messageId,
            sessionId=assistant_message.sessionId,
            role=assistant_message.role,
            timestamp=assistant_message.timestamp,
            content=assistant_message.content,
            artifacts=assistant_message.artifacts or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process vision chat message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze", response_model=MessageResponse)
async def analyze_data(
    message: str = Form(...), session_id: str = Form(...), user_id: str = Form(...)
):
    """
    Analyze data and get response with potential code artifacts.
    """
    try:
        # Create user message
        user_message = await message_service.create_user_message(
            session_id=session_id, user_id=user_id, content=message
        )

        if user_message is None:
            raise HTTPException(
                status_code=404, detail="Session not found or access denied"
            )

        # Get analysis response
        try:
            # TODO: This needs to be updated when llm.analyze_data is properly implemented
            # For now, treating as regular text completion
            llm_response = await llm.text_completion(message, session_id=session_id)
        except Exception as e:
            logger.error(f"Analysis completion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate analysis")

        # Create assistant message
        assistant_message = await message_service.create_assistant_message(
            session_id=session_id,
            user_id=user_id,
            content=llm_response,
            artifacts=None,  # TODO: Handle code artifacts from analysis
        )

        if assistant_message is None:
            raise HTTPException(
                status_code=500, detail="Failed to save analysis response"
            )

        return MessageResponse(
            messageId=assistant_message.messageId,
            sessionId=assistant_message.sessionId,
            role=assistant_message.role,
            timestamp=assistant_message.timestamp,
            content=assistant_message.content,
            artifacts=assistant_message.artifacts or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, user_id: str):
    """
    Get chat history for a session using the optimized session assembler.
    """
    try:
        complete_session = await session_assembler.get_complete_session(
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
