import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.chat_session import ChatSession
from backend.app.schemas.chat import ChatSessionResponse, ChatMessagePost
from backend.app.services.chat_service import ChatFSM, get_state_prompt, CATEGORIES, TIME_SLOTS

router = APIRouter(prefix="/chat", tags=["Chat"])

def get_formatted_session(session: ChatSession):
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "current_state": session.current_state,
        "chat_data": json.loads(session.chat_data),
        "state_history": json.loads(session.state_history),
        "messages": json.loads(session.messages),
        "updated_at": session.updated_at
    }

def get_buttons_for_state(state: str, user: User, chat_data: dict, db: Session):
    if state == "HOME_MENU":
        return [
            {"label": "🔧 Product Help / Repair", "value": "A"},
            {"label": "📦 Track Current Order", "value": "B"},
            {"label": "❓ Something Else", "value": "C"}
        ]
    elif state == "PRODUCT_CATEGORY":
        return [{"label": cat, "value": cat} for cat in CATEGORIES]
    elif state == "PRODUCT_MODEL":
        cat = chat_data.get("category")
        prods = db.query(Product).filter(Product.user_id == user.user_id, Product.category == cat).all()
        buttons = []
        for p in prods:
            buttons.append({
                "label": f"{p.model_number} (S/N: {p.serial_number})",
                "value": json.dumps({
                    "shortcut": True,
                    "product": {
                        "product_id": p.product_id,
                        "category": p.category,
                        "model_number": p.model_number,
                        "serial_number": p.serial_number,
                        "purchase_date": p.purchase_date,
                        "warranty_status": p.warranty_status,
                        "installation_date": p.installation_date
                    }
                })
            })
        return buttons
    elif state == "PRODUCT_WARRANTY":
        return [
            {"label": "🛡️ In Warranty", "value": "In Warranty"},
            {"label": "❌ Out of Warranty", "value": "Out of Warranty"}
        ]
    elif state == "CONFIRM_DETAILS_BEFORE_BOOKING":
        return [
            {"label": "📅 Yes, Book Service Appointment", "value": "Yes"},
            {"label": "❌ No, Back to Main Menu", "value": "No"}
        ]
    elif state == "ORDER_STATUS_DISPLAY":
        status = chat_data.get("order_status")
        buttons = []
        if status in ["Delayed", "Installation Pending", "Shipped"]:
            buttons = [
                {"label": "⚠️ Raise Complaint", "value": "Raise a complaint"},
                {"label": "📞 Request Callback", "value": "Request callback"},
                {"label": "🚀 Escalate Issue", "value": "Escalate to support"}
            ]
        elif status == "Delivered":
            buttons = [
                {"label": "🛠️ Schedule Installation", "value": "Schedule installation"},
                {"label": "⚠️ Raise Complaint", "value": "Raise a complaint"}
            ]
        return buttons
    elif state == "OTHER_HELP_MENU":
        return [{"label": opt, "value": opt} for opt in [
            "Warranty / AMC", "Product registration", "Installation request",
            "Bill / invoice help", "Cancellation / return", "Feedback",
            "Complaint escalation", "General FAQ"
        ]]
    return None

@router.post("/session", response_model=ChatSessionResponse)
def create_session(user_id: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    session_id = str(uuid.uuid4())
    session = ChatSession(
        session_id=session_id,
        user_id=user_id,
        current_state="HOME_MENU",
        chat_data="{}",
        state_history="[]",
        messages="[]",
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    fsm = ChatFSM(db, session)
    prompt = get_state_prompt("HOME_MENU", {})
    buttons = get_buttons_for_state("HOME_MENU", user, {}, db)
    fsm.add_message("assistant", prompt, buttons)
    fsm.save()
    
    return get_formatted_session(session)

@router.get("/session/{session_id}", response_model=ChatSessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return get_formatted_session(session)

@router.post("/session/{session_id}/message", response_model=ChatSessionResponse)
def post_message(session_id: str, payload: ChatMessagePost, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Check if user input value is serialized shortcut JSON
    input_value = payload.input_value
    if isinstance(input_value, str) and input_value.startswith('{"shortcut":'):
        try:
            input_value = json.loads(input_value)
        except Exception:
            pass
            
    fsm = ChatFSM(db, session)
    
    # 1. Add user reply message
    fsm.add_message("user", payload.user_display_str)
    
    # 2. Process FSM transition
    # Handled inside DB transaction, raises HTTPException if invalid
    success = fsm.process_transition(input_value, user)
    
    if success:
        # 3. Add bot's next state prompt
        next_state = session.current_state
        prompt = get_state_prompt(next_state, fsm.chat_data)
        buttons = get_buttons_for_state(next_state, user, fsm.chat_data, db)
        fsm.add_message("assistant", prompt, buttons)
        
    fsm.save()
    return get_formatted_session(session)

@router.post("/session/{session_id}/back", response_model=ChatSessionResponse)
def step_back(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    fsm = ChatFSM(db, session)
    if fsm.go_back():
        # Re-add prompt of the reverted state to keep chat consistent
        user = db.query(User).filter(User.user_id == session.user_id).first()
        current_state = session.current_state
        prompt = get_state_prompt(current_state, fsm.chat_data)
        buttons = get_buttons_for_state(current_state, user, fsm.chat_data, db)
        fsm.add_message("assistant", prompt, buttons)
        fsm.save()
    else:
        raise HTTPException(status_code=400, detail="Cannot go back further.")
        
    return get_formatted_session(session)

@router.post("/session/{session_id}/restart", response_model=ChatSessionResponse)
def restart_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    session.current_state = "HOME_MENU"
    session.chat_data = "{}"
    session.state_history = "[]"
    session.messages = "[]"
    
    fsm = ChatFSM(db, session)
    prompt = get_state_prompt("HOME_MENU", {})
    buttons = get_buttons_for_state("HOME_MENU", user, {}, db)
    fsm.add_message("assistant", prompt, buttons)
    fsm.save()
    
    return get_formatted_session(session)
