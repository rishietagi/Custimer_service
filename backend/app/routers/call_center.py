import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.chat_session import ChatSession
from backend.app.models.call_session import CallSession
from backend.app.schemas.call_center import CallSessionResponse
from backend.app.services.chat_service import ChatFSM
from backend.app.services.ai_service import transcribe_audio, generate_call_summary
from backend.app.routers.chat import (
    generate_and_save_tts,
    process_hybrid_chat_step,
    get_buttons_for_state
)

logger = logging.getLogger("call_center_router")

router = APIRouter(prefix="/call-center", tags=["Call Center"])

@router.post("/calls", response_model=CallSessionResponse)
def start_call(user_id: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
    start_time = datetime.utcnow().isoformat()
    
    # Create CallSession record
    call = CallSession(
        call_id=call_id,
        user_id=user_id,
        start_time=start_time,
        status="Active",
        transcript="[]"
    )
    db.add(call)
    
    # Create matching ChatSession
    chat_sess = ChatSession(
        session_id=call_id,
        user_id=user_id,
        current_state="SELECT_LANGUAGE",
        chat_data=json.dumps({"language": "English"}),
        state_history="[]",
        messages="[]",
        updated_at=start_time
    )
    db.add(chat_sess)
    db.commit()
    
    fsm = ChatFSM(db, chat_sess)
    from backend.app.services.chat_service import get_state_prompt
    greeting = get_state_prompt("SELECT_LANGUAGE", {})
    buttons = get_buttons_for_state("SELECT_LANGUAGE", user, {"language": "English"}, db)
    fsm.add_message("assistant", greeting, buttons)
    
    audio_base64, audio_src, tts_error = generate_and_save_tts(greeting, fsm.messages, "English")
    fsm.save()
    
    # Update call session transcript with the greeting
    call.transcript = json.dumps(fsm.messages)
    db.commit()
    
    return {
        "call_id": call_id,
        "user_id": user_id,
        "start_time": start_time,
        "end_time": None,
        "transcript": fsm.messages,
        "summary": None,
        "appointment_id": None,
        "status": "Active",
        "current_state": "SELECT_LANGUAGE",
        "chat_data": {"language": "English"},
        "audio": audio_base64,
        "latest_message": greeting
    }

@router.post("/calls/{call_id}/voice", response_model=CallSessionResponse)
def post_call_voice(
    call_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    call = db.query(CallSession).filter(CallSession.call_id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found.")
    if call.status != "Active":
        raise HTTPException(status_code=400, detail="Call is not active.")
        
    user = db.query(User).filter(User.user_id == call.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    try:
        audio_bytes = file.file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read audio file.")
        
    try:
        user_text = transcribe_audio(audio_bytes, filename=file.filename, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
    if not user_text or not user_text.strip():
        raise HTTPException(status_code=400, detail="No speech detected. Please speak clearly.")
        
    # Step FSM using transcribe results
    fsm_res = process_hybrid_chat_step(
        session_id=call_id,
        db=db,
        user=user,
        input_value=user_text,
        user_text=user_text,
        is_voice=True
    )
    
    # Fetch updated state
    chat_sess = db.query(ChatSession).filter(ChatSession.session_id == call_id).first()
    chat_data = json.loads(chat_sess.chat_data)
    messages = json.loads(chat_sess.messages)
    
    # Update transcript in CallSession
    call.transcript = json.dumps(messages)
    
    # Track appointment if scheduled
    apt_id = chat_data.get("appointment_id")
    if apt_id:
        call.appointment_id = apt_id
        
    final_states = ["BOOKING_CONFIRMATION", "TICKET_SUBMITTED", "ORDER_CALLBACK_CONFIRM", "ORDER_ESCALATE_CONFIRM"]
    if chat_sess.current_state in final_states:
        call.status = "Completed"
        call.end_time = datetime.utcnow().isoformat()
        plain_transcript = ""
        for msg in messages:
            plain_transcript += f"{msg['role'].capitalize()}: {msg['content']}\n"
        call.summary = generate_call_summary(plain_transcript, chat_data, user.full_name)
        
    db.commit()
    
    latest_assistant_msg = messages[-1]["content"] if messages and messages[-1]["role"] == "assistant" else ""
    
    return {
        "call_id": call_id,
        "user_id": call.user_id,
        "start_time": call.start_time,
        "end_time": call.end_time,
        "transcript": messages,
        "summary": call.summary,
        "appointment_id": call.appointment_id,
        "status": call.status,
        "current_state": chat_sess.current_state,
        "chat_data": chat_data,
        "audio": fsm_res.get("audio"),
        "latest_message": latest_assistant_msg
    }

@router.post("/calls/{call_id}/end", response_model=CallSessionResponse)
def end_call(call_id: str, db: Session = Depends(get_db)):
    call = db.query(CallSession).filter(CallSession.call_id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call session not found.")
        
    chat_sess = db.query(ChatSession).filter(ChatSession.session_id == call_id).first()
    chat_data = {}
    messages = []
    current_state = "HOME_MENU"
    if chat_sess:
        chat_data = json.loads(chat_sess.chat_data)
        messages = json.loads(chat_sess.messages)
        current_state = chat_sess.current_state
        
    if call.status == "Active":
        call.status = "Ended"
        call.end_time = datetime.utcnow().isoformat()
        
    user = db.query(User).filter(User.user_id == call.user_id).first()
    customer_name = user.full_name if user else "Customer"
    
    # Generate structured summary if not yet generated
    if not call.summary:
        plain_transcript = ""
        for msg in messages:
            plain_transcript += f"{msg['role'].capitalize()}: {msg['content']}\n"
        call.summary = generate_call_summary(plain_transcript, chat_data, customer_name)
        
    db.commit()
    
    latest_assistant_msg = messages[-1]["content"] if messages and messages[-1]["role"] == "assistant" else ""
    
    return {
        "call_id": call_id,
        "user_id": call.user_id,
        "start_time": call.start_time,
        "end_time": call.end_time,
        "transcript": messages,
        "summary": call.summary,
        "appointment_id": call.appointment_id,
        "status": call.status,
        "current_state": current_state,
        "chat_data": chat_data,
        "audio": None,
        "latest_message": latest_assistant_msg
    }

@router.get("/calls", response_model=List[CallSessionResponse])
def list_calls(user_id: str = Query(...), db: Session = Depends(get_db)):
    calls = db.query(CallSession).filter(CallSession.user_id == user_id).order_by(CallSession.start_time.desc()).all()
    res = []
    for c in calls:
        chat_sess = db.query(ChatSession).filter(ChatSession.session_id == c.call_id).first()
        current_state = chat_sess.current_state if chat_sess else "HOME_MENU"
        chat_data = json.loads(chat_sess.chat_data) if chat_sess else {}
        messages = json.loads(c.transcript) if c.transcript else []
        res.append({
            "call_id": c.call_id,
            "user_id": c.user_id,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "transcript": messages,
            "summary": c.summary,
            "appointment_id": c.appointment_id,
            "status": c.status,
            "current_state": current_state,
            "chat_data": chat_data,
            "audio": None,
            "latest_message": messages[-1]["content"] if messages and messages[-1]["role"] == "assistant" else ""
        })
    return res

@router.get("/calls/{call_id}", response_model=CallSessionResponse)
def get_call(call_id: str, db: Session = Depends(get_db)):
    c = db.query(CallSession).filter(CallSession.call_id == call_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Call session not found.")
        
    chat_sess = db.query(ChatSession).filter(ChatSession.session_id == call_id).first()
    current_state = chat_sess.current_state if chat_sess else "HOME_MENU"
    chat_data = json.loads(chat_sess.chat_data) if chat_sess else {}
    messages = json.loads(c.transcript) if c.transcript else []
    
    return {
        "call_id": c.call_id,
        "user_id": c.user_id,
        "start_time": c.start_time,
        "end_time": c.end_time,
        "transcript": messages,
        "summary": c.summary,
        "appointment_id": c.appointment_id,
        "status": c.status,
        "current_state": current_state,
        "chat_data": chat_data,
        "audio": None,
        "latest_message": messages[-1]["content"] if messages and messages[-1]["role"] == "assistant" else ""
    }
