"""
Service for creating and managing chat messages and artifacts.

This service implements the message creation workflow described in storage_options_temp.md:
1. Create message with artifacts if required
2. Store message in Redis cache
3. Add message ID to session's message index
4. Update session's last updated time
"""

from typing import List, Optional
from datetime import datetime

from app.models.object_models import Message, Artifact, Session
from app.services.storage.redis_cache import RedisCache, redis_cache
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)


class MessageService:
    """
    Service for creating and managing messages with proper indexing.
    """

    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or redis_cache

    async def create_user_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        artifacts: Optional[List[Artifact]] = None,
    ) -> Optional[Message]:
        """
        Create a new user message with optional artifacts.

        Args:
            session_id: The session ID to add the message to
            user_id: The user ID for ownership validation
            content: The message content
            artifacts: Optional list of artifacts to attach

        Returns:
            The created Message object, or None if failed
        """
        try:
            # Validate session exists and user has access
            session = self.cache.get_session(session_id, user_id=user_id)
            if session is None:
                logger.warning(
                    f"Session {session_id} not found or access denied for user {user_id}"
                )
                return None

            # Create the message
            message = Message(
                sessionId=session_id,
                role="user",
                content=content,
                artifacts=artifacts or [],
            )

            # Save message with cascade to handle artifacts
            self.cache.save_message(message, cascade=True)

            # Update session's last updated time and message count
            await self._update_session_after_message(session, message.messageId)

            logger.info(
                f"Created user message {message.messageId} in session {session_id}"
            )
            return message

        except Exception as e:
            logger.error(
                f"Failed to create user message in session {session_id}: {str(e)}"
            )
            return None

    async def create_assistant_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        artifacts: Optional[List[Artifact]] = None,
    ) -> Optional[Message]:
        """
        Create a new assistant message with optional artifacts.

        Args:
            session_id: The session ID to add the message to
            user_id: The user ID for ownership validation
            content: The message content
            artifacts: Optional list of artifacts to attach

        Returns:
            The created Message object, or None if failed
        """
        try:
            # Validate session exists and user has access
            session = self.cache.get_session(session_id, user_id=user_id)
            if session is None:
                logger.warning(
                    f"Session {session_id} not found or access denied for user {user_id}"
                )
                return None

            # Create the message
            message = Message(
                sessionId=session_id,
                role="assistant",
                content=content,
                artifacts=artifacts or [],
            )

            # Save message with cascade to handle artifacts
            self.cache.save_message(message, cascade=True)

            # Update session's last updated time and message count
            await self._update_session_after_message(session, message.messageId)

            logger.info(
                f"Created assistant message {message.messageId} in session {session_id}"
            )
            return message

        except Exception as e:
            logger.error(
                f"Failed to create assistant message in session {session_id}: {str(e)}"
            )
            return None

    async def add_artifact_to_message(
        self, message_id: str, session_id: str, user_id: str, artifact: Artifact
    ) -> bool:
        """
        Add an artifact to an existing message.

        Args:
            message_id: The message ID to add the artifact to
            session_id: The session ID for validation
            user_id: The user ID for ownership validation
            artifact: The artifact to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the message with full ownership validation
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                logger.warning(f"Message {message_id} not found or access denied")
                return False

            # Save the artifact
            self.cache.save_artifact(artifact)

            # Add artifact to message index
            self.cache._add_artifact_to_message_index(message_id, artifact.artifactId)

            logger.info(f"Added artifact {artifact.artifactId} to message {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add artifact to message {message_id}: {str(e)}")
            return False

    async def _update_session_after_message(
        self, session: Session, message_id: str
    ) -> None:
        """
        Update session metadata after adding a message.

        Args:
            session: The session object to update
            message_id: The ID of the message that was added
        """
        try:
            # Update session's last updated time
            session.updatedAt = datetime.now()

            # Update message count
            message_ids = self.cache.get_message_ids_for_session(session.sessionId)
            session.numMessages = len(message_ids) if message_ids else 0

            # Save updated session (without cascade to avoid infinite loop)
            self.cache.save_session(session, cascade=False)

            logger.debug(
                f"Updated session {session.sessionId} after adding message {message_id}"
            )

        except Exception as e:
            logger.error(f"Failed to update session after message: {str(e)}")

    async def delete_message(
        self, message_id: str, session_id: str, user_id: str
    ) -> bool:
        """
        Delete a message and all its artifacts.

        Args:
            message_id: The message ID to delete
            session_id: The session ID for validation
            user_id: The user ID for ownership validation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete with full ownership validation and cascade
            deleted_count = self.cache.delete_message_with_ownership(
                message_id, session_id, user_id, cascade=True
            )

            if deleted_count == 0:
                logger.warning(f"Message {message_id} not found or access denied")
                return False

            # Update session after message deletion
            session = self.cache.get_session(session_id, user_id=user_id)
            if session:
                await self._update_session_after_message(session, message_id)

            logger.info(f"Deleted message {message_id} with {deleted_count} Redis keys")
            return True

        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {str(e)}")
            return False

    async def get_message_with_artifacts(
        self, message_id: str, session_id: str, user_id: str
    ) -> Optional[Message]:
        """
        Get a message with all its artifacts loaded.

        Args:
            message_id: The message ID to fetch
            session_id: The session ID for validation
            user_id: The user ID for ownership validation

        Returns:
            Message with artifacts loaded, or None if not found/unauthorized
        """
        try:
            # Get message with ownership validation
            message = self.cache.get_message_with_full_ownership(
                message_id, session_id, user_id
            )
            if message is None:
                return None

            # Get artifacts for this message
            artifact_ids = self.cache.get_artifact_ids_for_message(
                message_id, session_id
            )
            if artifact_ids:
                artifacts = []
                for artifact_id in artifact_ids:
                    artifact = self.cache.get_artifact_with_full_ownership(
                        artifact_id, message_id, session_id, user_id
                    )
                    if artifact:
                        artifacts.append(artifact)
                message.artifacts = artifacts
            else:
                message.artifacts = []

            return message

        except Exception as e:
            logger.error(f"Failed to get message {message_id} with artifacts: {str(e)}")
            return None


# Default instance for convenience
message_service = MessageService()
