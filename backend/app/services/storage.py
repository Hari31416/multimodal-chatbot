"""In-memory session storage with simple TTL eviction (manual check on access)."""

import pandas as pd
import time
from typing import Optional, Dict, Union, List, Tuple

STORE: Dict[str, Tuple[Union[pd.DataFrame, Dict], float]] = {}
TTL_SECONDS = 60 * 60  # 1 hour for MVP


def put_dataframe(session_id: str, df: pd.DataFrame):
    key = f"df_{session_id}"
    STORE[key] = (df, time.time())


def get_dataframe(session_id: str) -> Optional[pd.DataFrame]:
    key = f"df_{session_id}"
    item = STORE.get(key)
    if not item:
        return None
    df, ts = item
    if time.time() - ts > TTL_SECONDS:
        # Expired
        del STORE[key]
        return None
    return df


def get_messages(session_id: str, no_tool_response: bool = True) -> Optional[Dict]:
    """Get messages for a session, returning None if not found or expired."""
    key = f"messages_{session_id}"
    item = STORE.get(key)

    if not item:
        return None

    messages, ts = item
    if time.time() - ts > TTL_SECONDS:
        # Expired
        del STORE[key]
        return None

    # remove tool responses if requested
    messages = [
        message
        for message in messages
        if not (no_tool_response and message.get("role") == "tool")
    ]
    return messages


def push_messages(session_id: str, messages: Union[Dict, List[Dict]]):
    """Push a message to the session, creating it if necessary."""
    existing_messages = get_messages(session_id)
    if existing_messages is None:
        existing_messages = []

    if isinstance(messages, dict):
        existing_messages.append(messages)
    elif isinstance(messages, list):
        existing_messages.extend(messages)

    STORE[f"messages_{session_id}"] = (existing_messages, time.time())


def cleanup_expired():
    now = time.time()
    expired = [k for k, (_, ts) in STORE.items() if now - ts > TTL_SECONDS]
    for k in expired:
        del STORE[k]


class SessionStorage:
    """Session storage manager with automatic cleanup."""

    def __init__(self):
        self._last_cleanup = time.time()

    def put_dataframe(self, session_id: str, df: pd.DataFrame):
        put_dataframe(session_id, df)

    def get_dataframe(self, session_id: str) -> Optional[pd.DataFrame]:
        return get_dataframe(session_id)

    def get_messages(self, session_id: str) -> Optional[Dict]:
        return get_messages(session_id)

    def push_messages(self, session_id: str, messages: Union[Dict, List[Dict]]):
        push_messages(session_id, messages)

    def cleanup(self):
        if time.time() - self._last_cleanup > TTL_SECONDS:
            cleanup_expired()
            self._last_cleanup = time.time()

    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs."""
        self.cleanup()
        return [k.split("_", 1)[-1] for k in STORE.keys()]

    def __del__(self):
        del STORE  # Clear store on deletion
        self._last_cleanup = time.time()
