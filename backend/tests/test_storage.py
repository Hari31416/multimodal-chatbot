"""Test cases for the storage module artifact creation and management."""

import pytest
import pandas as pd
from PIL import Image
import io
import base64
from typing import Optional

from app.services.storage.storage import (
    push_csv_artifact_to_redis,
    push_image_artifact_to_redis,
    push_text_artifact_to_redis,
)
from app.services.storage.redis_cache import RedisCache
from app.models.object_models import CSVArtifact, ImageArtifact, TextArtifact
from app.services.storage.files_handler import (
    compress_data,
    convert_df_to_parquet_bytes,
    encode_bytes_to_base64,
)


@pytest.fixture
def mock_cache(fake_redis):
    """Create a mock RedisCache for testing."""
    return RedisCache(redis_client=fake_redis, prefix="test:storage:", ttl_seconds=3600)


def test_push_csv_artifact_from_dataframe(mock_cache):
    """Test creating and storing a CSV artifact from a pandas DataFrame."""
    # Create a test DataFrame
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "London", "Tokyo"],
        }
    )

    message_id = "test_message_123"
    description = "Test CSV data"

    # Push to cache
    artifact = push_csv_artifact_to_redis(
        df=df, cache=mock_cache, message_id=message_id, description=description
    )

    # Verify artifact properties
    assert isinstance(artifact, CSVArtifact)
    assert artifact.type == "csv"
    assert artifact.description == description
    assert artifact.num_rows == 3
    assert artifact.num_columns == 3
    assert artifact.data is not None

    # Verify artifact was stored in cache
    stored_artifact = mock_cache.get_artifact(
        artifact.artifactId, message_id=message_id
    )
    assert stored_artifact is not None
    assert stored_artifact.artifactId == artifact.artifactId

    # Verify artifact was indexed to message
    artifact_ids = mock_cache.get_artifact_ids_for_message(message_id)
    assert artifact_ids is not None
    assert artifact.artifactId in artifact_ids


def test_push_csv_artifact_from_csv_string(mock_cache):
    """Test creating and storing a CSV artifact from a CSV string."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "London", "Tokyo"],
        }
    )
    bytes_ = convert_df_to_parquet_bytes(df)  # convert to bytes
    bytes_ = compress_data(bytes_, compression="gzip")  # compress the bytes

    csv_string = encode_bytes_to_base64(bytes_)

    artifact = push_csv_artifact_to_redis(
        df=csv_string,
        cache=mock_cache,
        message_id="test_msg_csv",
        description="CSV from string",
    )

    assert isinstance(artifact, CSVArtifact)
    assert artifact.type == "csv"
    assert artifact.description == "CSV from string"
    assert artifact.num_rows == 3  # Data rows (excluding header)
    assert artifact.num_columns == 3


def test_push_csv_artifact_from_bytes(mock_cache):
    """Test creating and storing a CSV artifact from bytes."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "London", "Tokyo"],
        }
    )
    csv_bytes = convert_df_to_parquet_bytes(df)  # convert to bytes
    csv_bytes = compress_data(csv_bytes, compression="gzip")  # compress the bytes

    artifact = push_csv_artifact_to_redis(
        df=csv_bytes, cache=mock_cache, description="CSV from bytes"
    )

    assert isinstance(artifact, CSVArtifact)
    assert artifact.type == "csv"
    assert artifact.description == "CSV from bytes"
    assert artifact.num_rows == 3
    assert artifact.num_columns == 3


def test_push_csv_artifact_default_description(mock_cache):
    """Test CSV artifact creation with default description."""
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    message_id = "msg_default_desc"

    artifact = push_csv_artifact_to_redis(
        df=df, cache=mock_cache, message_id=message_id
    )

    assert artifact.description == f"CSV Artifact for message {message_id}"


def test_push_image_artifact_from_pil(mock_cache):
    """Test creating and storing an Image artifact from PIL Image."""
    # Create a test image
    img = Image.new("RGB", (100, 50), color="red")

    message_id = "test_image_msg"
    description = "Test red image"
    alt_text = "A red rectangle"

    artifact = push_image_artifact_to_redis(
        image=img,
        cache=mock_cache,
        message_id=message_id,
        description=description,
        alt_text=alt_text,
    )

    # Verify artifact properties
    assert isinstance(artifact, ImageArtifact)
    assert artifact.type == "image"
    assert artifact.description == description
    assert artifact.alt_text == alt_text
    assert artifact.width == 100
    assert artifact.height == 50
    assert artifact.format == "png"  # Default format
    assert artifact.data is not None
    assert artifact.thumbnail_data is not None

    # Verify artifact was stored and indexed
    stored_artifact = mock_cache.get_artifact(
        artifact.artifactId, message_id=message_id
    )
    assert stored_artifact is not None

    artifact_ids = mock_cache.get_artifact_ids_for_message(message_id)
    assert artifact_ids is not None
    assert artifact.artifactId in artifact_ids


def test_push_image_artifact_from_bytes(mock_cache):
    """Test creating and storing an Image artifact from bytes."""
    # Create a simple PNG image as bytes
    img = Image.new("RGB", (50, 25), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()
    img_bytes = compress_data(img_bytes, compression="gzip")  # compress the bytes

    artifact = push_image_artifact_to_redis(
        image=img_bytes,
        cache=mock_cache,
        description="Blue image from bytes",
        compression="gzip",
    )

    assert isinstance(artifact, ImageArtifact)
    assert artifact.type == "image"
    assert artifact.width == 50
    assert artifact.height == 25
    assert artifact.format == "png"


def test_push_image_artifact_from_base64_string(mock_cache):
    """Test creating and storing an Image artifact from base64 string."""
    # Create a small image and convert to base64
    img = Image.new("RGB", (20, 10), color="green")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    base64_string = base64.b64encode(buffer.getvalue()).decode()

    artifact = push_image_artifact_to_redis(
        image=base64_string,
        cache=mock_cache,
        description="Green image from base64",
        compression=None,
    )

    assert isinstance(artifact, ImageArtifact)
    assert artifact.width == 20
    assert artifact.height == 10


def test_push_image_artifact_default_description(mock_cache):
    """Test Image artifact creation with default description."""
    img = Image.new("RGB", (10, 10), color="white")
    message_id = "img_default_desc"

    artifact = push_image_artifact_to_redis(
        image=img, cache=mock_cache, message_id=message_id
    )

    assert artifact.description == f"Image Artifact for message {message_id}"


def test_push_text_artifact(mock_cache):
    """Test creating and storing a Text artifact."""
    text_content = "This is a test text artifact with some content."
    message_id = "text_msg_123"
    description = "Sample text artifact"

    artifact = push_text_artifact_to_redis(
        text=text_content,
        cache=mock_cache,
        message_id=message_id,
        description=description,
    )

    # Verify artifact properties
    assert isinstance(artifact, TextArtifact)
    assert artifact.type == "text"
    assert artifact.data == text_content
    assert artifact.description == description
    assert artifact.length == len(text_content)

    # Verify artifact was stored and indexed
    stored_artifact = mock_cache.get_artifact(
        artifact.artifactId, message_id=message_id
    )
    assert stored_artifact is not None
    assert stored_artifact.data == text_content

    artifact_ids = mock_cache.get_artifact_ids_for_message(message_id)
    assert artifact_ids is not None
    assert artifact.artifactId in artifact_ids


def test_push_text_artifact_unicode(mock_cache):
    """Test text artifact with Unicode content."""
    unicode_text = "Hello 世界! 🌍 Ñiño café résumé"

    artifact = push_text_artifact_to_redis(
        text=unicode_text, cache=mock_cache, description="Unicode text"
    )

    assert artifact.data == unicode_text
    assert artifact.length == len(unicode_text)


def test_push_text_artifact_default_description(mock_cache):
    """Test Text artifact creation with default description."""
    text = "Sample text"
    message_id = "text_default_desc"

    artifact = push_text_artifact_to_redis(
        text=text, cache=mock_cache, message_id=message_id
    )

    assert artifact.description == f"Text Artifact for message {message_id}"


def test_artifacts_without_message_id(mock_cache):
    """Test creating artifacts without associating them to a message."""
    # CSV artifact without message
    df = pd.DataFrame({"a": [1, 2]})
    csv_artifact = push_csv_artifact_to_redis(df=df, cache=mock_cache)
    assert isinstance(csv_artifact, CSVArtifact)

    # Image artifact without message
    img = Image.new("RGB", (10, 10), color="black")
    img_artifact = push_image_artifact_to_redis(image=img, cache=mock_cache)
    assert isinstance(img_artifact, ImageArtifact)

    # Text artifact without message
    text_artifact = push_text_artifact_to_redis(text="No message", cache=mock_cache)
    assert isinstance(text_artifact, TextArtifact)

    # Verify artifacts are stored but not indexed to any message
    assert mock_cache.get_artifact(csv_artifact.artifactId) is not None
    assert mock_cache.get_artifact(img_artifact.artifactId) is not None
    assert mock_cache.get_artifact(text_artifact.artifactId) is not None


def test_large_dataframe_csv_artifact(mock_cache):
    """Test CSV artifact creation with a larger DataFrame."""
    # Create a larger test DataFrame
    large_df = pd.DataFrame(
        {
            "id": range(1000),
            "value": [f"value_{i}" for i in range(1000)],
            "score": [i * 0.1 for i in range(1000)],
        }
    )

    artifact = push_csv_artifact_to_redis(
        df=large_df, cache=mock_cache, description="Large CSV dataset"
    )

    assert artifact.num_rows == 1000
    assert artifact.num_columns == 3
    assert artifact.description == "Large CSV dataset"


def test_empty_dataframe_csv_artifact(mock_cache):
    """Test CSV artifact creation with an empty DataFrame."""
    empty_df = pd.DataFrame()

    artifact = push_csv_artifact_to_redis(
        df=empty_df, cache=mock_cache, description="Empty DataFrame"
    )

    assert artifact.num_rows == 0
    assert artifact.num_columns == 0


def test_empty_text_artifact(mock_cache):
    """Test text artifact creation with empty text."""
    artifact = push_text_artifact_to_redis(
        text="", cache=mock_cache, description="Empty text"
    )

    assert artifact.data == ""
    assert artifact.length == 0


def test_artifact_ids_uniqueness(mock_cache):
    """Test that each artifact gets a unique ID."""
    artifacts = []

    # Create multiple artifacts of different types
    for i in range(5):
        csv_artifact = push_csv_artifact_to_redis(
            df=pd.DataFrame({"col": [i]}), cache=mock_cache
        )
        img_artifact = push_image_artifact_to_redis(
            image=Image.new("RGB", (i + 1, i + 1), color="red"), cache=mock_cache
        )
        text_artifact = push_text_artifact_to_redis(text=f"Text {i}", cache=mock_cache)

        artifacts.extend([csv_artifact, img_artifact, text_artifact])

    # Verify all IDs are unique
    artifact_ids = [a.artifactId for a in artifacts]
    assert len(artifact_ids) == len(set(artifact_ids))
