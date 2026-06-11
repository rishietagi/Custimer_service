import uuid
from datetime import datetime, date
import streamlit as st
from core.db import lookup_order, create_appointment, create_support_case, get_user_products
from core.state_manager import transition_to, update_chat_data, set_error, clear_error
from core.validators import (
    validate_model_number, validate_pincode, validate_phone, 
    validate_future_date, validate_email, validate_serial_number
)

# Define State Definitions and metadata
STATES = {
    "SELECT_LANGUAGE": {
        "label": "Language Selection",
        "progress": 2
    },
    "HOME_MENU": {
        "label": "Home Menu",
        "progress": 5
    },
    # Path A: Product Help Flow
    "PRODUCT_CATEGORY": {
        "label": "Product Category",
        "progress": 15
    },
    "PRODUCT_MODEL": {
        "label": "Product Model",
        "progress": 25
    },
    "PRODUCT_PURCHASE_DATE": {
        "label": "Purchase Date",
        "progress": 35
    },
    "PRODUCT_WARRANTY": {
        "label": "Warranty Status",
        "progress": 45
    },
    "PRODUCT_SERIAL": {
        "label": "Serial Number",
        "progress": 55
    },
    "PRODUCT_INSTALL_DATE": {
        "label": "Installation Date",
        "progress": 65
    },
    "ISSUE_COLLECTION": {
        "label": "Issue Details",
        "progress": 75
    },
    "ISSUE_EXPLANATION": {
        "label": "Issue Explanation",
        "progress": 80
    },
    "CONFIRM_DETAILS_BEFORE_BOOKING": {
        "label": "Review Details",
        "progress": 85
    },
    "SERVICE_ADDRESS": {
        "label": "Service Address",
        "progress": 90
    },
    "SERVICE_SCHEDULE": {
        "label": "Appointment Date & Time",
        "progress": 95
    },
    "BOOKING_CONFIRMATION": {
        "label": "Booking Confirmed",
        "progress": 100
    },
    # Path B: Order Status Flow
    "ORDER_LOOKUP": {
        "label": "Order Lookup",
        "progress": 30
    },
    "ORDER_STATUS_DISPLAY": {
        "label": "Order Status Timeline",
        "progress": 70
    },
    "ORDER_COMPLAINT_FORM": {
        "label": "Submit Complaint",
        "progress": 90
    },
    "ORDER_CALLBACK_CONFIRM": {
        "label": "Callback Requested",
        "progress": 100
    },
    "ORDER_ESCALATE_CONFIRM": {
        "label": "Escalated to Support",
        "progress": 100
    },
    # Path C: Other Help Flow
    "OTHER_HELP_MENU": {
        "label": "Other Services",
        "progress": 25
    },
    "OTHER_WARRANTY_INFO": {
        "label": "Warranty & AMC Information",
        "progress": 60
    },
    "OTHER_PROD_REGISTRATION": {
        "label": "Product Registration",
        "progress": 60
    },
    "OTHER_INSTALL_REQUEST": {
        "label": "Request Installation",
        "progress": 60
    },
    "OTHER_BILL_HELP": {
        "label": "Billing & Invoices Help",
        "progress": 60
    },
    "OTHER_CANCEL_RETURN": {
        "label": "Cancellation / Return Request",
        "progress": 60
    },
    "OTHER_FEEDBACK": {
        "label": "Submit Feedback",
        "progress": 60
    },
    "OTHER_COMPLAINT": {
        "label": "Escalate Complaint",
        "progress": 60
    },
    "OTHER_FAQ": {
        "label": "Frequently Asked Questions",
        "progress": 60
    },
    "TICKET_SUBMITTED": {
        "label": "Request Submitted",
        "progress": 100
    }
}

# Category options
CATEGORIES = ["Refrigerator", "Washing Machine", "Microwave", "Dishwasher", "AC", "TV", "Others"]

# Issue options based on category
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
            return "कृपया अपने सेवा बुकिंग का विवरण प्रदान करें ताकि हम एक स्थानीय तकनीशियन नियुक्त कर सकें:"
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
        return "### Warranty & Annual Maintenance Contract (AMC) Information\n\nAll SmartCare home appliances come with a standard 1-year manufacturer warranty. You can purchase AMC extensions to cover parts and labor. Please complete the form below to request a customized AMC plan quotation:"
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
        return "### Frequently Asked Questions (FAQ)\n\nClick on any of the questions below to read the help article. If you still need help, feel free to return to the home menu or raise a ticket."
    elif state == "TICKET_SUBMITTED":
        if is_hindi:
            return f"### ✅ अनुरोध सफलतापूर्वक प्रस्तुत किया गया!\n\nआपकी टिकट संदर्भ आईडी **{chat_data.get('ticket_id', 'N/A')}** है।\nहमारी टीम आपके अनुरोध की समीक्षा करेगी और जल्द ही आपसे संपर्क करेगी।\n\nक्या आज मैं आपकी और कोई सहायता कर सकता हूँ?"
        return f"### ✅ Request Submitted Successfully!\n\nYour ticket reference ID is **{chat_data.get('ticket_id', 'N/A')}**.\nOur team will review your request and get back to you shortly.\n\nIs there anything else I can help you with today?"
    
    return "How else may I assist you?"

def process_state_transition(state: str, input_value: any, user_id: str, customer_name: str) -> bool:
    """
    Validates input for the current state and handles the state transitions.
    Returns True if transition succeeded, False if validation failed.
    """
    clear_error()
    
    if state == "SELECT_LANGUAGE":
        if input_value in ["English", "Hindi"]:
            update_chat_data("language", input_value)
            transition_to("HOME_MENU")
            return True
        else:
            set_error("Please select a valid language: English or Hindi.")
            return False

    elif state == "HOME_MENU":
        if input_value == "A":
            transition_to("PRODUCT_CATEGORY")
        elif input_value == "B":
            transition_to("ORDER_LOOKUP")
        elif input_value == "C":
            transition_to("OTHER_HELP_MENU")
        return True

    # Path A: Product Help Flow
    elif state == "PRODUCT_CATEGORY":
        if input_value not in CATEGORIES:
            set_error("Please select a valid product category.")
            return False
        update_chat_data("category", input_value)
        
        # See if user already has registered products of this category to prefill/suggest
        # We'll just transition to model entry
        transition_to("PRODUCT_MODEL")
        return True

    elif state == "PRODUCT_MODEL":
        ok, err = validate_model_number(input_value)
        if not ok:
            set_error(err)
            return False
        update_chat_data("model_number", input_value.strip())
        transition_to("PRODUCT_PURCHASE_DATE")
        return True

    elif state == "PRODUCT_PURCHASE_DATE":
        # Date value should be a date object
        if not input_value:
            set_error("Purchase date cannot be empty.")
            return False
        if isinstance(input_value, date) and input_value > date.today():
            set_error("Purchase date cannot be in the future.")
            return False
        update_chat_data("purchase_date", input_value.isoformat() if isinstance(input_value, date) else str(input_value))
        transition_to("PRODUCT_WARRANTY")
        return True

    elif state == "PRODUCT_WARRANTY":
        if input_value not in ["In Warranty", "Out of Warranty"]:
            set_error("Please select a valid warranty status.")
            return False
        update_chat_data("warranty_status", input_value)
        transition_to("PRODUCT_SERIAL")
        return True

    elif state == "PRODUCT_SERIAL":
        ok, err = validate_serial_number(input_value)
        if not ok:
            set_error(err)
            return False
        update_chat_data("serial_number", input_value.strip().upper())
        transition_to("PRODUCT_INSTALL_DATE")
        return True

    elif state == "PRODUCT_INSTALL_DATE":
        # Installation date is optional, but if entered, must be valid
        if input_value:
            if isinstance(input_value, date):
                # Installation date cannot be in the future
                if input_value > date.today():
                    set_error("Installation date cannot be in the future.")
                    return False
                # Installation date cannot be before purchase date
                p_date_str = st.session_state.chat_data.get("purchase_date")
                if p_date_str:
                    p_date = date.fromisoformat(p_date_str)
                    if input_value < p_date:
                        set_error("Installation date cannot be before the purchase date.")
                        return False
                update_chat_data("installation_date", input_value.isoformat())
            else:
                update_chat_data("installation_date", str(input_value))
        else:
            update_chat_data("installation_date", None)
            
        transition_to("ISSUE_COLLECTION")
        return True

    elif state == "ISSUE_COLLECTION":
        issue_opt = ""
        if isinstance(input_value, dict):
            issue_opt = input_value.get("issue_option", "").strip()
        else:
            issue_opt = str(input_value).strip()
            
        if not issue_opt:
            set_error("Please select your product issue option.")
            return False
            
        update_chat_data("issue_option", issue_opt)
        transition_to("ISSUE_EXPLANATION")
        return True

    elif state == "ISSUE_EXPLANATION":
        issue_desc = str(input_value).strip()
        if not issue_desc:
            is_hindi = st.session_state.chat_data.get("language") == "Hindi"
            err_msg = "कृपया अपनी समस्या का विस्तार से वर्णन करें।" if is_hindi else "Please describe the symptoms in detail."
            set_error(err_msg)
            return False
            
        update_chat_data("issue_description", f"{st.session_state.chat_data.get('issue_option')} - {issue_desc}")
        transition_to("CONFIRM_DETAILS_BEFORE_BOOKING")
        return True

    elif state == "CONFIRM_DETAILS_BEFORE_BOOKING":
        if input_value == "Yes":
            # Pre-fill user details into address form
            # Let's check if the user profile already has address/city/pincode
            # We can use get_user_by_id or just read from session state
            update_chat_data("service_address", st.session_state.get("address", ""))
            update_chat_data("service_city", st.session_state.get("city", ""))
            update_chat_data("service_pincode", st.session_state.get("pincode", ""))
            update_chat_data("service_phone", st.session_state.get("phone", ""))
            transition_to("SERVICE_ADDRESS")
        else:
            # Go back to main menu
            transition_to("HOME_MENU")
        return True

    elif state == "SERVICE_ADDRESS":
        addr = input_value.get("address", "").strip()
        city = input_value.get("city", "").strip()
        pin = input_value.get("pincode", "").strip()
        phone = input_value.get("phone", "").strip()
        notes = input_value.get("notes", "").strip()
        
        if not addr:
            set_error("Address cannot be empty.")
            return False
        if not city:
            set_error("City cannot be empty.")
            return False
            
        ok_pin, err_pin = validate_pincode(pin)
        if not ok_pin:
            set_error(err_pin)
            return False
            
        ok_phone, err_phone = validate_phone(phone)
        if not ok_phone:
            set_error(err_phone)
            return False
            
        update_chat_data("service_address", addr)
        update_chat_data("service_city", city)
        update_chat_data("service_pincode", pin)
        update_chat_data("service_phone", phone)
        update_chat_data("service_notes", notes)
        
        transition_to("SERVICE_SCHEDULE")
        return True

    elif state == "SERVICE_SCHEDULE":
        pref_date = input_value.get("preferred_date")
        pref_slot = input_value.get("preferred_time_slot", "").strip()
        
        ok_date, err_date = validate_future_date(pref_date)
        if not ok_date:
            set_error(err_date)
            return False
            
        if pref_slot not in TIME_SLOTS:
            set_error("Please select a valid service time slot.")
            return False
            
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
        category = st.session_state.chat_data.get("category", "Others")
        assigned_tech = technicians.get(category, "Certified Tech")
        
        update_chat_data("appointment_id", apt_id)
        update_chat_data("preferred_date", pref_date.isoformat())
        update_chat_data("preferred_time_slot", pref_slot)
        update_chat_data("technician_name", assigned_tech)
        
        # Save to database
        create_appointment(
            appointment_id=apt_id,
            user_id=user_id,
            customer_name=customer_name,
            product_category=category,
            product_model=st.session_state.chat_data.get("model_number"),
            serial_number=st.session_state.chat_data.get("serial_number"),
            purchase_date=st.session_state.chat_data.get("purchase_date"),
            warranty_status=st.session_state.chat_data.get("warranty_status"),
            issue_description=st.session_state.chat_data.get("issue_description"),
            address=st.session_state.chat_data.get("service_address"),
            city=st.session_state.chat_data.get("service_city"),
            pincode=st.session_state.chat_data.get("service_pincode"),
            preferred_date=pref_date.isoformat(),
            preferred_time_slot=pref_slot,
            status="Scheduled",
            technician_name=assigned_tech
        )
        
        transition_to("BOOKING_CONFIRMATION")
        return True

    # Path B: Order Status Flow
    elif state == "ORDER_LOOKUP":
        ord_id = input_value.get("order_id", "").strip()
        contact = input_value.get("contact_info", "").strip()
        
        if not ord_id:
            set_error("Order ID cannot be empty.")
            return False
        if not contact:
            set_error("Phone or Email registered with order is required.")
            return False
            
        # Lookup order
        order = lookup_order(ord_id, contact)
        if not order:
            set_error("No order found matching this Order ID and contact details. Please check the information and try again.")
            return False
            
        update_chat_data("order_id", order["order_id"])
        update_chat_data("product_name", order["product_name"])
        update_chat_data("order_status", order["status"])
        transition_to("ORDER_STATUS_DISPLAY")
        return True

    elif state == "ORDER_STATUS_DISPLAY":
        if input_value == "Escalate to support":
            ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
            update_chat_data("ticket_id", ticket_id)
            create_support_case(
                case_id=ticket_id,
                user_id=user_id,
                title=f"Order Escalation: {st.session_state.chat_data.get('order_id')}",
                description=f"User escalated order status inquiry for order {st.session_state.chat_data.get('order_id')} ({st.session_state.chat_data.get('product_name')}). Current status: {st.session_state.chat_data.get('order_status')}.",
                category="Complaint escalation"
            )
            transition_to("ORDER_ESCALATE_CONFIRM")
        elif input_value == "Request callback":
            transition_to("ORDER_CALLBACK_CONFIRM")
        elif input_value == "Raise a complaint":
            transition_to("ORDER_COMPLAINT_FORM")
        elif input_value == "Schedule installation":
            # Transition to product category flow with category pre-filled
            update_chat_data("category", "Others")
            # We can start booking flow
            update_chat_data("issue_description", "Installation Request for newly ordered product.")
            transition_to("PRODUCT_CATEGORY")
        return True

    elif state == "ORDER_COMPLAINT_FORM":
        subj = input_value.get("subject", "").strip()
        desc = input_value.get("description", "").strip()
        
        if not subj:
            set_error("Complaint subject is required.")
            return False
        if not desc:
            set_error("Please provide description of the complaint.")
            return False
            
        ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        
        create_support_case(
            case_id=ticket_id,
            user_id=user_id,
            title=f"Order Complaint: {subj}",
            description=f"Order ID: {st.session_state.chat_data.get('order_id')}\nDescription: {desc}",
            category="Complaint escalation"
        )
        transition_to("TICKET_SUBMITTED")
        return True

    # Path C: Other Help Flow
    elif state == "OTHER_HELP_MENU":
        valid_options = [
            "Warranty / AMC", "Product registration", "Installation request",
            "Bill / invoice help", "Cancellation / return", "Feedback",
            "Complaint escalation", "General FAQ"
        ]
        if input_value not in valid_options:
            set_error("Please select a valid option.")
            return False
            
        if input_value == "Warranty / AMC":
            transition_to("OTHER_WARRANTY_INFO")
        elif input_value == "Product registration":
            transition_to("OTHER_PROD_REGISTRATION")
        elif input_value == "Installation request":
            transition_to("OTHER_INSTALL_REQUEST")
        elif input_value == "Bill / invoice help":
            transition_to("OTHER_BILL_HELP")
        elif input_value == "Cancellation / return":
            transition_to("OTHER_CANCEL_RETURN")
        elif input_value == "Feedback":
            transition_to("OTHER_FEEDBACK")
        elif input_value == "Complaint escalation":
            transition_to("OTHER_COMPLAINT")
        elif input_value == "General FAQ":
            transition_to("OTHER_FAQ")
        return True

    elif state == "OTHER_WARRANTY_INFO":
        # Form submission for AMC query
        comments = input_value.get("comments", "").strip()
        cat = input_value.get("category", "").strip()
        
        if not cat:
            set_error("Please select a product category.")
            return False
            
        ticket_id = "CAS-WNT-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        
        create_support_case(
            case_id=ticket_id,
            user_id=user_id,
            title=f"AMC Quote Inquiry: {cat}",
            description=f"AMC Quotation Request for {cat}. Additional Notes: {comments}",
            category="Warranty / AMC"
        )
        transition_to("TICKET_SUBMITTED")
        return True

    elif state == "OTHER_PROD_REGISTRATION":
        # Register a new appliance
        cat = input_value.get("category", "").strip()
        model = input_value.get("model_number", "").strip()
        serial = input_value.get("serial_number", "").strip()
        p_date = input_value.get("purchase_date")
        
        if not cat:
            set_error("Please select a category.")
            return False
            
        ok_model, err_model = validate_model_number(model)
        if not ok_model:
            set_error(err_model)
            return False
            
        ok_serial, err_serial = validate_serial_number(serial)
        if not ok_serial:
            set_error(err_serial)
            return False
            
        if not p_date:
            set_error("Please select a purchase date.")
            return False
            
        if isinstance(p_date, date) and p_date > date.today():
            set_error("Purchase date cannot be in the future.")
            return False
            
        # We can add product directly to user profile
        import core.db as db
        prod_id = "prod_" + str(uuid.uuid4())[:8]
        db.add_product(
            product_id=prod_id,
            user_id=user_id,
            category=cat,
            model_number=model,
            serial_number=serial,
            purchase_date=p_date.isoformat(),
            warranty_status="In Warranty"  # default
        )
        
        ticket_id = "REG-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        transition_to("TICKET_SUBMITTED")
        return True

    elif state == "OTHER_INSTALL_REQUEST":
        cat = input_value.get("category", "").strip()
        model = input_value.get("model_number", "").strip()
        serial = input_value.get("serial_number", "").strip()
        addr = input_value.get("address", "").strip()
        pin = input_value.get("pincode", "").strip()
        pref_date = input_value.get("preferred_date")
        
        if not cat:
            set_error("Product category is required.")
            return False
        if not model:
            set_error("Model number is required.")
            return False
        if not addr:
            set_error("Service address is required.")
            return False
            
        ok_pin, err_pin = validate_pincode(pin)
        if not ok_pin:
            set_error(err_pin)
            return False
            
        ok_date, err_date = validate_future_date(pref_date)
        if not ok_date:
            set_error(err_date)
            return False
            
        # Book a special installation appointment
        apt_id = "APT-INS-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("appointment_id", apt_id)
        
        # Save to database as a Scheduled installation appointment
        create_appointment(
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
            city=st.session_state.get("city", "City"),
            pincode=pin,
            preferred_date=pref_date.isoformat(),
            preferred_time_slot="12:00 PM - 03:00 PM",
            status="Scheduled",
            technician_name="Installation Team"
        )
        
        ticket_id = "APT-" + apt_id.split("-")[-1]
        update_chat_data("ticket_id", ticket_id)
        transition_to("TICKET_SUBMITTED")
        return True

    elif state == "OTHER_BILL_HELP":
        ord_id = input_value.get("order_id", "").strip()
        subject = input_value.get("subject", "").strip()
        msg = input_value.get("message", "").strip()
        
        if not subject:
            set_error("Please enter a subject.")
            return False
        if not msg:
            set_error("Please describe your billing issue.")
            return False
            
        ticket_id = "CAS-BIL-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        
        create_support_case(
            case_id=ticket_id,
            user_id=user_id,
            title=f"Billing: {subject}",
            description=f"Order Ref: {ord_id}\nQuery: {msg}",
            category="Bill / invoice help"
        )
        transition_to("TICKET_SUBMITTED")
        return True

    elif state == "OTHER_CANCEL_RETURN":
        ord_id = input_value.get("order_id", "").strip()
        req_type = input_value.get("request_type", "Cancellation")
        reason = input_value.get("reason", "").strip()
        
        if not ord_id:
            set_error("Order ID is required.")
            return False
        if not reason:
            set_error("Please provide a reason.")
            return False
            
        ticket_id = "CAS-RTR-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        
        create_support_case(
            case_id=ticket_id,
            user_id=user_id,
            title=f"{req_type} Request: {ord_id}",
            description=f"Request Type: {req_type}\nOrder: {ord_id}\nReason: {reason}",
            category="Cancellation / return"
        )
        transition_to("TICKET_SUBMITTED")
        return True

    elif state == "OTHER_FEEDBACK":
        rating = input_value.get("rating", "5 Star")
        comments = input_value.get("comments", "").strip()
        
        ticket_id = "FBK-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        
        create_support_case(
            case_id=ticket_id,
            user_id=user_id,
            title=f"Feedback Submission (Rating: {rating})",
            description=f"Rating: {rating}\nComments: {comments}",
            category="Feedback"
        )
        transition_to("TICKET_SUBMITTED")
        return True

    elif state == "OTHER_COMPLAINT":
        title = input_value.get("title", "").strip()
        desc = input_value.get("description", "").strip()
        
        if not title:
            set_error("Complaint title is required.")
            return False
        if not desc:
            set_error("Please describe your complaint.")
            return False
            
        ticket_id = "CAS-ESC-" + str(uuid.uuid4())[:6].upper()
        update_chat_data("ticket_id", ticket_id)
        
        create_support_case(
            case_id=ticket_id,
            user_id=user_id,
            title=f"Escalation: {title}",
            description=desc,
            category="Complaint escalation"
        )
        transition_to("TICKET_SUBMITTED")
        return True

    return True
