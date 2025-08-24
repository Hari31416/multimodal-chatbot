from typing import List

from app.services.storage.redis_cache import RedisCache
from app.models.object_models import Session, Message, TextArtifact, SessionInfo


def test_save_and_get_artifact(cache: RedisCache):
    art = TextArtifact(data="hello", description="greeting")
    cache.save_artifact(art)

    fetched = cache.get_artifact(art.artifactId)
    assert fetched is not None
    assert fetched.artifactId == art.artifactId
    assert fetched.type == "text"
    assert fetched.data == "hello"


def test_save_and_get_message_and_indexes(cache: RedisCache):
    sess = Session(userId="u1", title="t1")
    msg = Message(sessionId=sess.sessionId, role="user", content="hi")
    art = TextArtifact(data="data")
    msg.artifacts = [art]

    cache.save_message(msg, cascade=True)

    # message can be fetched with proper ownership
    fetched = cache.get_message(msg.messageId, session_id=sess.sessionId)
    assert fetched is not None
    assert fetched.messageId == msg.messageId
    assert fetched.sessionId == sess.sessionId

    # artifact saved and indexed to message
    art_ids = cache.get_artifact_ids_for_message(msg.messageId)
    assert art_ids is not None and art.artifactId in art_ids
    assert cache.get_artifact(art.artifactId, message_id=msg.messageId) is not None

    # message indexed to session
    mids = cache.get_message_ids_for_session(sess.sessionId)
    assert mids is not None and msg.messageId in mids


def test_delete_message_cascade(cache: RedisCache):
    sess = Session(userId="u2")
    msg = Message(sessionId=sess.sessionId, role="user", content="hi")
    a1 = TextArtifact(data="1")
    a2 = TextArtifact(data="2")
    msg.artifacts = [a1, a2]

    cache.save_message(msg, cascade=True)

    deleted = cache.delete_message(
        msg.messageId, session_id=sess.sessionId, cascade=True
    )
    assert deleted >= 1  # message key
    # artifacts removed
    assert cache.get_artifact(a1.artifactId, message_id=msg.messageId) is None
    assert cache.get_artifact(a2.artifactId, message_id=msg.messageId) is None
    # artifact index cleared
    assert cache.get_artifact_ids_for_message(msg.messageId) in (None, [])
    # message index cleaned
    mids = cache.get_message_ids_for_session(sess.sessionId)
    assert mids in (None, []) or msg.messageId not in mids


def test_save_and_get_session_with_indexes(cache: RedisCache):
    s = Session(userId="userX", title="Title")
    m1 = Message(sessionId=s.sessionId, role="user", content="A")
    m2 = Message(sessionId=s.sessionId, role="assistant", content="B")
    s.messages.extend([m1, m2])
    s.numMessages = 2

    cache.save_session(s, cascade=True)

    # session fetch with ownership
    s2 = cache.get_session(s.sessionId, user_id="userX")
    assert s2 is not None and s2.sessionId == s.sessionId

    # user index contains SessionInfo
    infos: List[SessionInfo] | None = cache.get_sessions_for_user("userX")
    assert infos is not None
    assert any(info.sessionId == s.sessionId for info in infos)

    # message index built
    mids = cache.get_message_ids_for_session(s.sessionId)
    assert mids is not None and set(mids) >= {m1.messageId, m2.messageId}


def test_delete_session_cascade(cache: RedisCache):
    s = Session(userId="userY")
    m = Message(sessionId=s.sessionId, role="user", content="C")
    a = TextArtifact(data="Z")
    m.artifacts = [a]
    s.messages = [m]
    s.numMessages = 1

    cache.save_session(s, cascade=True)
    deleted = cache.delete_session(s.sessionId, user_id="userY", cascade=True)

    # session key deleted
    assert deleted >= 1
    # message/artifact keys gone
    assert cache.get_message(m.messageId, session_id=s.sessionId) is None
    assert cache.get_artifact(a.artifactId, message_id=m.messageId) is None
    # indexes cleaned
    assert cache.get_message_ids_for_session(s.sessionId) in (None, [])
    assert cache.get_artifact_ids_for_message(m.messageId) in (None, [])
    infos = cache.get_sessions_for_user("userY")
    assert not infos or all(info.sessionId != s.sessionId for info in infos)


def test_ownership_validation(cache: RedisCache):
    # Create session owned by user1
    s1 = Session(userId="user1", title="User1 Session")
    m1 = Message(sessionId=s1.sessionId, role="user", content="Hello from user1")
    a1 = TextArtifact(data="user1 data")
    m1.artifacts = [a1]
    s1.messages = [m1]
    s1.numMessages = 1

    cache.save_session(s1, cascade=True)

    # User1 can access their own data
    assert cache.get_session(s1.sessionId, user_id="user1") is not None
    assert cache.get_message(m1.messageId, session_id=s1.sessionId) is not None
    assert cache.get_artifact(a1.artifactId, message_id=m1.messageId) is not None

    # User2 cannot access user1's data
    assert cache.get_session(s1.sessionId, user_id="user2") is None

    # Test full ownership chain validation
    assert cache.get_session_with_full_ownership(s1.sessionId, "user1") is not None
    assert cache.get_session_with_full_ownership(s1.sessionId, "user2") is None

    assert (
        cache.get_message_with_full_ownership(m1.messageId, s1.sessionId, "user1")
        is not None
    )
    assert (
        cache.get_message_with_full_ownership(m1.messageId, s1.sessionId, "user2")
        is None
    )

    assert (
        cache.get_artifact_with_full_ownership(
            a1.artifactId, m1.messageId, s1.sessionId, "user1"
        )
        is not None
    )
    assert (
        cache.get_artifact_with_full_ownership(
            a1.artifactId, m1.messageId, s1.sessionId, "user2"
        )
        is None
    )

    # Test ownership on delete operations
    assert (
        cache.delete_session_with_ownership(s1.sessionId, "user2") == 0
    )  # Should fail
    assert (
        cache.delete_session_with_ownership(s1.sessionId, "user1") > 0
    )  # Should succeed
