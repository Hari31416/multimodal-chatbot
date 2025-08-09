"""In-memory session storage with simple TTL eviction (manual check on access)."""

import pandas as pd
import time
from typing import Optional, Dict

_STORE: Dict[str, tuple[pd.DataFrame, float]] = {}
_TTL_SECONDS = 60 * 60  # 1 hour for MVP


def put_dataframe(session_id: str, df: pd.DataFrame):
    _STORE[session_id] = (df, time.time())


def get_dataframe(session_id: str) -> Optional[pd.DataFrame]:
    item = _STORE.get(session_id)
    if not item:
        return None
    df, ts = item
    if time.time() - ts > _TTL_SECONDS:
        # Expired
        del _STORE[session_id]
        return None
    return df


def cleanup_expired():
    now = time.time()
    expired = [k for k, (_, ts) in _STORE.items() if now - ts > _TTL_SECONDS]
    for k in expired:
        del _STORE[k]
