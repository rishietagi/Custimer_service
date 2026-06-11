import os
import json
import logging
import base64
import re
from datetime import date
import requests
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
    Uses the 'tara' voice with contextual vocal direction tags for natural, human-like output.
    Returns raw audio bytes.
    """
    client = get_groq_client()
    if not client:
        raise ValueError("Groq API key not configured or invalid.")
    
    # Clean markdown notation and emojis from text since TTS reads it literally
    clean_text = text
    # Remove emojis
    for emoji in ["🎉", "📦", "🛠️", "📅", "❌", "⚠️", "📞", "🚀", "✅", "⭐", "🔧", "❓", "🛡️", "📋", "📝", "💡", "🏠", "📍"]:
        clean_text = clean_text.replace(emoji, "")
    # Remove markdown formatting
    clean_text = clean_text.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
    # Remove numbered lists (e.g., "1. ", "2) ") and bullet points
    clean_text = re.sub(r'^\s*\d+[\.\)]\s*', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'^\s*[-•]\s*', '', clean_text, flags=re.MULTILINE)
    # Remove HTML tags if any
    clean_text = re.sub(r'<[^>]*>', '', clean_text)
    # Collapse extra whitespace
    clean_text = re.sub(r'\n{2,}', '. ', clean_text)
    clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()
    
    # Choose contextual vocal direction based on text content for natural delivery
    text_lower = clean_text.lower()
    if any(word in text_lower for word in ["congratulations", "successfully", "confirmed", "booked", "registered", "submitted", "thank you"]):
        vocal_direction = "[cheerful]"
    elif any(word in text_lower for word in ["sorry", "invalid", "error", "failed", "couldn't", "unable", "unfortunately"]):
        vocal_direction = "[calm reassuring]"
    elif any(word in text_lower for word in ["welcome", "hello", "hi there", "good morning", "good afternoon", "how may i help", "how can i help"]):
        vocal_direction = "[warm friendly]"
    else:
        vocal_direction = "[conversational]"
    
    styled_text = f"{vocal_direction} {clean_text}"
    
    try:
        response = client.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="autumn",
            input=styled_text,
            response_format="wav"
        )
        return response.read()
    except Exception as e:
        error_str = str(e)
        if "terms" in error_str.lower() or "403" in error_str or "not allowed" in error_str.lower():
            logger.error(
                f"Canopy Labs Orpheus TTS failed - MODEL TERMS NOT ACCEPTED. "
                f"Please visit https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english "
                f"and accept the model terms. Error: {e}"
            )
        else:
            logger.error(f"Canopy Labs TTS failed: {e}")
        raise

def text_to_speech_hindi(text: str) -> bytes:
    """
    Converts Hindi text to speech audio using Sarvam AI Bulbul v3 model (primary)
    or falls back to Hugging Face Vibevoice if Sarvam API key is not configured.
    Uses the 'meera' voice for warm, natural Hindi speech.
    Returns raw audio bytes.
    """


    # Clean markdown notation and emojis from text since TTS reads it literally
    clean_text = text
    for emoji in ["🎉", "📦", "🛠️", "📅", "❌", "⚠️", "📞", "🚀", "✅", "⭐", "🔧", "❓", "🛡️", "📋", "📝", "💡", "🏠", "📍"]:
        clean_text = clean_text.replace(emoji, "")
    clean_text = clean_text.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
    clean_text = re.sub(r'^\s*\d+[\.\\)]\s*', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'^\s*[-•]\s*', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'<[^>]*>', '', clean_text)
    clean_text = re.sub(r'\n{2,}', '. ', clean_text)
    clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()

    # --- Primary: Sarvam AI Bulbul v3 (natural, fluent Hindi) ---
    sarvam_key = (settings.SARVAM_API_KEY or os.environ.get("SARVAM_API_KEY") or "").strip()
    if sarvam_key:
        try:
            sarvam_url = "https://api.sarvam.ai/text-to-speech"
            headers = {
                "api-subscription-key": sarvam_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": clean_text,
                "target_language_code": "hi-IN",
                "speaker": "priya",
                "model": "bulbul:v3"
            }
            response = requests.post(sarvam_url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                resp_json = response.json()
                # Sarvam returns base64-encoded audio in the response
                audio_b64 = resp_json.get("audios", [None])[0] or resp_json.get("audio", "")
                if audio_b64:
                    return base64.b64decode(audio_b64)
                else:
                    logger.warning("Sarvam TTS returned empty audio, falling back to Vibevoice.")
            else:
                logger.warning(f"Sarvam TTS failed with status {response.status_code}: {response.text}. Falling back to Vibevoice.")
        except Exception as e:
            logger.warning(f"Sarvam TTS failed: {e}. Falling back to Vibevoice.")

    # --- Fallback: Hugging Face Vibevoice ---
    api_key = settings.HUGGINGFACE_API_KEY or os.environ.get("HUGGINGFACE_API_KEY")
    if not api_key:
        raise ValueError("Neither Sarvam nor Hugging Face API key is configured. Please add SARVAM_API_KEY or HUGGINGFACE_API_KEY to your .env file.")

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": clean_text}
    model_id = "tarun7r/vibevoice-hindi-1.5B"
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code != 200:
            logger.error(f"Hugging Face TTS failed with status {response.status_code}: {response.text}")
            raise ValueError(f"Hugging Face TTS API returned status {response.status_code}")
        return response.content
    except Exception as e:
        logger.error(f"Hugging Face TTS failed: {e}")
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

    language = chat_data.get("language", "English")
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
The user's preferred language is: {language}. The user's input might be in {language} (which could be Hindi or English). 
If it is in Hindi, understand the meaning and map it correctly to the English structured values required by the FSM (for example, mapping "हाँ", "हाँ जी", "पहला विकल्प" to "Yes", "नहीं", "ना" to "No", "रेफ्रिजरेटर" or "फ्रिज" to "Refrigerator", and translating/mapping issue categories or details accordingly).
{buttons_context}

FSM State Requirements:
- SELECT_LANGUAGE: The user must select preferred language. Map to "English" or "Hindi".
- HOME_MENU: The user must select either "A" (Product Help/Repair), "B" (Track Current Order), or "C" (Something Else/Other Services). Map user intent to A, B, or C.
- PRODUCT_CATEGORY: The user must select a category. Must map to exactly one of: ["Refrigerator", "Washing Machine", "Microwave", "Dishwasher", "AC", "TV", "Others"].
- PRODUCT_MODEL: The user enters a model number. Extract it (e.g. LFXS26973S).
- PRODUCT_PURCHASE_DATE: The user states when they purchased it. Parse the date and format it strictly as YYYY-MM-DD. (Calculate relative dates based on Today's Date).
- PRODUCT_WARRANTY: Map to either "In Warranty" or "Out of Warranty".
- PRODUCT_SERIAL: Extract the product serial number (e.g., must be a string of at least 5 alphanumeric characters).
- PRODUCT_INSTALL_DATE: Extract installation date as YYYY-MM-DD, or return null if same as purchase date or skipped.
- ISSUE_COLLECTION: The user selects their appliance issue from the options. Output the issue option selected (must match one of the available buttons/options if provided, or represent the symptom e.g. "Not cooling").
- ISSUE_EXPLANATION: The user describes or explains their issue in detail. Extract the detailed description as a string.
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
If the user's input is incomplete, ambiguous, invalid, or off-topic for the current state, set "fsm_input" to null, and write a polite, helpful spoken prompt in "clarification" asking the user for the missing details. The clarification prompt MUST be written in the user's preferred language ({language}). If the language is Hindi, you MUST generate the clarification prompt in warm, conversational, natural Hindi (using Devanagari script). Otherwise, generate it in English.
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

    language = chat_data.get("language", "English")

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
6. The user's preferred language is {language}. If the language is Hindi, you MUST generate the entire spoken response in warm, conversational, natural Hindi (using Devanagari script). Otherwise, generate the response in English.
"""

    user_prompt = "Generate the spoken response in Hindi." if language == "Hindi" else "Generate the spoken response."

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
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
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return default_prompt

def generate_call_summary(transcript: str, chat_data: dict, customer_name: str) -> str:
    """
    Generates a structured call summary using Llama 3.3.
    """
    client = get_groq_client()
    if not client:
        # Fallback summary formatted identically
        return (
            f"Customer Name: {customer_name}\n"
            f"Product: {chat_data.get('category', 'N/A')}\n"
            f"Model: {chat_data.get('model_number', 'N/A')}\n"
            f"Issue: {chat_data.get('issue_description', 'N/A')}\n"
            f"Warranty: {chat_data.get('warranty_status', 'N/A')}\n"
            f"Preferred Date: {chat_data.get('preferred_date', 'N/A')}\n"
            f"Preferred Time: {chat_data.get('preferred_time_slot', 'N/A')}\n"
            f"Address: {chat_data.get('service_address', 'N/A')}\n"
            f"Appointment ID: {chat_data.get('appointment_id', 'N/A')}"
        )

    system_prompt = """You are a call center assistant. Generate a structured call summary for the support call.
The summary MUST strictly follow this format:
Customer Name: <name>
Product: <product category or N/A>
Model: <model number or N/A>
Issue: <issue description or N/A>
Warranty: <warranty status or N/A>
Preferred Date: <preferred appointment date or N/A>
Preferred Time: <preferred time slot or N/A>
Address: <service address or N/A>
Appointment ID: <appointment ID or N/A>

Do not include any extra text, pleasantries, or markdown formatting other than these key-value pairs.
"""

    user_prompt = f"""
Customer Name: {customer_name}
FSM Data: {json.dumps(chat_data)}
Transcript:
{transcript}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate call summary: {e}")
        # Try fallback model
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return (
                f"Customer Name: {customer_name}\n"
                f"Product: {chat_data.get('category', 'N/A')}\n"
                f"Model: {chat_data.get('model_number', 'N/A')}\n"
                f"Issue: {chat_data.get('issue_description', 'N/A')}\n"
                f"Warranty: {chat_data.get('warranty_status', 'N/A')}\n"
                f"Preferred Date: {chat_data.get('preferred_date', 'N/A')}\n"
                f"Preferred Time: {chat_data.get('preferred_time_slot', 'N/A')}\n"
                f"Address: {chat_data.get('service_address', 'N/A')}\n"
                f"Appointment ID: {chat_data.get('appointment_id', 'N/A')}"
            )
