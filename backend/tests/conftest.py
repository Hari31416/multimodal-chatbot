import pytest
import sys
from pathlib import Path

# Ensure 'backend' is on sys.path so 'app' package is importable in tests
THIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = THIS_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class FakeRedis:
    def __init__(self):
        self._store = {}

    # Minimal subset used by RedisCache
    def setex(self, key, ttl, value):
        # emulate redis returning bytes on get
        if isinstance(value, str):
            value = value.encode("utf-8")
        self._store[key] = value

    def get(self, key):
        return self._store.get(key)

    def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count


@pytest.fixture()
def fake_redis():
    return FakeRedis()


@pytest.fixture()
def cache(fake_redis):
    # Import inside to avoid module import at collection if packages are missing
    from app.services.storage.redis_cache import RedisCache

    return RedisCache(redis_client=fake_redis, prefix="test:chatapp:", ttl_seconds=3600)
