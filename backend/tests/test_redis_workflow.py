"""
Test script for the new Redis-based chat session storage system.

This script tests the workflow described in storage_options_temp.md:
1. Creating sessions
2. Adding messages
3. Batch retrieval of complete sessions
4. Cleanup
"""

import asyncio
import os
import sys
from datetime import datetime


from app.models.object_models import Session, Message, ImageArtifact, CSVArtifact
from app.services.session_assembler import session_assembler
from app.services.message_service import message_service
from app.services.storage.redis_cache import redis_cache


async def test_workflow():
    """Test the complete chat session workflow."""

    print("🚀 Testing Redis-based chat session workflow...")

    # Test data
    user_id = "test_user_123"
    test_session_id = None
    created_messages = []

    try:
        # Step 1: Create a new session
        print("\n📝 Step 1: Creating new session...")
        session = Session(userId=user_id, title="Test Chat Session")

        redis_cache.save_session(session, cascade=False)
        test_session_id = session.sessionId
        print(f"✅ Created session: {test_session_id}")

        # Step 2: Add some messages with artifacts
        print("\n💬 Step 2: Adding messages...")

        # User message 1
        user_msg1 = await message_service.push_user_message(
            session_id=test_session_id,
            user_id=user_id,
            content="Hello, can you help me analyze some data?",
        )
        created_messages.append(user_msg1.messageId)
        print(f"✅ Created user message 1: {user_msg1.messageId}")

        # Assistant response 1
        assistant_msg1 = await message_service.push_assistant_message(
            session_id=test_session_id,
            user_id=user_id,
            content="Of course! I'd be happy to help you analyze your data. Please upload your dataset.",
        )
        created_messages.append(assistant_msg1.messageId)
        print(f"✅ Created assistant message 1: {assistant_msg1.messageId}")

        # User message 2 with CSV artifact
        csv_artifact = CSVArtifact(
            data="name,age,salary\nJohn,30,50000\nJane,25,55000\nBob,35,60000",
            description="Sample employee data",
            num_rows=4,
            num_columns=3,
        )

        user_msg2 = await message_service.push_user_message(
            session_id=test_session_id,
            user_id=user_id,
            content="Here's my employee data. Can you create a visualization?",
            artifacts=[csv_artifact],
        )
        created_messages.append(user_msg2.messageId)
        print(f"✅ Created user message 2 with CSV artifact: {user_msg2.messageId}")

        # Assistant response 2 with image artifact (chart)
        chart_artifact = ImageArtifact(
            data="base64_encoded_chart_data_here",
            description="Salary distribution chart",
            width=800,
            height=600,
            format="png",
        )

        assistant_msg2 = await message_service.push_assistant_message(
            session_id=test_session_id,
            user_id=user_id,
            content="I've created a salary distribution chart for your employee data.",
            artifacts=[chart_artifact],
        )
        created_messages.append(assistant_msg2.messageId)
        print(
            f"✅ Created assistant message 2 with chart artifact: {assistant_msg2.messageId}"
        )

        # Step 3: Test optimized session retrieval
        print("\n🔍 Step 3: Testing optimized session retrieval...")

        complete_session = await session_assembler.get_complete_session(
            test_session_id, user_id
        )

        if complete_session:
            print(
                f"✅ Retrieved complete session with {complete_session.numMessages} messages"
            )

            # Verify message order and content
            messages = complete_session.messages
            assert len(messages) == 4, f"Expected 4 messages, got {len(messages)}"

            # Check first message
            assert messages[0].role == "user"
            assert "analyze some data" in messages[0].content
            assert len(messages[0].artifacts or []) == 0

            # Check second message
            assert messages[1].role == "assistant"
            assert "happy to help" in messages[1].content
            assert len(messages[1].artifacts or []) == 0

            # Check third message (with CSV artifact)
            assert messages[2].role == "user"
            assert "employee data" in messages[2].content
            assert len(messages[2].artifacts or []) == 1
            assert messages[2].artifacts[0].type == "csv"

            # Check fourth message (with image artifact)
            assert messages[3].role == "assistant"
            assert "salary distribution" in messages[3].content
            assert len(messages[3].artifacts or []) == 1
            assert messages[3].artifacts[0].type == "image"

            print("✅ All message content and artifacts verified correctly")

        else:
            print("❌ Failed to retrieve complete session")
            return False

        # Step 4: Test session summary
        print("\n📊 Step 4: Testing session summary...")

        session_info = await session_assembler.get_session_summary(
            test_session_id, user_id
        )
        if session_info:
            print(
                f"✅ Session summary: {session_info.numMessages} messages, {session_info.numArtifacts} artifacts"
            )
            assert session_info.numMessages == 4
            assert session_info.numArtifacts == 2
        else:
            print("❌ Failed to get session summary")
            return False

        # Step 5: Test user sessions list
        print("\n📋 Step 5: Testing user sessions list...")

        user_sessions = await session_assembler.get_all_user_sessions(user_id)
        print(f"✅ Found {len(user_sessions)} sessions for user {user_id}")

        # Verify our test session is in the list
        found_session = next(
            (s for s in user_sessions if s.sessionId == test_session_id), None
        )
        assert found_session is not None, "Test session not found in user sessions list"

        print("🎉 All tests passed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    # finally:
    #     # Cleanup: Delete the test session
    #     if test_session_id:
    #         print(f"\n🧹 Cleaning up test session {test_session_id}...")
    #         try:
    #             deleted_count = redis_cache.delete_session_with_ownership(
    #                 test_session_id, user_id, cascade=True
    #             )
    #             print(f"✅ Deleted {deleted_count} Redis keys")
    #         except Exception as e:
    #             print(f"⚠️ Cleanup failed: {str(e)}")


async def test_performance():
    """Test the performance difference between individual vs batch fetching."""

    print("\n🏃 Testing performance comparison...")

    user_id = "perf_test_user"
    session = Session(userId=user_id, title="Performance Test Session")
    redis_cache.save_session(session, cascade=False)

    # Create multiple messages for performance testing
    num_messages = 10
    print(f"Creating {num_messages} messages...")

    for i in range(num_messages):
        user_msg = await message_service.push_user_message(
            session_id=session.sessionId,
            user_id=user_id,
            content=f"Test message {i + 1}",
        )

        assistant_msg = await message_service.push_assistant_message(
            session_id=session.sessionId,
            user_id=user_id,
            content=f"Response to message {i + 1}",
        )

    # Test batch retrieval performance
    import time

    start_time = time.time()
    complete_session = await session_assembler.get_complete_session(
        session.sessionId, user_id
    )
    batch_time = time.time() - start_time

    print(f"✅ Batch retrieval took {batch_time:.3f} seconds")
    print(f"✅ Retrieved {complete_session.numMessages} messages")

    # Cleanup
    redis_cache.delete_session_with_ownership(session.sessionId, user_id, cascade=True)
    print("✅ Performance test cleanup completed")


async def main():
    """Run all tests."""
    print("Starting Redis chat session tests...")

    # Test basic workflow
    success = await test_workflow()

    if success:
        # Test performance
        await test_performance()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        return 1

    return 0


if __name__ == "__main__":
    # Run the async test
    exit_code = asyncio.run(main())
