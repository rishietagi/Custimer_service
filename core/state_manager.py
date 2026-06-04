import streamlit as st
from typing import Dict, List, Any, Optional

def init_session_state():
    """Initializes all session state variables with default values."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "full_name" not in st.session_state:
        st.session_state.full_name = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "phone" not in st.session_state:
        st.session_state.phone = None
    
    # Chatbot state machine states
    if "chat_state" not in st.session_state:
        st.session_state.chat_state = "HOME_MENU"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_data" not in st.session_state:
        st.session_state.chat_data = {}
    if "state_history" not in st.session_state:
        st.session_state.state_history = []
    if "current_error" not in st.session_state:
        st.session_state.current_error = None

def login_user(user_dict: Dict[str, Any]):
    """Logs in a user and saves their profile details to session state."""
    st.session_state.user_id = user_dict.get("user_id")
    st.session_state.username = user_dict.get("username")
    st.session_state.full_name = user_dict.get("full_name")
    st.session_state.email = user_dict.get("email")
    st.session_state.phone = user_dict.get("phone")

def logout_user():
    """Logs out the current user and clears session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()

def reset_chat_flow():
    """Resets the chat interface and transitions back to the main menu."""
    st.session_state.chat_state = "HOME_MENU"
    st.session_state.chat_history = []
    st.session_state.chat_data = {}
    st.session_state.state_history = []
    st.session_state.current_error = None

def transition_to(new_state: str):
    """Pushes current state onto the history stack and transitions to new state."""
    # Push to history stack if it's different
    if st.session_state.chat_state != new_state:
        st.session_state.state_history.append(st.session_state.chat_state)
        st.session_state.chat_state = new_state
        st.session_state.current_error = None

def go_back():
    """Pops the last state from the history stack and reverts to it."""
    if st.session_state.state_history:
        st.session_state.chat_state = st.session_state.state_history.pop()
        st.session_state.current_error = None
        # Remove last chatbot interaction if appropriate, or keep history as is
        return True
    return False

def add_chat_message(role: str, content: str, buttons: Optional[List[Dict[str, str]]] = None):
    """Adds a chat message to history."""
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "buttons": buttons
    })

def set_error(msg: str):
    """Sets a validation or execution error message to show to the user."""
    st.session_state.current_error = msg

def clear_error():
    """Clears the active error message."""
    st.session_state.current_error = None

def update_chat_data(key: str, value: Any):
    """Saves a pieces of information collected during chatbot flow."""
    st.session_state.chat_data[key] = value
