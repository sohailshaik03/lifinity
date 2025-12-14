# app.py
from __future__ import annotations

import streamlit as st

# When running via `streamlit run Retailsights/app.py` the module may be executed
# as a script (no package). Ensure relative imports work by setting package
# context and adding project root to `sys.path` when needed.
if __package__ is None:
    import sys, os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    __package__ = "Retailsights"

from .db import health_check
from .logger import log
from .repositories.shops_repo import ShopsRepository
from .ui.components import show_logout_button, show_top_bar, show_support_widget
from .ui.layout import apply_layout
from .ui.tabs.admin_tab import render_admin_tab
from .ui.tabs.history_tab import render_history_tab
from .ui.tabs.login_tab import render_login_tab
from .ui.tabs.manager_tab import render_manager_tab
from .ui.tabs.exports_tab import render_exports_tab
from .ui.tabs.upload_tab import render_upload_tab
from .ui.tabs.expiry_tab import render_expiry_tab
from .ui.tabs.ai_management_tab import render_ai_management_tab
from .ui.tabs.yellow_sticker_tab import render_yellow_sticker_tab
from .ui.tabs.enterprise_tab import render_enterprise_dashboard
from .ui.tabs.advanced_tech_tab import render_advanced_tech_tab
from .ui.tabs.support_tab import render_support_tab
from .ui.tabs.subscription_tab import render_subscription_tab


def render_main_shell(user: dict):
    st.sidebar.title("📍 Navigation")

    # --- Shop selector (sidebar) ---
    user_id = user.get("id") if user else None
    shops = []
    try:
        if user and user.get("role") == "admin":
            shops = ShopsRepository.get_all_shops()
        elif user_id:
            shops = ShopsRepository.get_user_shops(user_id)
    except Exception as e:
        log.exception("Failed to load shops for user_id=%s: %s", user_id, e)
        st.sidebar.error("Could not load shops. Please try again or contact support.")

    if shops:
        shop_options = {s["name"]: s for s in shops}
        selected_name = st.sidebar.selectbox(
            "Select shop", ["— Select shop —"] + list(shop_options.keys())
        )
        if selected_name and selected_name != "— Select shop —":
            st.session_state["current_shop"] = shop_options[selected_name]
    else:
        st.sidebar.info("No shops assigned. Ask an admin to add one.")

    tabs = st.sidebar.radio(
        "Select a page",
        [
            "🏢 Enterprise Dashboard",
            "🚀 Advanced Tech",
            "💎 Subscription",
            "Upload & Analyse",
            "History & Reports",
            "Manager Dashboard",
            "Report Exports",
            "Expiry & Waste",
            "Yellow Stickers 🏷️",
            "AI Models",
            "Admin",
            "🎧 Support",
        ],
        label_visibility="collapsed",
    )

    # Top bar (Apple-grade feel)
    show_top_bar(user)
    
    # Support widget in sidebar
    show_support_widget()

    state = st.session_state

    def _safe_render(name: str, fn, *a, **kw):
        try:
            fn(*a, **kw)
        except Exception as e:
            log.exception("Error rendering %s: %s", name, e)
            st.error(f"An internal error occurred loading {name}. Contact support.")

    if tabs == "🏢 Enterprise Dashboard":
        _safe_render("Enterprise Dashboard", render_enterprise_dashboard, state)

    elif tabs == "🚀 Advanced Tech":
        _safe_render("Advanced Tech", render_advanced_tech_tab, state)
    
    elif tabs == "💎 Subscription":
        _safe_render("Subscription", render_subscription_tab, state)

    elif tabs == "Upload & Analyse":
        _safe_render("Upload & Analyse", render_upload_tab, state)

    elif tabs == "History & Reports":
        _safe_render("History & Reports", render_history_tab, state)

    elif tabs == "Manager Dashboard":
        _safe_render("Manager Dashboard", render_manager_tab, state)

    elif tabs == "Report Exports":
        _safe_render("Report Exports", render_exports_tab, state)

    elif tabs == "Expiry & Waste":
        _safe_render("Expiry & Waste", render_expiry_tab, state)

    elif tabs == "Yellow Stickers 🏷️":
        _safe_render("Yellow Stickers", render_yellow_sticker_tab, state)

    elif tabs == "AI Models":
        _safe_render("AI Models", render_ai_management_tab, state)

    elif tabs == "Admin":
        _safe_render("Admin", render_admin_tab, state)

    elif tabs == "🎧 Support":
        _safe_render("Support", render_support_tab, state)

    else:
        st.header("🚧 Coming soon")
        st.info("This module will be added in the next steps of the build.")


def main():
    apply_layout()

    # Initialize database tables and run migrations on first run
    try:
        from .models import Base
        from .db import engine
        from sqlalchemy import text
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Run migration to add is_active column to existing users table
        try:
            with engine.connect() as conn:
                # Check if is_active column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='is_active'
                """))
                
                if result.fetchone() is None:
                    # Column doesn't exist, add it
                    log.info("Adding is_active column to users table...")
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL
                    """))
                    conn.commit()
                    
                    # Update existing users to be active
                    conn.execute(text("UPDATE users SET is_active = TRUE"))
                    conn.commit()
                    log.info("✅ is_active column added successfully")
        except Exception as migration_error:
            log.warning(f"Migration check: {migration_error}")
            
    except Exception as e:
        log.warning(f"Database initialization check: {e}")

    if not health_check():
        st.error("❌ Database connection FAILED. Check your .env and MySQL.")
        return

    user = st.session_state.get("auth_user")
    is_auth = st.session_state.get("is_authenticated", False)

    if not is_auth or not user:
        st.sidebar.title("RetailSight")
        st.sidebar.info("Please log in to continue.")
        render_login_tab()
        return

    show_logout_button()
    render_main_shell(user)


if __name__ == "__main__":
    main()
