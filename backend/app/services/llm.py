from litellm import acompletion
from typing import List, Any, AsyncGenerator, Dict, Optional, Union
import os
from dotenv import load_dotenv
import pandas as pd
from PIL import Image

from app.models.object_models import (
    Message,
    Artifact,
    ImageArtifact,
    CSVArtifact,
    CodeArtifact,
    TextArtifact,
)
from app.utils import convert_bytes_to_base64, create_simple_logger
from app.prompts import Prompts
from app.services.analyzer import handle_llm_response
from app.models.models import AnalysisResponseModalChatbot, AnalyzeResponse
from app.services.chat.chat_utils import get_messages, push_messages
from app.services.storage import redis_cache, ImageHandler, DataFrameHandler


# TODO: Legacy session_storage adapter - temporary compatibility layer
class LegacySessionStorageAdapter:
    """Temporary adapter to make existing LLM code work with Redis."""

    def __init__(self):
        self.cache = redis_cache

    def get_messages(self, session_id: str):
        """Get messages in legacy format."""
        try:
            # Use default user for legacy compatibility
            message_ids = self.cache.get_message_ids_for_session(session_id)
            if not message_ids:
                return []

            messages = []
            for msg_id in message_ids:
                msg = self.cache.get_message(msg_id)
                if msg:
                    messages.append({"role": msg.role, "content": msg.content})
            return messages
        except:
            return []

    def put_session_id(self, session_id: str):
        """Legacy compatibility - session creation is handled elsewhere."""
        pass

    def push_messages(self, session_id: str, message_dict: dict):
        """Legacy compatibility - message creation is handled elsewhere."""
        # In the new system, messages are created by MessageService
        # This is called after the fact, so we can ignore it
        pass


session_storage = LegacySessionStorageAdapter()

load_dotenv()

model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")
logger = create_simple_logger(__name__)
MAX_MESSAGES = 20


user_id = "default_user"  # TODO: Extract from authentication


async def atext_completion(messages: List[Dict[str, Any]], **kwargs: Dict) -> str:
    """Return full (non-streaming) completion text asynchronously.
    messages: list of {role, content}
    """
    if "stream" in kwargs:
        kwargs["stream"] = False
    try:
        response = await acompletion(
            model=kwargs.get("model", model),
            messages=messages,
            **kwargs,
        )
    except Exception as e:
        print(f"Error during async completion: {e}")
        return ""
    return response["choices"][0]["message"]["content"]


async def atext_completion_stream(
    messages: List[Dict[str, Any]], **kwargs: Dict
) -> AsyncGenerator[str, None]:
    """Async generator yielding incremental completion chunks without duplicates."""
    if "stream" not in kwargs:
        kwargs["stream"] = True
    kwargs["stream"] = True
    try:
        response_stream = await acompletion(
            model=kwargs.get("model", model),
            messages=messages,
            **kwargs,
        )
    except Exception as e:
        print(f"Error during async streaming completion: {e}")
        raise e

    assembled = ""
    async for chunk in response_stream:
        try:
            choice = (
                chunk["choices"][0] if isinstance(chunk, dict) else chunk.choices[0]
            )
        except Exception:
            continue

        delta = None
        if isinstance(choice, dict):
            delta = choice.get("delta") or choice.get("message")
        else:
            delta = getattr(choice, "delta", None) or getattr(choice, "message", None)

        token = ""
        if delta is not None:
            if isinstance(delta, dict):
                token = delta.get("content") or ""
            else:
                token = getattr(delta, "content", "") or ""

        if not token:
            continue

        if token.startswith(assembled):
            new_part = token[len(assembled) :]
        else:
            new_part = token
        if new_part:
            assembled += new_part
            yield new_part


async def _handle_messages_push(
    session_id: str,
    user_id: str,
    current_message: Message,
    system_prompt: str,
    artifacts: Optional[List[Artifact]] = None,
    include_artifacts: bool = True,
) -> None:
    """Helper function to handle pushing messages to session storage."""
    past_messages = await get_messages(session_id, user_id, include_artifacts)

    if not past_messages:
        logger.info(
            f"No past messages found for session {session_id}, initializing with system message."
        )
        past_messages = Message(
            sessionId=session_id,
            role="system",
            content=system_prompt,
        )
        await push_messages(
            messages=[past_messages],
            session_id=session_id,
            user_id=user_id,
            artifacts=None,  # if any artifact, it should be attached to the user message
            push_artifacts_in_message=True,
        )
    else:
        logger.info(
            f"A total of {len(past_messages)} past messages found for session {session_id}. Adding new message."
        )

    await push_messages(
        messages=[current_message],
        session_id=session_id,
        user_id=user_id,
        artifacts=[artifacts] if artifacts else None,
        push_artifacts_in_message=True,
    )
    messages = await get_messages(session_id, user_id, include_artifacts)
    logger.info(f"Total messages after push: {len(messages)}")

    if len(messages) > MAX_MESSAGES:
        logger.warning(
            f"Session {session_id} has more than {MAX_MESSAGES} messages, limiting to last {MAX_MESSAGES}."
        )
        messages = messages[-MAX_MESSAGES:]
    return messages


async def text_completion(message: str, session_id: str, user_id: str) -> Message:
    system_prompt = Prompts.SIMPLE_CHAT
    current_message = Message(
        sessionId=session_id,
        role="user",
        content=message,
    )
    messages = await _handle_messages_push(
        session_id=session_id,
        user_id=user_id,
        current_message=current_message,
        system_prompt=system_prompt,
        artifacts=None,
        include_artifacts=True,
    )

    try:
        response = await atext_completion(messages, session_id=session_id)
        response_message = Message(
            sessionId=session_id,
            role="assistant",
            content=response,
        )
        await push_messages(
            messages=[response_message],
            session_id=session_id,
            user_id=user_id,
            artifacts=None,
            push_artifacts_in_message=False,
        )
    except Exception as e:
        logger.warning(f"Error during text completion: {e}")
        return ""
    return response_message


async def vision_completion(
    message: str, image: Union[bytes, Image.Image], session_id: str, user_id: str
) -> Message:
    system_prompt = Prompts.SIMPLE_CHAT_WITH_IMAGE
    current_message = Message(
        sessionId=session_id,
        role="user",
        content=message,
    )
    image: ImageHandler = ImageHandler(data=image, compression=None)
    image_base64 = image.get_base64_representation()
    image_artifact = ImageArtifact(
        type="image",
        data=image_base64,
        description=f"Image artifact for message in session {session_id} messageid {current_message.messageId}",
    )
    messages = await _handle_messages_push(
        session_id=session_id,
        user_id=user_id,
        current_message=current_message,
        system_prompt=system_prompt,
        artifacts=[image_artifact],
        include_artifacts=True,
    )

    try:
        response = await atext_completion(messages, session_id=session_id)
        response_message = Message(
            sessionId=session_id,
            role="assistant",
            content=response,
        )
        await push_messages(
            messages=[response_message],
            session_id=session_id,
            user_id=user_id,
            artifacts=None,
            push_artifacts_in_message=False,
        )
    except Exception as e:
        print(f"Error during vision completion: {e}")
        return ""
    return response_message


async def analyze_data(
    df: pd.DataFrame,
    message: str,
    session_id: str = None,
    user_id: str = None,
    try_number: int = 0,
) -> AnalyzeResponse:
    """
    Analyze the DataFrame based on the provided message.
    """
    if try_number == 3:
        logger.error(f"Maximum retry attempts reached for session {session_id}.")
        return AnalyzeResponse(
            reply="Error during calling the LLM for data analysis. Please try again later.",
            code="",
            artifact="",
            artifact_is_mime_type=False,
            code_execution_failed=True,
        )
    system_prompt = Prompts.format_system_prompt_for_analyzer(df)
    current_message = Message(
        sessionId=session_id,
        role="user",
        content=message,
    )

    if try_number == 0:
        df_artifact = CSVArtifact(
            type="csv",
            data=DataFrameHandler(data=df).get_base64_representation(),
            description=f"CSV Artifact for message in session {session_id} messageid {current_message.messageId}",
            num_rows=len(df),
            num_columns=len(df.columns),
        )
        messages = await _handle_messages_push(
            session_id=session_id,
            user_id=user_id,
            current_message=current_message,
            system_prompt=system_prompt,
            artifacts=[df_artifact],
            include_artifacts=True,
        )
    else:
        messages = await _handle_messages_push(
            session_id=session_id,
            user_id=user_id,
            current_message=current_message,
            system_prompt=system_prompt,
            artifacts=None,
            include_artifacts=True,
        )

    try:
        response = await atext_completion(
            messages,
            session_id=session_id,
            response_format=AnalysisResponseModalChatbot,
            temperature=0.5,
        )
        response_message = Message(
            sessionId=session_id,
            role="assistant",
            content=response,
        )
        await push_messages(
            messages=[response_message],
            session_id=session_id,
            user_id=user_id,
            artifacts=None,
            push_artifacts_in_message=False,
        )
    except Exception as e:
        logger.error(f"Error during calling the LLM for data analysis: {e}")
        return AnalyzeResponse(
            reply="Error during calling the LLM for data analysis. Please try again.",
            code="",
            artifact="",
            artifact_is_mime_type=False,
        )

    result = await handle_llm_response(
        response=response,
        df=df,
    )

    if result.code_execution_failed:
        logger.warning(f"Code execution failed in LLM response handling. Trying again.")
        return await analyze_data(
            df=df,
            message=result.reply,
            session_id=session_id,
            user_id=user_id,
            try_number=try_number + 1,
        )

    result_message = Message(
        sessionId=session_id,
        role="user",
        content=result.reply,
    )
    artifacts = []
    if result.code:
        logger.info(f"Code generated. Creating code artifact.")
        code_artifact = CodeArtifact(
            type="code",
            data=result.code,
            description=f"Code artifact for message in session {session_id} messageid {current_message.messageId}",
            language="python",
        )
        artifacts.append(code_artifact)

    if result.artifact and result.artifact_is_mime_type:
        logger.info(f"Image generated. Creating image artifact.")
        base64_code = result.artifact.split("base64,")[-1]
        image_handler = ImageHandler(data=base64_code)
        pil_image = image_handler.get_python_friendly_format()
        image_artifact = ImageArtifact(
            type="image",
            data=base64_code,
            description=f"Image artifact for message in session {session_id} messageid {current_message.messageId}",
            height=pil_image.height if pil_image else 0,
            width=pil_image.width if pil_image else 0,
            format=image_handler.image_format.lower() if pil_image else "png",
            thumbnail_data=image_handler.get_thumbnail_base64((128, 128)),
        )
        artifacts.append(image_artifact)

    if result.artifact and not result.artifact_is_mime_type:
        logger.info(f"Text generated. Creating text artifact.")
        text_data = result.artifact
        artifact = TextArtifact(
            type="text",
            data=text_data,
            description=f"Text artifact for message in session {session_id} messageid {current_message.messageId}",
            length=len(text_data),
        )
        artifacts.append(artifact)

    logger.info(f"Pushing final response message and {len(artifacts)} artifacts.")
    await push_messages(
        messages=[result_message],
        session_id=session_id,
        user_id=user_id,
        artifacts=[artifacts],
        push_artifacts_in_message=True,
    )
    return result
