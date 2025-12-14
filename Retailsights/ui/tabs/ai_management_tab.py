from __future__ import annotations

import streamlit as st
from ...services.ai_service import get_active_model, get_rollout_status
from ...repositories.users_repo import list_users
from ...logger import logger

import os


def render_ai_management_tab(state) -> None:
    """Admin UI for AI model rollout management."""
    st.title("🤖 AI Model Management")

    user = st.session_state.get("auth_user")
    if not user or user.get("role") != "admin":
        st.error("Admin access required.")
        return

    # Current status
    st.markdown("### Current Rollout Status")
    status = get_rollout_status()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Model", status["model_name"])
    with col2:
        st.metric("Fallback Model", status["fallback_model"])
    with col3:
        st.metric("Rollout %", status["rollout_percent"])

    st.markdown("---")

    # Configuration
    st.markdown("### Configure Rollout")
    st.info(
        "Set environment variables and restart the app for changes to take effect: "
        "`MODEL_NAME`, `AI_FALLBACK_MODEL`, `AI_ROLLOUT_PERCENT`"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        new_model = st.text_input("Model name", value=status["model_name"], help="e.g., gpt-5-mini, gpt-4-turbo")
    with col2:
        new_fallback = st.text_input("Fallback model", value=status["fallback_model"])
    with col3:
        new_rollout = st.slider("Rollout % (0-100)", 0, 100, status["rollout_percent"], help="Percentage of users using new model")

    if st.button("Save configuration (local demo)"):
        st.info("In production, update your env vars and redeploy. For now, restart the app with updated env:")
        st.code(
            f"""
export MODEL_NAME={new_model}
export AI_FALLBACK_MODEL={new_fallback}
export AI_ROLLOUT_PERCENT={new_rollout}
streamlit run app.py
        """
        )

    st.markdown("---")

    # Cost / usage estimation
    st.markdown("### Estimated Monthly Cost (Demo)")
    users = list_users()
    num_users = len(users)
    avg_requests_per_user = st.slider("Avg requests per user per day", 0, 100, 10)
    cost_per_1k_tokens = st.number_input("Cost per 1K tokens ($)", 0.0, 1.0, 0.002)

    est_requests = num_users * avg_requests_per_user * 30
    est_tokens = est_requests * 500  # assume avg 500 tokens per request
    est_cost = (est_tokens / 1000) * cost_per_1k_tokens

    st.metric("Est. monthly cost", f"${est_cost:.2f}")
    st.write(f"Based on: {num_users} users × {avg_requests_per_user} requests/day × 30 days × ~500 tokens/request")

    st.markdown("---")

    # Canary rollout strategy
    st.markdown("### Canary Rollout Strategy")
    st.markdown("""
    **Recommended approach:**
    1. Start with 5% rollout (observe for regressions)
    2. Monitor: latency, errors, cost
    3. Increase to 10%, then 25%, then 50%, then 100%
    4. Keep fallback model available for quick rollback
    """)

    # Safety checks
    st.markdown("### Safety Checks")
    col1, col2 = st.columns(2)
    with col1:
        if st.checkbox("API key is configured in secrets", value=False):
            st.success("API key secure")
        else:
            st.warning("⚠️ Ensure OPENAI_API_KEY is in env/secrets, not code")

    with col2:
        if st.checkbox("Rate limits configured", value=False):
            st.success("Rate limits active")
        else:
            st.warning("⚠️ Consider adding per-user quotas")

    st.markdown("---")

    # Debug info
    with st.expander("Debug info"):
        st.json(status)
        st.code(f"ROLLOUT_PERCENT env: {os.getenv('AI_ROLLOUT_PERCENT', 'not set')}")
        st.code(f"MODEL_NAME env: {os.getenv('MODEL_NAME', 'not set')}")
