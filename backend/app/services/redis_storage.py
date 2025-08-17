"""Redis-based session storage with TTL management."""

import redis
import pandas as pd
import pickle
import zlib
import json
import time
from typing import Optional, Dict, Union, List
from dotenv import load_dotenv
import os

from ..utils import create_simple_logger

load_dotenv()
logger = create_simple_logger(__name__)

redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    username=os.environ.get("REDIS_USERNAME"),
    password=os.environ.get("REDIS_PASSWORD"),
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)


class RedisSessionStorage:
    """Redis session storage manager with automatic cleanup."""

    def __init__(self, redis_client=None, ttl_seconds=60 * 60):
        """
        Initialize Redis session storage.

        Args:
            redis_client: Redis client instance (if None, creates new one)
            ttl_seconds: TTL for stored items (default: 1 hour)
        """
        self.ttl_seconds = ttl_seconds
        self._last_cleanup = time.time()

        if redis_client is None:
            self.redis = redis.Redis(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", 6379)),
                username=os.environ.get("REDIS_USERNAME"),
                password=os.environ.get("REDIS_PASSWORD"),
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        else:
            self.redis = redis_client
        logger.info(
            f"Initialized RedisSessionStorage with TTL {self.ttl_seconds} seconds"
        )

    def get_all_sessions(self) -> List[str]:
        key = "all_session_ids"
        sessions = self.redis.get(key)
        if sessions is None:
            return []
        return json.loads(sessions)

    def put_session_id(self, session_id: str):
        """Store a session ID in Redis."""
        key = "all_session_ids"
        sessions = self.get_all_sessions()
        if sessions is None:
            sessions = []

        if session_id not in sessions:
            sessions.append(session_id)
            self.redis.setex(key, self.ttl_seconds, json.dumps(sessions))
            logger.debug(f"Stored session ID {session_id} in Redis")

    def delete_session_id(self, session_id: str):
        """Delete a session ID from Redis."""
        key = "all_session_ids"
        sessions = self.get_all_sessions()
        if session_id in sessions:
            sessions.remove(session_id)
            self.redis.setex(key, self.ttl_seconds, json.dumps(sessions))
            logger.info(f"Deleted session ID {session_id} from Redis")

    def put_dataframe(self, session_id: str, df: pd.DataFrame):
        """Store DataFrame for a session with TTL."""
        key = f"df_{session_id}"
        try:
            # Compress and store DataFrame
            compressed_data = zlib.compress(pickle.dumps(df))
            self.redis.setex(key, self.ttl_seconds, compressed_data)
        except Exception as e:
            logger.error(f"Error storing DataFrame for session {session_id}: {e}")
            raise

    def get_dataframe(self, session_id: str) -> Optional[pd.DataFrame]:
        """Get DataFrame for a session, returning None if not found or expired."""
        key = f"df_{session_id}"
        try:
            compressed_data = self.redis.get(key)
            if compressed_data is None:
                return None

            # Decompress and return DataFrame
            df = pickle.loads(zlib.decompress(compressed_data))
            return df
        except Exception as e:
            logger.error(f"Error retrieving DataFrame for session {session_id}: {e}")
            return None

    def get_messages(
        self, session_id: str, no_tool_response: bool = True
    ) -> Optional[List[Dict]]:
        """Get messages for a session, returning None if not found or expired."""
        key = f"messages_{session_id}"
        try:
            messages_data = self.redis.get(key)
            if messages_data is None:
                logger.info(f"No messages found for session {session_id}")
                return None

            # Decode messages (stored as JSON string)
            if isinstance(messages_data, bytes):
                messages_data = messages_data.decode("utf-8")

            messages = json.loads(messages_data)

            # Remove tool responses if requested
            if no_tool_response:
                messages = [
                    message
                    for message in messages
                    if not (message.get("role") == "tool")
                ]
            logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
        except Exception as e:
            logger.error(f"Error retrieving messages for session {session_id}: {e}")
            return None

    def push_messages(self, session_id: str, messages: Union[Dict, List[Dict]]):
        """Push a message to the session, creating it if necessary."""
        try:
            existing_messages = self.get_messages(session_id, no_tool_response=False)
            if existing_messages is None:
                existing_messages = []

            if isinstance(messages, dict):
                existing_messages.append(messages)
            elif isinstance(messages, list):
                existing_messages.extend(messages)

            key = f"messages_{session_id}"
            # Store as JSON string for text compatibility
            messages_json = json.dumps(existing_messages)
            self.redis.setex(key, self.ttl_seconds, messages_json)
            logger.info(
                f"Pushed {len(messages) if isinstance(messages, list) else 1} messages for session {session_id}"
            )
        except Exception as e:
            logger.error(f"Error pushing messages for session {session_id}: {e}")
            raise

    def get_messages_by_role(self, session_id: str, role: str) -> Optional[List[Dict]]:
        """Get messages for a session filtered by role."""
        messages = self.get_messages(session_id, no_tool_response=False)
        if messages is None:
            return None
        return [msg for msg in messages if msg.get("role") == role]

    def session_exists(self, session_id: str) -> bool:
        """Check if a session has any data (DataFrame or messages)."""
        all_sessions = self.get_all_sessions()
        if session_id not in all_sessions:
            return False

        return True

    def delete_session(self, session_id: str) -> int:
        """Delete all data for a session. Returns number of keys deleted."""
        df_key = f"df_{session_id}"
        messages_key = f"messages_{session_id}"
        keys_deleted = self.redis.delete(df_key, messages_key)
        self.delete_session_id(session_id)
        logger.info(f"Deleted session {session_id} with {keys_deleted} keys removed")
        return keys_deleted

    def get_session_ttl(self, session_id: str) -> Dict[str, int]:
        """Get remaining TTL for session data."""
        df_key = f"df_{session_id}"
        messages_key = f"messages_{session_id}"

        return {
            "dataframe_ttl": self.redis.ttl(df_key),
            "messages_ttl": self.redis.ttl(messages_key),
        }

    def extend_session_ttl(self, session_id: str, ttl_seconds: int = None) -> bool:
        """Extend TTL for all session data."""
        ttl = ttl_seconds or self.ttl_seconds
        df_key = f"df_{session_id}"
        messages_key = f"messages_{session_id}"

        results = []
        if self.redis.exists(df_key):
            results.append(self.redis.expire(df_key, ttl))
        if self.redis.exists(messages_key):
            results.append(self.redis.expire(messages_key, ttl))

        return all(results) if results else False

    def get_session_info(self, session_id: str) -> Dict:
        """Get comprehensive session information."""
        df_key = f"df_{session_id}"
        messages_key = f"messages_{session_id}"
        user_messages = self.get_messages_by_role(session_id, "user")
        if user_messages and len(user_messages) != 0:
            first_user_message = user_messages[0].get("content", "")
            if isinstance(first_user_message, list):
                first_user_message = first_user_message[0].get("text", "")
        else:
            first_user_message = "Working on it..."

        info = {
            "session_id": session_id,
            "has_dataframe": bool(self.redis.exists(df_key)),
            "has_messages": bool(self.redis.exists(messages_key)),
            "dataframe_ttl": self.redis.ttl(df_key),
            "messages_ttl": self.redis.ttl(messages_key),
            "first_user_message": first_user_message,
            "last_accessed": time.time(),
        }

        # Add message count if messages exist
        if info["has_messages"]:
            messages = self.get_messages(session_id, no_tool_response=False)
            info["message_count"] = len(messages) if messages else 0

        # Add DataFrame info if it exists
        if info["has_dataframe"]:
            df = self.get_dataframe(session_id)
            if df is not None:
                info["dataframe_shape"] = df.shape
                info["dataframe_columns"] = list(df.columns)

        other_metadata = self.get_session_metadata(session_id)
        if other_metadata:
            info = {**info, **other_metadata}
        return info

    def ping(self) -> bool:
        """Test Redis connection."""
        try:
            return self.redis.ping()
        except Exception:
            logger.error("Redis ping failed")
            return False

    def close(self):
        """Close Redis connection."""
        try:
            self.redis.close()
        except Exception:
            pass

    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Get data for a session by key, returning None if not found or expired."""
        key = f"meta_{session_id}"
        data = self.redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    def put_data_to_session_metadata(self, session_id: str, data: Dict):
        """Put data to a specific name for a session."""
        key = f"meta_{session_id}"
        existing_data = self.get_session_metadata(session_id)
        if existing_data is None:
            existing_data = {}
        existing_data = {**existing_data, **data}
        self.redis.setex(key, self.ttl_seconds, json.dumps(existing_data))
        logger.info(
            f"Puted data to session metadata for session {session_id} under key {key}"
        )

    def get(self, session_id: str, key: str) -> Optional[Dict]:
        """Get data for a session by key, returning None if not found or expired."""
        return self.get_session_metadata(session_id, key)

    def put(self, session_id: str, key: str, data: Dict):
        """Put data to a specific key for a session."""
        self.put_data_to_session_metadata(session_id, key, data)

    def delete_session_data(self, session_id: str):
        """Delete specific data for a session."""
        all_keys = self.redis.keys(f"*{session_id}*")
        if all_keys:
            deleted_count = self.redis.delete(*all_keys)
            logger.info(f"Deleted {deleted_count} keys for session {session_id}")
            return deleted_count
        else:
            logger.info(f"No keys found for session {session_id}")
            return 0

    def delete_all_session_data(self):
        """Delete all session data."""
        all_keys = (
            self.redis.keys("df_*")
            + self.redis.keys("messages_*")
            + self.redis.keys("meta_*")
            + self.redis.keys("all_session_ids")
            + self.redis.keys("session_*")
        )
        if all_keys:
            deleted_count = self.redis.delete(*all_keys)
            logger.info(f"Deleted {deleted_count+1} keys for all sessions")
            return deleted_count + 1
        else:
            logger.info("No keys found for any sessions")
            return 0


session_storage = RedisSessionStorage()
