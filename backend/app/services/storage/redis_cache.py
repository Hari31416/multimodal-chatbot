"""Typed Redis cache helper for artifacts, messages, sessions, and indexes.

Key prefix and structure follow storage_options_temp.md:

- prefix: "chatapp:prod:"
- Artifacts: prefix + "artifact:{artifact_id}"
- Messages:  prefix + "message:{message_id}"
- Sessions:  prefix + "session:{session_id}"
- Indexes:
  - Session Indexes on User ID:          prefix + "session_index:user:{user_id}" -> JSON list[SessionInfo]
  - Message Indexes on Session ID:        prefix + "message_index:session:{session_id}" -> JSON list[str] (messageIds)
  - Artifact Indexes on Message ID:       prefix + "artifact_index:message:{message_id}" -> JSON list[str] (artifactIds)

This helper provides typed get/set/delete plus index maintenance. It uses
Pydantic models from app.models.object_models.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional, Union

import redis
from pydantic import TypeAdapter

from app.models.object_models import Artifact, Message, Session, SessionInfo
from app.utils import create_simple_logger


logger = create_simple_logger(__name__)

All_Objects = Union[Artifact, Message, Session, SessionInfo]


def _build_redis_client() -> redis.Redis:
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        username=os.environ.get("REDIS_USERNAME"),
        password=os.environ.get("REDIS_PASSWORD"),
        socket_connect_timeout=5,
        socket_timeout=5,
    )


class RedisCache:
    """Redis cache helper for artifacts/messages/sessions with indexes."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        *,
        prefix: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        self.redis = redis_client or _build_redis_client()
        # Allow overriding via env; default per spec
        self.prefix = prefix or os.environ.get("CACHE_PREFIX", "chatapp:prod:")
        # Default TTL 1 hour (align with existing redis storage)
        self.ttl = ttl_seconds or int(os.environ.get("CACHE_TTL_SECONDS", 6 * 60 * 60))

    # --- key builders -----------------------------------------------------
    def k_artifact(self, artifact_id: str) -> str:
        return f"{self.prefix}artifact:{artifact_id}"

    def k_message(self, message_id: str) -> str:
        return f"{self.prefix}message:{message_id}"

    def k_session(self, session_id: str) -> str:
        return f"{self.prefix}session:{session_id}"

    def k_session_index_by_user(self, user_id: str) -> str:
        return f"{self.prefix}session_index:user:{user_id}"

    def k_message_index_by_session(self, session_id: str) -> str:
        return f"{self.prefix}message_index:session:{session_id}"

    def k_artifact_index_by_message(self, message_id: str) -> str:
        return f"{self.prefix}artifact_index:message:{message_id}"

    # --- low-level helpers ------------------------------------------------
    def _set_json(self, key: str, payload_json: str, ttl: Optional[int] = None) -> None:
        self.redis.setex(key, ttl or self.ttl, payload_json)

    def _get_json(self, key: str) -> Optional[str]:
        raw = self.redis.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return str(raw)

    def _validate_ownership(
        self, item: All_Objects, key_to_check: str, owner_id: Optional[str]
    ) -> bool:
        """Validate ownership by checking if the item's ownership field matches the provided owner_id."""
        if not owner_id:
            # assume public access if no owner_id provided
            return True

        if not hasattr(item, key_to_check):
            logger.warning(
                f"Key {key_to_check} not found in object for ownership validation."
            )
            return False

        item_owner = getattr(item, key_to_check, None)
        if item_owner != owner_id:
            logger.warning(
                f"Ownership validation failed for key {key_to_check}. Expected: {owner_id}, Got: {item_owner}"
            )
            return False
        return True

    # --- session operations ----------------------------------------------
    def save_session(
        self, session: Session, *, cascade: bool = True, ttl: Optional[int] = None
    ) -> None:
        key = self.k_session(session.sessionId)
        self._set_json(key, session.model_dump_json(), ttl)
        logger.debug(f"Saved session {session.sessionId}")

        # Index by user
        if session.userId:
            info = SessionInfo(
                sessionId=session.sessionId,
                userId=session.userId,
                createdAt=session.createdAt,
                updatedAt=session.updatedAt,
                title=session.title,
                numMessages=session.numMessages,
                numArtifacts=sum(len(m.artifacts or []) for m in session.messages),
            )
            self._add_session_to_user_index(session.userId, info, ttl=ttl)

        if cascade:
            # Persist contained messages and artifacts, and build indexes
            for msg in session.messages:
                # Ensure sessionId consistency
                if msg.sessionId != session.sessionId:
                    logger.warning(
                        f"Message {msg.messageId} has mismatched sessionId {msg.sessionId}; correcting to {session.sessionId}"
                    )
                    msg.sessionId = session.sessionId
                self.save_message(msg, cascade=True, ttl=ttl)

    def get_session(
        self, session_id: str, user_id: Optional[str] = None
    ) -> Optional[Session]:
        raw = self._get_json(self.k_session(session_id))
        if raw is None:
            return None
        res = Session.model_validate_json(raw)
        if not self._validate_ownership(res, "userId", user_id):
            return None
        return res

    def delete_session(
        self, session_id: str, user_id: Optional[str] = None, *, cascade: bool = False
    ) -> int:
        """Delete a session; if cascade, also delete messages and artifacts and clean indexes.

        Returns number of keys removed from Redis (best-effort count).
        """
        deleted = 0
        session = self.get_session(session_id, user_id=user_id) if cascade else None

        # Check ownership before deletion even in non-cascade mode
        if not cascade:
            session = self.get_session(session_id, user_id=user_id)
            if session is None:
                return 0

        if cascade and session is not None:
            # Remove session from user index
            if session.userId:
                self._remove_session_from_user_index(session.userId, session.sessionId)

            # Remove indexed messages and artifacts
            msg_ids = self.get_message_ids_for_session(session_id) or []
            for mid in msg_ids:
                deleted += self.delete_message(mid, session_id=session_id, cascade=True)
            # Clear the message index key itself
            deleted += int(
                self.redis.delete(self.k_message_index_by_session(session_id))
            )

        # Delete the session key
        deleted += int(self.redis.delete(self.k_session(session_id)))
        return deleted

    # --- message operations ----------------------------------------------
    def save_message(
        self, message: Message, *, cascade: bool = True, ttl: Optional[int] = None
    ) -> None:
        key = self.k_message(message.messageId)
        self._set_json(key, message.model_dump_json(), ttl)
        logger.debug(f"Saved message {message.messageId}")

        # Index message under session
        self._add_message_to_session_index(
            message.sessionId, message.messageId, ttl=ttl
        )

        if cascade and message.artifacts:
            for art in message.artifacts:
                self.save_artifact(art, ttl=ttl)
                self._add_artifact_to_message_index(
                    message.messageId, art.artifactId, ttl=ttl
                )

    def get_message(
        self, message_id: str, session_id: Optional[str] = None
    ) -> Optional[Message]:
        raw = self._get_json(self.k_message(message_id))
        if raw is None:
            return None
        res = Message.model_validate_json(raw)
        if not self._validate_ownership(res, "sessionId", session_id):
            return None
        return res

    def delete_message(
        self,
        message_id: str,
        session_id: Optional[str] = None,
        *,
        cascade: bool = False,
    ) -> int:
        deleted = 0
        msg = self.get_message(message_id, session_id=session_id) if cascade else None

        # Check ownership before deletion even in non-cascade mode
        if not cascade:
            msg = self.get_message(message_id, session_id=session_id)
            if msg is None:
                return 0

        if cascade and msg is not None:
            # Remove messageId from its session index
            self._remove_message_from_session_index(msg.sessionId, message_id)
            # Remove artifacts
            art_ids = self.get_artifact_ids_for_message(message_id) or []
            for aid in art_ids:
                deleted += self.delete_artifact(aid, message_id=message_id)
            # Clear artifact index key
            deleted += int(
                self.redis.delete(self.k_artifact_index_by_message(message_id))
            )

        deleted += int(self.redis.delete(self.k_message(message_id)))
        return deleted

    # --- artifact operations ---------------------------------------------
    def save_artifact(self, artifact: Artifact, *, ttl: Optional[int] = None) -> None:
        key = self.k_artifact(artifact.artifactId)
        # Artifact is a Union type; .json() works on actual instance
        self._set_json(key, artifact.model_dump_json(), ttl)
        logger.debug(f"Saved artifact {artifact.artifactId}")

    def get_artifact(
        self, artifact_id: str, message_id: Optional[str] = None
    ) -> Optional[Artifact]:
        raw = self._get_json(self.k_artifact(artifact_id))
        if not raw:
            return None
        res = TypeAdapter(Artifact).validate_json(raw)

        # For artifacts, we validate ownership through the message ownership chain
        if message_id is not None:
            # Check if this artifact is actually associated with the given message
            art_ids = self.get_artifact_ids_for_message(message_id)
            if art_ids is None or artifact_id not in art_ids:
                logger.warning(
                    f"Artifact {artifact_id} not associated with message {message_id}"
                )
                return None

        return res

    def delete_artifact(
        self, artifact_id: str, message_id: Optional[str] = None
    ) -> int:
        # Validate ownership through message association
        artifact = self.get_artifact(artifact_id, message_id=message_id)
        if artifact is None:
            return 0
        # Remove from message index if message_id provided
        if message_id is not None:
            self._remove_artifact_from_message_index(message_id, artifact_id)
        return int(self.redis.delete(self.k_artifact(artifact_id)))

    # --- index helpers ----------------------------------------------------
    def _add_session_to_user_index(
        self, user_id: str, info: SessionInfo, *, ttl: Optional[int] = None
    ) -> None:
        key = self.k_session_index_by_user(user_id)
        existing = self._get_json(key)
        items: List[SessionInfo] = []
        if existing:
            try:
                items = TypeAdapter(List[SessionInfo]).validate_json(existing)
            except Exception:
                logger.warning("Corrupt session index payload; resetting")
        # Replace if same sessionId exists; else append
        found = False
        for i, it in enumerate(items):
            if it.sessionId == info.sessionId:
                items[i] = info
                found = True
                break
        if not found:
            items.append(info)
        payload = TypeAdapter(List[SessionInfo]).dump_json(items).decode("utf-8")
        self._set_json(key, payload, ttl)

    def _remove_session_from_user_index(self, user_id: str, session_id: str) -> None:
        key = self.k_session_index_by_user(user_id)
        existing = self._get_json(key)
        if not existing:
            return
        try:
            items = TypeAdapter(List[SessionInfo]).validate_json(existing)
        except Exception:
            return

        items = [i for i in items if i.sessionId != session_id]
        payload = TypeAdapter(List[SessionInfo]).dump_json(items).decode("utf-8")
        self._set_json(key, payload)

    def get_sessions_for_user(self, user_id: str) -> Optional[List[SessionInfo]]:
        raw = self._get_json(self.k_session_index_by_user(user_id))
        if not raw:
            return None
        return TypeAdapter(List[SessionInfo]).validate_json(raw)

    def _add_message_to_session_index(
        self, session_id: str, message_id: str, *, ttl: Optional[int] = None
    ) -> None:
        key = self.k_message_index_by_session(session_id)
        existing = self._get_json(key)
        ids: List[str] = []
        if existing:
            try:
                ids = json.loads(existing)
            except Exception:
                logger.warning("Corrupt message index payload; resetting")
        if message_id not in ids:
            ids.append(message_id)
        self._set_json(key, json.dumps(ids), ttl)

    def _remove_message_from_session_index(
        self, session_id: str, message_id: str
    ) -> None:
        key = self.k_message_index_by_session(session_id)
        existing = self._get_json(key)
        if not existing:
            return
        try:
            ids = json.loads(existing)
        except Exception:
            return
        ids = [i for i in ids if i != message_id]
        self._set_json(key, json.dumps(ids))

    def get_message_ids_for_session(
        self, session_id: str, user_id: Optional[str] = None
    ) -> Optional[List[str]]:
        # Validate session ownership first if user_id provided
        if user_id is not None:
            session = self.get_session(session_id, user_id=user_id)
            if session is None:
                return None

        raw = self._get_json(self.k_message_index_by_session(session_id))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def _add_artifact_to_message_index(
        self, message_id: str, artifact_id: str, *, ttl: Optional[int] = None
    ) -> None:
        key = self.k_artifact_index_by_message(message_id)
        existing = self._get_json(key)
        ids: List[str] = []
        if existing:
            try:
                ids = json.loads(existing)
            except Exception:
                logger.warning("Corrupt artifact index payload; resetting")
        if artifact_id not in ids:
            ids.append(artifact_id)
        self._set_json(key, json.dumps(ids), ttl)

    def _remove_artifact_from_message_index(
        self, message_id: str, artifact_id: str
    ) -> None:
        key = self.k_artifact_index_by_message(message_id)
        existing = self._get_json(key)
        if not existing:
            return
        try:
            ids = json.loads(existing)
        except Exception:
            return
        ids = [i for i in ids if i != artifact_id]
        self._set_json(key, json.dumps(ids))

    def get_artifact_ids_for_message(
        self, message_id: str, session_id: Optional[str] = None
    ) -> Optional[List[str]]:
        # Validate message ownership first if session_id provided
        if session_id is not None:
            message = self.get_message(message_id, session_id=session_id)
            if message is None:
                return None

        raw = self._get_json(self.k_artifact_index_by_message(message_id))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    # --- High-level ownership validation methods ----------------------------
    def get_session_with_full_ownership(
        self, session_id: str, user_id: str
    ) -> Optional[Session]:
        """Get a session with strict user ownership validation."""
        return self.get_session(session_id, user_id=user_id)

    def get_message_with_full_ownership(
        self, message_id: str, session_id: str, user_id: str
    ) -> Optional[Message]:
        """Get a message with full ownership chain validation (user -> session -> message)."""
        # First validate session ownership
        session = self.get_session(session_id, user_id=user_id)
        if session is None:
            return None
        # Then get message with session validation
        return self.get_message(message_id, session_id=session_id)

    def get_artifact_with_full_ownership(
        self, artifact_id: str, message_id: str, session_id: str, user_id: str
    ) -> Optional[Artifact]:
        """Get an artifact with full ownership chain validation (user -> session -> message -> artifact)."""
        # First validate message ownership through the chain
        message = self.get_message_with_full_ownership(message_id, session_id, user_id)
        if message is None:
            return None
        # Then get artifact with message validation
        return self.get_artifact(artifact_id, message_id=message_id)

    def delete_session_with_ownership(
        self, session_id: str, user_id: str, *, cascade: bool = False
    ) -> int:
        """Delete a session with strict ownership validation."""
        return self.delete_session(session_id, user_id=user_id, cascade=cascade)

    def delete_message_with_ownership(
        self, message_id: str, session_id: str, user_id: str, *, cascade: bool = False
    ) -> int:
        """Delete a message with full ownership chain validation."""
        # Validate ownership through the chain first
        message = self.get_message_with_full_ownership(message_id, session_id, user_id)
        if message is None:
            return 0
        return self.delete_message(message_id, session_id=session_id, cascade=cascade)

    def delete_artifact_with_ownership(
        self, artifact_id: str, message_id: str, session_id: str, user_id: str
    ) -> int:
        """Delete an artifact with full ownership chain validation."""
        # Validate ownership through the chain first
        artifact = self.get_artifact_with_full_ownership(
            artifact_id, message_id, session_id, user_id
        )
        if artifact is None:
            return 0
        return self.delete_artifact(artifact_id, message_id=message_id)


# Convenience default instance
redis_cache = RedisCache()
