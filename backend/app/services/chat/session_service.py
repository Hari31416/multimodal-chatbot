"""
Service for efficiently assembling chat session data using batch operations.

This service implements the optimized approach described in storage_options_temp.md
to minimize Redis round-trips when fetching complete session data.
"""

from typing import Dict, List, Optional, Set
import json
from pydantic import TypeAdapter
import pandas as pd

from app.models.object_models import Session, Message, Artifact, SessionInfo
from app.models.response_models import SessionResponse
from app.services.storage.redis_cache import RedisCache, redis_cache
from app.services.storage.storage import DataFrameHandler
from app.utils import create_simple_logger


logger = create_simple_logger(__name__)


class SessionService:
    """
    Efficiently assembles complete chat session data using batch Redis operations.

    Follows the optimization strategy from storage_options_temp.md:
    1. Fetch all message IDs for session (LRANGE)
    2. Batch-fetch all messages (MGET)
    3. Collect all artifact IDs from messages
    4. Batch-fetch all artifacts (MGET)
    5. Assemble final response with full artifact objects
    """

    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or redis_cache

    async def create_new_session(
        self, user_id: str, title: Optional[str] = None
    ) -> Session:
        """
        Create a new chat session for a user.

        Args:
            user_id: The user ID to associate with the session
            title: Optional title for the session

        Returns:
            The created Session object
        """
        session = Session(userId=user_id, title=title)
        self.cache.save_session(session)
        return session

    async def get_complete_session(
        self,
        session_id: str,
        user_id: str,
        include_artifacts: bool = True,
        include_only_for_frontend: bool = False,
    ) -> Optional[SessionResponse]:
        """
        Get a complete session with all messages and artifacts using optimized batch operations.

        Args:
            session_id: The session ID to fetch
            user_id: The user ID for ownership validation

        Returns:
            Complete SessionResponse with nested messages and artifacts, or None if not found/unauthorized
        """
        try:
            # Step 1: Get session metadata and validate ownership
            session_metadata = self.cache.get_session(session_id, user_id=user_id)
            if session_metadata is None:
                logger.warning(
                    f"Session {session_id} not found or access denied for user {user_id}"
                )
                return None

            # Step 2: Get all message IDs for the session
            message_ids = self.cache.get_message_ids_for_session(
                session_id, user_id=user_id
            )
            if not message_ids:
                logger.info(f"No messages found for session {session_id}")
                # Return session with empty messages list
                return SessionResponse(
                    sessionId=session_metadata.sessionId,
                    userId=session_metadata.userId,
                    createdAt=session_metadata.createdAt,
                    updatedAt=session_metadata.updatedAt,
                    title=session_metadata.title,
                    messages=[],
                    numMessages=0,
                )

            # Step 3: Batch-fetch all message objects
            messages = await self._batch_fetch_messages(message_ids, session_id)
            if include_only_for_frontend:
                logger.info("Filtering messages for frontend display only")
                before = len(messages)
                messages = [m for m in messages if m.should_display_in_frontend()]
                after = len(messages)
                logger.info(f"Filtered messages from {before} to {after} for frontend")
            if not messages:
                logger.warning(f"Failed to fetch messages for session {session_id}")
                return None

            if include_artifacts:
                messages = await self._attach_artifacts_to_messages(messages)

            # Step 5: Assemble final response
            return SessionResponse(
                sessionId=session_metadata.sessionId,
                userId=session_metadata.userId,
                createdAt=session_metadata.createdAt,
                updatedAt=session_metadata.updatedAt,
                title=session_metadata.title,
                messages=messages,
                numMessages=len(messages),
            )

        except Exception as e:
            logger.error(f"Error assembling session {session_id}: {str(e)}")
            return None

    async def _batch_fetch_messages(
        self, message_ids: List[str], session_id: str
    ) -> List[Message]:
        """
        Batch-fetch all message objects using a single MGET command.

        Args:
            message_ids: List of message IDs to fetch
            session_id: Session ID for validation

        Returns:
            List of Message objects, excluding any that failed to load
        """
        if not message_ids:
            return []

        # Prepare message keys for MGET
        message_keys = [self.cache.k_message(msg_id) for msg_id in message_ids]

        try:
            # Execute single MGET command
            raw_messages = self.cache.redis.mget(message_keys)

            # Process results and filter out nulls
            messages = []
            for i, raw_msg in enumerate(raw_messages):
                if raw_msg is None:
                    logger.warning(f"Message {message_ids[i]} not found in Redis")
                    continue

                try:
                    # Decode if bytes
                    if isinstance(raw_msg, bytes):
                        raw_msg = raw_msg.decode("utf-8")

                    message = Message.model_validate_json(raw_msg)

                    # Validate session ownership
                    if message.sessionId != session_id:
                        logger.warning(
                            f"Message {message.messageId} belongs to session {message.sessionId}, not {session_id}"
                        )
                        continue

                    messages.append(message)

                except Exception as e:
                    logger.error(f"Failed to parse message {message_ids[i]}: {str(e)}")
                    continue

            logger.debug(
                f"Successfully fetched {len(messages)}/{len(message_ids)} messages for session {session_id}"
            )
            return messages

        except Exception as e:
            logger.error(f"Failed to batch fetch messages: {str(e)}")
            return []

    async def _attach_artifacts_to_messages(
        self, messages: List[Message]
    ) -> List[Message]:
        """
        Collect all artifact IDs and batch-fetch artifacts, then attach to messages.

        Args:
            messages: List of messages to attach artifacts to

        Returns:
            List of messages with full artifact objects attached
        """
        if not messages:
            return []

        # Step 1: Collect all unique artifact IDs from all messages
        all_artifact_ids: Set[str] = set()
        message_to_artifact_ids: Dict[str, List[str]] = {}

        for message in messages:
            # Get artifact IDs for this message from the index
            artifact_ids = self.cache.get_artifact_ids_for_message(message.messageId)
            if artifact_ids:
                message_to_artifact_ids[message.messageId] = artifact_ids
                all_artifact_ids.update(artifact_ids)

        if not all_artifact_ids:
            logger.debug("No artifacts found for any messages")
            # Return messages with empty artifacts lists
            for message in messages:
                message.artifacts = []
            return messages

        # Step 2: Batch-fetch all artifacts
        artifact_lookup = await self._batch_fetch_artifacts(list(all_artifact_ids))

        # Step 3: Attach artifacts to their respective messages
        for message in messages:
            artifact_ids = message_to_artifact_ids.get(message.messageId, [])
            message_artifacts = []

            for artifact_id in artifact_ids:
                artifact = artifact_lookup.get(artifact_id)
                if artifact:
                    message_artifacts.append(artifact)
                else:
                    logger.warning(
                        f"Artifact {artifact_id} not found for message {message.messageId}"
                    )

            message.artifacts = message_artifacts

        return messages

    async def _batch_fetch_artifacts(
        self, artifact_ids: List[str]
    ) -> Dict[str, Artifact]:
        """
        Batch-fetch artifacts using MGET and return as lookup dictionary.

        Args:
            artifact_ids: List of artifact IDs to fetch

        Returns:
            Dictionary mapping artifact_id -> Artifact object
        """
        if not artifact_ids:
            return {}

        # Prepare artifact keys for MGET
        artifact_keys = [self.cache.k_artifact(art_id) for art_id in artifact_ids]

        try:
            # Execute single MGET command
            raw_artifacts = self.cache.redis.mget(artifact_keys)

            # Process results into lookup dictionary
            artifact_lookup: Dict[str, Artifact] = {}
            for i, raw_artifact in enumerate(raw_artifacts):
                if raw_artifact is None:
                    logger.warning(f"Artifact {artifact_ids[i]} not found in Redis")
                    continue

                try:
                    # Decode if bytes
                    if isinstance(raw_artifact, bytes):
                        raw_artifact = raw_artifact.decode("utf-8")

                    artifact = TypeAdapter(Artifact).validate_json(raw_artifact)
                    artifact_lookup[artifact_ids[i]] = artifact

                except Exception as e:
                    logger.error(
                        f"Failed to parse artifact {artifact_ids[i]}: {str(e)}"
                    )
                    continue

            logger.debug(
                f"Successfully fetched {len(artifact_lookup)}/{len(artifact_ids)} artifacts"
            )
            return artifact_lookup

        except Exception as e:
            logger.error(f"Failed to batch fetch artifacts: {str(e)}")
            return {}

    async def get_session_summary(
        self, session_id: str, user_id: str
    ) -> Optional[SessionInfo]:
        """
        Get basic session information without messages/artifacts.

        Args:
            session_id: The session ID to fetch
            user_id: The user ID for ownership validation

        Returns:
            SessionInfo object or None if not found/unauthorized
        """
        try:
            session = self.cache.get_session(session_id, user_id=user_id)
            if session is None:
                return None

            # Calculate artifact count by checking all messages
            message_ids = self.cache.get_message_ids_for_session(
                session_id, user_id=user_id
            )
            total_artifacts = 0

            if message_ids:
                for msg_id in message_ids:
                    artifact_ids = self.cache.get_artifact_ids_for_message(msg_id)
                    if artifact_ids:
                        total_artifacts += len(artifact_ids)

            return SessionInfo(
                sessionId=session.sessionId,
                userId=session.userId,
                createdAt=session.createdAt,
                updatedAt=session.updatedAt,
                title=session.title,
                numMessages=len(message_ids) if message_ids else 0,
                numArtifacts=total_artifacts,
            )

        except Exception as e:
            logger.error(f"Error getting session summary {session_id}: {str(e)}")
            return None

    async def get_all_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """
        Get all session summaries for a user.

        Args:
            user_id: The user ID to fetch sessions for

        Returns:
            List of SessionInfo objects
        """
        try:
            sessions = self.cache.get_sessions_for_user(user_id)
            # filter for only those that have non-zero messages
            sessions = [s for s in sessions if s.numMessages > 0]
            return sessions or []

        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
            return []

    async def get_df_from_session(
        self, session_id: str, user_id: str
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve the DataFrame associated with the latest message in a session.

        Args:
            session_id: The session ID to fetch the DataFrame from
            user_id: The user ID for ownership validation

        Returns:
            The DataFrame if found, else None
        """
        try:
            session_metadata = self.cache.get_session(session_id, user_id=user_id)
            if session_metadata is None:
                logger.warning(
                    f"Session {session_id} not found or access denied for user {user_id}"
                )
                return None
            # Get all message IDs for the session
            message_ids = self.cache.get_message_ids_for_session(
                session_id, user_id=user_id
            )
            if not message_ids:
                logger.info(f"No messages found for session {session_id}")
                return None

            artifact_ids = [
                self.cache.get_artifact_ids_for_message(msg_id)
                for msg_id in message_ids
            ]
            artifact_ids = [ids for ids in artifact_ids if ids]
            artifact_ids = [id for sublist in artifact_ids for id in sublist]

            if not artifact_ids:
                logger.info(f"No artifacts found in session {session_id}")
                return None

            all_artifacts = self._batch_fetch_artifacts(artifact_ids)
            if not all_artifacts:
                logger.info(f"No artifacts found in session {session_id}")
                return None

            df_artifacts = [
                art for art in all_artifacts if art and art["type"] == "csv"
            ]
            if not df_artifacts:
                logger.info(f"No CSV artifacts found in session {session_id}")
                return None

            # Assume the latest CSV artifact is the relevant DataFrame
            latest_artifact = df_artifacts[-1]
            df_handler = DataFrameHandler(latest_artifact["data"])
            return df_handler.get_python_friendly_format()

        except Exception as e:
            logger.error(
                f"Error retrieving DataFrame from session {session_id}: {str(e)}"
            )
            return None


# Default instance for convenience
session_service = SessionService()
