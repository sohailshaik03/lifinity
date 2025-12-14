# ui/tabs/admin_tab.py
from __future__ import annotations

import streamlit as st

from ...logger import log
from ...repositories.shops_repo import ShopsRepository
from ...repositories.users_repo import create_user, get_user_by_email
from ...repositories import alerts_repo
from ...utils.security import hash_password


def render_admin_tab(state) -> None:
    """
    Admin tab for managing shops and users.
    """
    st.header("⚙️ Admin Panel")

    user = st.session_state.get("auth_user")
    if not user or user.get("role") != "admin":
        st.error("❌ You do not have permission to access this page.")
        return

    # Create tabs for different admin functions
    admin_tabs = st.tabs(["Manage Shops", "Manage Users", "Shop-User Assignment", "Alert Settings"])

    with admin_tabs[0]:
        _render_shops_management()

    with admin_tabs[1]:
        _render_users_management()

    with admin_tabs[2]:
        _render_shop_user_assignment()

    with admin_tabs[3]:
        _render_alert_settings()


def _render_shops_management():
    """Manage shops - create, view, edit, delete."""
    st.subheader("📍 Manage Shops")

    action = st.radio(
        "Choose action", ["View Shops", "Create Shop", "Update Shop", "Delete Shop"]
    )

    if action == "View Shops":
        shops = ShopsRepository.get_all_shops()
        if shops:
            st.dataframe(shops, use_container_width=True)
        else:
            st.info("No shops found.")

    elif action == "Create Shop":
        with st.form("create_shop_form"):
            shop_name = st.text_input(
                "Shop Name", placeholder="e.g., Main Street Store"
            )
            address_line1 = st.text_input(
                "Address Line 1", placeholder="e.g., 123 Main Street"
            )
            city = st.text_input("City", placeholder="e.g., London")
            postcode = st.text_input("Postcode", placeholder="e.g., SW1A 1AA")
            country = st.text_input("Country", placeholder="e.g., United Kingdom")

            if st.form_submit_button("➕ Create Shop"):
                if not shop_name.strip():
                    st.error("Shop name is required.")
                else:
                    shop_id = ShopsRepository.create_shop(
                        shop_name, address_line1, city, postcode, country
                    )
                    if shop_id:
                        st.success(f"✅ Shop '{shop_name}' created successfully!")
                        log.info("Shop created by admin: %s", shop_name)
                    else:
                        st.error("Failed to create shop.")

    elif action == "Update Shop":
        shops = ShopsRepository.get_all_shops()
        if not shops:
            st.info("No shops available to update.")
            return

        shop_options = {shop["name"]: shop["id"] for shop in shops}
        selected_shop_name = st.selectbox("Select Shop", shop_options.keys())
        selected_shop_id = shop_options[selected_shop_name]

        # Get current shop details
        shop = ShopsRepository.get_shop_by_id(selected_shop_id)

        with st.form("update_shop_form"):
            new_name = st.text_input(
                "Shop Name", value=shop.get("name", "") if shop else ""
            )
            new_address = st.text_input(
                "Address Line 1", value=shop.get("address_line1", "") if shop else ""
            )
            new_city = st.text_input("City", value=shop.get("city", "") if shop else "")
            new_postcode = st.text_input(
                "Postcode", value=shop.get("postcode", "") if shop else ""
            )
            new_country = st.text_input(
                "Country", value=shop.get("country", "") if shop else ""
            )

            if st.form_submit_button("✏️ Update Shop"):
                success = ShopsRepository.update_shop(
                    selected_shop_id,
                    new_name,
                    new_address,
                    new_city,
                    new_postcode,
                    new_country,
                )
                if success:
                    st.success("✅ Shop updated successfully!")
                    log.info("Shop updated by admin: ID %s", selected_shop_id)
                else:
                    st.error("Failed to update shop.")

    elif action == "Delete Shop":
        shops = ShopsRepository.get_all_shops()
        if not shops:
            st.info("No shops available to delete.")
            return

        shop_options = {shop["name"]: shop["id"] for shop in shops}
        selected_shop_name = st.selectbox("Select Shop to Delete", shop_options.keys())
        selected_shop_id = shop_options[selected_shop_name]

        if st.button("🗑️ Delete Shop", type="secondary"):
            success = ShopsRepository.delete_shop(selected_shop_id)
            if success:
                st.success("✅ Shop deleted successfully!")
                log.info("Shop deleted by admin: ID %s", selected_shop_id)
            else:
                st.error("Failed to delete shop.")


def _render_users_management():
    """Manage users - create, view."""
    st.subheader("👥 Manage Users")

    action = st.radio("Choose action", ["Create User", "View Users"])

    if action == "Create User":
        with st.form("create_user_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            full_name = st.text_input("Full Name", placeholder="John Doe")
            password = st.text_input(
                "Password", type="password", placeholder="Secure password"
            )
            # Offer roles that exist in the DB enum (now includes 'manager')
            role = st.selectbox("Role", ["owner", "manager", "staff", "admin"], index=0)

            if st.form_submit_button("➕ Create User"):
                if not email or not full_name or not password:
                    st.error("All fields are required.")
                elif "@" not in email:
                    st.error("Please enter a valid email.")
                else:
                    # Check if user already exists
                    existing_user = get_user_by_email(email)
                    if existing_user:
                        st.error(f"User with email '{email}' already exists.")
                    else:
                        password_hash = hash_password(password)
                        user_id = create_user(email, full_name, password_hash, role)
                        if user_id:
                            st.success(f"✅ User '{full_name}' created successfully!")
                            log.info("User created by admin: %s", email)
                        else:
                            st.error("Failed to create user.")

    elif action == "View Users":
        from repositories.users_repo import list_users

        st.subheader("All Users")

        users = list_users()
        if not users:
            st.info("No users found in the database.")
        else:
            # optional filters
            cols = st.columns([2, 2, 1])
            with cols[0]:
                email_q = st.text_input("Filter by email", value="")
            with cols[1]:
                roles = ["all"] + sorted(
                    {u.get("role") for u in users if u.get("role")}
                )
                role_filter = st.selectbox("Role", roles, index=0)

            # apply filters
            filtered = users
            if email_q:
                filtered = [
                    u
                    for u in filtered
                    if email_q.lower() in (u.get("email") or "").lower()
                ]
            if role_filter and role_filter != "all":
                filtered = [u for u in filtered if u.get("role") == role_filter]

            st.dataframe(filtered, use_container_width=True)

            # export
            import pandas as pd

            df = pd.DataFrame(filtered)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export CSV", data=csv, file_name="users.csv", mime="text/csv"
            )

            # --- Manage selected user ---
            st.markdown("---")
            st.subheader("Manage Selected User")
            from repositories.users_repo import deactivate_user, update_user

            user_map = {f"{u['email']} ({u['role']})": u for u in filtered}
            if user_map:
                sel = st.selectbox("Select user to manage", list(user_map.keys()))
                selected = user_map[sel]

                with st.form("edit_user_form"):
                    edit_full_name = st.text_input(
                        "Full name", value=selected.get("full_name") or ""
                    )
                    edit_role = st.selectbox(
                        "Role",
                        sorted({u.get("role") for u in users if u.get("role")}),
                        index=(
                            list(
                                sorted({u.get("role") for u in users if u.get("role")})
                            ).index(selected.get("role"))
                            if selected.get("role")
                            in sorted({u.get("role") for u in users if u.get("role")})
                            else 0
                        ),
                    )
                    edit_active = st.checkbox(
                        "Is active", value=bool(selected.get("is_active"))
                    )
                    new_password = st.text_input(
                        "Set new password (leave blank to keep)", type="password"
                    )

                    if st.form_submit_button("💾 Save changes"):
                        pwd_hash = None
                        if new_password:
                            from utils.security import hash_password as _hash

                            pwd_hash = _hash(new_password)

                        ok = update_user(
                            selected["id"],
                            full_name=edit_full_name,
                            role=edit_role,
                            password_hash=pwd_hash if pwd_hash else None,
                            is_active=edit_active,
                        )
                        if ok:
                            st.success("✅ User updated")
                        else:
                            st.error("Failed to update user.")

                # Deactivate flow with explicit confirmation
                if st.button("🗑️ Deactivate user", key=f"del_btn_{selected['id']}"):
                    st.session_state["confirm_deactivate_user"] = selected["id"]

                if st.session_state.get("confirm_deactivate_user") == selected["id"]:
                    st.warning(
                        f"Are you sure you want to deactivate {selected.get('email')}? This will prevent the user from logging in."
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(
                            "Confirm Deactivate", key=f"confirm_del_{selected['id']}"
                        ):
                            if deactivate_user(selected["id"]):
                                st.success("User deactivated")
                                # clear confirmation flag
                                del st.session_state["confirm_deactivate_user"]
                            else:
                                st.error("Failed to deactivate user")
                    with c2:
                        if st.button("Cancel", key=f"cancel_del_{selected['id']}"):
                            if "confirm_deactivate_user" in st.session_state:
                                del st.session_state["confirm_deactivate_user"]


def _render_shop_user_assignment():
    """Assign or remove users from shops."""
    st.subheader("🔗 Shop-User Assignment")

    action = st.radio("Choose action", ["Assign User to Shop", "Remove User from Shop"])

    shops = ShopsRepository.get_all_shops()
    if not shops:
        st.warning("No shops available. Please create a shop first.")
        return

    shop_options = {shop["name"]: shop["id"] for shop in shops}

    if action == "Assign User to Shop":
        with st.form("assign_form"):
            selected_shop_name = st.selectbox("Select Shop", shop_options.keys())
            selected_shop_id = shop_options[selected_shop_name]

            email = st.text_input("User Email")

            if st.form_submit_button("➕ Assign User"):
                if not email:
                    st.error("Email is required.")
                else:
                    user = get_user_by_email(email)
                    if not user:
                        st.error(f"User with email '{email}' not found.")
                    else:
                        success = ShopsRepository.assign_user_to_shop(
                            user["id"], selected_shop_id
                        )
                        if success:
                            st.success(
                                f"✅ User '{email}' assigned to shop '{selected_shop_name}'!"
                            )
                            log.info(
                                "User assigned to shop by admin: user %s, shop %s",
                                user["id"],
                                selected_shop_id,
                            )
                        else:
                            st.error("Failed to assign user to shop.")

    elif action == "Remove User from Shop":
        with st.form("remove_form"):
            selected_shop_name = st.selectbox("Select Shop", shop_options.keys())
            selected_shop_id = shop_options[selected_shop_name]

            email = st.text_input("User Email")

            if st.form_submit_button("🗑️ Remove User"):
                if not email:
                    st.error("Email is required.")
                else:
                    user = get_user_by_email(email)
                    if not user:
                        st.error(f"User with email '{email}' not found.")
                    else:
                        success = ShopsRepository.remove_user_from_shop(
                            user["id"], selected_shop_id
                        )
                        if success:
                            st.success(
                                f"✅ User '{email}' removed from shop '{selected_shop_name}'!"
                            )
                            log.info(
                                "User removed from shop by admin: user %s, shop %s",
                                user["id"],
                                selected_shop_id,
                            )
                        else:
                            st.error("Failed to remove user from shop.")


def _render_alert_settings():
    """Configure alert notifications (email/SMS) per shop."""
    st.subheader("🔔 Alert settings")
    
    shops = ShopsRepository.get_all_shops()
    if not shops:
        st.info("No shops found.")
        return
    
    shop_names = {s["id"]: s.get("name", f"Shop {s['id']}") for s in shops}
    selected_shop_id = st.selectbox(
        "Select shop",
        options=list(shop_names.keys()),
        format_func=lambda x: shop_names[x],
    )
    
    try:
        # Get current settings or create default
        settings = alerts_repo.get_alert_settings(selected_shop_id)
        if not settings:
            settings = {
                "shop_id": selected_shop_id,
                "email_enabled": True,
                "sms_enabled": False,
                "alert_days_threshold": 7,
                "alert_emails": "",
                "alert_phones": "",
            }
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            email_enabled = st.checkbox(
                "Enable email alerts",
                value=settings.get("email_enabled", True)
            )
        with col2:
            sms_enabled = st.checkbox(
                "Enable SMS alerts",
                value=settings.get("sms_enabled", False)
            )
        
        threshold_days = st.slider(
            "Alert threshold (days before expiry)",
            min_value=1,
            max_value=30,
            value=settings.get("alert_days_threshold", 7)
        )
        
        st.markdown("---")
        
        if email_enabled:
            st.markdown("#### Email Recipients")
            st.caption("Enter email addresses, one per line")
            emails_text = st.text_area(
                "Email addresses",
                value=settings.get("alert_emails", ""),
                height=120,
                key="alert_emails",
            )
        else:
            emails_text = ""
        
        if sms_enabled:
            st.markdown("#### SMS Recipients")
            st.caption("Enter phone numbers (E.164 format: +441234567890), one per line")
            phones_text = st.text_area(
                "Phone numbers",
                value=settings.get("alert_phones", ""),
                height=120,
                key="alert_phones",
            )
        else:
            phones_text = ""
        
        st.markdown("---")
        
        if st.button("💾 Save alert settings"):
            try:
                alerts_repo.save_alert_settings(
                    shop_id=selected_shop_id,
                    email_enabled=email_enabled,
                    sms_enabled=sms_enabled,
                    alert_days_threshold=threshold_days,
                    alert_emails=emails_text,
                    alert_phones=phones_text,
                )
                st.success("✅ Alert settings saved!")
                log.info(f"Alert settings updated for shop {selected_shop_id}")
            except Exception as e:
                log.exception("Save alert settings error")
                st.error(f"Failed to save settings: {e}")
    
    except Exception as e:
        log.exception("Alert settings render error")
        st.error(f"Error loading alert settings: {e}")
