import streamlit as st
import core.db as db

def render_profile():
    """Renders the Customer Profile dashboard tab."""
    st.markdown("<div class='brand-header'><h1>👤 Customer Profile & Dashboard</h1></div>", unsafe_allow_html=True)

    user_id = st.session_state.user_id
    user_info = db.get_user_by_id(user_id)
    products = db.get_user_products(user_id)
    tickets = db.get_user_support_cases(user_id)

    if not user_info:
        st.error("Error loading user profile details.")
        return

    # Layout: Profile Details vs Registered Products
    st.markdown("<div class='portal-card'>", unsafe_allow_html=True)
    st.subheader("Account Details")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Full Name:** {user_info['full_name']}")
        st.markdown(f"**Username:** `{user_info['username']}`")
        st.markdown(f"**Email Address:** {user_info['email']}")
    with c2:
        st.markdown(f"**Contact Number:** {user_info['phone']}")
        st.markdown(f"**Location Address:** {user_info['address'] or 'Not provided'}")
        st.markdown(f"**City & Pincode:** {user_info['city'] or ''} - {user_info['pincode'] or ''}")
        
    st.markdown("</div>", unsafe_allow_html=True)

    # Tabs for registered products and support cases
    tab_products, tab_tickets = st.tabs(["🛡️ Registered Appliances", "🎫 My Support Tickets"])

    with tab_products:
        if not products:
            st.info("You don't have any appliances registered to this account. Register one in the Chatbot assistant under 'Something Else > Product registration'.")
        else:
            st.write(f"Showing {len(products)} registered home appliances:")
            for p in products:
                st.markdown("<div class='portal-card' style='border-left: 3px solid #2e7d32;'>", unsafe_allow_html=True)
                
                col_title, col_war = st.columns([2, 1])
                with col_title:
                    st.markdown(f"##### **{p['category']}** (Model: `{p['model_number']}`)")
                with col_war:
                    badge_color = "success-green" if p['warranty_status'] == "In Warranty" else "primary-color"
                    st.markdown(f"<div style='text-align: right;'><span class='status-badge' style='background-color: var(--{badge_color}); color: white;'>{p['warranty_status'].upper()}</span></div>", unsafe_allow_html=True)
                
                st.markdown(f"**Serial Number:** `{p['serial_number']}`")
                st.markdown(f"**Purchase Date:** {p['purchase_date']}")
                if p.get('installation_date'):
                    st.markdown(f"**Installation Date:** {p['installation_date']}")
                    
                st.markdown("</div>", unsafe_allow_html=True)

    with tab_tickets:
        if not tickets:
            st.info("You don't have any active support tickets or complaints.")
        else:
            st.write(f"Showing {len(tickets)} support tickets:")
            for t in tickets:
                st.markdown("<div class='portal-card' style='border-left: 3px solid #1565c0;'>", unsafe_allow_html=True)
                
                col_t, col_s = st.columns([2, 1])
                with col_t:
                    st.markdown(f"##### **{t['title']}**")
                    st.caption(f"Category: {t['category']} | Created: {t['created_at'][:16].replace('T', ' ')}")
                with col_s:
                    st_val = t['status']
                    badge_style = "info-blue"
                    if st_val.lower() == "resolved":
                        badge_style = "success-green"
                    st.markdown(f"<div style='text-align: right;'><span class='status-badge' style='background-color: var(--{badge_style}); color: white;'>{st_val.upper()}</span></div>", unsafe_allow_html=True)
                
                st.markdown(f"**Description:**")
                st.write(t['description'])
                st.markdown("</div>", unsafe_allow_html=True)
