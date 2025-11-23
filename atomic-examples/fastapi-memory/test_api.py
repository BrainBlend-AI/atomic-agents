"""Quick API test script to verify the multi-session architecture."""

import httpx

BASE_URL = "http://localhost:8000"


def test_api():
    """Test the basic API flow."""
    print("Testing FastAPI Memory API...\n")

    # Test user ID
    user_id = "test-user-123"

    # 1. Get user sessions (should be empty initially)
    print(f"1. Fetching sessions for user: {user_id}")
    response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    # 2. Create a new session
    print("2. Creating new session...")
    response = httpx.post(f"{BASE_URL}/users/{user_id}/sessions")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
    session_id = data["session_id"]
    print(f"   Created session: {session_id}\n")

    # 3. Send a chat message
    print("3. Sending first chat message...")
    response = httpx.post(
        f"{BASE_URL}/chat", json={"message": "Hello, how are you?", "user_id": user_id, "session_id": session_id}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    # 3b. Send another message to build conversation
    print("3b. Sending second chat message...")
    response = httpx.post(f"{BASE_URL}/chat", json={"message": "Tell me a joke", "user_id": user_id, "session_id": session_id})
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    # 3c. Get conversation history
    print("3c. Fetching conversation history...")
    response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions/{session_id}/history")
    print(f"   Status: {response.status_code}")
    history = response.json()
    print(f"   Number of messages: {len(history.get('messages', []))}")
    for i, msg in enumerate(history.get("messages", []), 1):
        role = msg.get("role")
        content = msg.get("content", "")[:50]  # Truncate for display
        suggested = msg.get("suggested_questions")
        print(f"   Message {i} ({role}): {content}...")
        if role == "assistant":
            print(f"   Suggested questions: {suggested}")
    print()

    # 4. Get user sessions (should have 1 session now)
    print("4. Fetching sessions again...")
    response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    # 5. Create another session
    print("5. Creating second session...")
    response = httpx.post(f"{BASE_URL}/users/{user_id}/sessions")
    data = response.json()
    session_id_2 = data["session_id"]
    print(f"   Created session: {session_id_2}\n")

    # 6. Get user sessions (should have 2 sessions now)
    print("6. Fetching sessions (should have 2)...")
    response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    # 7. Delete first session
    print(f"7. Deleting session {session_id}...")
    response = httpx.delete(f"{BASE_URL}/users/{user_id}/sessions/{session_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    # 8. Get user sessions (should have 1 session now)
    print("8. Fetching sessions (should have 1)...")
    response = httpx.get(f"{BASE_URL}/users/{user_id}/sessions")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")

    print("✅ All tests completed!")


if __name__ == "__main__":
    try:
        test_api()
    except httpx.ConnectError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
