import streamlit as st
import hashlib
import uuid
import core.db as db
from core.state_manager import login_user
from core.validators import validate_phone, validate_pincode, validate_email

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def render_login():
    """Renders the login/registration interface."""
    st.markdown("<div style='text-align: center; margin-bottom: 2rem;'>", unsafe_allow_html=True)
    st.write("🔒")
    st.markdown("<h2>SmartCare customer Portal</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Use tabs for Login vs Register
    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

    with tab_login:
        st.markdown("<div class='portal-card'>", unsafe_allow_html=True)
        st.subheader("Welcome Back")
        st.caption("Sign in to check service requests, trace orders, or talk to an assistant.")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. customer1").strip().lower()
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Sign In", use_container_width=True)

            if submit_btn:
                if not username or not password:
                    st.error("Please fill in both username and password.")
                else:
                    user = db.get_user_by_username(username)
                    if user and user["password_hash"] == hash_password(password):
                        login_user(user)
                        st.success(f"Welcome back, {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Try customer1 / password123")
        st.markdown("</div>", unsafe_allow_html=True)

        # Show helper info for demo purposes
        st.info("💡 **Demo Accounts:**\n- Username: `customer1` | Password: `password123`\n- Username: `customer2` | Password: `password123`")

    with tab_register:
        st.markdown("<div class='portal-card'>", unsafe_allow_html=True)
        st.subheader("Register a New Account")
        st.caption("Fill in your details to create an SmartCare account.")

        with st.form("register_form"):
            reg_username = st.text_input("Username *", placeholder="e.g. johndoe123").strip().lower()
            reg_password = st.text_input("Password *", type="password", placeholder="••••••••")
            reg_fullname = st.text_input("Full Name *", placeholder="e.g. John Doe")
            reg_email = st.text_input("Email Address *", placeholder="e.g. john@example.com")
            reg_phone = st.text_input("Phone Number *", placeholder="e.g. 5550199283")
            
            st.markdown("---")
            st.markdown("##### Home Address (Used for Technician Visits)")
            reg_addr = st.text_input("Street Address", placeholder="e.g. 123 Maple St")
            reg_city = st.text_input("City", placeholder="e.g. Chicago")
            reg_pin = st.text_input("Pincode", placeholder="e.g. 60601")

            submit_reg = st.form_submit_button("Register Account", use_container_width=True)

            if submit_reg:
                # Validation checks
                if not reg_username or not reg_password or not reg_fullname or not reg_email or not reg_phone:
                    st.error("Please fill in all required fields marked with *.")
                elif len(reg_username) < 3:
                    st.error("Username must be at least 3 characters long.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    # Validate email, phone, pincode
                    email_ok, email_err = validate_email(reg_email)
                    phone_ok, phone_err = validate_phone(reg_phone)
                    
                    pin_ok = True
                    pin_err = ""
                    if reg_pin:
                        pin_ok, pin_err = validate_pincode(reg_pin)

                    if not email_ok:
                        st.error(email_ok)
                    elif not phone_ok:
                        st.error(phone_err)
                    elif not pin_ok:
                        st.error(pin_err)
                    else:
                        # Attempt to write to database
                        user_id = "usr_" + str(uuid.uuid4())[:8]
                        success = db.create_user(
                            user_id=user_id,
                            username=reg_username,
                            password_hash=hash_password(reg_password),
                            full_name=reg_fullname,
                            email=reg_email,
                            phone=reg_phone,
                            address=reg_addr or None,
                            city=reg_city or None,
                            pincode=reg_pin or None
                        )
                        if success:
                            st.success("Account created successfully! You can now sign in.")
                        else:
                            st.error("Username already exists. Please choose a different username.")
        st.markdown("</div>", unsafe_allow_html=True)
