# ui/tabs/login_tab.py
from __future__ import annotations

import streamlit as st

from Retailsights.services.user_service import authenticate_user, register_user
from Retailsights.utils.session_manager import SessionManager


def render_login_tab():
    st.markdown("## Welcome to RetailSight")
    st.caption("Sign in or create an account to access your shop analytics.")

    tabs = st.tabs(["Sign In", "Register"])

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            remember_me = st.checkbox("Remember me for 30 days", value=False, key="remember_me")
            submitted = st.form_submit_button("Sign in")

        if submitted:
            ok, user, msg = authenticate_user(email, password)
            if not ok:
                st.error(msg)
            else:
                # Set session state
                st.session_state["is_authenticated"] = True
                st.session_state["auth_user"] = user
                st.session_state["_auto_login_attempted"] = False  # Reset for next session
                
                # Save to cookies if remember me is checked
                if remember_me:
                    try:
                        session_mgr = SessionManager()
                        session_mgr.save_session(user, remember_me=True)
                        st.success("✅ Logged in successfully (session saved for 30 days)")
                    except Exception as e:
                        st.warning(f"Logged in but couldn't save session: {e}")
                        st.success("✅ Logged in successfully")
                else:
                    st.success("✅ Logged in successfully")
                
                st.rerun()

    with tabs[1]:
        with st.form("register_form"):
            reg_email = st.text_input("Email", placeholder="you@example.com", key="reg_email")
            reg_full_name = st.text_input("Full Name", placeholder="John Doe", key="reg_full_name")
            reg_password = st.text_input("Password", type="password", placeholder="At least 8 characters", key="reg_password")
            reg_password2 = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_password2")
            submitted_reg = st.form_submit_button("Register")

        if submitted_reg:
            if not reg_email or not reg_full_name or not reg_password or not reg_password2:
                st.error("All fields are required.")
            elif reg_password != reg_password2:
                st.error("Passwords do not match.")
            else:
                ok, user_id, msg = register_user(reg_email, reg_full_name, reg_password)
                if not ok:
                    st.error(msg)
                else:
                    st.success("Registration successful! You can now sign in.")
