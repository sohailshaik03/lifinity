from __future__ import annotations

import streamlit as st
from ...repositories.exports_repo import get_exports_for_shop, get_export_by_task_id


def render_exports_tab(state) -> None:
    st.title("📁 Report Exports")

    user = st.session_state.get("auth_user")
    shop = st.session_state.get("current_shop")

    if not user:
        st.error("You are not logged in.")
        return

    st.markdown("### Recent exports for selected shop")
    if not shop:
        st.info("Select a shop from the sidebar to view exports.")
    else:
        rows = get_exports_for_shop(shop["id"])
        if not rows:
            st.info("No exports found for this shop.")
        else:
            st.table(rows)

    st.markdown("---")
    st.markdown("### Lookup by Task ID")
    tid = st.text_input("Celery Task ID")
    if tid and st.button("Lookup task"):
        row = get_export_by_task_id(tid)
        if not row:
            st.info("No export found for that task id yet. It may be pending.")
        else:
            st.json(row)
