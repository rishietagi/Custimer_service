from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str
    buttons: Optional[List[Dict[str, str]]] = None

class ChatSessionCreate(BaseModel):
    # Optional field in case we want to customize or link it
    pass

class ChatMessagePost(BaseModel):
    input_value: Any
    user_display_str: str

class ChatSessionResponse(BaseModel):
    session_id: str
    user_id: str
    current_state: str
    chat_data: Dict[str, Any]
    state_history: List[str]
    messages: List[ChatMessage]
    updated_at: str

    class Config:
        from_attributes = True
