"""In-memory session storage with simple TTL eviction (manual check on access)."""

import pandas as pd
from PIL import Image
from typing import Optional, Union

from .redis_cache import redis_cache, RedisCache
from .files_handler import DataFrameHandler, ImageHandler
from app.utils import create_simple_logger
from app.models.object_models import CSVArtifact, ImageArtifact, TextArtifact

logger = create_simple_logger(__name__)


def push_csv_artifact_to_redis(
    df: Union[pd.DataFrame, str, bytes],
    cache: RedisCache = redis_cache,
    message_id: Optional[str] = None,
    description: Optional[str] = None,
    compression: Optional[str] = "gzip",
) -> CSVArtifact:
    """Process and store a CSV artifact in Redis.

    Args:
        artifact (CSVArtifact): The CSV artifact to be processed and stored.
        cache (redis_cache): The Redis cache instance for storage.

    Returns:
        CSVArtifact: The updated CSV artifact with the URL set if applicable.
    """
    handler = DataFrameHandler(data=df, compression=compression)
    pandas_df = handler.get_python_friendly_format()
    artifact = CSVArtifact(
        data=handler.get_base64_representation(),
        type="csv",
        description=description or f"CSV Artifact for message {message_id}",
        num_rows=len(pandas_df) if pandas_df is not None else 0,
        num_columns=len(pandas_df.columns) if pandas_df is not None else 0,
    )

    cache.save_artifact(artifact)
    if message_id:
        cache._add_artifact_to_message_index(
            message_id=message_id, artifact_id=artifact.artifactId
        )

    return artifact


def push_image_artifact_to_redis(
    image: Union[Image.Image, str, bytes],
    cache: RedisCache = redis_cache,
    message_id: Optional[str] = None,
    description: Optional[str] = None,
    alt_text: Optional[str] = None,
    compression: Optional[str] = None,
) -> ImageArtifact:
    """Process and store an Image artifact in Redis.

    Args:
        image (Union[Image.Image, str, bytes]): The image to be processed and stored.
        cache (RedisCache): The Redis cache instance for storage.
        message_id (Optional[str]): The ID of the message to associate the artifact with.

    Returns:
        ImageArtifact: The updated Image artifact with the URL set if applicable.
    """
    handler = ImageHandler(data=image, compression=compression)
    pil_image = handler.get_python_friendly_format()
    thumbnail_data = (
        handler.get_thumbnail_base64(size=(128, 128)) if pil_image else None
    )
    artifact = ImageArtifact(
        data=handler.get_base64_representation(),
        type="image",
        description=description or f"Image Artifact for message {message_id}",
        width=pil_image.width if pil_image is not None else 0,
        height=pil_image.height if pil_image is not None else 0,
        thumbnail_data=thumbnail_data,
        format=handler.image_format.lower() if pil_image is not None else "png",
        alt_text=alt_text,
    )

    cache.save_artifact(artifact)
    if message_id:
        cache._add_artifact_to_message_index(
            message_id=message_id, artifact_id=artifact.artifactId
        )
    return artifact


def push_text_artifact_to_redis(
    text: str,
    cache: RedisCache = redis_cache,
    message_id: Optional[str] = None,
    description: Optional[str] = None,
) -> TextArtifact:
    """Process and store a Text artifact in Redis.

    Args:
        text (str): The text to be processed and stored.
        cache (RedisCache): The Redis cache instance for storage.
        message_id (Optional[str]): The ID of the message to associate the artifact with.

    Returns:
        TextArtifact: The updated Text artifact with the URL set if applicable.
    """
    artifact = TextArtifact(
        data=text,
        type="text",
        description=description or f"Text Artifact for message {message_id}",
        length=len(text),
    )

    cache.save_artifact(artifact)
    if message_id:
        cache._add_artifact_to_message_index(
            message_id=message_id, artifact_id=artifact.artifactId
        )
    return artifact
