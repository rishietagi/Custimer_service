import os
import json
import logging
import base64
from datetime import date
from groq import Groq
from backend.app.core.config import settings

logger = logging.getLogger("ai_service")

# Initialize client lazily or when key is set
def get_groq_client():
    api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None

def transcribe_audio(audio_bytes: bytes, filename: str = "input.wav", content_type: str = "audio/wav") -> str:
    """
    Transcribes audio bytes to text using Groq's whisper-large-v3 model.
    """
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key not configured or invalid.")
    
    try:
        # Groq expects a tuple (filename, bytes, content_type)
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(filename, audio_bytes, content_type)
        )
        return response.text
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise

def text_to_speech(text: str) -> bytes:
    """
    Converts text to WAV speech audio using Groq's canopylabs/orpheus-v1-english model.
    Returns raw audio bytes.
    """
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key not configured or invalid.")
    
    # Clean markdown notation from text since TTS reads it literally
    clean_text = text.replace("**", "").replace("###", "").replace("🎉", "").replace("📦", "").replace("🛠️", "").replace("📅", "").replace("❌", "").replace("⚠️", "").replace("📞", "").replace("🚀", "").replace("✅", "").replace("⭐", "")
    
    try:
        response = client.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="troy",
            input=clean_text,
            response_format="wav"
        )
        return response.content
    except Exception as e:
        logger.error(f"Canopy Labs TTS failed: {e}")
        raise

def parse_nlu_input(current_state: str, user_text: str, chat_data: dict, available_buttons: list = None) -> dict:
    """
    Uses Llama 3.3 to map free-form user text into a structured FSM input.
    Returns a dict with:
      "fsm_input": the parsed value to transition with (str/dict/null)
      "clarification": text prompt to say to the user if input was ambiguous/invalid (str/null)
    """
    client = get_groq_client()
    if not client:
        # Return fallback flag indicating API is unavailable
        return {"fsm_input": None, "clarification": None, "fallback": True}

    buttons_context = ""
    if available_buttons:
        buttons_context = "\nAvailable Options/Buttons for this state:\n" + "\n".join(
            [f"- Label: '{btn['label']}', Value: '{btn['value']}'" for btn in available_buttons]
        )

    system_prompt = f"""You are the NLU parser for a home appliance customer support state machine.
Your job is to read the user's natural language speech/text and extract the structured input required for the current FSM state.

Current State: {current_state}
Current FSM Data: {json.dumps(chat_data)}
Today's Date: {date.today().isoformat()}
{buttons_context}

FSM State Requirements:
- HOME_MENU: The user must select either "A" (Product Help/Repair), "B" (Track Current Order), or "C" (Something Else/Other Services). Map user intent to A, B, or C.
- PRODUCT_CATEGORY: The user must select a category. Must map to exactly one of: ["Refrigerator", "Washing Machine", "Microwave", "Dishwasher", "AC", "TV", "Others"].
- PRODUCT_MODEL: The user enters a model number. Extract it (e.g. LFXS26973S).
- PRODUCT_PURCHASE_DATE: The user states when they purchased it. Parse the date and format it strictly as YYYY-MM-DD. (Calculate relative dates based on Today's Date).
- PRODUCT_WARRANTY: Map to either "In Warranty" or "Out of Warranty".
- PRODUCT_SERIAL: Extract the product serial number (e.g., must be a string of at least 5 alphanumeric characters).
- PRODUCT_INSTALL_DATE: Extract installation date as YYYY-MM-DD, or return null if same as purchase date or skipped.
- ISSUE_COLLECTION: The user describes their appliance issue. Output either a string description or a dict: {{"issue_option": "OptionName", "issue_description": "User description"}}.
- CONFIRM_DETAILS_BEFORE_BOOKING: User answers yes/no to book. Map to "Yes" or "No".
- SERVICE_ADDRESS: Extract address details into a dict: {{"address": "street", "city": "city name", "pincode": "6 digit pin", "phone": "10-15 digit phone number", "notes": "any extra info"}}. Ensure phone and pincode contain only digits.
- SERVICE_SCHEDULE: Extract scheduling details into a dict: {{"preferred_date": "YYYY-MM-DD", "preferred_time_slot": "exact slot name"}}. Slots: "09:00 AM - 12:00 PM (Morning)", "12:00 PM - 03:00 PM (Afternoon)", "03:00 PM - 06:00 PM (Evening)".
- ORDER_LOOKUP: Extract order lookup details into a dict: {{"order_id": "ORD-XXXX", "contact_info": "email or phone"}}.
- ORDER_STATUS_DISPLAY: Extract order action selection. Map to: "Escalate to support", "Request callback", "Raise a complaint", or "Schedule installation".
- ORDER_COMPLAINT_FORM: Extract complaint title and description: {{"subject": "topic", "description": "details"}}.
- OTHER_HELP_MENU: Map user request to one of the generic options: "Warranty / AMC", "Product registration", "Installation request", "Bill / invoice help", "Cancellation / return", "Feedback", "Complaint escalation", "General FAQ".
- OTHER_WARRANTY_INFO: Extract AMC details: {{"category": "category name", "comments": "notes"}}.
- OTHER_PROD_REGISTRATION: Extract registration details: {{"category": "category", "model_number": "model", "serial_number": "serial", "purchase_date": "YYYY-MM-DD"}}.
- OTHER_INSTALL_REQUEST: Extract installation details: {{"category": "category", "model_number": "model", "serial_number": "serial", "address": "addr", "pincode": "pin", "preferred_date": "YYYY-MM-DD"}}.
- OTHER_BILL_HELP: Extract billing case details: {{"order_id": "ORD-XXXX", "subject": "subject", "message": "description"}}.
- OTHER_CANCEL_RETURN: Extract cancel/return details: {{"order_id": "ORD-XXXX", "request_type": "Cancellation" or "Return", "reason": "reason description"}}.
- OTHER_FEEDBACK: Extract feedback: {{"rating": "1 Star" to "5 Star", "comments": "comments"}}.
- OTHER_COMPLAINT: Extract complaint escalation details: {{"title": "subject", "description": "description"}}.

JSON OUTPUT FORMAT:
You MUST respond strictly with a valid JSON object. Do not include markdown code block styling or extra text.
Format:
{{
  "fsm_input": <parsed_value_or_object_or_null>,
  "clarification": <spoken_clarification_string_or_null>
}}

Rule:
If the user's input is incomplete, ambiguous, invalid, or off-topic for the current state, set "fsm_input" to null, and write a polite, helpful spoken prompt in "clarification" asking the user for the missing details.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Input: \"{user_text}\""}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        return parsed
    except Exception as e:
        logger.error(f"Llama NLU parsing failed: {e}")
        # Try fallback model
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Input: \"{user_text}\""}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(response.choices[0].message.content)
            return parsed
        except Exception as fallback_e:
            logger.error(f"Llama fallback NLU parsing failed: {fallback_e}")
            return {"fsm_input": None, "clarification": None, "fallback": True}

def generate_voice_response(next_state: str, chat_data: dict, user_text: str, default_prompt: str) -> str:
    """
    Uses Llama 3.3 to re-word the default FSM prompt into a natural, conversational spoken reply.
    """
    client = get_groq_client()
    if not client:
        return default_prompt

    system_prompt = f"""You are the voice interface for a home appliance customer service assistant.
Your job is to generate a warm, conversational spoken response for the user.

Next State: {next_state}
Current FSM Data: {json.dumps(chat_data)}
User's Last Input: "{user_text}"
Default System Prompt to deliver: "{default_prompt}"

Instructions:
1. Rephrase the Default System Prompt so it flows naturally from the User's Last Input.
2. Maintain a warm, professional, helpful tone.
3. Keep the response concise and optimized for text-to-speech reading (avoid lists, markdown, or complex tables in the spoken text). 
4. Explain any summaries clearly in complete spoken sentences (e.g. "You have requested a refrigerator repair for model LFXS26973S...").
5. Do NOT include markdown styling (like asterisks or hashtags) in your response, as it will be converted directly to audio.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the spoken response."}
            ],
            temperature=0.3,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Llama response styling failed: {e}")
        # Try fallback model
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the spoken response."}
                ],
                temperature=0.3,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return default_prompt
