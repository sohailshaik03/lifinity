# ui/theme.py
import streamlit as st


def inject_theme():
    css = """
    <style>
        body { font-family: 'Inter', sans-serif; }
        .main { padding: 2rem; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
