# ui/tabs/login_tab.py
from __future__ import annotations

import streamlit as st

from ...services.user_service import authenticate_user, register_user


def render_login_tab():
    st.markdown("## Welcome to RetailSight")
    st.caption("Sign in or create an account to access your shop analytics.")

    tabs = st.tabs(["Sign In", "Register"])

    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            submitted = st.form_submit_button("Sign in")

        if submitted:
            ok, user, msg = authenticate_user(email, password)
            if not ok:
                st.error(msg)
            else:
                st.session_state["is_authenticated"] = True
                st.session_state["auth_user"] = user
                st.success("Logged in successfully.")
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
