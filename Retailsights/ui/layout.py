# ui/layout.py
import streamlit as st

from .theme import inject_theme


def apply_layout():
    st.set_page_config(
        page_title="RetailSight",
        page_icon="🛒",
        layout="wide",
    )
    inject_theme()


