import uuid
import json
from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.user import User
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.appointment import Appointment
from backend.app.models.support_case import SupportCase
from backend.app.models.chat_session import ChatSession

from backend.app.core.validators import (
    validate_model_number, validate_pincode, validate_phone, 
    validate_future_date, validate_email, validate_serial_number
)

STATES = {
    "SELECT_LANGUAGE": {"label": "Language Selection", "progress": 2},
    "HOME_MENU": {"label": "Home Menu", "progress": 5},
    # Path A: Product Help Flow
    "PRODUCT_CATEGORY": {"label": "Product Category", "progress": 15},
    "PRODUCT_MODEL": {"label": "Product Model", "progress": 25},
    "PRODUCT_PURCHASE_DATE": {"label": "Purchase Date", "progress": 35},
    "PRODUCT_WARRANTY": {"label": "Warranty Status", "progress": 45},
    "PRODUCT_SERIAL": {"label": "Serial Number", "progress": 55},
    "PRODUCT_INSTALL_DATE": {"label": "Installation Date", "progress": 65},
    "ISSUE_COLLECTION": {"label": "Issue Details", "progress": 75},
    "ISSUE_EXPLANATION": {"label": "Issue Explanation", "progress": 80},
    "CONFIRM_DETAILS_BEFORE_BOOKING": {"label": "Review Details", "progress": 85},
    "SERVICE_ADDRESS": {"label": "Service Address", "progress": 90},
    "SERVICE_SCHEDULE": {"label": "Appointment Date & Time", "progress": 95},
    "BOOKING_CONFIRMATION": {"label": "Booking Confirmed", "progress": 100},
    # Path B: Order Status Flow
    "ORDER_LOOKUP": {"label": "Order Lookup", "progress": 30},
    "ORDER_STATUS_DISPLAY": {"label": "Order Status Timeline", "progress": 70},
    "ORDER_COMPLAINT_FORM": {"label": "Submit Complaint", "progress": 90},
    "ORDER_CALLBACK_CONFIRM": {"label": "Callback Requested", "progress": 100},
    "ORDER_ESCALATE_CONFIRM": {"label": "Escalated to Support", "progress": 100},
    # Path C: Other Help Flow
    "OTHER_HELP_MENU": {"label": "Other Services", "progress": 25},
    "OTHER_WARRANTY_INFO": {"label": "Warranty & AMC Information", "progress": 60},
    "OTHER_PROD_REGISTRATION": {"label": "Product Registration", "progress": 60},
    "OTHER_INSTALL_REQUEST": {"label": "Request Installation", "progress": 60},
    "OTHER_BILL_HELP": {"label": "Billing & Invoices Help", "progress": 60},
    "OTHER_CANCEL_RETURN": {"label": "Cancellation / Return Request", "progress": 60},
    "OTHER_FEEDBACK": {"label": "Submit Feedback", "progress": 60},
    "OTHER_COMPLAINT": {"label": "Escalate Complaint", "progress": 60},
    "OTHER_FAQ": {"label": "Frequently Asked Questions", "progress": 60},
    "TICKET_SUBMITTED": {"label": "Request Submitted", "progress": 100}
}

CATEGORIES = ["Refrigerator", "Washing Machine", "Microwave", "Dishwasher", "AC", "TV", "Others"]

CATEGORY_ISSUES = {
    "Refrigerator": ["Not cooling", "Leaking water", "Making noise", "Door not closing", "Ice maker not working", "Other"],
    "Washing Machine": ["Not turning on", "Spin cycle not working", "Leaking water", "Making noise", "Error code displayed", "Other"],
    "Microwave": ["Not heating", "Turntable not spinning", "Sparking inside", "Touchpad unresponsive", "Other"],
    "Dishwasher": ["Leaking water", "Not draining", "Loud noise", "Dishes not clean", "Other"],
    "AC": ["Not cooling", "Leaking water", "Blowing warm air", "Remote not working", "Other"],
    "TV": ["No screen display", "Sound but no picture", "Lines on screen", "Remote unresponsive", "Other"],
    "Others": ["Not turning on", "Leaking water", "Making noise", "Error code displayed", "Other"]
}

TIME_SLOTS = [
    "09:00 AM - 12:00 PM (Morning)",
    "12:00 PM - 03:00 PM (Afternoon)",
    "03:00 PM - 06:00 PM (Evening)"
]

def get_state_prompt(state: str, chat_data: dict) -> str:
    """Returns the bot's greeting/prompt text for the current state."""
    is_hindi = chat_data.get("language") == "Hindi"
    
    if state == "SELECT_LANGUAGE":
        return "Please select your preferred language / कृपया अपनी पसंदीदा भाषा चुनें:"
    
    elif state == "HOME_MENU":
        if is_hindi:
            return "नमस्ते! आज मैं आपकी क्या सहायता कर सकता हूँ? शुरू करने के लिए कृपया नीचे दिए गए विकल्पों में से एक चुनें:"
        return "Hello! How may I help you today? Please choose one of the options below to get started:"
    
    # Path A: Product Help Flow
    elif state == "PRODUCT_CATEGORY":
        if is_hindi:
            return "आपको किस उत्पाद श्रेणी (product category) में सहायता की आवश्यकता है?"
        return "Which product category do you need help with?"
    elif state == "PRODUCT_MODEL":
        if is_hindi:
            return "कृपया अपने उत्पाद का मॉडल नंबर दर्ज करें (जैसे LFXS26973S):"
        return "Please enter your product's model number (e.g. LFXS26973S):"
    elif state == "PRODUCT_PURCHASE_DATE":
        if is_hindi:
            return "आपने उत्पाद कब खरीदा था? (यदि आपको सटीक तारीख नहीं पता है, तो आप अनुमानित तारीख चुन सकते हैं):"
        return "When did you purchase the product? (If you don't know the exact date, you can select an approximate date):"
    elif state == "PRODUCT_WARRANTY":
        if is_hindi:
            return "आपके उत्पाद की वारंटी स्थिति (warranty status) क्या है? (यदि अनिश्चित हैं, तो हम इसे बाद में देख सकते हैं):"
        return "What is the warranty status of your product? (If unsure, we can check it later):"
    elif state == "PRODUCT_SERIAL":
        if is_hindi:
            return "कृपया उत्पाद का सीरियल नंबर दर्ज करें (आमतौर पर उपकरण के अंदर या पीछे एक स्टिकर पर पाया जाता है):"
        return "Please enter the product serial number (often found on a sticker inside or behind the appliance):"
    elif state == "PRODUCT_INSTALL_DATE":
        if is_hindi:
            return "उत्पाद कब स्थापित (install) किया गया था? (वैकल्पिक, यदि खरीद की तारीख के समान है तो आप इसे खाली छोड़ सकते हैं):"
        return "When was the product installed? (Optional, you can leave it blank if same as purchase date):"
    elif state == "ISSUE_COLLECTION":
        category = chat_data.get("category", "Others")
        cat_trans = {
            "Refrigerator": "रेफ्रिजरेटर",
            "Washing Machine": "वाशिंग मशीन",
            "Microwave": "माइक्रोवेव",
            "Dishwasher": "डिशवॉशर",
            "AC": "एसी",
            "TV": "टीवी",
            "Others": "अन्य"
        }
        category_display = cat_trans.get(category, category) if is_hindi else category
        if is_hindi:
            return f"आपको अपने {category_display} के साथ क्या समस्या आ रही है?"
        return f"What issue are you facing with your {category}?"
    elif state == "ISSUE_EXPLANATION":
        issue_option = chat_data.get("issue_option", "issue")
        if is_hindi:
            return f"आपने '{issue_option}' चुना है। कृपया इस समस्या के बारे में विस्तार से बताएं (जैसे कि यह कब शुरू हुई, इसके क्या लक्षण हैं):"
        return f"You selected '{issue_option}'. Please describe/explain this issue in detail so our technician is fully prepared (e.g. specific symptoms, when it started):"
    elif state == "CONFIRM_DETAILS_BEFORE_BOOKING":
        category = chat_data.get("category", "Product")
        model = chat_data.get("model_number", "")
        issue_opt = chat_data.get("issue_option", "")
        issue_desc = chat_data.get("issue_description", "")
        serial = chat_data.get("serial_number", "")
        warranty = chat_data.get("warranty_status", "")
        
        if is_hindi:
            cat_trans = {"Refrigerator": "रेफ्रिजरेटर", "Washing Machine": "वाशिंग मशीन", "Microwave": "माइक्रोवेव", "Dishwasher": "डिशवॉशर", "AC": "एसी", "TV": "टीवी", "Others": "अन्य"}
            category = cat_trans.get(category, category)
            warranty = "वारंटी में (In Warranty)" if warranty == "In Warranty" else "वारंटी से बाहर (Out of Warranty)"
            summary = (
                f"यहाँ आपके द्वारा दिए गए विवरणों का सारांश है:\n\n"
                f"**उत्पाद श्रेणी:** {category}\n"
                f"**मॉडल नंबर:** {model}\n"
                f"**सीरियल नंबर:** {serial}\n"
                f"**वारंटी स्थिति:** {warranty}\n"
                f"**समस्या:** {issue_opt}\n"
                f"**विवरण:** {issue_desc}\n\n"
                "क्या आप आगे बढ़ना चाहते हैं और तकनीशियन के घर आने के लिए सेवा नियुक्ति (service appointment) बुक करना चाहते हैं?"
            )
        else:
            summary = (
                f"Here is a summary of the details you provided:\n\n"
                f"**Product Category:** {category}\n"
                f"**Model Number:** {model}\n"
                f"**Serial Number:** {serial}\n"
                f"**Warranty Status:** {warranty}\n"
                f"**Selected Issue:** {issue_opt}\n"
                f"**Issue Explanation:** {issue_desc}\n\n"
                "Would you like to proceed and book a service appointment for a technician to visit your home?"
            )
        return summary
    elif state == "SERVICE_ADDRESS":
        if is_hindi:
            return "कृपया अपने सेवा बुकिंग विवरण प्रदान करें ताकि हम एक स्थानीय तकनीशियन नियुक्त कर सकें:"
        return "Please provide your service booking details so we can assign a local technician:"
    elif state == "SERVICE_SCHEDULE":
        if is_hindi:
            return "आप तकनीशियन से कब मिलने को प्राथमिकता देंगे? कृपया एक तारीख और समय स्लॉट चुनें:"
        return "When would you prefer the technician to visit? Please select a date and time slot:"
    elif state == "BOOKING_CONFIRMATION":
        apt_id = chat_data.get("appointment_id", "N/A")
        tech = chat_data.get("technician_name", "Certified Tech")
        date_str = chat_data.get("preferred_date", "N/A")
        slot = chat_data.get("preferred_time_slot", "N/A")
        model = chat_data.get("model_number", "N/A")
        category = chat_data.get("category", "Product")
        
        if is_hindi:
            cat_trans = {"Refrigerator": "रेफ्रिजरेटर", "Washing Machine": "वाशिंग मशीन", "Microwave": "माइक्रोवेव", "Dishwasher": "डिशवॉशर", "AC": "एसी", "TV": "टीवी", "Others": "अन्य"}
            category = cat_trans.get(category, category)
            msg = (
                f"### 🎉 बुकिंग की पुष्टि हो गई है!\n\n"
                f"**नियुक्ति (Appointment) आईडी:** {apt_id}\n"
                f"**बुकिंग स्थिति:** निर्धारित (Scheduled)\n"
                f"**उत्पाद:** {category} (मॉडल: {model})\n"
                f"**निर्धारित तिथि:** {date_str}\n"
                f"**समय स्लॉट:** {slot}\n"
                f"**नियुक्त तकनीशियन:** {tech}\n\n"
                f"हमारे तकनीशियन आगमन से 30 मिनट पहले आपको कॉल करेंगे। यदि आपको कोई बदलाव करना है, तो आप 'My Appointments' टैब में जाकर कभी भी इसे बदल या रद्द कर सकते हैं।\n\n"
                f"आज मैं आपकी और क्या सहायता कर सकता हूँ?"
            )
        else:
            msg = (
                f"### 🎉 Booking Confirmed!\n\n"
                f"**Appointment ID:** {apt_id}\n"
                f"**Booking Status:** Scheduled\n"
                f"**Product:** {category} (Model: {model})\n"
                f"**Scheduled Date:** {date_str}\n"
                f"**Time Slot:** {slot}\n"
                f"**Assigned Technician:** {tech}\n\n"
                f"Our technician will call you 30 minutes before arrival. If you need to make changes, you can reschedule or cancel this appointment anytime in the 'My Appointments' tab.\n\n"
                f"How else can I assist you today?"
            )
        return msg

    # Path B: Order Status Flow
    elif state == "ORDER_LOOKUP":
        if is_hindi:
            return "अपना ऑर्डर ट्रैक करने के लिए, कृपया अपना ऑर्डर आईडी और उस ऑर्डर के साथ पंजीकृत फोन नंबर या ईमेल दर्ज करें:"
        return "To track your order, please enter your Order ID and the phone number or email registered with that order:"
    elif state == "ORDER_STATUS_DISPLAY":
        order_id = chat_data.get("order_id", "N/A")
        prod = chat_data.get("product_name", "N/A")
        status = chat_data.get("order_status", "N/A")
        
        if is_hindi:
            msg = (
                f"### 📦 ऑर्डर की स्थिति: **{status}**\n"
                f"**ऑर्डर आईडी:** {order_id}\n"
                f"**उत्पाद:** {prod}\n\n"
                f"यहाँ आपके ऑर्डर वितरण स्थिति की समयरेखा है। यदि आपके ऑर्डर में कोई समस्या है, तो आप नीचे दिए गए एक्शन बटनों का उपयोग कर सकते हैं।"
            )
        else:
            msg = (
                f"### 📦 Order Status: **{status}**\n"
                f"**Order ID:** {order_id}\n"
                f"**Product:** {prod}\n\n"
                f"Here is your order delivery status timeline. If your order needs attention, you can use the action buttons below."
            )
        return msg
    elif state == "ORDER_COMPLAINT_FORM":
        if is_hindi:
            return "कृपया नीचे अपने ऑर्डर के संबंध में अपनी शिकायत या पूछताछ का वर्णन करें:"
        return "Please describe your complaint or inquiry regarding your order below:"
    elif state == "ORDER_CALLBACK_CONFIRM":
        if is_hindi:
            return "धन्यवाद। एक कॉलबैक अनुरोध बनाया गया है। एक सहायता अधिकारी 2 से 4 व्यावसायिक घंटों के भीतर आपके पंजीकृत फोन नंबर पर आपसे संपर्क करेगा।"
        return "Thank you. A callback request has been created. A support executive will contact you at your registered phone number within 2 to 4 business hours."
    elif state == "ORDER_ESCALATE_CONFIRM":
        if is_hindi:
            return "आपके ऑर्डर की समस्या को वरिष्ठ सहायता प्रबंधक के पास भेज दिया गया है। टिकट संदर्भ आईडी: " + chat_data.get("ticket_id", "N/A") + "। हम सक्रिय रूप से इसकी समीक्षा कर रहे हैं और ईमेल के माध्यम से आपसे संपर्क करेंगे।"
        return "Your order issue has been escalated to senior support manager. Ticket reference ID: " + chat_data.get("ticket_id", "N/A") + ". We are actively reviewing this and will contact you via email."

    # Path C: Other Help Flow
    elif state == "OTHER_HELP_MENU":
        if is_hindi:
            return "आज मैं आपकी और क्या मदद कर सकता हूँ? कृपया नीचे दिए गए मेनू से एक विकल्प चुनें:"
        return "What else can I help you with today? Please select an option from the menu below:"
    elif state == "OTHER_WARRANTY_INFO":
        if is_hindi:
            return "### वारंटी और वार्षिक रखरखाव अनुबंध (AMC) की जानकारी\n\nसभी स्मार्टकेयर घरेलू उपकरण 1 साल की मानक निर्माता वारंटी के साथ आते हैं। पार्ट्स और लेबर को कवर करने के लिए आप एएमसी खरीद सकते हैं। अनुकूलित एएमसी योजना उद्धरण का अनुरोध करने के लिए कृपया नीचे दिया गया फॉर्म पूरा करें:"
        return "### Centralized Warranty & Annual Maintenance Contract (AMC) Information\n\nAll SmartCare home appliances come with a standard 1-year manufacturer warranty. You can purchase AMC extensions to cover parts and labor. Please complete the form below to request a customized AMC plan quotation:"
    elif state == "OTHER_PROD_REGISTRATION":
        if is_hindi:
            return "### अपना उत्पाद पंजीकृत करें\n\nअपना उत्पाद पंजीकृत करने से वारंटी सहायता में तेजी आती है। कृपया नीचे दिए गए विवरण भरें:"
        return "### Register Your Product\n\nRegistering your product speeds up warranty support and provides you with software updates. Please fill in the details below:"
    elif state == "OTHER_INSTALL_REQUEST":
        if is_hindi:
            return "### उत्पाद स्थापना (Installation) का अनुरोध करें\n\nनए उपकरण को स्थापित करने में सहायता चाहिए? स्थापना सहायता का अनुरोध करने के लिए नीचे दिए गए विवरण प्रदान करें:"
        return "### Request Product Installation\n\nNeed help setting up a new appliance? Provide the details below to request installation support:"
    elif state == "OTHER_BILL_HELP":
        if is_hindi:
            return "### बिलिंग और चालान (Invoice) सहायता\n\nचालान की प्रति, बिलिंग विवाद, या भुगतान प्रश्नों के लिए, कृपया टिकट उठाने के लिए नीचे दिए गए फॉर्म का उपयोग करें:"
        return "### Billing and Invoice Support\n\nFor copy of invoice, billing disputes, or payment queries, please use the form below to raise a ticket:"
    elif state == "OTHER_CANCEL_RETURN":
        if is_hindi:
            return "### रद्दीकरण और वापसी का अनुरोध\n\nऑर्डर को रद्द करने या उत्पाद को वापस करने के लिए, कृपया यह अनुरोध फॉर्म जमा करें:"
        return "### Cancellation & Return Request\n\nTo cancel an unshipped order or return a delivered appliance, please submit this request form:"
    elif state == "OTHER_FEEDBACK":
        if is_hindi:
            return "### फीडबैक सबमिट करें\n\nआपका फीडबैक हमें अपने उत्पादों और सेवाओं को बेहतर बनाने में मदद करता है। कृपया नीचे अपने अनुभव को रेट करें:"
        return "### Submit Feedback\n\nYour feedback helps us improve our products and services. Please rate your experience below:"
    elif state == "OTHER_COMPLAINT":
        if is_hindi:
            return "### शिकायत दर्ज करें\n\nयदि आपके पास किसी सेवा या उत्पाद के साथ कोई अनसुलझा मुद्दा है, तो कृपया इसे नीचे विस्तार से बताएं ताकि हम इसे एक शिकायत प्रबंधक को सौंप सकें:"
        return "### Escalate a Complaint\n\nIf you have an unresolved issue with a service or product, please describe it in detail below so we can assign it to an escalation manager:"
    elif state == "OTHER_FAQ":
        if is_hindi:
            return "### अक्सर पूछे जाने वाले प्रश्न (FAQ)\n\nमदद लेख पढ़ने के लिए नीचे दिए गए किसी भी प्रश्न पर क्लिक करें। यदि आपको अभी भी मदद की आवश्यकता है, तो बेझिझक होम मेनू पर लौटें या टिकट उठाएं।"
        return "### Frequently Asked Questions (FAQ)\n\nBelow are some helpful answers. If you still need help, feel free to return to the home menu or raise a ticket."
    elif state == "TICKET_SUBMITTED":
        if is_hindi:
            return f"### ✅ अनुरोध सफलतापूर्वक प्रस्तुत किया गया!\n\nआपकी टिकट संदर्भ आईडी **{chat_data.get('ticket_id', 'N/A')}** है।\nहमारी टीम आपके अनुरोध की समीक्षा करेगी और जल्द ही आपसे संपर्क करेगी\n\nक्या आज मैं आपकी और कोई सहायता कर सकता हूँ?"
        return f"### ✅ Request Submitted Successfully!\n\nYour ticket reference ID is **{chat_data.get('ticket_id', 'N/A')}**.\nOur team will review your request and get back to you shortly.\n\nIs there anything else I can help you with today?"
    
    return "How else may I assist you?"

class ChatFSM:
    def __init__(self, db: Session, session: ChatSession):
        self.db = db
        self.session = session
        self.chat_data = json.loads(session.chat_data)
        self.state_history = json.loads(session.state_history)
        self.messages = json.loads(session.messages)

    def transition_to(self, new_state: str):
        if self.session.current_state != new_state:
            self.state_history.append(self.session.current_state)
            self.session.current_state = new_state

    def save(self):
        self.session.chat_data = json.dumps(self.chat_data)
        self.session.state_history = json.dumps(self.state_history)
        self.session.messages = json.dumps(self.messages)
        self.session.updated_at = datetime.utcnow().isoformat()
        self.db.commit()

    def add_message(self, role: str, content: str, buttons: list = None):
        self.messages.append({
            "role": role,
            "content": content,
            "buttons": buttons
        })

    def process_transition(self, input_value: any, user: User) -> bool:
        """
        Validates input for the current state and handles the state transitions.
        Raises HTTPException on validation errors so client knows why it failed.
        """
        state = self.session.current_state
        user_id = user.user_id
        customer_name = user.full_name

        if state == "SELECT_LANGUAGE":
            if input_value in ["English", "Hindi"]:
                self.chat_data["language"] = input_value
                self.transition_to("HOME_MENU")
                return True
            else:
                raise HTTPException(status_code=400, detail="Please select a valid language: English or Hindi.")

        elif state == "HOME_MENU":
            if input_value == "A":
                self.transition_to("PRODUCT_CATEGORY")
            elif input_value == "B":
                self.transition_to("ORDER_LOOKUP")
            elif input_value == "C":
                self.transition_to("OTHER_HELP_MENU")
            else:
                raise HTTPException(status_code=400, detail="Invalid menu option selection.")
            return True

        # Path A: Product Help Flow
        elif state == "PRODUCT_CATEGORY":
            if input_value not in CATEGORIES:
                raise HTTPException(status_code=400, detail="Please select a valid product category.")
            self.chat_data["category"] = input_value
            self.transition_to("PRODUCT_MODEL")
            return True

        elif state == "PRODUCT_MODEL":
            # Check if user passed model number directly or is bypassing with quick select
            if isinstance(input_value, dict) and "shortcut" in input_value:
                # Shortcut prefilled all product details
                p = input_value["product"]
                self.chat_data["model_number"] = p["model_number"]
                self.chat_data["serial_number"] = p["serial_number"]
                self.chat_data["purchase_date"] = p["purchase_date"]
                self.chat_data["warranty_status"] = p["warranty_status"]
                self.chat_data["installation_date"] = p.get("installation_date")
                self.transition_to("ISSUE_COLLECTION")
                return True
            else:
                ok, err = validate_model_number(str(input_value))
                if not ok:
                    raise HTTPException(status_code=400, detail=err)
                self.chat_data["model_number"] = str(input_value).strip()
                self.transition_to("PRODUCT_PURCHASE_DATE")
                return True

        elif state == "PRODUCT_PURCHASE_DATE":
            if not input_value:
                raise HTTPException(status_code=400, detail="Purchase date cannot be empty.")
            # Date can be string "YYYY-MM-DD"
            try:
                purchase_date_val = datetime.strptime(str(input_value), "%Y-%m-%d").date()
                if purchase_date_val > date.today():
                    raise HTTPException(status_code=400, detail="Purchase date cannot be in the future.")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
            
            self.chat_data["purchase_date"] = str(input_value)
            self.transition_to("PRODUCT_WARRANTY")
            return True

        elif state == "PRODUCT_WARRANTY":
            if input_value not in ["In Warranty", "Out of Warranty"]:
                raise HTTPException(status_code=400, detail="Please select a valid warranty status.")
            self.chat_data["warranty_status"] = input_value
            self.transition_to("PRODUCT_SERIAL")
            return True

        elif state == "PRODUCT_SERIAL":
            ok, err = validate_serial_number(str(input_value))
            if not ok:
                raise HTTPException(status_code=400, detail=err)
            self.chat_data["serial_number"] = str(input_value).strip().upper()
            self.transition_to("PRODUCT_INSTALL_DATE")
            return True

        elif state == "PRODUCT_INSTALL_DATE":
            if input_value: # User supplied install date
                try:
                    install_date_val = datetime.strptime(str(input_value), "%Y-%m-%d").date()
                    if install_date_val > date.today():
                        raise HTTPException(status_code=400, detail="Installation date cannot be in the future.")
                    p_date_str = self.chat_data.get("purchase_date")
                    if p_date_str:
                        p_date = datetime.strptime(p_date_str, "%Y-%m-%d").date()
                        if install_date_val < p_date:
                            raise HTTPException(status_code=400, detail="Installation date cannot be before purchase date.")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
                
                self.chat_data["installation_date"] = str(input_value)
            else:
                self.chat_data["installation_date"] = None
                
            self.transition_to("ISSUE_COLLECTION")
            return True

        elif state == "ISSUE_COLLECTION":
            # Accept dict or string
            issue_opt = ""
            if isinstance(input_value, dict):
                issue_opt = input_value.get("issue_option", "").strip()
            else:
                issue_opt = str(input_value).strip()
            
            if not issue_opt:
                raise HTTPException(status_code=400, detail="Please select your product issue option.")
                
            self.chat_data["issue_option"] = issue_opt
            self.transition_to("ISSUE_EXPLANATION")
            return True

        elif state == "ISSUE_EXPLANATION":
            issue_desc = str(input_value).strip()
            if not issue_desc:
                is_hindi = self.chat_data.get("language") == "Hindi"
                err_msg = "कृपया अपनी समस्या का विस्तार से वर्णन करें।" if is_hindi else "Please describe the issue symptoms in detail."
                raise HTTPException(status_code=400, detail=err_msg)
                
            self.chat_data["issue_description"] = f"{self.chat_data.get('issue_option')} - {issue_desc}"
            self.transition_to("CONFIRM_DETAILS_BEFORE_BOOKING")
            return True

        elif state == "CONFIRM_DETAILS_BEFORE_BOOKING":
            if input_value == "Yes":
                # Pre-fill user profile details if available
                self.chat_data["service_address"] = user.address or ""
                self.chat_data["service_city"] = user.city or ""
                self.chat_data["service_pincode"] = user.pincode or ""
                self.chat_data["service_phone"] = user.phone or ""
                self.transition_to("SERVICE_ADDRESS")
            else:
                self.transition_to("HOME_MENU")
            return True

        elif state == "SERVICE_ADDRESS":
            addr = ""
            city = ""
            pin = ""
            phone = ""
            notes = ""
            if isinstance(input_value, dict):
                addr = input_value.get("address", "").strip()
                city = input_value.get("city", "").strip()
                pin = input_value.get("pincode", "").strip()
                phone = input_value.get("phone", "").strip()
                notes = input_value.get("notes", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Address input must be provided.")
                
            if not addr:
                raise HTTPException(status_code=400, detail="Address cannot be empty.")
            if not city:
                raise HTTPException(status_code=400, detail="City cannot be empty.")
                
            ok_pin, err_pin = validate_pincode(pin)
            if not ok_pin:
                raise HTTPException(status_code=400, detail=err_pin)
                
            ok_phone, err_phone = validate_phone(phone)
            if not ok_phone:
                raise HTTPException(status_code=400, detail=err_phone)
                
            self.chat_data["service_address"] = addr
            self.chat_data["service_city"] = city
            self.chat_data["service_pincode"] = pin
            self.chat_data["service_phone"] = phone
            self.chat_data["service_notes"] = notes
            
            self.transition_to("SERVICE_SCHEDULE")
            return True

        elif state == "SERVICE_SCHEDULE":
            pref_date = ""
            pref_slot = ""
            if isinstance(input_value, dict):
                pref_date = input_value.get("preferred_date", "").strip()
                pref_slot = input_value.get("preferred_time_slot", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Scheduling details must be provided.")
                
            ok_date, err_date = validate_future_date(pref_date)
            if not ok_date:
                raise HTTPException(status_code=400, detail=err_date)
                
            if pref_slot not in TIME_SLOTS:
                raise HTTPException(status_code=400, detail="Please select a valid service time slot.")
                
            # Complete booking
            apt_id = "APT-" + str(uuid.uuid4())[:8].upper()
            technicians = {
                "Refrigerator": "David Chen (Refrigerator Expert)",
                "Washing Machine": "Sarah Miller (Laundry Specialist)",
                "Microwave": "Tom Wilson (Kitchen Appliance Tech)",
                "Dishwasher": "Elena Rostova (Dishwasher Master)",
                "AC": "James O'Connor (HVAC Engineer)",
                "TV": "Kenji Sato (OLED Display Tech)",
                "Others": "Marcus Vance (General Support Tech)"
            }
            category = self.chat_data.get("category", "Others")
            assigned_tech = technicians.get(category, "Certified Tech")
            
            self.chat_data["appointment_id"] = apt_id
            self.chat_data["preferred_date"] = pref_date
            self.chat_data["preferred_time_slot"] = pref_slot
            self.chat_data["technician_name"] = assigned_tech
            
            # Save Appointment to db
            apt_obj = Appointment(
                appointment_id=apt_id,
                user_id=user_id,
                customer_name=customer_name,
                product_category=category,
                product_model=self.chat_data.get("model_number"),
                serial_number=self.chat_data.get("serial_number"),
                purchase_date=self.chat_data.get("purchase_date"),
                warranty_status=self.chat_data.get("warranty_status"),
                issue_description=self.chat_data.get("issue_description"),
                address=self.chat_data.get("service_address"),
                city=self.chat_data.get("service_city"),
                pincode=self.chat_data.get("service_pincode"),
                preferred_date=pref_date,
                preferred_time_slot=pref_slot,
                status="Scheduled",
                technician_name=assigned_tech,
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(apt_obj)
            self.transition_to("BOOKING_CONFIRMATION")
            return True

        # Path B: Order Status Flow
        elif state == "ORDER_LOOKUP":
            ord_id = ""
            contact = ""
            if isinstance(input_value, dict):
                ord_id = input_value.get("order_id", "").strip()
                contact = input_value.get("contact_info", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Order ID and contact details are required.")
                
            if not ord_id:
                raise HTTPException(status_code=400, detail="Order ID cannot be empty.")
            if not contact:
                raise HTTPException(status_code=400, detail="Phone or email registered is required.")
                
            # Look up order in database
            order = self.db.query(Order).filter(
                Order.order_id.ilike(ord_id.strip()),
                (Order.registered_phone.ilike(contact.strip()) | Order.registered_email.ilike(contact.strip()))
            ).first()
            
            if not order:
                raise HTTPException(status_code=400, detail="No order found matching details. Try ORD-1153 with jane.smith@support-example.com")
                
            self.chat_data["order_id"] = order.order_id
            self.chat_data["product_name"] = order.product_name
            self.chat_data["order_status"] = order.status
            self.transition_to("ORDER_STATUS_DISPLAY")
            return True

        elif state == "ORDER_STATUS_DISPLAY":
            if input_value == "Escalate to support":
                ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
                self.chat_data["ticket_id"] = ticket_id
                
                ticket = SupportCase(
                    case_id=ticket_id,
                    user_id=user_id,
                    title=f"Order Escalation: {self.chat_data.get('order_id')}",
                    description=f"User escalated order status inquiry for order {self.chat_data.get('order_id')} ({self.chat_data.get('product_name')}). Current status: {self.chat_data.get('order_status')}.",
                    category="Complaint escalation",
                    status="Open",
                    created_at=datetime.utcnow().isoformat()
                )
                self.db.add(ticket)
                self.transition_to("ORDER_ESCALATE_CONFIRM")
                
            elif input_value == "Request callback":
                self.transition_to("ORDER_CALLBACK_CONFIRM")
                
            elif input_value == "Raise a complaint":
                self.transition_to("ORDER_COMPLAINT_FORM")
                
            elif input_value == "Schedule installation":
                self.chat_data["category"] = "Others"
                self.chat_data["issue_description"] = "Installation Request for newly ordered product."
                self.transition_to("PRODUCT_CATEGORY")
                
            return True

        elif state == "ORDER_COMPLAINT_FORM":
            subj = ""
            desc = ""
            if isinstance(input_value, dict):
                subj = input_value.get("subject", "").strip()
                desc = input_value.get("description", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Complaint subject and description required.")
                
            if not subj:
                raise HTTPException(status_code=400, detail="Complaint subject is required.")
            if not desc:
                raise HTTPException(status_code=400, detail="Please provide details of complaint.")
                
            ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            
            ticket = SupportCase(
                case_id=ticket_id,
                user_id=user_id,
                title=f"Order Complaint: {subj}",
                description=f"Order ID: {self.chat_data.get('order_id')}\nDescription: {desc}",
                category="Complaint escalation",
                status="Open",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(ticket)
            self.transition_to("TICKET_SUBMITTED")
            return True

        # Path C: Other Help Flow
        elif state == "OTHER_HELP_MENU":
            valid_options = [
                "Warranty / AMC", "Product registration", "Installation request",
                "Bill / invoice help", "Cancellation / return", "Feedback",
                "Complaint escalation", "General FAQ"
            ]
            if input_value not in valid_options:
                raise HTTPException(status_code=400, detail="Please select a valid option.")
                
            if input_value == "Warranty / AMC":
                self.transition_to("OTHER_WARRANTY_INFO")
            elif input_value == "Product registration":
                self.transition_to("OTHER_PROD_REGISTRATION")
            elif input_value == "Installation request":
                self.transition_to("OTHER_INSTALL_REQUEST")
            elif input_value == "Bill / invoice help":
                self.transition_to("OTHER_BILL_HELP")
            elif input_value == "Cancellation / return":
                self.transition_to("OTHER_CANCEL_RETURN")
            elif input_value == "Feedback":
                self.transition_to("OTHER_FEEDBACK")
            elif input_value == "Complaint escalation":
                self.transition_to("OTHER_COMPLAINT")
            elif input_value == "General FAQ":
                self.transition_to("OTHER_FAQ")
            return True

        elif state == "OTHER_WARRANTY_INFO":
            comments = ""
            cat = ""
            if isinstance(input_value, dict):
                comments = input_value.get("comments", "").strip()
                cat = input_value.get("category", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Appliance category required.")
                
            if not cat:
                raise HTTPException(status_code=400, detail="Please select a product category.")
                
            ticket_id = "CAS-WNT-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            
            ticket = SupportCase(
                case_id=ticket_id,
                user_id=user_id,
                title=f"AMC Quote Inquiry: {cat}",
                description=f"AMC Quotation Request for {cat}. Additional Notes: {comments}",
                category="Warranty / AMC",
                status="Open",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(ticket)
            self.transition_to("TICKET_SUBMITTED")
            return True

        elif state == "OTHER_PROD_REGISTRATION":
            cat = ""
            model = ""
            serial = ""
            p_date = ""
            if isinstance(input_value, dict):
                cat = input_value.get("category", "").strip()
                model = input_value.get("model_number", "").strip()
                serial = input_value.get("serial_number", "").strip()
                p_date = input_value.get("purchase_date", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Appliance registration details required.")
                
            if not cat:
                raise HTTPException(status_code=400, detail="Please select a category.")
                
            ok_model, err_model = validate_model_number(model)
            if not ok_model:
                raise HTTPException(status_code=400, detail=err_model)
                
            ok_serial, err_serial = validate_serial_number(serial)
            if not ok_serial:
                raise HTTPException(status_code=400, detail=err_serial)
                
            if not p_date:
                raise HTTPException(status_code=400, detail="Please select a purchase date.")
                
            try:
                purchase_date_val = datetime.strptime(p_date, "%Y-%m-%d").date()
                if purchase_date_val > date.today():
                    raise HTTPException(status_code=400, detail="Purchase date cannot be in the future.")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
                
            prod_id = "prod_" + str(uuid.uuid4())[:8]
            prod = Product(
                product_id=prod_id,
                user_id=user_id,
                category=cat,
                model_number=model,
                serial_number=serial.upper(),
                purchase_date=p_date,
                warranty_status="In Warranty", # default
                installation_date=None
            )
            self.db.add(prod)
            
            ticket_id = "REG-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            self.transition_to("TICKET_SUBMITTED")
            return True

        elif state == "OTHER_INSTALL_REQUEST":
            cat = ""
            model = ""
            serial = ""
            addr = ""
            pincode = ""
            pref_date = ""
            if isinstance(input_value, dict):
                cat = input_value.get("category", "").strip()
                model = input_value.get("model_number", "").strip()
                serial = input_value.get("serial_number", "").strip()
                addr = input_value.get("address", "").strip()
                pincode = input_value.get("pincode", "").strip()
                pref_date = input_value.get("preferred_date", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Installation request details required.")
                
            if not cat:
                raise HTTPException(status_code=400, detail="Product category is required.")
            if not model:
                raise HTTPException(status_code=400, detail="Model number is required.")
            if not addr:
                raise HTTPException(status_code=400, detail="Service address is required.")
                
            ok_pin, err_pin = validate_pincode(pincode)
            if not ok_pin:
                raise HTTPException(status_code=400, detail=err_pin)
                
            ok_date, err_date = validate_future_date(pref_date)
            if not ok_date:
                raise HTTPException(status_code=400, detail=err_date)
                
            apt_id = "APT-INS-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["appointment_id"] = apt_id
            
            apt = Appointment(
                appointment_id=apt_id,
                user_id=user_id,
                customer_name=customer_name,
                product_category=cat,
                product_model=model,
                serial_number=serial or "MOCK_SERIAL",
                purchase_date=date.today().isoformat(),
                warranty_status="In Warranty",
                issue_description="Installation Request",
                address=addr,
                city=user.city or "City",
                pincode=pincode,
                preferred_date=pref_date,
                preferred_time_slot="12:00 PM - 03:00 PM",
                status="Scheduled",
                technician_name="Installation Team",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(apt)
            
            self.chat_data["ticket_id"] = "APT-" + apt_id.split("-")[-1]
            self.transition_to("TICKET_SUBMITTED")
            return True

        elif state == "OTHER_BILL_HELP":
            ord_id = ""
            subject = ""
            msg = ""
            if isinstance(input_value, dict):
                ord_id = input_value.get("order_id", "").strip()
                subject = input_value.get("subject", "").strip()
                msg = input_value.get("message", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Invoice details required.")
                
            if not subject:
                raise HTTPException(status_code=400, detail="Please enter a subject.")
            if not msg:
                raise HTTPException(status_code=400, detail="Please describe your billing issue.")
                
            ticket_id = "CAS-BIL-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            
            ticket = SupportCase(
                case_id=ticket_id,
                user_id=user_id,
                title=f"Billing: {subject}",
                description=f"Order Ref: {ord_id}\nQuery: {msg}",
                category="Bill / invoice help",
                status="Open",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(ticket)
            self.transition_to("TICKET_SUBMITTED")
            return True

        elif state == "OTHER_CANCEL_RETURN":
            ord_id = ""
            req_type = "Cancellation"
            reason = ""
            if isinstance(input_value, dict):
                ord_id = input_value.get("order_id", "").strip()
                req_type = input_value.get("request_type", "Cancellation")
                reason = input_value.get("reason", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Order details required.")
                
            if not ord_id:
                raise HTTPException(status_code=400, detail="Order ID is required.")
            if not reason:
                raise HTTPException(status_code=400, detail="Please provide a reason.")
                
            ticket_id = "CAS-RTR-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            
            ticket = SupportCase(
                case_id=ticket_id,
                user_id=user_id,
                title=f"{req_type} Request: {ord_id}",
                description=f"Request Type: {req_type}\nOrder: {ord_id}\nReason: {reason}",
                category="Cancellation / return",
                status="Open",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(ticket)
            self.transition_to("TICKET_SUBMITTED")
            return True

        elif state == "OTHER_FEEDBACK":
            rating = "5 Star"
            comments = ""
            if isinstance(input_value, dict):
                rating = input_value.get("rating", "5 Star")
                comments = input_value.get("comments", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Rating is required.")
                
            ticket_id = "FBK-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            
            ticket = SupportCase(
                case_id=ticket_id,
                user_id=user_id,
                title=f"Feedback Submission (Rating: {rating})",
                description=f"Rating: {rating}\nComments: {comments}",
                category="Feedback",
                status="Resolved",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(ticket)
            self.transition_to("TICKET_SUBMITTED")
            return True

        elif state == "OTHER_COMPLAINT":
            title = ""
            desc = ""
            if isinstance(input_value, dict):
                title = input_value.get("title", "").strip()
                desc = input_value.get("description", "").strip()
            else:
                raise HTTPException(status_code=400, detail="Complaint details required.")
                
            if not title:
                raise HTTPException(status_code=400, detail="Complaint title is required.")
            if not desc:
                raise HTTPException(status_code=400, detail="Please describe your complaint.")
                
            ticket_id = "CAS-ESC-" + str(uuid.uuid4())[:6].upper()
            self.chat_data["ticket_id"] = ticket_id
            
            ticket = SupportCase(
                case_id=ticket_id,
                user_id=user_id,
                title=f"Escalation: {title}",
                description=desc,
                category="Complaint escalation",
                status="Open",
                created_at=datetime.utcnow().isoformat()
            )
            self.db.add(ticket)
            self.transition_to("TICKET_SUBMITTED")
            return True

        return True

    def go_back(self):
        """Pops state from history stack and removes the user/assistant message pair."""
        if self.state_history:
            self.session.current_state = self.state_history.pop()
            # Clean history: remove last user message and last assistant prompt
            # Usually message logs end with assistant prompt, preceded by user reply
            if len(self.messages) >= 2:
                # Remove assistant reply
                self.messages.pop()
                # Remove user reply
                self.messages.pop()
            return True
        return False
