import uuid
import json
import base64
import re
import logging
import os
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.chat_session import ChatSession
from backend.app.schemas.chat import ChatSessionResponse, ChatMessagePost
from backend.app.services.chat_service import ChatFSM, get_state_prompt, CATEGORIES, TIME_SLOTS
from backend.app.services.ai_service import (
    transcribe_audio, text_to_speech, text_to_speech_hindi, parse_nlu_input, generate_voice_response, get_groq_client
)

logger = logging.getLogger("chat_router")

router = APIRouter(prefix="/chat", tags=["Chat"])

def generate_and_save_tts(text: str, messages: list, language: str = "English") -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Generates TTS audio bytes, writes to a unique WAV file,
    updates the last message in `messages` with `audio_src` and `tts_error`,
    and returns (audio_base64, audio_src, tts_error).
    """
    audio_base64 = None
    audio_src = None
    tts_error = None
    try:
        if language == "Hindi":
            audio_bytes = text_to_speech_hindi(text)
        else:
            audio_bytes = text_to_speech(text)
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        STATIC_DIR = os.path.join(BASE_DIR, "static")
        AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        audio_id = str(uuid.uuid4())
        filename = f"{audio_id}.wav"
        file_path = os.path.join(AUDIO_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
            
        audio_src = f"/api/static/audio/{filename}"
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        tts_error = "Text-to-speech failed to generate."
        
    # Update last assistant message in history
    if messages and messages[-1]["role"] == "assistant":
        messages[-1]["audio_src"] = audio_src
        messages[-1]["tts_error"] = tts_error
        
    return audio_base64, audio_src, tts_error


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
    is_hindi = chat_data.get("language") == "Hindi"

    if state == "SELECT_LANGUAGE":
        return [
            {"label": "English", "value": "English"},
            {"label": "हिंदी", "value": "Hindi"}
        ]
    elif state == "HOME_MENU":
        if is_hindi:
            return [
                {"label": "🔧 उत्पाद सहायता / मरम्मत", "value": "A"},
                {"label": "📦 वर्तमान ऑर्डर ट्रैक करें", "value": "B"},
                {"label": "❓ कुछ और", "value": "C"}
            ]
        return [
            {"label": "🔧 Product Help / Repair", "value": "A"},
            {"label": "📦 Track Current Order", "value": "B"},
            {"label": "❓ Something Else", "value": "C"}
        ]
    elif state == "PRODUCT_CATEGORY":
        if is_hindi:
            cat_trans = {
                "Refrigerator": "रेफ्रिजरेटर",
                "Washing Machine": "वाशिंग मशीन",
                "Microwave": "माइक्रोवेव",
                "Dishwasher": "डिशवॉशर",
                "AC": "एसी",
                "TV": "टीवी",
                "Others": "अन्य"
            }
            return [{"label": cat_trans.get(cat, cat), "value": cat} for cat in CATEGORIES]
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
        if is_hindi:
            return [
                {"label": "🛡️ वारंटी में", "value": "In Warranty"},
                {"label": "❌ वारंटी से बाहर", "value": "Out of Warranty"}
            ]
        return [
            {"label": "🛡️ In Warranty", "value": "In Warranty"},
            {"label": "❌ Out of Warranty", "value": "Out of Warranty"}
        ]
    elif state == "CONFIRM_DETAILS_BEFORE_BOOKING":
        if is_hindi:
            return [
                {"label": "📅 हाँ, सेवा नियुक्ति बुक करें", "value": "Yes"},
                {"label": "❌ नहीं, मुख्य मेनू पर जाएँ", "value": "No"}
            ]
        return [
            {"label": "📅 Yes, Book Service Appointment", "value": "Yes"},
            {"label": "❌ No, Back to Main Menu", "value": "No"}
        ]
    elif state == "ORDER_STATUS_DISPLAY":
        status = chat_data.get("order_status")
        buttons = []
        if status in ["Delayed", "Installation Pending", "Shipped"]:
            if is_hindi:
                buttons = [
                    {"label": "⚠️ शिकायत दर्ज करें", "value": "Raise a complaint"},
                    {"label": "📞 कॉलबैक का अनुरोध करें", "value": "Request callback"},
                    {"label": "🚀 मुद्दा आगे बढ़ाएं", "value": "Escalate to support"}
                ]
            else:
                buttons = [
                    {"label": "⚠️ Raise Complaint", "value": "Raise a complaint"},
                    {"label": "📞 Request Callback", "value": "Request callback"},
                    {"label": "🚀 Escalate Issue", "value": "Escalate to support"}
                ]
        elif status == "Delivered":
            if is_hindi:
                buttons = [
                    {"label": "🛠️ स्थापना निर्धारित करें", "value": "Schedule installation"},
                    {"label": "⚠️ शिकायत दर्ज करें", "value": "Raise a complaint"}
                ]
            else:
                buttons = [
                    {"label": "🛠️ Schedule Installation", "value": "Schedule installation"},
                    {"label": "⚠️ Raise Complaint", "value": "Raise a complaint"}
                ]
        return buttons
    elif state == "OTHER_HELP_MENU":
        opts = [
            "Warranty / AMC", "Product registration", "Installation request",
            "Bill / invoice help", "Cancellation / return", "Feedback",
            "Complaint escalation", "General FAQ"
        ]
        if is_hindi:
            opt_trans = {
                "Warranty / AMC": "वारंटी / एएमसी",
                "Product registration": "उत्पाद पंजीकरण",
                "Installation request": "स्थापना का अनुरोध",
                "Bill / invoice help": "बिल / चालान सहायता",
                "Cancellation / return": "रद्दीकरण / वापसी",
                "Feedback": "प्रतिक्रिया (Feedback)",
                "Complaint escalation": "शिकायत वृद्धि",
                "General FAQ": "अक्सर पूछे जाने वाले प्रश्न"
            }
            return [{"label": opt_trans.get(opt, opt), "value": opt} for opt in opts]
        return [{"label": opt, "value": opt} for opt in opts]
    return None

def find_matching_button(state: str, text: str, user: User, chat_data: dict, db: Session):
    buttons = get_buttons_for_state(state, user, chat_data, db)
    if not buttons:
        return None
    
    clean_text = text.strip().lower()
    for btn in buttons:
        # Check if match label or value exactly
        if clean_text == btn["label"].strip().lower() or clean_text == btn["value"].strip().lower():
            return btn["value"]
        # Check if matched after removing emojis and special characters from label
        clean_label = re.sub(r"[^\w\s\/]", "", btn["label"]).strip().lower()
        # E.g. "product help / repair"
        if clean_text == clean_label:
            return btn["value"]
    return None

def deterministic_fallback_parse(state: str, text: str) -> Any:
    clean_text = text.strip().lower()
    
    if state == "HOME_MENU":
        if any(w in clean_text for w in ["repair", "product", "help", "a", "one"]):
            return "A"
        if any(w in clean_text for w in ["order", "track", "shipment", "b", "two"]):
            return "B"
        if any(w in clean_text for w in ["other", "something else", "c", "three", "faq", "invoice"]):
            return "C"
            
    elif state == "PRODUCT_CATEGORY":
        for cat in CATEGORIES:
            if cat.lower() in clean_text:
                return cat
                
    elif state == "PRODUCT_MODEL":
        # Extract alphanumeric model numbers (typically 3 to 20 characters)
        match = re.search(r"[a-z0-9\-]{3,20}", clean_text)
        if match:
            return match.group(0).upper()
            
    elif state == "PRODUCT_PURCHASE_DATE" or state == "PRODUCT_INSTALL_DATE":
        # Match YYYY-MM-DD
        match = re.search(r"\d{4}-\d{2}-\d{2}", clean_text)
        if match:
            return match.group(0)
            
    elif state == "PRODUCT_WARRANTY":
        if any(w in clean_text for w in ["in", "yes", "under", "within"]):
            return "In Warranty"
        if any(w in clean_text for w in ["out", "no", "expire", "outside"]):
            return "Out of Warranty"
            
    elif state == "PRODUCT_SERIAL":
        # Extract alphanumeric serial numbers (typically 5 to 25 characters)
        match = re.search(r"[a-z0-9\-]{5,25}", clean_text)
        if match:
            return match.group(0).upper()
            
    elif state == "CONFIRM_DETAILS_BEFORE_BOOKING":
        if any(w in clean_text for w in ["yes", "yeah", "sure", "proceed", "book", "ok"]):
            return "Yes"
        if any(w in clean_text for w in ["no", "back", "cancel", "menu"]):
            return "No"
            
    elif state == "ORDER_STATUS_DISPLAY":
        if "escalate" in clean_text or "support" in clean_text:
            return "Escalate to support"
        if "callback" in clean_text or "call" in clean_text:
            return "Request callback"
        if "complaint" in clean_text or "raise" in clean_text:
            return "Raise a complaint"
        if "install" in clean_text or "schedule" in clean_text:
            return "Schedule installation"
            
    elif state == "OTHER_HELP_MENU":
        valid_options = [
            "Warranty / AMC", "Product registration", "Installation request",
            "Bill / invoice help", "Cancellation / return", "Feedback",
            "Complaint escalation", "General FAQ"
        ]
        for opt in valid_options:
            opt_words = opt.lower().split(" / ")
            for w in opt_words:
                if w in clean_text:
                    return opt
                    
    return None

def process_hybrid_chat_step(
    session_id: str,
    db: Session,
    user: User,
    input_value: Any = None,
    user_text: str = None,
    is_voice: bool = False
) -> dict:
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    fsm = ChatFSM(db, session)
    current_state = session.current_state
    language = fsm.chat_data.get("language", "English")
    
    display_str = user_text or str(input_value)
    fsm.add_message("user", display_str)
    
    # 1. Determine target FSM input
    fsm_input = None
    if isinstance(input_value, dict) and "shortcut" in input_value:
        fsm_input = input_value
    else:
        # Check if the text matches a button exactly
        fsm_input = find_matching_button(current_state, display_str, user, fsm.chat_data, db)
        if current_state == "PRODUCT_INSTALL_DATE" and (input_value == "" or input_value is None or "skip" in str(input_value).lower()):
            fsm_input = ""
            
    clarification_message = None
    
    # 2. Run NLU mapping if FSM input is not yet resolved
    if fsm_input is None:
        buttons = get_buttons_for_state(current_state, user, fsm.chat_data, db)
        nlu_result = parse_nlu_input(current_state, display_str, fsm.chat_data, buttons)
        
        if nlu_result.get("fallback"):
            # Fallback to deterministic rules
            fsm_input = deterministic_fallback_parse(current_state, display_str)
            if fsm_input is None:
                # Ask a standard fallback clarification query
                if language == "Hindi":
                    clarification_message = "मुझे खेद है, मैं उसे समझ नहीं पाया। क्या आप कृपया अपना चयन या विवरण स्पष्ट कर सकते हैं?"
                else:
                    clarification_message = "I'm sorry, I couldn't quite get that. Could you please specify your selection or details?"
        else:
            fsm_input = nlu_result.get("fsm_input")
            clarification_message = nlu_result.get("clarification")
            
    # 3. Process transition or handle clarification
    if fsm_input is not None:
        try:
            success = fsm.process_transition(fsm_input, user)
            if success:
                # FSM transitioned successfully! Get next state and generate conversational prompt
                next_state = session.current_state
                default_prompt = get_state_prompt(next_state, fsm.chat_data)
                
                # Dynamic rephrasing of prompt using Llama
                styled_prompt = generate_voice_response(next_state, fsm.chat_data, display_str, default_prompt)
                
                # Fetch buttons for new state
                buttons = get_buttons_for_state(next_state, user, fsm.chat_data, db)
                fsm.add_message("assistant", styled_prompt, buttons)
                assistant_reply_text = styled_prompt
            else:
                raise HTTPException(status_code=400, detail="Failed to transition state machine.")
        except HTTPException as e:
            # Transition validation failed (e.g. invalid serial format, date in future, etc.)
            validation_error_detail = e.detail
            client = get_groq_client()
            if client:
                try:
                    sys_prompt = (
                        f"The user provided an input that failed FSM validation. State: {current_state}. "
                        f"Error detail: {validation_error_detail}. The user's preferred language is {language}. "
                        f"If the language is Hindi, you MUST generate the entire spoken explanation in warm, conversational, natural Hindi (using Devanagari script). "
                        f"Otherwise, generate a warm, polite spoken explanation explaining why it was invalid and what the format should be in English. "
                        f"Keep it short and spoken-friendly. No markdown."
                    )
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"User Input: \"{display_str}\""}
                        ],
                        temperature=0.3,
                        max_tokens=150
                    )
                    clarification_message = response.choices[0].message.content.strip()
                except Exception:
                    if language == "Hindi":
                        clarification_message = f"वह मान अमान्य है। {validation_error_detail}"
                    else:
                        clarification_message = f"That value is invalid. {validation_error_detail}"
            else:
                if language == "Hindi":
                    clarification_message = f"वह मान अमान्य है। {validation_error_detail}"
                else:
                    clarification_message = f"That value is invalid. {validation_error_detail}"
                
            # Stay in the same state, re-add buttons and explanation
            buttons = get_buttons_for_state(current_state, user, fsm.chat_data, db)
            fsm.add_message("assistant", clarification_message, buttons)
            assistant_reply_text = clarification_message
    else:
        if not clarification_message:
            if language == "Hindi":
                clarification_message = "क्या आप कृपया अपने अनुरोध को स्पष्ट कर सकते हैं?"
            else:
                clarification_message = "Could you please clarify your request?"
            
        buttons = get_buttons_for_state(current_state, user, fsm.chat_data, db)
        fsm.add_message("assistant", clarification_message, buttons)
        assistant_reply_text = clarification_message
        
    # 4. Generate Speech Audio
    current_language = fsm.chat_data.get("language", "English")
    audio_base64, audio_src, tts_error = generate_and_save_tts(assistant_reply_text, fsm.messages, current_language)
    fsm.save()
    
    formatted = get_formatted_session(session)
    formatted["audio"] = audio_base64
    formatted["transcript"] = display_str if is_voice else None
    return formatted

@router.post("/session", response_model=ChatSessionResponse)
def create_session(user_id: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    session_id = str(uuid.uuid4())
    session = ChatSession(
        session_id=session_id,
        user_id=user_id,
        current_state="SELECT_LANGUAGE",
        chat_data="{}",
        state_history="[]",
        messages="[]",
        updated_at=datetime.utcnow().isoformat()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    fsm = ChatFSM(db, session)
    prompt = get_state_prompt("SELECT_LANGUAGE", {})
    buttons = get_buttons_for_state("SELECT_LANGUAGE", user, {}, db)
    
    fsm.add_message("assistant", prompt, buttons)
    audio_base64, audio_src, tts_error = generate_and_save_tts(prompt, fsm.messages, "English")
    fsm.save()
    
    formatted = get_formatted_session(session)
    formatted["audio"] = audio_base64
    return formatted

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
        
    input_value = payload.input_value
    if isinstance(input_value, str) and input_value.startswith('{"shortcut":'):
        try:
            input_value = json.loads(input_value)
        except Exception:
            pass
            
    return process_hybrid_chat_step(
        session_id=session_id,
        db=db,
        user=user,
        input_value=input_value,
        user_text=payload.user_display_str,
        is_voice=False
    )

@router.post("/session/{session_id}/voice", response_model=ChatSessionResponse)
def post_voice_message(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    user = db.query(User).filter(User.user_id == session.user_id).first()
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
        
    return process_hybrid_chat_step(
        session_id=session_id,
        db=db,
        user=user,
        input_value=user_text,
        user_text=user_text,
        is_voice=True
    )

@router.post("/session/{session_id}/back", response_model=ChatSessionResponse)
def step_back(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    fsm = ChatFSM(db, session)
    if fsm.go_back():
        user = db.query(User).filter(User.user_id == session.user_id).first()
        current_state = session.current_state
        prompt = get_state_prompt(current_state, fsm.chat_data)
        buttons = get_buttons_for_state(current_state, user, fsm.chat_data, db)
        
        fsm.add_message("assistant", prompt, buttons)
        language = fsm.chat_data.get("language", "English")
        audio_base64, audio_src, tts_error = generate_and_save_tts(prompt, fsm.messages, language)
        fsm.save()
    else:
        raise HTTPException(status_code=400, detail="Cannot go back further.")
        
    formatted = get_formatted_session(session)
    formatted["audio"] = audio_base64
    return formatted

@router.post("/session/{session_id}/restart", response_model=ChatSessionResponse)
def restart_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    user = db.query(User).filter(User.user_id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    session.current_state = "SELECT_LANGUAGE"
    session.chat_data = "{}"
    session.state_history = "[]"
    session.messages = "[]"
    
    fsm = ChatFSM(db, session)
    prompt = get_state_prompt("SELECT_LANGUAGE", {})
    buttons = get_buttons_for_state("SELECT_LANGUAGE", user, {}, db)
    
    fsm.add_message("assistant", prompt, buttons)
    audio_base64, audio_src, tts_error = generate_and_save_tts(prompt, fsm.messages, "English")
    fsm.save()
    
    formatted = get_formatted_session(session)
    formatted["audio"] = audio_base64
    return formatted
