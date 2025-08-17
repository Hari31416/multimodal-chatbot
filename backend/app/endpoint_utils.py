import uuid
import time

from .services.redis_storage import session_storage


def start_new_session() -> str:
    """
    Start a new session and return the session ID.
    """
    session_id = str(uuid.uuid4())
    session_storage.put_session_id(session_id)
    now = time.time()
    session_metadata = {
        "session_id": session_id,
        "created_at": now,
        "last_accessed": now,
    }
    session_storage.put_data_to_session_metadata(session_id, session_metadata)
    return session_id


def get_session_info(session_id: str) -> dict:
    """
    Retrieve session metadata for a given session ID.
    """
    session_metadata = session_storage.get_session_info(session_id)
    if not session_metadata:
        raise ValueError(f"Session {session_id} not found or expired.")

    return {
        "session_id": session_metadata["session_id"],
        "created_at": session_metadata["created_at"],
        "last_accessed": time.time(),
        "title": session_metadata["first_user_message"],
    }


def get_all_sessions_info() -> dict:
    """
    Retrieve metadata for all sessions.
    """
    session_ids = session_storage.get_all_sessions()
    titles = [
        get_session_info(session_id).get("title", "Working Session")
        for session_id in session_ids
    ]
    return {
        "sessionIds": session_ids,
        "titles": titles,
    }
