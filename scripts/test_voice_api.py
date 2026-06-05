import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app.main import app

def run_tests():
    client = TestClient(app)
    
    print("--- 1. Testing Create Session ---")
    res = client.post("/api/v1/chat/session?user_id=usr_john1")
    assert res.status_code == 200, f"Failed to create session: {res.text}"
    data = res.json()
    
    session_id = data["session_id"]
    print(f"Created Session ID: {session_id}")
    
    # Check audio base64 is generated
    audio = data.get("audio")
    assert audio is not None, "Audio base64 was not returned in create_session response"
    print(f"Audio base64 length: {len(audio)}")
    
    # Check messages array
    messages = data.get("messages", [])
    assert len(messages) == 1, f"Expected 1 message (greeting), got {len(messages)}"
    greeting_msg = messages[0]
    assert greeting_msg["role"] == "assistant"
    
    # Check audio_src is present
    audio_src = greeting_msg.get("audio_src")
    assert audio_src is not None, "audio_src was not stored in the greeting message object"
    print(f"Stored Audio Reference: {audio_src}")
    
    # Check if the file actually exists on the filesystem
    static_file_path = audio_src.replace("/api/static", "backend/static")
    assert os.path.exists(static_file_path), f"Audio file does not exist on disk: {static_file_path}"
    print(f"WAV File verified on disk: {static_file_path}")
    
    print("\n--- 2. Testing Post Message (FSM Transition) ---")
    payload = {
        "input_value": "A",
        "user_display_str": "Product Help / Repair"
    }
    res_msg = client.post(f"/api/v1/chat/session/{session_id}/message", json=payload)
    assert res_msg.status_code == 200, f"Failed to post message: {res_msg.text}"
    data_msg = res_msg.json()
    
    # Check audio base64 is generated for transition
    transition_audio = data_msg.get("audio")
    assert transition_audio is not None, "Audio base64 was not returned in post_message response"
    print(f"Transition Audio base64 length: {len(transition_audio)}")
    
    # Check messages array
    messages_msg = data_msg.get("messages", [])
    # 1 user + 1 assistant message added
    assert len(messages_msg) == 3, f"Expected 3 messages in total, got {len(messages_msg)}"
    
    # User message
    user_msg = messages_msg[1]
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "Product Help / Repair"
    
    # Assistant message
    assistant_msg = messages_msg[2]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg.get("audio_src") is not None, "audio_src was not stored in assistant reply"
    print(f"Stored Audio Reference for transition: {assistant_msg.get('audio_src')}")
    
    # Check if the file actually exists on the filesystem
    transition_file_path = assistant_msg.get("audio_src").replace("/api/static", "backend/static")
    assert os.path.exists(transition_file_path), f"Transition audio file does not exist on disk: {transition_file_path}"
    print(f"WAV File verified on disk for transition: {transition_file_path}")
    
    print("\n--- ALL BACKEND VOICE TESTS COMPLETED SUCCESSFULLY! ---")

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\nTEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)
