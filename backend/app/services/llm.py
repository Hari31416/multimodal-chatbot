from litellm import acompletion
from typing import List, Any, AsyncGenerator, Dict
import os
from dotenv import load_dotenv
import pandas as pd
from io import StringIO

from .storage import SessionStorage
from .files import convert_bytes_to_base64
from ..prompts import Prompts
from ..analyzer import handle_llm_response
from ..models import AnalysisResponseModalChatbot, AnalyzeResponse
from ..utils import create_simple_logger

load_dotenv()

model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")
session_storage = SessionStorage()
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


async def text_completion(message: str, session_id: str = None) -> str:
    past_messages = session_storage.get_messages(session_id)
    if past_messages is None:
        past_messages = []

    if not past_messages:
        # Initialize with a system message if no past messages exist
        print("No past messages found, initializing with system message.")
        past_messages = [{"role": "system", "content": Prompts.SIMPLE_CHAT}]
    else:
        print(
            f"A total of {len(past_messages)} past messages found. Adding new message."
        )
    current_message = [
        {"role": "user", "content": message},
    ]
    session_storage.push_messages(session_id, current_message)
    messages = past_messages + current_message

    if len(messages) > 10:
        # Limit to last 10 messages for performance
        messages = messages[-10:]

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
    past_messages = session_storage.get_messages(session_id)
    if past_messages is None:
        past_messages = [{"role": "system", "content": Prompts.SIMPLE_CHAT_WITH_IMAGE}]

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
    session_storage.push_messages(session_id, current_message)
    messages = [
        *past_messages,
        current_message,
    ]

    if len(messages) > MAX_MESSAGES:
        # Limit to last MAX_MESSAGES messages for performance
        messages = messages[-MAX_MESSAGES:]

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
    past_messages = session_storage.get_messages(session_id)
    if past_messages is None:
        past_messages = [
            {
                "role": "system",
                "content": Prompts.format_system_prompt_for_analyzer(df),
            }
        ]

    current_message = {"role": "user", "content": message}
    session_storage.push_messages(session_id, current_message)
    messages = [
        *past_messages,
        current_message,
    ]

    if len(messages) > MAX_MESSAGES:
        # Limit to last MAX_MESSAGES messages for performance
        messages = messages[-MAX_MESSAGES:]

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
