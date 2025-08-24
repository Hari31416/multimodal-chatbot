"""
Service for creating and managing artifacts.

This service provides a unified interface for creating, retrieving, and managing
artifacts of different types (image, CSV, text, code). It integrates with the
existing storage functions while providing proper validation and error handling.
"""

import pandas as pd
from PIL import Image
from typing import List, Optional, Union, Dict
from datetime import datetime
from pydantic import TypeAdapter

from app.models.object_models import (
    Artifact,
    ImageArtifact,
    CSVArtifact,
    TextArtifact,
    CodeArtifact,
    BaseArtifact,
)
from app.services.storage.redis_cache import RedisCache, redis_cache
from app.services.storage.storage import (
    push_csv_artifact_to_redis,
    push_image_artifact_to_redis,
    push_text_artifact_to_redis,
    push_code_artifact_to_redis,
)
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)


class ArtifactService:
    """
    Service for creating and managing artifacts with proper validation.
    """

    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or redis_cache

    async def create_csv_artifact(
        self,
        data: Union[pd.DataFrame, str, bytes],
        message_id: str,
        session_id: str,
        user_id: str,
        description: Optional[str] = None,
        compression: Optional[str] = "gzip",
    ) -> Optional[CSVArtifact]:
        """
        Create a CSV artifact from DataFrame or CSV data.

        Args:
            data: DataFrame, CSV string, or CSV bytes
            message_id: The message ID to associate the artifact with
            session_id: The session ID for validation
            user_id: The user ID for ownership validation
            description: Optional description for the artifact
            compression: Compression method for storage

        Returns:
            The created CSVArtifact object, or None if failed
        """
        try:
            # Validate message exists and user has access
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                logger.warning(
                    f"Message {message_id} not found or access denied for user {user_id}"
                )
                return None

            # Create and store the CSV artifact
            artifact = push_csv_artifact_to_redis(
                df=data,
                cache=self.cache,
                message_id=message_id,
                description=description,
                compression=compression,
            )

            logger.info(
                f"Created CSV artifact {artifact.artifactId} for message {message_id}"
            )
            return artifact

        except Exception as e:
            logger.error(
                f"Failed to create CSV artifact for message {message_id}: {str(e)}"
            )
            return None

    async def create_image_artifact(
        self,
        image: Union[Image.Image, str, bytes],
        message_id: str,
        session_id: str,
        user_id: str,
        description: Optional[str] = None,
        alt_text: Optional[str] = None,
        compression: Optional[str] = None,
    ) -> Optional[ImageArtifact]:
        """
        Create an image artifact from PIL Image or image data.

        Args:
            image: PIL Image, image bytes, or base64 string
            message_id: The message ID to associate the artifact with
            session_id: The session ID for validation
            user_id: The user ID for ownership validation
            description: Optional description for the artifact
            alt_text: Optional alt text for accessibility
            compression: Compression method for storage

        Returns:
            The created ImageArtifact object, or None if failed
        """
        try:
            # Validate message exists and user has access
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                logger.warning(
                    f"Message {message_id} not found or access denied for user {user_id}"
                )
                return None

            # Create and store the image artifact
            artifact = push_image_artifact_to_redis(
                image=image,
                cache=self.cache,
                message_id=message_id,
                description=description,
                alt_text=alt_text,
                compression=compression,
            )

            logger.info(
                f"Created image artifact {artifact.artifactId} for message {message_id}"
            )
            return artifact

        except Exception as e:
            logger.error(
                f"Failed to create image artifact for message {message_id}: {str(e)}"
            )
            return None

    async def create_text_artifact(
        self,
        text: str,
        message_id: str,
        session_id: str,
        user_id: str,
        description: Optional[str] = None,
    ) -> Optional[TextArtifact]:
        """
        Create a text artifact from string data.

        Args:
            text: The text content for the artifact
            message_id: The message ID to associate the artifact with
            session_id: The session ID for validation
            user_id: The user ID for ownership validation
            description: Optional description for the artifact

        Returns:
            The created TextArtifact object, or None if failed
        """
        try:
            # Validate message exists and user has access
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                logger.warning(
                    f"Message {message_id} not found or access denied for user {user_id}"
                )
                return None

            # Create and store the text artifact
            artifact = push_text_artifact_to_redis(
                text=text,
                cache=self.cache,
                message_id=message_id,
                description=description,
            )

            logger.info(
                f"Created text artifact {artifact.artifactId} for message {message_id}"
            )
            return artifact

        except Exception as e:
            logger.error(
                f"Failed to create text artifact for message {message_id}: {str(e)}"
            )
            return None

    async def create_code_artifact(
        self,
        code: str,
        message_id: str,
        session_id: str,
        user_id: str,
        language: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[CodeArtifact]:
        """
        Create a code artifact from code string.

        Args:
            code: The code content for the artifact
            message_id: The message ID to associate the artifact with
            session_id: The session ID for validation
            user_id: The user ID for ownership validation
            language: Programming language of the code
            description: Optional description for the artifact

        Returns:
            The created CodeArtifact object, or None if failed
        """
        try:
            # Validate message exists and user has access
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                logger.warning(
                    f"Message {message_id} not found or access denied for user {user_id}"
                )
                return None

            # Create and store the code artifact
            artifact = push_code_artifact_to_redis(
                code=code,
                cache=self.cache,
                message_id=message_id,
                description=description,
                language=language,
            )

            logger.info(
                f"Created code artifact {artifact.artifactId} for message {message_id}"
            )
            return artifact

        except Exception as e:
            logger.error(
                f"Failed to create code artifact for message {message_id}: {str(e)}"
            )
            return None

    async def get_artifact(
        self,
        artifact_id: str,
        message_id: str,
        session_id: str,
        user_id: str,
    ) -> Optional[Artifact]:
        """
        Get an artifact with full ownership validation.

        Args:
            artifact_id: The artifact ID to fetch
            message_id: The message ID for validation
            session_id: The session ID for validation
            user_id: The user ID for ownership validation

        Returns:
            The artifact object, or None if not found/unauthorized
        """
        try:
            artifact = self.cache.get_artifact_with_full_ownership(
                artifact_id, message_id, session_id, user_id
            )

            if artifact is None:
                logger.warning(
                    f"Artifact {artifact_id} not found or access denied for user {user_id}"
                )
                return None

            logger.debug(f"Retrieved artifact {artifact_id}")
            return artifact

        except Exception as e:
            logger.error(f"Failed to get artifact {artifact_id}: {str(e)}")
            return None

    async def update_artifact_description(
        self,
        artifact_id: str,
        message_id: str,
        session_id: str,
        user_id: str,
        description: str,
    ) -> bool:
        """
        Update an artifact's description.

        Args:
            artifact_id: The artifact ID to update
            message_id: The message ID for validation
            session_id: The session ID for validation
            user_id: The user ID for ownership validation
            description: New description for the artifact

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the artifact with ownership validation
            artifact = self.cache.get_artifact_with_full_ownership(
                artifact_id, message_id, session_id, user_id
            )

            if artifact is None:
                logger.warning(
                    f"Artifact {artifact_id} not found or access denied for user {user_id}"
                )
                return False

            # Update the description
            artifact.description = description

            # Save the updated artifact
            self.cache.save_artifact(artifact)

            logger.info(f"Updated description for artifact {artifact_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update artifact {artifact_id}: {str(e)}")
            return False

    async def delete_artifact(
        self,
        artifact_id: str,
        message_id: str,
        session_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete an artifact with full ownership validation.

        Args:
            artifact_id: The artifact ID to delete
            message_id: The message ID for validation
            session_id: The session ID for validation
            user_id: The user ID for ownership validation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete with full ownership validation
            deleted_count = self.cache.delete_artifact_with_ownership(
                artifact_id, message_id, session_id, user_id
            )

            if deleted_count == 0:
                logger.warning(
                    f"Artifact {artifact_id} not found or access denied for user {user_id}"
                )
                return False

            logger.info(f"Deleted artifact {artifact_id} ({deleted_count} Redis keys)")
            return True

        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {str(e)}")
            return False

    async def get_artifacts_for_message(
        self,
        message_id: str,
        session_id: str,
        user_id: str,
    ) -> List[Artifact]:
        """
        Get all artifacts for a message with ownership validation.

        Args:
            message_id: The message ID to get artifacts for
            session_id: The session ID for validation
            user_id: The user ID for ownership validation

        Returns:
            List of artifacts for the message
        """
        try:
            # Validate message exists and user has access
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                logger.warning(
                    f"Message {message_id} not found or access denied for user {user_id}"
                )
                return []

            # Get artifact IDs for the message
            artifact_ids = self.cache.get_artifact_ids_for_message(
                message_id, session_id
            )

            if not artifact_ids:
                return []

            # Fetch all artifacts
            artifacts = []
            raw_artifacts = self.cache.redis.mget(artifact_ids)
            for i, raw_artifact in enumerate(raw_artifacts):
                if raw_artifact is None:
                    logger.warning(f"Artifact {artifact_ids[i]} not found in Redis")
                    continue

                try:
                    # Decode if bytes
                    if isinstance(raw_artifact, bytes):
                        raw_artifact = raw_artifact.decode("utf-8")

                    artifact = TypeAdapter(Artifact).validate_json(raw_artifact)
                    artifacts.append(artifact)

                except Exception as e:
                    logger.error(
                        f"Failed to parse artifact {artifact_ids[i]}: {str(e)}"
                    )
                continue

            logger.debug(
                f"Retrieved {len(artifacts)} artifacts for message {message_id}"
            )
            return artifacts

        except Exception as e:
            logger.error(f"Failed to get artifacts for message {message_id}: {str(e)}")
            return []

    async def get_artifact_data(
        self,
        artifact_id: str,
        message_id: str,
        session_id: str,
        user_id: str,
    ) -> Optional[Union[str, bytes, pd.DataFrame, Image.Image]]:
        """
        Get the processed data from an artifact in its native format.

        Args:
            artifact_id: The artifact ID to get data for
            message_id: The message ID for validation
            session_id: The session ID for validation
            user_id: The user ID for ownership validation

        Returns:
            The artifact data in its native format, or None if failed
        """
        try:
            artifact = await self.get_artifact(
                artifact_id, message_id, session_id, user_id
            )

            if artifact is None:
                return None

            # Return data based on artifact type
            if isinstance(artifact, CSVArtifact):
                # For CSV artifacts, we'd need to reconstruct the DataFrame
                # This would require implementing a method to decode the stored data
                logger.warning("CSV data reconstruction not yet implemented")
                return artifact.data

            elif isinstance(artifact, ImageArtifact):
                # For image artifacts, we'd need to reconstruct the PIL Image
                # This would require implementing a method to decode the stored data
                logger.warning("Image data reconstruction not yet implemented")
                return artifact.data

            elif isinstance(artifact, (TextArtifact, CodeArtifact)):
                # Text and code artifacts store data directly
                return artifact.data

            else:
                logger.warning(f"Unknown artifact type: {type(artifact)}")
                return artifact.data

        except Exception as e:
            logger.error(f"Failed to get data for artifact {artifact_id}: {str(e)}")
            return None


# Default instance for convenience
artifact_service = ArtifactService()
