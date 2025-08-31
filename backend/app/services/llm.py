from litellm import acompletion
from typing import List, Any, AsyncGenerator, Dict, Optional, Union
import os
from dotenv import load_dotenv

from app.models.object_models import (
    Message,
    Artifact,
    ImageArtifact,
    CSVArtifact,
    TextArtifact,
)
from app.utils import create_simple_logger
from app.prompts import Prompts
from app.services.analyzer import handle_llm_response
from app.models.object_models import AnalysisResponseModalChatbot
from app.services.chat.chat_utils import (
    get_messages,
    push_messages,
    create_image_artifact,
)
from app.services.storage import redis_cache, DataFrameHandler


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
    message: str,
    image_artifacts: Union[ImageArtifact, List[ImageArtifact]],
    session_id: str,
    user_id: str,
) -> Message:
    system_prompt = Prompts.SIMPLE_CHAT_WITH_IMAGE
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
        artifacts=(
            [image_artifacts]
            if isinstance(image_artifacts, ImageArtifact)
            else image_artifacts
        ),
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
    message: str,
    df_artifact: CSVArtifact,
    image_artifacts: Optional[Union[ImageArtifact, List[ImageArtifact]]] = None,
    session_id: str = None,
    user_id: str = None,
    try_number: int = 0,
) -> Message:
    """
    Analyze the DataFrame based on the provided message.
    """
    if try_number == 3:
        logger.error(f"Maximum retry attempts reached for session {session_id}.")
        return Message(
            sessionId=session_id,
            role="assistant",
            content="Error during calling the LLM for data analysis after multiple attempts. Please try again later.",
        )
    if df_artifact is None:
        logger.info(
            f"No DataFrame artifact provided, fetching from session {session_id}."
        )
        df_artifact = redis_cache.get_session_csv_artifact(session_id, user_id)
        push_df_artifact = False
    else:
        push_df_artifact = True

    df_handler = DataFrameHandler(df_artifact.data)
    df = df_handler.get_python_friendly_format()
    system_prompt = Prompts.format_system_prompt_for_analyzer(df)
    current_message = Message(
        sessionId=session_id,
        role="user",
        content=message,
    )

    if try_number == 0:
        artifacts = [df_artifact] if push_df_artifact else []
        if image_artifacts:
            if isinstance(image_artifacts, ImageArtifact):
                artifacts.append(image_artifacts)
            elif isinstance(image_artifacts, list):
                artifacts.extend(image_artifacts)

        messages = await _handle_messages_push(
            session_id=session_id,
            user_id=user_id,
            current_message=current_message,
            system_prompt=system_prompt,
            artifacts=artifacts,
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
        return Message(
            sessionId=session_id,
            role="assistant",
            content="Error during calling the LLM for data analysis. Please try again later.",
        )

    result = await handle_llm_response(
        response=response,
        df=df,
    )

    if result.code_execution_failed:
        logger.warning(f"Code execution failed in LLM response handling. Trying again.")
        return await analyze_data(
            df_artifact=df_artifact,
            message=result.reply,
            session_id=session_id,
            user_id=user_id,
            try_number=try_number + 1,
        )

    if not result.code:
        logger.info(f"No code executed. Nothing extra to push.")
        return Message(
            sessionId=session_id,
            role="assistant",
            content=result.reply,
        )

    result_message = Message(
        sessionId=session_id,
        role="assistant",
        content="After running the code, here is the result. I will for any follow-up questions if needed.",
    )
    artifacts = []
    # if result.code:
    #     logger.info(f"Code generated. Creating code artifact.")
    #     code_artifact = CodeArtifact(
    #         type="code",
    #         data=result.code,
    #         description=f"Code artifact for message in session {session_id} messageid {current_message.messageId}",
    #         language="python",
    #     )
    #     artifacts.append(code_artifact)

    if result.artifact and result.artifact_is_mime_type:
        logger.info(f"Image generated. Creating image artifact.")
        base64_code = result.artifact.split("base64,")[-1]
        image_artifact = create_image_artifact(
            base64_code,
            description=f"Image artifact for message in session {session_id} messageid {current_message.messageId}",
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
    result_message.artifacts = artifacts
    return result_message
