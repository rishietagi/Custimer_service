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

    # 1. Initialize chatbot history if empty
    if not st.session_state.chat_history:
        first_prompt = flow.get_state_prompt("HOME_MENU", {})
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
            if st.button("⬅️ Go Back", use_container_width=True, disabled=not st.session_state.state_history):
                if go_back():
                    # Re-seed last bot prompt if history gets back
                    st.rerun()
        with c2:
            if st.button("🔄 Restart", use_container_width=True, type="secondary"):
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
    st.markdown("### Reply to Assistant")
    
    # We will use st.form or clean widgets to collect the reply
    with st.container():
        # Render different forms depending on FSM state
        
        # --- HOME MENU ---
        if current_state == "HOME_MENU":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔧 Product Help / Repair", use_container_width=True, type="primary"):
                    handle_input("A", "I need help with a product / request a repair.")
            with c2:
                if st.button("📦 Track Current Order", use_container_width=True):
                    handle_input("B", "I want a status update on my current order.")
            with c3:
                if st.button("❓ Something Else", use_container_width=True):
                    handle_input("C", "I need help with another service.")

        # --- PRODUCT CATEGORY ---
        elif current_state == "PRODUCT_CATEGORY":
            cols = st.columns(4)
            for idx, cat in enumerate(flow.CATEGORIES):
                col_idx = idx % 4
                with cols[col_idx]:
                    if st.button(cat, use_container_width=True):
                        handle_input(cat, f"Product Category: {cat}")

        # --- PRODUCT MODEL ---
        elif current_state == "PRODUCT_MODEL":
            # Show registered products if any, as shortcuts
            registered_prods = st.session_state.get("registered_products", [])
            selected_cat = st.session_state.chat_data.get("category")
            matching_prods = [p for p in registered_prods if p["category"] == selected_cat]

            if matching_prods:
                st.caption("Or select one of your registered appliances:")
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
                            
                            add_chat_message("user", f"Select Registered Product: {p['model_number']}")
                            transition_to("ISSUE_COLLECTION")
                            add_chat_message("assistant", flow.get_state_prompt("ISSUE_COLLECTION", st.session_state.chat_data))
                            st.rerun()

            with st.form("model_form", clear_on_submit=True):
                model_num = st.text_input("Enter Model Number", placeholder="e.g. LFXS26973S").strip()
                submit = st.form_submit_button("Continue")
                if submit:
                    handle_input(model_num, f"Model Number: {model_num}")

        # --- PRODUCT PURCHASE DATE ---
        elif current_state == "PRODUCT_PURCHASE_DATE":
            with st.form("purchase_date_form", clear_on_submit=True):
                pur_date = st.date_input("Purchase Date", max_value=date.today())
                submit = st.form_submit_button("Continue")
                if submit:
                    handle_input(pur_date, f"Purchase Date: {pur_date}")

        # --- PRODUCT WARRANTY ---
        elif current_state == "PRODUCT_WARRANTY":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🛡️ In Warranty", use_container_width=True):
                    handle_input("In Warranty", "Status: In Warranty")
            with c2:
                if st.button("❌ Out of Warranty", use_container_width=True):
                    handle_input("Out of Warranty", "Status: Out of Warranty")

        # --- PRODUCT SERIAL ---
        elif current_state == "PRODUCT_SERIAL":
            with st.form("serial_form", clear_on_submit=True):
                serial_num = st.text_input("Enter Serial Number", placeholder="e.g. REF123456789").strip()
                submit = st.form_submit_button("Continue")
                if submit:
                    handle_input(serial_num, f"Serial Number: {serial_num}")

        # --- PRODUCT INSTALL DATE ---
        elif current_state == "PRODUCT_INSTALL_DATE":
            with st.form("install_date_form", clear_on_submit=True):
                st.write("If installation date was the same as purchase date, you can leave this empty.")
                has_install_date = st.checkbox("Enter different installation date", value=False)
                install_date = st.date_input("Installation Date", max_value=date.today()) if has_install_date else None
                
                submit = st.form_submit_button("Continue")
                if submit:
                    val = install_date if has_install_date else None
                    val_str = f"Installation Date: {val}" if has_install_date else "Skip Installation Date"
                    handle_input(val, val_str)

        # --- ISSUE COLLECTION ---
        elif current_state == "ISSUE_COLLECTION":
            cat = st.session_state.chat_data.get("category", "Others")
            issue_opts = flow.CATEGORY_ISSUES.get(cat, ["Other"])
            
            with st.form("issue_form", clear_on_submit=True):
                issue_opt = st.selectbox("Select the issue", issue_opts)
                issue_desc = st.text_area("Describe the issue in detail (Optional if selected above, required if 'Other')", placeholder="Describe symptoms, error codes, etc.")
                
                submit = st.form_submit_button("Submit Issue")
                if submit:
                    val = {"issue_option": issue_opt, "issue_description": issue_desc}
                    user_str = f"Issue: {issue_opt}" + (f" ({issue_desc})" if issue_desc else "")
                    handle_input(val, user_str)

        # --- CONFIRM DETAILS BEFORE BOOKING ---
        elif current_state == "CONFIRM_DETAILS_BEFORE_BOOKING":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📅 Yes, Book Service Appointment", use_container_width=True, type="primary"):
                    handle_input("Yes", "Yes, proceed with booking.")
            with c2:
                if st.button("❌ No, Back to Main Menu", use_container_width=True):
                    handle_input("No", "No, cancel booking.")

        # --- SERVICE ADDRESS ---
        elif current_state == "SERVICE_ADDRESS":
            with st.form("service_address_form", clear_on_submit=True):
                addr = st.text_input("Full Address", value=st.session_state.chat_data.get("service_address", ""))
                city = st.text_input("City", value=st.session_state.chat_data.get("service_city", ""))
                pincode = st.text_input("Pincode", value=st.session_state.chat_data.get("service_pincode", ""))
                phone = st.text_input("Contact Phone Number", value=st.session_state.chat_data.get("service_phone", ""))
                notes = st.text_area("Additional Notes for Technician (Optional)", placeholder="e.g. gate code, ring bell, parking instructions")
                
                submit = st.form_submit_button("Proceed to Scheduling")
                if submit:
                    val = {"address": addr, "city": city, "pincode": pincode, "phone": phone, "notes": notes}
                    user_str = f"Address: {addr}, {city} - {pincode} (Phone: {phone})"
                    handle_input(val, user_str)

        # --- SERVICE SCHEDULE ---
        elif current_state == "SERVICE_SCHEDULE":
            with st.form("service_schedule_form", clear_on_submit=True):
                pref_date = st.date_input("Preferred Service Date", min_value=date.today())
                pref_slot = st.selectbox("Preferred Time Slot", flow.TIME_SLOTS)
                
                submit = st.form_submit_button("Confirm Service Appointment")
                if submit:
                    val = {"preferred_date": pref_date, "preferred_time_slot": pref_slot}
                    user_str = f"Date: {pref_date} | Slot: {pref_slot}"
                    handle_input(val, user_str)

        # --- BOOKING CONFIRMATION ---
        elif current_state == "BOOKING_CONFIRMATION":
            if st.button("🏠 Back to Home Menu", use_container_width=True, type="primary"):
                reset_chat_flow()
                st.rerun()

        # --- ORDER LOOKUP ---
        elif current_state == "ORDER_LOOKUP":
            with st.form("order_lookup_form", clear_on_submit=True):
                ord_id = st.text_input("Order ID", placeholder="ORD-XXXX")
                contact = st.text_input("Registered Phone or Email", placeholder="e.g. john.doe@support-example.com")
                
                submit = st.form_submit_button("Lookup Order")
                if submit:
                    val = {"order_id": ord_id, "contact_info": contact}
                    user_str = f"Looking up Order ID: {ord_id} | Contact: {contact}"
                    handle_input(val, user_str)

        # --- ORDER STATUS DISPLAY ---
        elif current_state == "ORDER_STATUS_DISPLAY":
            status = st.session_state.chat_data.get("order_status")
            
            # Show a custom HTML Timeline based on the order status
            render_order_timeline(status)
            
            st.write("##### Actions:")
            
            # Action buttons depending on order status
            if status in ["Delayed", "Installation Pending", "Shipped"]:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("⚠️ Raise Complaint", use_container_width=True):
                        handle_input("Raise a complaint", "Raise complaint regarding order status.")
                with c2:
                    if st.button("📞 Request Callback", use_container_width=True):
                        handle_input("Request callback", "Request call back from representative.")
                with c3:
                    if st.button("🚀 Escalate Issue", use_container_width=True, type="primary"):
                        handle_input("Escalate to support", "Escalate order delay.")
            elif status == "Delivered":
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🛠️ Schedule Installation", use_container_width=True, type="primary"):
                        handle_input("Schedule installation", "Schedule installation for delivered product.")
                with c2:
                    if st.button("⚠️ Raise Complaint", use_container_width=True):
                        handle_input("Raise a complaint", "Raise support issue.")
            else:
                if st.button("🏠 Back to Home Menu", use_container_width=True):
                    reset_chat_flow()
                    st.rerun()

        # --- ORDER COMPLAINT FORM ---
        elif current_state == "ORDER_COMPLAINT_FORM":
            with st.form("order_complaint_form", clear_on_submit=True):
                subj = st.text_input("Complaint Subject", placeholder="e.g. Delayed Delivery / Damaged Box")
                desc = st.text_area("Complaint Details", placeholder="Describe the issue in detail.")
                
                submit = st.form_submit_button("Submit Complaint")
                if submit:
                    val = {"subject": subj, "description": desc}
                    user_str = f"Submitted Complaint: {subj}"
                    handle_input(val, user_str)

        # --- ORDER CALLBACK / ESCALATION CONFIRM ---
        elif current_state in ["ORDER_CALLBACK_CONFIRM", "ORDER_ESCALATE_CONFIRM", "TICKET_SUBMITTED"]:
            if st.button("🏠 Back to Home Menu", use_container_width=True, type="primary"):
                reset_chat_flow()
                st.rerun()

        # --- OTHER HELP MENU ---
        elif current_state == "OTHER_HELP_MENU":
            submenu_options = [
                "Warranty / AMC", "Product registration", "Installation request",
                "Bill / invoice help", "Cancellation / return", "Feedback",
                "Complaint escalation", "General FAQ"
            ]
            cols = st.columns(2)
            for idx, opt in enumerate(submenu_options):
                col_idx = idx % 2
                with cols[col_idx]:
                    if st.button(opt, use_container_width=True):
                        handle_input(opt, f"Option: {opt}")

        # --- OTHER WARRANTY INFO ---
        elif current_state == "OTHER_WARRANTY_INFO":
            with st.form("amc_form", clear_on_submit=True):
                cat = st.selectbox("Product Category", flow.CATEGORIES)
                comments = st.text_area("Additional Details / Appliance Age", placeholder="e.g. I want to renew warranty for my 2 year old SmartCare Refrigerator.")
                submit = st.form_submit_button("Request AMC Quotation")
                if submit:
                    val = {"category": cat, "comments": comments}
                    handle_input(val, f"Requested AMC quote for {cat}")

        # --- OTHER PRODUCT REGISTRATION ---
        elif current_state == "OTHER_PROD_REGISTRATION":
            with st.form("prod_reg_form", clear_on_submit=True):
                cat = st.selectbox("Product Category", flow.CATEGORIES)
                model = st.text_input("Model Number")
                serial = st.text_input("Serial Number")
                p_date = st.date_input("Purchase Date", max_value=date.today())
                
                submit = st.form_submit_button("Register Product")
                if submit:
                    val = {"category": cat, "model_number": model, "serial_number": serial, "purchase_date": p_date}
                    handle_input(val, f"Registered product: {cat} (Model: {model})")

        # --- OTHER INSTALLATION REQUEST ---
        elif current_state == "OTHER_INSTALL_REQUEST":
            with st.form("install_req_form", clear_on_submit=True):
                cat = st.selectbox("Product Category", flow.CATEGORIES)
                model = st.text_input("Model Number")
                serial = st.text_input("Serial Number (Optional)")
                addr = st.text_area("Installation Address")
                pincode = st.text_input("Pincode")
                pref_date = st.date_input("Preferred Date", min_value=date.today())
                
                submit = st.form_submit_button("Request Installation")
                if submit:
                    val = {
                        "category": cat, "model_number": model, "serial_number": serial,
                        "address": addr, "pincode": pincode, "preferred_date": pref_date
                    }
                    handle_input(val, f"Requested installation for {cat} on {pref_date}")

        # --- OTHER BILL HELP ---
        elif current_state == "OTHER_BILL_HELP":
            with st.form("bill_help_form", clear_on_submit=True):
                ord_id = st.text_input("Order ID (Optional)")
                subj = st.text_input("Subject")
                msg = st.text_area("Message / Details")
                
                submit = st.form_submit_button("Submit Invoice Inquiry")
                if submit:
                    val = {"order_id": ord_id, "subject": subj, "message": msg}
                    handle_input(val, f"Invoice inquiry: {subj}")

        # --- OTHER CANCEL / RETURN ---
        elif current_state == "OTHER_CANCEL_RETURN":
            with st.form("cancel_return_form", clear_on_submit=True):
                ord_id = st.text_input("Order ID *")
                req_type = st.selectbox("Request Type", ["Cancellation", "Return"])
                reason = st.text_area("Reason *")
                
                submit = st.form_submit_button("Submit Request")
                if submit:
                    val = {"order_id": ord_id, "request_type": req_type, "reason": reason}
                    handle_input(val, f"Requested {req_type} for order {ord_id}")

        # --- OTHER FEEDBACK ---
        elif current_state == "OTHER_FEEDBACK":
            with st.form("feedback_form", clear_on_submit=True):
                rating = st.select_slider("Rating", options=["1 Star", "2 Star", "3 Star", "4 Star", "5 Star"], value="5 Star")
                comments = st.text_area("Comments")
                
                submit = st.form_submit_button("Submit Feedback")
                if submit:
                    val = {"rating": rating, "comments": comments}
                    handle_input(val, f"Submitted {rating} feedback.")

        # --- OTHER COMPLAINT ESCALATION ---
        elif current_state == "OTHER_COMPLAINT":
            with st.form("complaint_escalation_form", clear_on_submit=True):
                title = st.text_input("Complaint Title *")
                desc = st.text_area("Detailed Description *")
                
                submit = st.form_submit_button("Submit Complaint")
                if submit:
                    val = {"title": title, "description": desc}
                    handle_input(val, f"Escalated complaint: {title}")

        # --- FAQ ---
        elif current_state == "OTHER_FAQ":
            faqs = [
                ("How long is the standard warranty on appliances?", "appliances come with a standard 1-year parts and labor warranty. Some appliances like washing machine motors and refrigerator compressors have extended warranties of up to 10 years on the key part."),
                ("How can I reschedule my technician visit?", "You can easily reschedule your booking in the 'My Appointments' tab in this customer portal. Simply click the 'Reschedule' button, choose a new date and time slot, and click save."),
                ("Where do I find my appliance serial number?", "For refrigerators, the serial number is on a label inside the fresh food compartment on the side wall. For washing machines, it is inside the door or on the back. For TVs, it is on the back panel."),
                ("What should I do if my refrigerator is not cooling?", "1. Check if the door is fully closed.\n2. Ensure there is at least 2 inches of space around the unit for ventilation.\n3. Clean the condenser coils at the bottom/back.\n4. Check if the temperature settings are set correctly (recommended: 37°F for fridge, 0°F for freezer)."),
                ("Can I cancel my service appointment?", "Yes, you can cancel your appointment up to 2 hours before the scheduled time slot in the 'My Appointments' tab.")
            ]
            
            for q, a in faqs:
                with st.expander(f"❓ {q}"):
                    st.write(a)
                    
            if st.button("🏠 Back to Home Menu", use_container_width=True, type="primary"):
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

def render_order_timeline(status: str):
    """Renders a visual horizontal or vertical step timeline using HTML/CSS."""
    steps = [
        ("Order Confirmed", "We have received your order."),
        ("Shipped", "Your order has left our regional warehouse."),
        ("Out for Delivery", "A local courier is delivering your product today."),
        ("Delivered", "The package was signed and delivered."),
        ("Installation Pending", "Our installation team will contact you."),
        ("Installation Completed", "Product was successfully set up."),
    ]
    
    # Determine the index of the current status in the timeline
    status_index = -1
    for idx, (step_title, _) in enumerate(steps):
        if status.upper() == step_title.upper():
            status_index = idx
            break
            
    # Handle specific status deviations
    is_delayed = status == "Delayed"
    
    html = "<div class='timeline-container'>"
    
    for idx, (title, desc) in enumerate(steps):
        step_class = ""
        icon_content = str(idx + 1)
        
        if is_delayed and idx == 2:  # Mark delay on 'Out for Delivery' step for demo
            step_class = "timeline-step active"
            title = f"{title} (Delayed)"
            desc = "Your shipment was delayed due to route congestion."
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
