import streamlit as st
import os

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="SmartCare Customer Portal",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and seed data
import core.db as db
from core.sample_data import seed_data
db.init_db()
seed_data()

# Initialize session state
from core.state_manager import init_session_state, logout_user
init_session_state()

# Inject Custom CSS Stylesheet
CSS_PATH = os.path.join("assets", "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("Custom CSS file not found in assets/style.css.")

# --- NAVIGATION FLOW ---

# Check if user is logged in
if st.session_state.user_id is None:
    # Render Login Page
    from pages.login import render_login
    render_login()
else:
    # User is logged in, sync their registered products in session state
    st.session_state.registered_products = db.get_user_products(st.session_state.user_id)

    # Sidebar Brand Header
    st.sidebar.markdown(
        "<div style='text-align: center; margin-bottom: 20px;'>"
        "<img src='https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png' width='80'><br>"
        "<h3 style='margin-top: 10px; color:#2c2c2c;'>SmartCare</h3>"
        "</div>",
        unsafe_allow_html=True
    )

    # Sidebar User Card
    st.sidebar.markdown(
        f"<div style='background-color: #f1f3f4; padding: 12px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #a50034;'>"
        f"👤 <b>Welcome, {st.session_state.full_name}</b><br>"
        f"<span style='font-size: 12px; color: #666;'>User ID: {st.session_state.username}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Sidebar Navigation Menu
    nav_option = st.sidebar.radio(
        "Navigate Portal",
        options=[
            "💬 Assistant Chatbot",
            "📅 My Appointments",
            "📦 Track Orders",
            "👤 My Profile & Tickets"
        ]
    )

    st.sidebar.markdown("---")

    # Logout Button at the bottom
    if st.sidebar.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        logout_user()
        st.rerun()

    # Footer
    st.sidebar.markdown(
        "<div style='text-align: center; font-size: 11px; color: #888; margin-top: 40px;'>"
        "© 2026 SmartCare Corp.<br>All rights reserved."
        "</div>",
        unsafe_allow_html=True
    )

    # Main Panel Router
    if nav_option == "💬 Assistant Chatbot":
        from pages.chatbot import render_chatbot
        render_chatbot()
    elif nav_option == "📅 My Appointments":
        from pages.appointments import render_appointments
        render_appointments()
    elif nav_option == "📦 Track Orders":
        from pages.orders import render_orders
        render_orders()
    elif nav_option == "👤 My Profile & Tickets":
        from pages.profile import render_profile
        render_profile()
