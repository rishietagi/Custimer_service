import streamlit as st
from datetime import date, datetime
import core.flow_engine as flow
from core.state_manager import (
    transition_to, go_back, reset_chat_flow, add_chat_message, 
    update_chat_data, set_error, clear_error
)

def render_chatbot():
    """Renders the main customer care chatbot assistant."""
    st.markdown("<div class='brand-header'><h1>💬 SmartCare Assistant</h1></div>", unsafe_allow_html=True)

    # Check if language is Hindi
    is_hindi = st.session_state.chat_data.get("language") == "Hindi"

    # 1. Initialize chatbot history if empty
    if not st.session_state.chat_history:
        first_prompt = flow.get_state_prompt("SELECT_LANGUAGE", {})
        add_chat_message("assistant", first_prompt)

    # 2. Sidebar control inside the main panel: Flow Controls
    col_step, col_btn = st.columns([3, 2])
    
    current_state = st.session_state.chat_state
    state_meta = flow.STATES.get(current_state, {"label": "Chatting", "progress": 50})
    
    with col_step:
        st.markdown(f"**Current Step:** {state_meta['label']}")
        st.progress(state_meta["progress"] / 100.0)
        
    with col_btn:
        # Show Go Back and Restart buttons
        c1, c2 = st.columns(2)
        with c1:
            btn_lbl = "⬅️ वापस जाएँ" if is_hindi else "⬅️ Go Back"
            if st.button(btn_lbl, use_container_width=True, disabled=not st.session_state.state_history):
                if go_back():
                    # Re-seed last bot prompt if history gets back
                    st.rerun()
        with c2:
            btn_lbl = "🔄 रीस्टार्ट" if is_hindi else "🔄 Restart"
            if st.button(btn_lbl, use_container_width=True, type="secondary"):
                reset_chat_flow()
                st.rerun()

    # 3. Render Chat History Bubbles
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    # We display chat history inside a container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            role_class = "bot" if msg["role"] == "assistant" else "user"
            
            # Format markdown paragraphs inside bubbles nicely
            msg_content = msg["content"].replace("\n", "<br>")
            
            st.markdown(
                f"<div class='chat-bubble-container'><div class='chat-bubble {role_class}'>{msg_content}</div></div>", 
                unsafe_allow_html=True
            )

    st.markdown("<div style='clear: both; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # 4. Display active error message if any
    if st.session_state.current_error:
        st.error(f"⚠️ {st.session_state.current_error}")

    # 5. Render input field based on active state
    reply_header = "सहायक को उत्तर दें" if is_hindi else "Reply to Assistant"
    st.markdown(f"### {reply_header}")
    
    # We will use st.form or clean widgets to collect the reply
    with st.container():
        # Render different forms depending on FSM state
        
        # --- SELECT LANGUAGE ---
        if current_state == "SELECT_LANGUAGE":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🇬🇧 English", use_container_width=True, type="primary"):
                    handle_input("English", "English")
            with c2:
                if st.button("🇮🇳 हिंदी (Hindi)", use_container_width=True, type="primary"):
                    handle_input("Hindi", "Hindi")

        # --- HOME MENU ---
        elif current_state == "HOME_MENU":
            c1, c2, c3 = st.columns(3)
            with c1:
                btn_lbl = "🔧 उत्पाद सहायता / मरम्मत" if is_hindi else "🔧 Product Help / Repair"
                usr_str = "मुझे किसी उत्पाद में सहायता चाहिए / मरम्मत का अनुरोध करना है।" if is_hindi else "I need help with a product / request a repair."
                if st.button(btn_lbl, use_container_width=True, type="primary"):
                    handle_input("A", usr_str)
            with c2:
                btn_lbl = "📦 वर्तमान ऑर्डर ट्रैक करें" if is_hindi else "📦 Track Current Order"
                usr_str = "मैं अपने वर्तमान ऑर्डर की स्थिति जानना चाहता हूँ।" if is_hindi else "I want a status update on my current order."
                if st.button(btn_lbl, use_container_width=True):
                    handle_input("B", usr_str)
            with c3:
                btn_lbl = "❓ कुछ और" if is_hindi else "❓ Something Else"
                usr_str = "मुझे किसी अन्य सेवा में सहायता चाहिए।" if is_hindi else "I need help with another service."
                if st.button(btn_lbl, use_container_width=True):
                    handle_input("C", usr_str)

        # --- PRODUCT CATEGORY ---
        elif current_state == "PRODUCT_CATEGORY":
            cols = st.columns(4)
            cat_trans = {
                "Refrigerator": "रेफ्रिजरेटर",
                "Washing Machine": "वाशिंग मशीन",
                "Microwave": "माइक्रोवेव",
                "Dishwasher": "डिशवॉशर",
                "AC": "एसी",
                "TV": "टीवी",
                "Others": "अन्य"
            }
            for idx, cat in enumerate(flow.CATEGORIES):
                col_idx = idx % 4
                with cols[col_idx]:
                    btn_lbl = cat_trans.get(cat, cat) if is_hindi else cat
                    usr_str = f"उत्पाद श्रेणी: {cat_trans.get(cat, cat)}" if is_hindi else f"Product Category: {cat}"
                    if st.button(btn_lbl, use_container_width=True):
                        handle_input(cat, usr_str)

        # --- PRODUCT MODEL ---
        elif current_state == "PRODUCT_MODEL":
            # Show registered products if any, as shortcuts
            registered_prods = st.session_state.get("registered_products", [])
            selected_cat = st.session_state.chat_data.get("category")
            matching_prods = [p for p in registered_prods if p["category"] == selected_cat]

            if matching_prods:
                lbl = "या अपने पंजीकृत उपकरणों में से एक चुनें:" if is_hindi else "Or select one of your registered appliances:"
                st.caption(lbl)
                cols = st.columns(len(matching_prods))
                for idx, p in enumerate(matching_prods):
                    with cols[idx]:
                        btn_label = f"{p['model_number']} (S/N: {p['serial_number']})"
                        if st.button(btn_label, use_container_width=True):
                            # Prepopulate data and jump multiple states or just autofill
                            update_chat_data("model_number", p["model_number"])
                            update_chat_data("serial_number", p["serial_number"])
                            update_chat_data("purchase_date", p["purchase_date"])
                            update_chat_data("warranty_status", p["warranty_status"])
                            update_chat_data("installation_date", p["installation_date"])
                            
                            usr_str = f"पंजीकृत उत्पाद चुनें: {p['model_number']}" if is_hindi else f"Select Registered Product: {p['model_number']}"
                            add_chat_message("user", usr_str)
                            transition_to("ISSUE_COLLECTION")
                            add_chat_message("assistant", flow.get_state_prompt("ISSUE_COLLECTION", st.session_state.chat_data))
                            st.rerun()

            with st.form("model_form", clear_on_submit=True):
                lbl = "मॉडल नंबर दर्ज करें" if is_hindi else "Enter Model Number"
                ph = "जैसे LFXS26973S" if is_hindi else "e.g. LFXS26973S"
                btn_lbl = "जारी रखें" if is_hindi else "Continue"
                model_num = st.text_input(lbl, placeholder=ph).strip()
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    usr_str = f"मॉडल नंबर: {model_num}" if is_hindi else f"Model Number: {model_num}"
                    handle_input(model_num, usr_str)

        # --- PRODUCT PURCHASE DATE ---
        elif current_state == "PRODUCT_PURCHASE_DATE":
            with st.form("purchase_date_form", clear_on_submit=True):
                lbl = "खरीद की तारीख" if is_hindi else "Purchase Date"
                btn_lbl = "जारी रखें" if is_hindi else "Continue"
                pur_date = st.date_input(lbl, max_value=date.today())
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    usr_str = f"खरीद की तारीख: {pur_date}" if is_hindi else f"Purchase Date: {pur_date}"
                    handle_input(pur_date, usr_str)

        # --- PRODUCT WARRANTY ---
        elif current_state == "PRODUCT_WARRANTY":
            c1, c2 = st.columns(2)
            with c1:
                btn_lbl = "🛡️ वारंटी में" if is_hindi else "🛡️ In Warranty"
                usr_str = "स्थिति: वारंटी में" if is_hindi else "Status: In Warranty"
                if st.button(btn_lbl, use_container_width=True):
                    handle_input("In Warranty", usr_str)
            with c2:
                btn_lbl = "❌ वारंटी से बाहर" if is_hindi else "❌ Out of Warranty"
                usr_str = "स्थिति: वारंटी से बाहर" if is_hindi else "Status: Out of Warranty"
                if st.button(btn_lbl, use_container_width=True):
                    handle_input("Out of Warranty", usr_str)

        # --- PRODUCT SERIAL ---
        elif current_state == "PRODUCT_SERIAL":
            with st.form("serial_form", clear_on_submit=True):
                lbl = "सीरियल नंबर दर्ज करें" if is_hindi else "Enter Serial Number"
                ph = "जैसे REF123456789" if is_hindi else "e.g. REF123456789"
                btn_lbl = "जारी रखें" if is_hindi else "Continue"
                serial_num = st.text_input(lbl, placeholder=ph).strip()
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    usr_str = f"सीरियल नंबर: {serial_num}" if is_hindi else f"Serial Number: {serial_num}"
                    handle_input(serial_num, usr_str)

        # --- PRODUCT INSTALL DATE ---
        elif current_state == "PRODUCT_INSTALL_DATE":
            with st.form("install_date_form", clear_on_submit=True):
                info_lbl = "यदि स्थापना तिथि खरीद की तिथि के समान थी, तो आप इसे खाली छोड़ सकते हैं।" if is_hindi else "If installation date was the same as purchase date, you can leave this empty."
                st.write(info_lbl)
                chk_lbl = "अलग स्थापना तिथि दर्ज करें" if is_hindi else "Enter different installation date"
                has_install_date = st.checkbox(chk_lbl, value=False)
                
                date_lbl = "स्थापना तिथि" if is_hindi else "Installation Date"
                install_date = st.date_input(date_lbl, max_value=date.today()) if has_install_date else None
                
                btn_lbl = "जारी रखें" if is_hindi else "Continue"
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = install_date if has_install_date else None
                    if is_hindi:
                        val_str = f"स्थापना तिथि: {val}" if has_install_date else "स्थापना तिथि छोड़ें"
                    else:
                        val_str = f"Installation Date: {val}" if has_install_date else "Skip Installation Date"
                    handle_input(val, val_str)

        # --- ISSUE COLLECTION ---
        elif current_state == "ISSUE_COLLECTION":
            cat = st.session_state.chat_data.get("category", "Others")
            issue_opts = flow.CATEGORY_ISSUES.get(cat, ["Other"])
            
            with st.form("issue_form", clear_on_submit=True):
                lbl = "समान लक्षण चुनें" if is_hindi else "Select the issue option"
                issue_opt = st.selectbox(lbl, issue_opts)
                
                btn_lbl = "जारी रखें" if is_hindi else "Continue"
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    usr_str = f"चयनित समस्या: {issue_opt}" if is_hindi else f"Selected Issue: {issue_opt}"
                    handle_input(issue_opt, usr_str)

        # --- ISSUE EXPLANATION ---
        elif current_state == "ISSUE_EXPLANATION":
            issue_opt = st.session_state.chat_data.get("issue_option", "Issue")
            
            with st.form("issue_explanation_form", clear_on_submit=True):
                lbl = f"कृपया '{issue_opt}' समस्या का विस्तार से वर्णन करें" if is_hindi else f"Please describe the details of '{issue_opt}' issue"
                ph = "लक्षण, त्रुटि कोड आदि का वर्णन करें।" if is_hindi else "Describe symptoms, error codes, etc."
                btn_lbl = "विवरण सबमिट करें" if is_hindi else "Submit details"
                issue_desc = st.text_area(lbl, placeholder=ph)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    usr_str = f"विवरण: {issue_desc}" if is_hindi else f"Explanation: {issue_desc}"
                    handle_input(issue_desc, usr_str)

        # --- CONFIRM DETAILS BEFORE BOOKING ---
        elif current_state == "CONFIRM_DETAILS_BEFORE_BOOKING":
            c1, c2 = st.columns(2)
            with c1:
                btn_lbl = "📅 हाँ, सेवा नियुक्ति बुक करें" if is_hindi else "📅 Yes, Book Service Appointment"
                usr_str = "हाँ, बुकिंग के साथ आगे बढ़ें।" if is_hindi else "Yes, proceed with booking."
                if st.button(btn_lbl, use_container_width=True, type="primary"):
                    handle_input("Yes", usr_str)
            with c2:
                btn_lbl = "❌ नहीं, मुख्य मेनू पर वापस जाएँ" if is_hindi else "❌ No, Back to Main Menu"
                usr_str = "नहीं, बुकिंग रद्द करें।" if is_hindi else "No, cancel booking."
                if st.button(btn_lbl, use_container_width=True):
                    handle_input("No", usr_str)

        # --- SERVICE ADDRESS ---
        elif current_state == "SERVICE_ADDRESS":
            with st.form("service_address_form", clear_on_submit=True):
                addr_lbl = "पूरा पता" if is_hindi else "Full Address"
                city_lbl = "शहर" if is_hindi else "City"
                pin_lbl = "पिनकोड" if is_hindi else "Pincode"
                phone_lbl = "संपर्क फोन नंबर" if is_hindi else "Contact Phone Number"
                notes_lbl = "तकनीशियन के लिए अतिरिक्त निर्देश (वैकल्पिक)" if is_hindi else "Additional Notes for Technician (Optional)"
                notes_ph = "जैसे: गेट कोड, घंटी बजाएं, पार्किंग निर्देश" if is_hindi else "e.g. gate code, ring bell, parking instructions"
                btn_lbl = "शेड्यूलिंग पर आगे बढ़ें" if is_hindi else "Proceed to Scheduling"
                
                addr = st.text_input(addr_lbl, value=st.session_state.chat_data.get("service_address", ""))
                city = st.text_input(city_lbl, value=st.session_state.chat_data.get("service_city", ""))
                pincode = st.text_input(pin_lbl, value=st.session_state.chat_data.get("service_pincode", ""))
                phone = st.text_input(phone_lbl, value=st.session_state.chat_data.get("service_phone", ""))
                notes = st.text_area(notes_lbl, placeholder=notes_ph)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"address": addr, "city": city, "pincode": pincode, "phone": phone, "notes": notes}
                    user_str = f"पता: {addr}, {city} - {pincode} (फोन: {phone})" if is_hindi else f"Address: {addr}, {city} - {pincode} (Phone: {phone})"
                    handle_input(val, user_str)

        # --- SERVICE SCHEDULE ---
        elif current_state == "SERVICE_SCHEDULE":
            with st.form("service_schedule_form", clear_on_submit=True):
                date_lbl = "पसंदीदा सेवा तिथि" if is_hindi else "Preferred Service Date"
                slot_lbl = "पसंदीदा समय स्लॉट" if is_hindi else "Preferred Time Slot"
                btn_lbl = "सेवा नियुक्ति की पुष्टि करें" if is_hindi else "Confirm Service Appointment"
                
                pref_date = st.date_input(date_lbl, min_value=date.today())
                
                SLOT_TRANS = {
                    "09:00 AM - 12:00 PM (Morning)": "सुबह 09:00 - दोपहर 12:00 (Morning)",
                    "12:00 PM - 03:00 PM (Afternoon)": "दोपहर 12:00 - दोपहर 03:00 (Afternoon)",
                    "03:00 PM - 06:00 PM (Evening)": "दोपहर 03:00 - शाम 06:00 (Evening)"
                }
                pref_slot = st.selectbox(
                    slot_lbl, 
                    flow.TIME_SLOTS,
                    format_func=lambda x: SLOT_TRANS.get(x, x) if is_hindi else x
                )
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"preferred_date": pref_date, "preferred_time_slot": pref_slot}
                    user_str = f"तिथि: {pref_date} | स्लॉट: {SLOT_TRANS.get(pref_slot, pref_slot) if is_hindi else pref_slot}"
                    handle_input(val, user_str)

        # --- BOOKING CONFIRMATION ---
        elif current_state == "BOOKING_CONFIRMATION":
            btn_lbl = "🏠 मुख्य मेनू पर वापस जाएँ" if is_hindi else "🏠 Back to Home Menu"
            if st.button(btn_lbl, use_container_width=True, type="primary"):
                reset_chat_flow()
                st.rerun()

        # --- ORDER LOOKUP ---
        elif current_state == "ORDER_LOOKUP":
            with st.form("order_lookup_form", clear_on_submit=True):
                ord_lbl = "ऑर्डर आईडी" if is_hindi else "Order ID"
                contact_lbl = "पंजीकृत फोन या ईमेल" if is_hindi else "Registered Phone or Email"
                contact_ph = "जैसे: john.doe@support-example.com" if is_hindi else "e.g. john.doe@support-example.com"
                btn_lbl = "ऑर्डर खोजें" if is_hindi else "Lookup Order"
                
                ord_id = st.text_input(ord_lbl, placeholder="ORD-XXXX")
                contact = st.text_input(contact_lbl, placeholder=contact_ph)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"order_id": ord_id, "contact_info": contact}
                    user_str = f"ऑर्डर आईडी खोज रहे हैं: {ord_id} | संपर्क: {contact}" if is_hindi else f"Looking up Order ID: {ord_id} | Contact: {contact}"
                    handle_input(val, user_str)

        # --- ORDER STATUS DISPLAY ---
        elif current_state == "ORDER_STATUS_DISPLAY":
            status = st.session_state.chat_data.get("order_status")
            
            # Show a custom HTML Timeline based on the order status
            render_order_timeline(status, is_hindi)
            
            actions_lbl = "##### क्रियाएं:" if is_hindi else "##### Actions:"
            st.write(actions_lbl)
            
            # Action buttons depending on order status
            if status in ["Delayed", "Installation Pending", "Shipped"]:
                c1, c2, c3 = st.columns(3)
                with c1:
                    btn_lbl = "⚠️ शिकायत दर्ज करें" if is_hindi else "⚠️ Raise Complaint"
                    usr_str = "शिकायत दर्ज करें" if is_hindi else "Raise complaint regarding order status."
                    if st.button(btn_lbl, use_container_width=True):
                        handle_input("Raise a complaint", usr_str)
                with c2:
                    btn_lbl = "📞 कॉलबैक का अनुरोध करें" if is_hindi else "📞 Request Callback"
                    usr_str = "कॉलबैक का अनुरोध करें" if is_hindi else "Request call back from representative."
                    if st.button(btn_lbl, use_container_width=True):
                        handle_input("Request callback", usr_str)
                with c3:
                    btn_lbl = "🚀 मुद्दा आगे बढ़ाएं" if is_hindi else "🚀 Escalate Issue"
                    usr_str = "मुद्दा आगे बढ़ाएं" if is_hindi else "Escalate order delay."
                    if st.button(btn_lbl, use_container_width=True, type="primary"):
                        handle_input("Escalate to support", usr_str)
            elif status == "Delivered":
                c1, c2 = st.columns(2)
                with c1:
                    btn_lbl = "🛠️ स्थापना निर्धारित करें" if is_hindi else "🛠️ Schedule Installation"
                    usr_str = "स्थापना निर्धारित करें" if is_hindi else "Schedule installation for delivered product."
                    if st.button(btn_lbl, use_container_width=True, type="primary"):
                        handle_input("Schedule installation", usr_str)
                with c2:
                    btn_lbl = "⚠️ शिकायत दर्ज करें" if is_hindi else "⚠️ Raise Complaint"
                    usr_str = "शिकायत दर्ज करें" if is_hindi else "Raise support issue."
                    if st.button(btn_lbl, use_container_width=True):
                        handle_input("Raise a complaint", usr_str)
            else:
                btn_lbl = "🏠 मुख्य मेनू पर वापस जाएँ" if is_hindi else "🏠 Back to Home Menu"
                if st.button(btn_lbl, use_container_width=True):
                    reset_chat_flow()
                    st.rerun()

        # --- ORDER COMPLAINT FORM ---
        elif current_state == "ORDER_COMPLAINT_FORM":
            with st.form("order_complaint_form", clear_on_submit=True):
                subj_lbl = "शिकायत का विषय" if is_hindi else "Complaint Subject"
                subj_ph = "जैसे: विलंबित वितरण / क्षतिग्रस्त बॉक्स" if is_hindi else "e.g. Delayed Delivery / Damaged Box"
                desc_lbl = "शिकायत का विवरण" if is_hindi else "Complaint Details"
                desc_ph = "समस्या का विस्तार से वर्णन करें।" if is_hindi else "Describe the issue in detail."
                btn_lbl = "शिकायत सबमिट करें" if is_hindi else "Submit Complaint"
                
                subj = st.text_input(subj_lbl, placeholder=subj_ph)
                desc = st.text_area(desc_lbl, placeholder=desc_ph)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"subject": subj, "description": desc}
                    user_str = f"शिकायत दर्ज की गई: {subj}" if is_hindi else f"Submitted Complaint: {subj}"
                    handle_input(val, user_str)

        # --- ORDER CALLBACK / ESCALATION CONFIRM ---
        elif current_state in ["ORDER_CALLBACK_CONFIRM", "ORDER_ESCALATE_CONFIRM", "TICKET_SUBMITTED"]:
            btn_lbl = "🏠 मुख्य मेनू पर वापस जाएँ" if is_hindi else "🏠 Back to Home Menu"
            if st.button(btn_lbl, use_container_width=True, type="primary"):
                reset_chat_flow()
                st.rerun()

        # --- OTHER HELP MENU ---
        elif current_state == "OTHER_HELP_MENU":
            submenu_options = [
                "Warranty / AMC", "Product registration", "Installation request",
                "Bill / invoice help", "Cancellation / return", "Feedback",
                "Complaint escalation", "General FAQ"
            ]
            opt_trans = {
                "Warranty / AMC": "वारंटी / एएमसी (Warranty / AMC)",
                "Product registration": "उत्पाद पंजीकरण (Product registration)",
                "Installation request": "स्थापना अनुरोध (Installation request)",
                "Bill / invoice help": "बिल / चालान सहायता (Bill / invoice help)",
                "Cancellation / return": "रद्द करना / वापसी (Cancellation / return)",
                "Feedback": "फीडबैक (Feedback)",
                "Complaint escalation": "शिकायत वृद्धि (Complaint escalation)",
                "General FAQ": "सामान्य अक्सर पूछे जाने वाले प्रश्न (General FAQ)"
            }
            cols = st.columns(2)
            for idx, opt in enumerate(submenu_options):
                col_idx = idx % 2
                with cols[col_idx]:
                    btn_lbl = opt_trans.get(opt, opt) if is_hindi else opt
                    usr_str = f"विकल्प: {opt_trans.get(opt, opt)}" if is_hindi else f"Option: {opt}"
                    if st.button(btn_lbl, use_container_width=True):
                        handle_input(opt, usr_str)

        # --- OTHER WARRANTY INFO ---
        elif current_state == "OTHER_WARRANTY_INFO":
            with st.form("amc_form", clear_on_submit=True):
                cat_lbl = "उत्पाद श्रेणी" if is_hindi else "Product Category"
                comm_lbl = "अतिरिक्त विवरण / उपकरण की आयु" if is_hindi else "Additional Details / Appliance Age"
                comm_ph = "जैसे: मैं अपने 2 साल पुराने रेफ्रिजरेटर के लिए वारंटी नवीनीकृत करना चाहता हूँ।" if is_hindi else "e.g. I want to renew warranty for my 2 year old Refrigerator."
                btn_lbl = "एएमसी उद्धरण का अनुरोध करें" if is_hindi else "Request AMC Quotation"
                
                cat_trans = {"Refrigerator": "रेफ्रिजरेटर", "Washing Machine": "वाशिंग मशीन", "Microwave": "माइक्रोवेव", "Dishwasher": "डिशवॉशर", "AC": "एसी", "TV": "टीवी", "Others": "अन्य"}
                cat = st.selectbox(
                    cat_lbl, 
                    flow.CATEGORIES,
                    format_func=lambda x: cat_trans.get(x, x) if is_hindi else x
                )
                comments = st.text_area(comm_lbl, placeholder=comm_ph)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"category": cat, "comments": comments}
                    display_cat = cat_trans.get(cat, cat) if is_hindi else cat
                    user_str = f"{display_cat} के लिए एएमसी उद्धरण का अनुरोध किया" if is_hindi else f"Requested AMC quote for {cat}"
                    handle_input(val, user_str)

        # --- OTHER PRODUCT REGISTRATION ---
        elif current_state == "OTHER_PROD_REGISTRATION":
            with st.form("prod_reg_form", clear_on_submit=True):
                cat_lbl = "उत्पाद श्रेणी" if is_hindi else "Product Category"
                model_lbl = "मॉडल नंबर" if is_hindi else "Model Number"
                serial_lbl = "सीरियल नंबर" if is_hindi else "Serial Number"
                date_lbl = "खरीद की तारीख" if is_hindi else "Purchase Date"
                btn_lbl = "उत्पाद पंजीकृत करें" if is_hindi else "Register Product"
                
                cat_trans = {"Refrigerator": "रेफ्रिजरेटर", "Washing Machine": "वाशिंग मशीन", "Microwave": "माइक्रोवेव", "Dishwasher": "डिशवॉशर", "AC": "एसी", "TV": "टीवी", "Others": "अन्य"}
                cat = st.selectbox(
                    cat_lbl, 
                    flow.CATEGORIES,
                    format_func=lambda x: cat_trans.get(x, x) if is_hindi else x
                )
                model = st.text_input(model_lbl)
                serial = st.text_input(serial_lbl)
                p_date = st.date_input(date_lbl, max_value=date.today())
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"category": cat, "model_number": model, "serial_number": serial, "purchase_date": p_date}
                    display_cat = cat_trans.get(cat, cat) if is_hindi else cat
                    user_str = f"पंजीकृत उत्पाद: {display_cat} (मॉडल: {model})" if is_hindi else f"Registered product: {cat} (Model: {model})"
                    handle_input(val, user_str)

        # --- OTHER INSTALLATION REQUEST ---
        elif current_state == "OTHER_INSTALL_REQUEST":
            with st.form("install_req_form", clear_on_submit=True):
                cat_lbl = "उत्पाद श्रेणी" if is_hindi else "Product Category"
                model_lbl = "मॉडल नंबर" if is_hindi else "Model Number"
                serial_lbl = "सीरियल नंबर (वैकल्पिक)" if is_hindi else "Serial Number (Optional)"
                addr_lbl = "स्थापना का पता" if is_hindi else "Installation Address"
                pin_lbl = "पिनकोड" if is_hindi else "Pincode"
                date_lbl = "पसंदीदा तिथि" if is_hindi else "Preferred Date"
                btn_lbl = "स्थापना का अनुरोध करें" if is_hindi else "Request Installation"
                
                cat_trans = {"Refrigerator": "रेफ्रिजरेटर", "Washing Machine": "वाशिंग मशीन", "Microwave": "माइक्रोवेव", "Dishwasher": "डिशवॉशर", "AC": "एसी", "TV": "टीवी", "Others": "अन्य"}
                cat = st.selectbox(
                    cat_lbl, 
                    flow.CATEGORIES,
                    format_func=lambda x: cat_trans.get(x, x) if is_hindi else x
                )
                model = st.text_input(model_lbl)
                serial = st.text_input(serial_lbl)
                addr = st.text_area(addr_lbl)
                pincode = st.text_input(pin_lbl)
                pref_date = st.date_input(date_lbl, min_value=date.today())
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {
                        "category": cat, "model_number": model, "serial_number": serial,
                        "address": addr, "pincode": pincode, "preferred_date": pref_date
                    }
                    display_cat = cat_trans.get(cat, cat) if is_hindi else cat
                    user_str = f"{display_cat} की स्थापना का अनुरोध {pref_date} को किया" if is_hindi else f"Requested installation for {cat} on {pref_date}"
                    handle_input(val, user_str)

        # --- OTHER BILL HELP ---
        elif current_state == "OTHER_BILL_HELP":
            with st.form("bill_help_form", clear_on_submit=True):
                ord_lbl = "ऑर्डर आईडी (वैकल्पिक)" if is_hindi else "Order ID (Optional)"
                subj_lbl = "विषय" if is_hindi else "Subject"
                msg_lbl = "संदेश / विवरण" if is_hindi else "Message / Details"
                btn_lbl = "चालान पूछताछ सबमिट करें" if is_hindi else "Submit Invoice Inquiry"
                
                ord_id = st.text_input(ord_lbl)
                subj = st.text_input(subj_lbl)
                msg = st.text_area(msg_lbl)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"order_id": ord_id, "subject": subj, "message": msg}
                    user_str = f"चालान पूछताछ: {subj}" if is_hindi else f"Invoice inquiry: {subj}"
                    handle_input(val, user_str)

        # --- OTHER CANCEL / RETURN ---
        elif current_state == "OTHER_CANCEL_RETURN":
            with st.form("cancel_return_form", clear_on_submit=True):
                ord_lbl = "ऑर्डर आईडी *" if is_hindi else "Order ID *"
                req_lbl = "अनुरोध प्रकार" if is_hindi else "Request Type"
                reason_lbl = "कारण *" if is_hindi else "Reason *"
                btn_lbl = "अनुरोध सबमिट करें" if is_hindi else "Submit Request"
                
                ord_id = st.text_input(ord_lbl)
                req_trans = {"Cancellation": "रद्द करना (Cancellation)", "Return": "वापसी (Return)"}
                req_type = st.selectbox(
                    req_lbl, 
                    ["Cancellation", "Return"],
                    format_func=lambda x: req_trans.get(x, x) if is_hindi else x
                )
                reason = st.text_area(reason_lbl)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"order_id": ord_id, "request_type": req_type, "reason": reason}
                    display_req = req_trans.get(req_type, req_type) if is_hindi else req_type
                    user_str = f"ऑर्डर {ord_id} के लिए {display_req} का अनुरोध किया" if is_hindi else f"Requested {req_type} for order {ord_id}"
                    handle_input(val, user_str)

        # --- OTHER FEEDBACK ---
        elif current_state == "OTHER_FEEDBACK":
            with st.form("feedback_form", clear_on_submit=True):
                rating_lbl = "रेटिंग" if is_hindi else "Rating"
                comm_lbl = "टिप्पणियाँ" if is_hindi else "Comments"
                btn_lbl = "फीडबैक सबमिट करें" if is_hindi else "Submit Feedback"
                
                rating = st.select_slider(rating_lbl, options=["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"], value="5 Star")
                comments = st.text_area(comm_lbl)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"rating": rating, "comments": comments}
                    user_str = f"{rating} फीडबैक सबमिट किया।" if is_hindi else f"Submitted {rating} feedback."
                    handle_input(val, user_str)

        # --- OTHER COMPLAINT ESCALATION ---
        elif current_state == "OTHER_COMPLAINT":
            with st.form("complaint_escalation_form", clear_on_submit=True):
                title_lbl = "शिकायत का शीर्षक *" if is_hindi else "Complaint Title *"
                desc_lbl = "विस्तृत विवरण *" if is_hindi else "Detailed Description *"
                btn_lbl = "शिकायत सबमिट करें" if is_hindi else "Submit Complaint"
                
                title = st.text_input(title_lbl)
                desc = st.text_area(desc_lbl)
                
                submit = st.form_submit_button(btn_lbl)
                if submit:
                    val = {"title": title, "description": desc}
                    user_str = f"शिकायत आगे बढ़ाई: {title}" if is_hindi else f"Escalated complaint: {title}"
                    handle_input(val, user_str)

        # --- FAQ ---
        elif current_state == "OTHER_FAQ":
            english_faqs = [
                ("How long is the standard warranty on appliances?", "appliances come with a standard 1-year parts and labor warranty. Some appliances like washing machine motors and refrigerator compressors have extended warranties of up to 10 years on the key part."),
                ("How can I reschedule my technician visit?", "You can easily reschedule your booking in the 'My Appointments' tab in this customer portal. Simply click the 'Reschedule' button, choose a new date and time slot, and click save."),
                ("Where do I find my appliance serial number?", "For refrigerators, the serial number is on a label inside the fresh food compartment on the side wall. For washing machines, it is inside the door or on the back. For TVs, it is on the back panel."),
                ("What should I do if my refrigerator is not cooling?", "1. Check if the door is fully closed.\n2. Ensure there is at least 2 inches of space around the unit for ventilation.\n3. Clean the condenser coils at the bottom/back.\n4. Check if the temperature settings are set correctly (recommended: 37°F for fridge, 0°F for freezer)."),
                ("Can I cancel my service appointment?", "Yes, you can cancel your appointment up to 2 hours before the scheduled time slot in the 'My Appointments' tab.")
            ]
            hindi_faqs = [
                ("उपकरणों पर मानक वारंटी कितने समय की होती है?", "उपकरणों पर मानक 1 वर्ष की पार्ट्स और लेबर वारंटी आती है। कुछ उपकरणों जैसे वाशिंग मशीन मोटर्स और रेफ्रिजरेटर कंप्रेशर्स पर प्रमुख पार्ट पर 10 साल तक की विस्तारित वारंटी होती है।"),
                ("मैं अपने तकनीशियन की यात्रा को कैसे पुनर्निर्धारित (reschedule) कर सकता हूँ?", "आप इस ग्राहक पोर्टल में 'My Appointments' टैब में जाकर अपनी बुकिंग को आसानी से पुनर्निर्धारित कर सकते हैं। बस 'Reschedule' बटन पर क्लिक करें, एक नई तारीख और समय स्लॉट चुनें, और सेव पर क्लिक करें।"),
                ("मुझे अपने उपकरण का सीरियल नंबर कहाँ मिलेगा?", "रेफ्रिजरेटर के लिए, सीरियल नंबर ताजे खाद्य कंपार्टमेंट के अंदर साइड वॉल पर एक लेबल पर होता है। वाशिंग मशीन के लिए, यह दरवाजे के अंदर या पीछे होता है। टीवी के लिए, यह पीछे के पैनल पर होता है।"),
                ("अगर मेरा रेफ्रिजरेटर ठंडा नहीं हो रहा है तो मुझे क्या करना चाहिए?", "1. जांचें कि क्या दरवाजा पूरी तरह से बंद है।\n2. सुनिश्चित करें कि वेंटिलेशन के लिए यूनिट के चारों ओर कम से कम 2 इंच की जगह हो।\n3. नीचे/पीछे लगे कंडेंसर कॉइल्स को साफ करें।\n4. जांचें कि क्या तापमान सेटिंग्स सही ढंग से सेट हैं (अनुशंसित: फ्रिज के लिए 37°F, फ्रीजर के लिए 0°F)।"),
                ("क्या मैं अपनी सेवा नियुक्ति रद्द कर सकता हूँ?", "हाँ, आप 'My Appointments' टैब में निर्धारित समय स्लॉट से 2 घंटे पहले तक अपनी नियुक्ति रद्द कर सकते हैं।")
            ]
            
            faqs = hindi_faqs if is_hindi else english_faqs
            for q, a in faqs:
                with st.expander(f"❓ {q}"):
                    st.write(a)
                    
            btn_lbl = "🏠 मुख्य मेनू पर वापस जाएँ" if is_hindi else "🏠 Back to Home Menu"
            if st.button(btn_lbl, use_container_width=True, type="primary"):
                reset_chat_flow()
                st.rerun()

def handle_input(value: any, user_display_str: str):
    """Processes user input, updates state, and generates the next bot response."""
    # 1. Add user reply to chat history
    add_chat_message("user", user_display_str)
    
    # 2. Process state transition
    user_id = st.session_state.user_id
    customer_name = st.session_state.full_name
    
    success = flow.process_state_transition(
        state=st.session_state.chat_state, 
        input_value=value, 
        user_id=user_id, 
        customer_name=customer_name
    )
    
    if success:
        # 3. Add bot's next state prompt to chat history
        next_state = st.session_state.chat_state
        bot_prompt = flow.get_state_prompt(next_state, st.session_state.chat_data)
        add_chat_message("assistant", bot_prompt)
    else:
        # If transition failed, we keep the state the same but we display an error.
        # Remove the user message from history so the user can re-submit after fixing
        if st.session_state.chat_history:
            st.session_state.chat_history.pop()
            
    st.rerun()

def render_order_timeline(status: str, is_hindi: bool = False):
    """Renders a visual horizontal or vertical step timeline using HTML/CSS."""
    english_steps = [
        ("Order Confirmed", "We have received your order."),
        ("Shipped", "Your order has left our regional warehouse."),
        ("Out for Delivery", "A local courier is delivering your product today."),
        ("Delivered", "The package was signed and delivered."),
        ("Installation Pending", "Our installation team will contact you."),
        ("Installation Completed", "Product was successfully set up."),
    ]
    hindi_steps = [
        ("ऑर्डर की पुष्टि हो गई", "हमें आपका ऑर्डर मिल गया है।"),
        ("शिप कर दिया गया", "आपका ऑर्डर हमारे क्षेत्रीय गोदाम से निकल चुका है।"),
        ("वितरण के लिए बाहर", "एक स्थानीय कूरियर आज आपका उत्पाद वितरित कर रहा है।"),
        ("वितरित कर दिया गया", "पैकेज पर हस्ताक्षर करके वितरित किया गया।"),
        ("स्थापना लंबित", "हमारी स्थापना टीम आपसे संपर्क करेगी।"),
        ("स्थापना पूरी हो गई", "उत्पाद सफलतापूर्वक स्थापित किया गया था।"),
    ]
    
    # Determine the index of the current status in the timeline
    status_index = -1
    for idx, (step_title, _) in enumerate(english_steps):
        if status.upper() == step_title.upper():
            status_index = idx
            break
            
    # Handle specific status deviations
    is_delayed = status == "Delayed"
    
    steps = hindi_steps if is_hindi else english_steps
    html = "<div class='timeline-container'>"
    
    for idx, (title, desc) in enumerate(steps):
        step_class = ""
        icon_content = str(idx + 1)
        
        if is_delayed and idx == 2:  # Mark delay on 'Out for Delivery' step for demo
            step_class = "timeline-step active"
            title = f"{title} (विलंबित)" if is_hindi else f"{title} (Delayed)"
            desc = "मार्ग में भीड़ के कारण आपके शिपमेंट में देरी हुई।" if is_hindi else "Your shipment was delayed due to route congestion."
            icon_content = "⚠️"
        elif idx < status_index:
            step_class = "timeline-step completed"
            icon_content = "✓"
        elif idx == status_index:
            step_class = "timeline-step active"
            icon_content = "●"
        else:
            step_class = "timeline-step"
            
        html += f"""
        <div class='{step_class}'>
            <div class='timeline-icon'>{icon_content}</div>
            <div class='timeline-content'>
                <div class='timeline-title'>{title}</div>
                <div class='timeline-desc'>{desc}</div>
            </div>
        </div>
        """
        
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
