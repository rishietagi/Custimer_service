import streamlit as st
import uuid
import core.db as db

def render_orders():
    """Renders the Orders management dashboard tab."""
    st.markdown("<div class='brand-header'><h1>📦 Order Tracking & History</h1></div>", unsafe_allow_html=True)
    
    user_id = st.session_state.user_id
    user_orders = db.get_user_orders(user_id)

    # We use tabs for User Orders vs General Lookup
    tab_my_orders, tab_lookup = st.tabs(["🛒 My Orders", "🔍 Search Any Order"])

    with tab_my_orders:
        if not user_orders:
            st.info("You don't have any purchase orders on record.")
        else:
            st.write(f"Showing {len(user_orders)} orders:")
            for idx, order in enumerate(user_orders):
                render_order_card(order, idx)

    with tab_lookup:
        st.write("##### Track an order using Order ID and contact details:")
        
        with st.form("general_order_lookup"):
            search_id = st.text_input("Order ID", placeholder="e.g. ORD-1153").strip()
            search_contact = st.text_input("Registered Phone or Email", placeholder="e.g. jane.smith@support-example.com").strip()
            search_submit = st.form_submit_button("Search Order", use_container_width=True)

            if search_submit:
                if not search_id or not search_contact:
                    st.error("Please enter both Order ID and Phone/Email.")
                else:
                    found_order = db.lookup_order(search_id, search_contact)
                    if found_order:
                        st.session_state["searched_order"] = found_order
                        st.success("Order found!")
                    else:
                        st.session_state["searched_order"] = None
                        st.error("No order found matching these details. Try: ORD-1153 with jane.smith@support-example.com")

        if "searched_order" in st.session_state and st.session_state["searched_order"]:
            st.markdown("---")
            st.write("### Search Result:")
            render_order_card(st.session_state["searched_order"], 999) # 999 is a unique key offset

def render_order_card(order: dict, key_idx: int):
    """Renders a single order card with timeline and actions."""
    order_id = order["order_id"]
    status = order["status"]
    
    st.markdown("<div class='portal-card'>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown(f"#### Order **#{order_id}**")
        st.markdown(f"**Product:** {order['product_name']}")
        st.markdown(f"**Ordered On:** {order['created_at'][:10]}")
    with col_r:
        # Status styling badge
        badge_style = "info-blue"
        if status == "Delivered" or status == "Installation Completed":
            badge_style = "success-green"
        elif status == "Delayed":
            badge_style = "primary-color"
            
        st.markdown(
            f"<div style='text-align: right;'><span class='status-badge' style='background-color: var(--{badge_style}); color: white;'>{status.upper()}</span></div>", 
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.write("##### Delivery Timeline:")
    render_timeline_widget(status)

    # Action panel inside the card if order requires attention
    action_key = f"order_act_{order_id}_{key_idx}"
    if action_key not in st.session_state:
        st.session_state[action_key] = None

    st.markdown("---")
    
    # We display actions depending on status
    st.write("##### Need help with this order?")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("⚠️ Raise Complaint", key=f"comp_{order_id}_{key_idx}", use_container_width=True):
            st.session_state[action_key] = "complaint"
    with c2:
        if st.button("📞 Call Back", key=f"call_{order_id}_{key_idx}", use_container_width=True):
            st.session_state[action_key] = "callback"
    with c3:
        if st.button("🚀 Escalate", key=f"esc_{order_id}_{key_idx}", use_container_width=True):
            st.session_state[action_key] = "escalate"
    with c4:
        # Schedule installation button is disabled if installation is completed or order not delivered yet
        install_disabled = status not in ["Delivered", "Installation Pending"]
        if st.button("🛠️ Install", key=f"inst_{order_id}_{key_idx}", use_container_width=True, disabled=install_disabled):
            st.session_state[action_key] = "installation"

    # Handle active action rendering
    current_action = st.session_state[action_key]
    
    if current_action == "callback":
        st.info("📞 **Callback Requested:** A service representative will call you at " + order["registered_phone"] + " within 2 hours.")
        if st.button("Close", key=f"cls_cb_{order_id}_{key_idx}"):
            st.session_state[action_key] = None
            st.rerun()

    elif current_action == "escalate":
        ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
        db.create_support_case(
            case_id=ticket_id,
            user_id=st.session_state.user_id,
            title=f"Order Escalation: {order_id}",
            description=f"User escalated order status inquiry for order {order_id} ({order['product_name']}). Current status: {status}.",
            category="Complaint escalation"
        )
        st.success(f"🚀 **Issue Escalated!** Escalation Ticket Reference ID: **{ticket_id}**. A support manager will review it.")
        if st.button("Close", key=f"cls_esc_{order_id}_{key_idx}"):
            st.session_state[action_key] = None
            st.rerun()

    elif current_action == "complaint":
        with st.form(f"comp_form_{order_id}_{key_idx}"):
            subj = st.text_input("Complaint Subject", placeholder="e.g. Package damaged / Missing items")
            desc = st.text_area("Complaint Details", placeholder="Describe the problem.")
            sub_btn = st.form_submit_button("Submit Ticket")
            
            if sub_btn:
                if not subj or not desc:
                    st.error("Please fill in both subject and description.")
                else:
                    ticket_id = "CAS-ORD-" + str(uuid.uuid4())[:6].upper()
                    db.create_support_case(
                        case_id=ticket_id,
                        user_id=st.session_state.user_id,
                        title=f"Order Complaint: {subj}",
                        description=f"Order ID: {order_id}\nDetails: {desc}",
                        category="Complaint escalation"
                    )
                    st.success(f"✅ Complaint Ticket Submitted. Reference ID: **{ticket_id}**.")
                    st.session_state[action_key] = None
                    # We don't rerun right inside form submit but we can close it
                    
            if st.form_submit_button("Close"):
                st.session_state[action_key] = None
                st.rerun()

    elif current_action == "installation":
        st.info("📝 To schedule product installation, please head over to the **💬 Chatbot Assistant** and choose **🔧 Product Help / Repair** or **❓ Something Else > Request Installation**.")
        if st.button("Close", key=f"cls_inst_{order_id}_{key_idx}"):
            st.session_state[action_key] = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

def render_timeline_widget(status: str):
    """Timeline visualizer inside order details."""
    steps = [
        ("Order Confirmed", "Order received"),
        ("Shipped", "Sent from factory"),
        ("Out for Delivery", "Courier carrying item"),
        ("Delivered", "Delivered at doorstep"),
        ("Installation Pending", "Setup requested"),
        ("Installation Completed", "Fully configured"),
    ]
    
    status_index = -1
    for idx, (t, _) in enumerate(steps):
        if status.upper() == t.upper():
            status_index = idx
            break
            
    is_delayed = status == "Delayed"
    
    html = "<div class='timeline-container'>"
    
    for idx, (title, desc) in enumerate(steps):
        step_class = ""
        icon = str(idx + 1)
        
        if is_delayed and idx == 2:
            step_class = "timeline-step active"
            title = f"{title} (Delayed)"
            desc = "Awaiting transport sorting"
            icon = "⚠️"
        elif idx < status_index:
            step_class = "timeline-step completed"
            icon = "✓"
        elif idx == status_index:
            step_class = "timeline-step active"
            icon = "●"
        else:
            step_class = "timeline-step"
            
        html += f"""
        <div class='{step_class}'>
            <div class='timeline-icon'>{icon}</div>
            <div class='timeline-content'>
                <div class='timeline-title' style='font-size: 14px;'>{title}</div>
                <div class='timeline-desc' style='font-size: 11px;'>{desc}</div>
            </div>
        </div>
        """
        
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
