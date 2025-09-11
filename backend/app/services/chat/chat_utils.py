import pandas as pd
from PIL import Image
from typing import List, Optional, Union, Dict
from datetime import datetime
from pydantic import TypeAdapter
from io import StringIO
from textwrap import dedent

from .artifact_service import artifact_service
from .message_service import message_service
from .session_service import session_service

from app.models.object_models import (
    Message,
    Artifact,
    Session,
    ImageArtifact,
    CSVArtifact,
)
from app.services.storage.redis_cache import RedisCache, redis_cache
from app.services.storage.files_handler import DataFrameHandler, ImageHandler


from app.utils import create_simple_logger

logger = create_simple_logger(__name__)


def get_info_from_df_for_llm(df: pd.DataFrame) -> str:
    """Generate a summary of a DataFrame for LLM consumption.

    Args:
        df (pd.DataFrame): The DataFrame to summarize.

    Returns:
        str: A textual summary of the DataFrame.
    """
    info = "\n\n## Dataframe Information\nYou have access to a pandas DataFrame named `df`. It contains the dataset you need to analyze. The DataFrame has the following columns:\n\n"
    columns = df.columns.tolist()
    columns = ", ".join(columns)
    info += f"{columns}\n\n"

    buffer = StringIO()
    df.info(buf=buffer)
    info_ = buffer.getvalue()

    info += f"A brief description of the DataFrame is provided below:\n\n{info_}\n\n"

    head_info = df.head(min(5, len(df))).to_markdown(index=False, tablefmt="json")
    info += f"The first 5 rows of the DataFrame are as follows:\n\n{head_info}\n\n"

    info = dedent(info).strip()
    return info


def convert_message_for_llm(
    message: Message,
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """Convert a Message object to LLM-compatible format.

    Args:
        message (Message): The message to convert.

    Returns:
        Dict[str, Union[str, List[Dict[str, str]]]] The converted message with 'role' and 'content'.
    """
    content = message.content or ""
    if not message.artifacts:
        return {"role": message.role, "content": content}

    message_json = {"role": message.role}
    content_list = []
    for artifact in message.artifacts:
        if artifact.type == "image":
            content_list.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": artifact.url,
                    },
                }
            )
        elif artifact.type == "csv":
            df_handler = DataFrameHandler(data=artifact.data)
            content += f"\n\n{get_info_from_df_for_llm(df_handler.get_python_friendly_format())}"
        else:
            type_ = artifact.type or "text"
            if type_ == "code":
                language = artifact.language or "plaintext"
                content += f"\n\n```{language}\n{artifact.data}\n```"
            else:
                content += f"\n\n{artifact.data}"

        if content_list:
            message_json["content"] = [{"type": "text", "text": content}, *content_list]
        else:
            message_json["content"] = content

    return message_json


async def get_messages(
    session_id: str,
    user_id: Optional[str] = None,
    include_artifacts: bool = True,
) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
    """Fetch messages by IDs with optional artifact inclusion.

    Args:
        message_ids (List[str]): List of message IDs to fetch.
        user_id (Optional[str]): User ID for access validation.
        include_artifacts (bool): Whether to include artifacts in the messages.

    Returns:
        List[Message]: List of fetched Message objects.
    """
    session_info: Session = await session_service.get_complete_session(
        session_id=session_id, user_id=user_id, include_artifacts=include_artifacts
    )
    if session_info is None:
        return []

    return [convert_message_for_llm(message) for message in session_info.messages]


# for now, since LLM only generates text, no need to worry about artifacts
async def push_messages(
    messages: Union[Message, List[Message]],
    session_id: str,
    user_id: str,
    artifacts: Optional[List[List[Artifact]]] = None,
    push_artifacts_in_message: bool = False,
):
    """Push a new message to a session with optional artifacts.

    Args:
        session_id (str): The session ID to add the message to.
        user_id (str): The user ID for ownership validation.
        content (str): The message content.
        role (str): The role of the message sender ('user' or 'assistant').
        artifacts (Optional[List[Artifact]]): Optional list of artifacts to attach.
        push_artifacts_in_message (bool): Whether to push artifacts in the message.

    Returns:
        Optional[Message]: The created Message object, or None if failed.
    """
    if not isinstance(messages, list):
        messages = [messages]

    for message, artifacts_ in zip(messages, artifacts or [[]] * len(messages)):
        await message_service.push_message(
            session_id=session_id,
            user_id=user_id,
            message=message,
            artifacts=artifacts_,
            push_artifacts_in_message=push_artifacts_in_message,
        )


def create_image_artifact(
    image: Union[bytes, Image.Image, str], **kwargs
) -> ImageArtifact:
    """Create an ImageArtifact from various input types.

    Args:
        image (Union[bytes, Image.Image, str]): The image data as bytes, PIL Image, or file path.
        **kwargs: Additional keyword arguments for the ImageArtifact.

    Returns:
        ImageArtifact: The created ImageArtifact object.
    """
    image_handler = ImageHandler(data=image)
    pil_image = image_handler.get_python_friendly_format()
    thubmnail = image_handler.get_thumbnail_base64()
    base_64_str = image_handler.get_base64_representation()
    image_artifact = ImageArtifact(
        type="image",
        data=base_64_str,
        thumbnail_data=thubmnail,
        height=pil_image.height,
        width=pil_image.width,
        format=pil_image.format,
        **kwargs,
    )
    return image_artifact


def create_csv_artifact(df: Union[pd.DataFrame, str, bytes], **kwargs) -> CSVArtifact:
    """Create a CSVArtifact from a DataFrame or CSV data.

    Args:
        df (Union[pd.DataFrame, str, bytes]): The DataFrame or CSV data as string/bytes.
        **kwargs: Additional keyword arguments for the CSVArtifact.

    Returns:
        CSVArtifact: The created CSVArtifact object.
    """
    df_handler = DataFrameHandler(data=df)
    pandas_df = df_handler.get_python_friendly_format()
    csv_data = df_handler.get_base64_representation()
    num_rows, num_columns = pandas_df.shape
    columns = list(pandas_df.columns)

    csv_artifact = CSVArtifact(
        type="csv",
        data=csv_data,
        num_rows=num_rows,
        num_columns=num_columns,
        columns=columns,
        **kwargs,
    )
    return csv_artifact
