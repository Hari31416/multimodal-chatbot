"""Tests for the ArtifactService."""

import pytest
import pandas as pd
from PIL import Image
import io
import base64

from app.services.chat.artifact_service import ArtifactService
from app.models.object_models import (
    Session,
    Message,
    CSVArtifact,
    ImageArtifact,
    TextArtifact,
    CodeArtifact,
)
from app.services.storage.redis_cache import RedisCache


class TestArtifactService:
    """Test cases for ArtifactService."""

    @pytest.fixture
    def mock_cache(self, mocker):
        """Create a mock Redis cache."""
        cache = mocker.Mock(spec=RedisCache)
        return cache

    @pytest.fixture
    def artifact_service(self, mock_cache):
        """Create an ArtifactService with mock cache."""
        return ArtifactService(cache=mock_cache)

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing."""
        return Message(
            messageId="message_123",
            sessionId="session_456",
            role="user",
            content="Test message",
            artifacts=[],
        )

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "city": ["New York", "London", "Tokyo"],
            }
        )

    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing."""
        # Create a simple 100x100 red image
        img = Image.new("RGB", (100, 100), color="red")
        return img

    @pytest.mark.asyncio
    async def test_create_csv_artifact_success(
        self, artifact_service, mock_cache, sample_message, sample_dataframe, mocker
    ):
        """Test successful CSV artifact creation."""
        # Setup
        mock_cache.get_message_with_full_ownership.return_value = sample_message

        # Create mock CSV artifact
        mock_csv_artifact = CSVArtifact(
            artifactId="artifact_123",
            type="csv",
            data="mock_base64_data",
            description="Test CSV",
            num_rows=3,
            num_columns=3,
        )

        # Mock the push function
        artifact_service.cache = mock_cache
        with mocker.patch(
            "app.services.artifact_service.push_csv_artifact_to_redis",
            return_value=mock_csv_artifact,
        ):
            # Execute
            result = await artifact_service.create_csv_artifact(
                data=sample_dataframe,
                message_id="message_123",
                session_id="session_456",
                user_id="user_789",
                description="Test CSV artifact",
            )

        # Verify
        assert result is not None
        assert result.artifactId == "artifact_123"
        assert result.type == "csv"
        mock_cache.get_message_with_full_ownership.assert_called_once_with(
            "message_123", "session_456", "user_789"
        )

    @pytest.mark.asyncio
    async def test_create_csv_artifact_unauthorized(
        self, artifact_service, mock_cache, sample_dataframe
    ):
        """Test CSV artifact creation with unauthorized access."""
        # Setup - message not found/unauthorized
        mock_cache.get_message_with_full_ownership.return_value = None

        # Execute
        result = await artifact_service.create_csv_artifact(
            data=sample_dataframe,
            message_id="message_123",
            session_id="session_456",
            user_id="unauthorized_user",
        )

        # Verify
        assert result is None
        mock_cache.get_message_with_full_ownership.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_image_artifact_success(
        self, artifact_service, mock_cache, sample_message, sample_image, mocker
    ):
        """Test successful image artifact creation."""
        # Setup
        mock_cache.get_message_with_full_ownership.return_value = sample_message

        # Create mock image artifact
        mock_image_artifact = ImageArtifact(
            artifactId="artifact_456",
            type="image",
            data="mock_base64_image_data",
            description="Test Image",
            width=100,
            height=100,
            format="png",
        )

        # Mock the push function
        with mocker.patch(
            "app.services.artifact_service.push_image_artifact_to_redis",
            return_value=mock_image_artifact,
        ):
            # Execute
            result = await artifact_service.create_image_artifact(
                image=sample_image,
                message_id="message_123",
                session_id="session_456",
                user_id="user_789",
                description="Test image artifact",
                alt_text="Red square",
            )

        # Verify
        assert result is not None
        assert result.artifactId == "artifact_456"
        assert result.type == "image"

    @pytest.mark.asyncio
    async def test_create_text_artifact_success(
        self, artifact_service, mock_cache, sample_message, mocker
    ):
        """Test successful text artifact creation."""
        # Setup
        mock_cache.get_message_with_full_ownership.return_value = sample_message

        # Create mock text artifact
        mock_text_artifact = TextArtifact(
            artifactId="artifact_789",
            type="text",
            data="This is a test text artifact",
            description="Test Text",
            length=28,
        )

        # Mock the push function
        with mocker.patch(
            "app.services.artifact_service.push_text_artifact_to_redis",
            return_value=mock_text_artifact,
        ):
            # Execute
            result = await artifact_service.create_text_artifact(
                text="This is a test text artifact",
                message_id="message_123",
                session_id="session_456",
                user_id="user_789",
                description="Test text artifact",
            )

        # Verify
        assert result is not None
        assert result.artifactId == "artifact_789"
        assert result.type == "text"

    @pytest.mark.asyncio
    async def test_create_code_artifact_success(
        self, artifact_service, mock_cache, sample_message, mocker
    ):
        """Test successful code artifact creation."""
        # Setup
        mock_cache.get_message_with_full_ownership.return_value = sample_message

        code_content = "def hello_world():\n    print('Hello, World!')"

        # Create mock code artifact
        mock_code_artifact = CodeArtifact(
            artifactId="artifact_code_123",
            type="code",
            data=code_content,
            description="Test code artifact",
            length=len(code_content),
            language="python",
        )

        # Mock the push function
        with mocker.patch(
            "app.services.artifact_service.push_code_artifact_to_redis",
            return_value=mock_code_artifact,
        ):
            # Execute
            result = await artifact_service.create_code_artifact(
                code=code_content,
                message_id="message_123",
                session_id="session_456",
                user_id="user_789",
                language="python",
                description="Test code artifact",
            )

        # Verify
        assert result is not None
        assert result.artifactId == "artifact_code_123"
        assert result.type == "code"
        assert result.language == "python"
        mock_cache.get_message_with_full_ownership.assert_called_once_with(
            "message_123", "session_456", "user_789"
        )

    @pytest.mark.asyncio
    async def test_get_artifact_success(self, artifact_service, mock_cache):
        """Test successful artifact retrieval."""
        # Setup
        mock_artifact = TextArtifact(
            artifactId="artifact_123",
            type="text",
            data="Test content",
            description="Test artifact",
        )
        mock_cache.get_artifact_with_full_ownership.return_value = mock_artifact

        # Execute
        result = await artifact_service.get_artifact(
            artifact_id="artifact_123",
            message_id="message_456",
            session_id="session_789",
            user_id="user_123",
        )

        # Verify
        assert result is not None
        assert result.artifactId == "artifact_123"
        mock_cache.get_artifact_with_full_ownership.assert_called_once_with(
            "artifact_123", "message_456", "session_789", "user_123"
        )

    @pytest.mark.asyncio
    async def test_delete_artifact_success(self, artifact_service, mock_cache):
        """Test successful artifact deletion."""
        # Setup
        mock_cache.delete_artifact_with_ownership.return_value = 1  # One key deleted

        # Execute
        result = await artifact_service.delete_artifact(
            artifact_id="artifact_123",
            message_id="message_456",
            session_id="session_789",
            user_id="user_123",
        )

        # Verify
        assert result is True
        mock_cache.delete_artifact_with_ownership.assert_called_once_with(
            "artifact_123", "message_456", "session_789", "user_123"
        )

    @pytest.mark.asyncio
    async def test_delete_artifact_not_found(self, artifact_service, mock_cache):
        """Test artifact deletion when artifact not found."""
        # Setup
        mock_cache.delete_artifact_with_ownership.return_value = 0  # No keys deleted

        # Execute
        result = await artifact_service.delete_artifact(
            artifact_id="nonexistent_artifact",
            message_id="message_456",
            session_id="session_789",
            user_id="user_123",
        )

        # Verify
        assert result is False

    @pytest.mark.asyncio
    async def test_get_artifacts_for_message_success(
        self, artifact_service, mock_cache, sample_message
    ):
        """Test getting all artifacts for a message."""
        # Setup
        mock_cache.get_message_with_full_ownership.return_value = sample_message
        mock_cache.get_artifact_ids_for_message.return_value = [
            "artifact_1",
            "artifact_2",
        ]

        mock_artifact_1 = TextArtifact(
            artifactId="artifact_1", type="text", data="Text 1"
        )
        mock_artifact_2 = TextArtifact(
            artifactId="artifact_2", type="text", data="Text 2"
        )

        mock_cache.get_artifact_with_full_ownership.side_effect = [
            mock_artifact_1,
            mock_artifact_2,
        ]

        # Execute
        result = await artifact_service.get_artifacts_for_message(
            message_id="message_123", session_id="session_456", user_id="user_789"
        )

        # Verify
        assert len(result) == 2
        assert result[0].artifactId == "artifact_1"
        assert result[1].artifactId == "artifact_2"

    @pytest.mark.asyncio
    async def test_update_artifact_description_success(
        self, artifact_service, mock_cache
    ):
        """Test successful artifact description update."""
        # Setup
        mock_artifact = TextArtifact(
            artifactId="artifact_123",
            type="text",
            data="Test content",
            description="Old description",
        )
        mock_cache.get_artifact_with_full_ownership.return_value = mock_artifact

        # Execute
        result = await artifact_service.update_artifact_description(
            artifact_id="artifact_123",
            message_id="message_456",
            session_id="session_789",
            user_id="user_123",
            description="New description",
        )

        # Verify
        assert result is True
        assert mock_artifact.description == "New description"
        mock_cache.save_artifact.assert_called_once_with(mock_artifact)

    @pytest.mark.asyncio
    async def test_get_artifacts_for_message_empty(
        self, artifact_service, mock_cache, sample_message
    ):
        """Test getting artifacts for a message with no artifacts."""
        # Setup
        mock_cache.get_message_with_full_ownership.return_value = sample_message
        mock_cache.get_artifact_ids_for_message.return_value = []

        # Execute
        result = await artifact_service.get_artifacts_for_message(
            message_id="message_123", session_id="session_456", user_id="user_789"
        )

        # Verify
        assert len(result) == 0
        assert result == []

    @pytest.mark.asyncio
    async def test_get_artifacts_for_message_unauthorized(
        self, artifact_service, mock_cache
    ):
        """Test getting artifacts for a message with unauthorized access."""
        # Setup - message not found/unauthorized
        mock_cache.get_message_with_full_ownership.return_value = None

        # Execute
        result = await artifact_service.get_artifacts_for_message(
            message_id="message_123",
            session_id="session_456",
            user_id="unauthorized_user",
        )

        # Verify
        assert len(result) == 0
        assert result == []

    @pytest.mark.asyncio
    async def test_update_artifact_description_unauthorized(
        self, artifact_service, mock_cache
    ):
        """Test updating artifact description with unauthorized access."""
        # Setup - artifact not found/unauthorized
        mock_cache.get_artifact_with_full_ownership.return_value = None

        # Execute
        result = await artifact_service.update_artifact_description(
            artifact_id="artifact_123",
            message_id="message_456",
            session_id="session_789",
            user_id="unauthorized_user",
            description="New description",
        )

        # Verify
        assert result is False

    @pytest.mark.asyncio
    async def test_get_artifact_data_text_artifact(self, artifact_service, mock_cache):
        """Test getting data from a text artifact."""
        # Setup
        mock_artifact = TextArtifact(
            artifactId="artifact_123",
            type="text",
            data="This is test content",
            description="Test artifact",
        )

        # Mock the get_artifact method to return our test artifact
        async def mock_get_artifact(*args, **kwargs):
            return mock_artifact

        artifact_service.get_artifact = mock_get_artifact

        # Execute
        result = await artifact_service.get_artifact_data(
            artifact_id="artifact_123",
            message_id="message_456",
            session_id="session_789",
            user_id="user_123",
        )

        # Verify
        assert result == "This is test content"

    @pytest.mark.asyncio
    async def test_get_artifact_data_not_found(self, artifact_service, mock_cache):
        """Test getting data from a non-existent artifact."""

        # Setup
        async def mock_get_artifact(*args, **kwargs):
            return None

        artifact_service.get_artifact = mock_get_artifact

        # Execute
        result = await artifact_service.get_artifact_data(
            artifact_id="nonexistent_artifact",
            message_id="message_456",
            session_id="session_789",
            user_id="user_123",
        )

        # Verify
        assert result is None
