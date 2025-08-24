from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.models import models
from app.services import storage, llm
from app.utils import create_simple_logger


load_dotenv()

logger = create_simple_logger(__name__)

app = FastAPI(title="Multimodal Chatbot", version="0.2.0")
# TODO: Legacy session_storage - needs to be replaced with Redis implementation
# session_storage = storage.session_storage
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")


from app.routes import sessions, artifacts, uploads, chat
from app.models.response_models import HealthResponse


load_dotenv()


app = FastAPI(title="Multimodal Chatbot", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(root.router)
app.include_router(sessions.router)
app.include_router(artifacts.router)
app.include_router(uploads.router)
app.include_router(chat.router)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/chat", response_model=models.ChatResponse)
async def chat_legacy(body: models.ChatRequest):
    """Legacy chat endpoint - redirects to new chat workflow."""
    from app.services.message_service import message_service
    from app.services import llm

    # For backward compatibility, use a default user_id if not provided
    user_id = "default_user"  # TODO: Extract from authentication

    if not body.sessionId:
        raise HTTPException(status_code=400, detail="Session ID is required")

    try:
        # Create user message
        user_message = await message_service.create_user_message(
            session_id=body.sessionId, user_id=user_id, content=body.message
        )

        if user_message is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get LLM response
        reply = await llm.text_completion(body.message, session_id=body.sessionId)

        # Create assistant message
        await message_service.create_assistant_message(
            session_id=body.sessionId, user_id=user_id, content=reply
        )

        return {"reply": reply}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Legacy chat endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat processing failed")


@app.post("/all-previous-chats", response_model=models.AllChatResponse)
async def all_previous_chats_legacy(sessionId: str = Form(...)):
    """Legacy endpoint for getting chat history."""
    from app.services.session_assembler import session_assembler

    user_id = "default_user"  # TODO: Extract from authentication

    try:
        complete_session = await session_assembler.get_complete_session(
            sessionId, user_id
        )

        if complete_session is None:
            # Return empty messages for backward compatibility
            return models.AllChatResponse(sessionId=sessionId, messages=[])

        # Convert to legacy format
        messages = []
        for msg in complete_session.messages:
            if msg.role != "system":  # Filter out system messages
                messages.append(
                    models.OneChatMessage(role=msg.role, content=msg.content)
                )

        return models.AllChatResponse(sessionId=sessionId, messages=messages)

    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        return models.AllChatResponse(sessionId=sessionId, messages=[])


@app.post("/delete-session", response_model=models.DeleteSessionResponse)
async def delete_session_legacy(sessionId: str = Form(...)):
    """Legacy endpoint for deleting sessions."""
    from app.services.storage.redis_cache import redis_cache

    user_id = "default_user"  # TODO: Extract from authentication

    try:
        deleted_count = redis_cache.delete_session_with_ownership(
            sessionId, user_id, cascade=True
        )

        if deleted_count == 0:
            return {"message": "Session not found or already deleted"}

        return {"message": "Session deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        return {"message": "Session not found or already deleted"}


@app.post("/vision-chat", response_model=models.ChatResponse)
async def vision_chat_legacy(
    message: str = Form(...),
    image: UploadFile = File(...),
    sessionId: str | None = Form(None),
):
    """Legacy vision chat endpoint."""
    from app.services.message_service import message_service

    user_id = "default_user"  # TODO: Extract from authentication

    # Basic validation
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    if not sessionId:
        raise HTTPException(status_code=400, detail="Session ID is required")

    try:
        # Create user message
        user_message = await message_service.create_user_message(
            session_id=sessionId, user_id=user_id, content=message
        )

        if user_message is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # Process image and get LLM response
        image_bytes = await image.read()
        reply = await llm.vision_completion(
            message=message, image_bytes=image_bytes, session_id=sessionId
        )

        # Create assistant message
        await message_service.create_assistant_message(
            session_id=sessionId, user_id=user_id, content=reply
        )

        return {"reply": reply}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Vision chat processing failed")


@app.post("/analyze", response_model=models.AnalyzeResponse)
async def analyze_legacy(body: models.AnalyzeRequest):
    """Legacy analyze endpoint."""
    from app.services.message_service import message_service

    user_id = "default_user"  # TODO: Extract from authentication

    try:
        # Create user message
        user_message = await message_service.create_user_message(
            session_id=body.sessionId, user_id=user_id, content=body.message
        )

        if user_message is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # TODO: Implement proper dataframe retrieval from Redis artifacts
        # For now, return a placeholder response
        raise HTTPException(
            status_code=501,
            detail="Analysis endpoint not yet implemented with Redis backend",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis processing failed")


# Simple root redirect/info
@app.get("/")
async def root():
    return {
        "message": "Multimodal Chatbot running",
    }
