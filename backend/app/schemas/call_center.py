from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CallSessionResponse(BaseModel):
    call_id: str
    user_id: str
    start_time: str
    end_time: Optional[str] = None
    transcript: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    appointment_id: Optional[str] = None
    status: str
    
    current_state: Optional[str] = None
    chat_data: Optional[Dict[str, Any]] = None
    audio: Optional[str] = None
    latest_message: Optional[str] = None

    class Config:
        from_attributes = True
