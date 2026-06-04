import streamlit as st
from datetime import date
import core.db as db
import core.flow_engine as flow
from core.validators import validate_future_date

def render_appointments():
    """Renders the Appointments dashboard tab."""
    st.markdown("<div class='brand-header'><h1>📅 Service Appointments</h1></div>", unsafe_allow_html=True)
    
    user_id = st.session_state.user_id
    appointments = db.get_user_appointments(user_id)
    
    if not appointments:
        st.info("You don't have any service appointments scheduled. You can book one by using the Chatbot Assistant!")
        return

    st.write(f"Showing {len(appointments)} service appointments:")

    for idx, apt in enumerate(appointments):
        apt_id = apt["appointment_id"]
        status = apt["status"]
        
        # Color coding status badge
        status_color = "scheduled"
        if status.lower() == "rescheduled":
            status_color = "rescheduled"
        elif status.lower() == "cancelled":
            status_color = "cancelled"
        elif status.lower() == "completed":
            status_color = "completed"

        # Card container
        st.markdown(f"<div class='portal-card'>", unsafe_allow_html=True)
        
        col_header_left, col_header_right = st.columns([3, 1])
        with col_header_left:
            st.markdown(f"#### Appointment **#{apt_id}**")
        with col_header_right:
            st.markdown(
                f"<div style='text-align: right;'><span class='status-badge {status_color}'>{status.upper()}</span></div>", 
                unsafe_allow_html=True
            )
            
        st.markdown(f"**Customer:** {apt['customer_name']}")
        st.markdown(f"**Product Category:** {apt['product_category']} (Model: `{apt['product_model']}`)")
        st.markdown(f"**Issue Description:** *\"{apt['issue_description']}\"*")
        st.markdown(f"**Scheduled Date/Time:** 📅 `{apt['preferred_date']}` | 🕒 `{apt['preferred_time_slot']}`")
        st.markdown(f"**Assigned Tech:** {apt['technician_name']}")
        
        st.markdown("---")
        
        # Create unique keys for forms/buttons per appointment
        btn_key_prefix = f"apt_{apt_id}_{idx}"
        
        # Action Buttons row
        c1, c2, c3 = st.columns(3)
        
        # We track which action is active using session state to avoid page reload issues
        action_state_key = f"active_action_{apt_id}"
        if action_state_key not in st.session_state:
            st.session_state[action_state_key] = None

        with c1:
            # We can use expander for More Info as required, or a button toggle.
            # Expander is extremely elegant and allows details to slide open nicely.
            more_info_open = st.checkbox("🔍 More Info", key=f"check_info_{btn_key_prefix}")
            
        with c2:
            resched_clicked = st.button("📅 Reschedule", key=f"btn_resched_{btn_key_prefix}", disabled=(status == "Cancelled"))
            if resched_clicked:
                st.session_state[action_state_key] = "reschedule" if st.session_state[action_state_key] != "reschedule" else None
                
        with c3:
            cancel_clicked = st.button("❌ Cancel", key=f"btn_cancel_{btn_key_prefix}", disabled=(status == "Cancelled"))
            if cancel_clicked:
                st.session_state[action_state_key] = "cancel" if st.session_state[action_state_key] != "cancel" else None

        # 1. More Info Section
        if more_info_open:
            st.markdown("<div style='background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #a50034;'>", unsafe_allow_html=True)
            st.write("##### Diagnostic & Booking Details:")
            
            det_c1, det_c2 = st.columns(2)
            with det_c1:
                st.markdown(f"**Serial Number:** `{apt['serial_number']}`")
                st.markdown(f"**Purchase Date:** {apt['purchase_date']}")
                st.markdown(f"**Warranty Status:** {apt['warranty_status']}")
                st.markdown(f"**Created At:** {apt['created_at']}")
            with det_c2:
                st.markdown(f"**Service Address:** {apt['address']}")
                st.markdown(f"**City:** {apt['city']}")
                st.markdown(f"**Pincode:** {apt['pincode']}")
            st.markdown("</div>", unsafe_allow_html=True)

        # 2. Reschedule Form Section
        if st.session_state[action_state_key] == "reschedule":
            st.markdown("<div style='background-color: #fffde7; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #f9a825;'>", unsafe_allow_html=True)
            st.write("##### Reschedule Appointment")
            
            with st.form(key=f"form_resched_{apt_id}"):
                new_date = st.date_input("Select New Date", min_value=date.today(), key=f"date_val_{apt_id}")
                new_slot = st.selectbox("Select New Time Slot", flow.TIME_SLOTS, key=f"slot_val_{apt_id}")
                
                sub_cols = st.columns([1, 1])
                with sub_cols[0]:
                    submit_resched = st.form_submit_button("Confirm Reschedule", use_container_width=True)
                with sub_cols[1]:
                    cancel_resched_action = st.form_submit_button("Keep Original", use_container_width=True)
                    
                if submit_resched:
                    ok_date, err_date = validate_future_date(new_date)
                    if not ok_date:
                        st.error(err_date)
                    else:
                        db.reschedule_appointment(apt_id, new_date.isoformat(), new_slot)
                        st.session_state[action_state_key] = None
                        st.success("Appointment rescheduled successfully!")
                        st.rerun()
                        
                if cancel_resched_action:
                    st.session_state[action_state_key] = None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # 3. Cancel Form Section
        if st.session_state[action_state_key] == "cancel":
            st.markdown("<div style='background-color: #ffebee; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #a50034;'>", unsafe_allow_html=True)
            st.write("⚠️ **Are you sure you want to cancel this appointment?**")
            st.write("This action cannot be undone.")
            
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("Yes, Cancel Appointment", key=f"confirm_cancel_{apt_id}", type="primary", use_container_width=True):
                    db.cancel_appointment(apt_id)
                    st.session_state[action_state_key] = None
                    st.success("Appointment cancelled successfully.")
                    st.rerun()
            with c_no:
                if st.button("No, Keep Appointment", key=f"abort_cancel_{apt_id}", use_container_width=True):
                    st.session_state[action_state_key] = None
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
