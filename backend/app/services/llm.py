from litellm import acompletion
from typing import List, Any, AsyncGenerator, Dict
import os
from dotenv import load_dotenv
import pandas as pd

from .storage.redis_cache import redis_cache
from app.models.object_models import Message


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
from app.utils import convert_bytes_to_base64, create_simple_logger
from app.prompts import Prompts
from app.services.analyzer import handle_llm_response
from app.models.models import AnalysisResponseModalChatbot, AnalyzeResponse

load_dotenv()

model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")
logger = create_simple_logger(__name__)
MAX_MESSAGES = 20


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


def _handle_messages_push(
    session_id: str, current_message: Dict[str, Any], system_prompt: str
) -> None:
    """Helper function to handle pushing messages to session storage."""
    past_messages = session_storage.get_messages(session_id)

    if past_messages is None:
        logger.info(
            f"No past messages found for session {session_id}, initializing with system message."
        )
        session_storage.put_session_id(session_id)
        past_messages = [{"role": "system", "content": system_prompt}]
        session_storage.push_messages(session_id, past_messages[0])
    else:
        logger.info(
            f"A total of {len(past_messages)} past messages found for session {session_id}. Adding new message."
        )

    session_storage.push_messages(session_id, current_message)
    messages = past_messages + [current_message]

    if len(messages) > MAX_MESSAGES:
        logger.warning(
            f"Session {session_id} has more than {MAX_MESSAGES} messages, limiting to last {MAX_MESSAGES}."
        )
        messages = messages[-MAX_MESSAGES:]
    return messages


async def text_completion(message: str, session_id: str = None) -> str:
    system_prompt = Prompts.SIMPLE_CHAT
    current_message = {"role": "user", "content": message}
    messages = _handle_messages_push(
        session_id=session_id,
        current_message=current_message,
        system_prompt=system_prompt,
    )

    try:
        response = await atext_completion(messages, session_id=session_id)
        session_storage.push_messages(
            session_id, {"role": "assistant", "content": response}
        )
    except Exception as e:
        print(f"Error during text completion: {e}")
        return ""
    return response


async def vision_completion(message: str, image_bytes: bytes, session_id: str) -> str:
    system_prompt = Prompts.SIMPLE_CHAT_WITH_IMAGE
    current_message = {
        "role": "user",
        "content": [
            {"type": "text", "text": message},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{convert_bytes_to_base64(image_bytes)}",
                },
            },
        ],
    }
    messages = _handle_messages_push(
        session_id=session_id,
        current_message=current_message,
        system_prompt=system_prompt,
    )

    try:
        response = await atext_completion(messages, session_id=session_id)
        session_storage.push_messages(
            session_id, {"role": "assistant", "content": response}
        )
    except Exception as e:
        print(f"Error during vision completion: {e}")
        return ""
    return response


async def analyze_data(
    df: pd.DataFrame,
    message: str,
    session_id: str = None,
) -> AnalyzeResponse:
    """
    Analyze the DataFrame based on the provided message.
    """
    system_prompt = Prompts.format_system_prompt_for_analyzer(df)
    current_message = {"role": "user", "content": message}

    messages = _handle_messages_push(
        session_id=session_id,
        current_message=current_message,
        system_prompt=system_prompt,
    )

    try:
        response = await atext_completion(
            messages,
            session_id=session_id,
            response_format=AnalysisResponseModalChatbot,
            temperature=0.5,
        )
        session_storage.push_messages(
            session_id, {"role": "assistant", "content": response}
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

    # if no mime type, artifact is the result of code execution
    # push the result to session storage for future reference
    if not result.artifact_is_mime_type and session_id:
        session_storage.push_messages(
            session_id, {"role": "assistant", "content": result.artifact}
        )
    return result
