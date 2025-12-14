from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ...repositories.products_repo import (
    get_products_by_shop,
    get_expiring_products,
    add_expiry_record,
    record_waste,
    get_waste_records,
    get_discount_rules,
    create_discount_rule,
)
from ...services.expiry_service import ExpiryService
from ...services.bulk_import_service import BulkImportService
from ...services.discount_report_service import DiscountReportService
from ...logger import log


def render_expiry_tab(state) -> None:
    st.title("🕐 Expiry & Waste Management")

    user = st.session_state.get("auth_user")
    shop = st.session_state.get("current_shop")

    if not user or not shop:
        st.error("Login and select a shop first.")
        return

    shop_id = shop["id"]
    user_id = user["id"]

    tabs = st.tabs(
        [
            "Expiring Products",
            "Record Waste",
            "Discount Rules",
            "Waste Analytics",
            "Bulk Import",
            "Discount Reports",
        ]
    )

    # --- Tab 1: Expiring Products ---
    with tabs[0]:
        st.markdown("### Products expiring soon")
        threshold = st.slider("Show products expiring within (days)", 1, 90, 30)
        expiring = get_expiring_products(shop_id, days_threshold=threshold)

        if not expiring:
            st.info("No products expiring soon.")
        else:
            # Display with discount calculation
            rows = []
            for prod in expiring:
                disc = ExpiryService.calculate_discount(
                    shop_id,
                    prod.get("days_left", 0),
                    prod.get("quantity_remaining", 0),
                    prod.get("selling_price", 0),
                )
                rows.append(
                    {
                        "SKU": prod["sku"],
                        "Product": prod["name"],
                        "Qty": prod.get("quantity_remaining", 0),
                        "Days Left": prod.get("days_left", 0),
                        "Base Price": prod.get("selling_price", 0),
                        "Discount %": disc["discount_percent"],
                        "Sale Price": disc["discounted_price"],
                        "Reason": disc["reason"],
                        "Expiry Date": prod.get("expiry_date"),
                    }
                )

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # Mark as wasted
            st.markdown("#### Mark product as wasted")
            prod_idx = st.selectbox("Select product", range(len(expiring)))
            selected_prod = expiring[prod_idx]
            qty = st.number_input("Quantity", min_value=1, value=1)
            reason = st.selectbox("Reason", ["Expired", "Damaged", "Recall", "Other"])

            if st.button("Record waste"):
                try:
                    waste_id = record_waste(
                        product_id=selected_prod["id"],
                        quantity_wasted=qty,
                        reason=reason,
                        expiry_record_id=selected_prod.get("expiry_id"),
                        user_id=user_id,
                    )
                    if waste_id:
                        st.success(f"Recorded waste: {qty} units")
                    else:
                        st.error("Failed to record waste.")
                except Exception as e:
                    log.exception("Record waste error")
                    st.error(str(e))

    # --- Tab 2: Record Waste ---
    with tabs[1]:
        st.markdown("### Manually record waste")
        products = get_products_by_shop(shop_id)

        if not products:
            st.info("No products in this shop.")
        else:
            prod_names = {p["id"]: p["name"] for p in products}
            selected_prod_id = st.selectbox("Product", list(prod_names.keys()), format_func=lambda x: prod_names[x])
            qty = st.number_input("Quantity wasted", min_value=1, value=1)
            reason = st.selectbox("Reason", ["Expired", "Damaged", "Recall", "Returned", "Other"])

            if st.button("Submit waste record"):
                try:
                    waste_id = record_waste(
                        product_id=selected_prod_id,
                        quantity_wasted=qty,
                        reason=reason,
                        user_id=user_id,
                    )
                    if waste_id:
                        st.success(f"Waste recorded (ID: {waste_id})")
                    else:
                        st.error("Failed to record waste.")
                except Exception as e:
                    log.exception("Record waste error")
                    st.error(str(e))

    # --- Tab 3: Discount Rules ---
    with tabs[2]:
        st.markdown("### Discount rules (dynamic pricing)")
        rules = get_discount_rules(shop_id)

        if rules:
            st.markdown("#### Current rules")
            rule_df = pd.DataFrame(rules)
            st.dataframe(rule_df[["name", "days_left_min", "days_left_max", "quantity_min", "discount_percent"]], use_container_width=True)

        st.markdown("#### Add new rule")
        col1, col2 = st.columns(2)
        with col1:
            rule_name = st.text_input("Rule name (e.g., 'Yellow Sticker 3-5 days')")
            days_min = st.number_input("Days left (minimum)", min_value=0, value=3)
            qty_min = st.number_input("Quantity minimum", min_value=1, value=1)
        with col2:
            days_max = st.number_input("Days left (maximum)", min_value=0, value=5)
            discount = st.number_input("Discount %", min_value=0, max_value=100, value=10)

        if st.button("Create rule"):
            try:
                rule_id = create_discount_rule(
                    shop_id=shop_id,
                    name=rule_name,
                    days_left_min=days_min,
                    days_left_max=days_max,
                    quantity_min=qty_min,
                    discount_percent=discount,
                )
                if rule_id:
                    st.success(f"Discount rule created (ID: {rule_id})")
                    st.rerun()
                else:
                    st.error("Failed to create rule.")
            except Exception as e:
                log.exception("Create discount rule error")
                st.error(str(e))

    # --- Tab 4: Waste Analytics ---
    with tabs[3]:
        st.markdown("### Waste analytics")
        days_lookback = st.slider("Last N days", 1, 365, 7)
        waste_records = get_waste_records(shop_id, days=days_lookback)

        if not waste_records:
            st.info("No waste records in this period.")
        else:
            waste_df = pd.DataFrame(waste_records)
            summary = ExpiryService.get_waste_summary(waste_records)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total units wasted", summary["total_wasted"])
            with col2:
                st.metric("Records count", len(waste_records))

            st.markdown("#### Waste by reason")
            reason_df = pd.DataFrame(
                list(summary["by_reason"].items()),
                columns=["Reason", "Qty"],
            )
            st.bar_chart(reason_df.set_index("Reason"))

    # --- Tab 5: Bulk Import ---
    with tabs[4]:
        st.markdown("### Bulk product import")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download template CSV"):
                try:
                    importer = BulkImportService()
                    template_csv = importer.generate_csv_template()
                    st.download_button(
                        label="template.csv",
                        data=template_csv,
                        file_name="products_template.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Template generation failed: {e}")
        
        with col2:
            st.markdown("**Required columns:** sku, name, cost_price, selling_price")

        st.markdown("---")
        
        uploaded_file = st.file_uploader("Upload CSV", type="csv")
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write(f"File preview ({len(df)} rows):")
                st.dataframe(df.head(10))
                
                include_expiry = st.checkbox(
                    "Include expiry records (expiry_date, batch_number, qty_received)",
                    value=False
                )
                
                if st.button("🚀 Import products"):
                    with st.spinner("Importing..."):
                        importer = BulkImportService()
                        result = importer.import_products_from_csv(
                            df,
                            shop_id=shop_id,
                            include_expiry=include_expiry,
                        )
                    
                    if result["success"]:
                        st.success(f"✓ {result['created']} products created")
                        
                        if result["warnings"]:
                            st.warning(f"⚠️ {len(result['warnings'])} warnings:")
                            for warn in result["warnings"]:
                                st.caption(warn)
                        
                        if result["errors"]:
                            st.error(f"❌ {len(result['errors'])} errors:")
                            for err in result["errors"]:
                                st.caption(err)
                    else:
                        st.error("Import failed:")
                        for err in result.get("errors", []):
                            st.caption(err)

            except Exception as e:
                log.exception("Bulk import error")
                st.error(f"Failed to process file: {e}")

    # --- Tab 6: Discount Reports ---
    with tabs[5]:
        st.markdown("### Discount impact reports")
        
        days_lookback = st.slider("Analyze last N days", 1, 365, 30, key="discount_report_days")
        
        try:
            report_svc = DiscountReportService()
            
            col1, col2, col3 = st.columns(3)
            
            # Applied discounts
            applied = report_svc.get_discount_applied_records(shop_id, days=days_lookback)
            with col1:
                st.metric("Discount transactions", len(applied))
            
            # Revenue impact
            impact = report_svc.calculate_discount_impact(applied)
            with col2:
                st.metric("Revenue forgone (£)", f"{impact.get('total_revenue_forgone', 0):.2f}")
            
            with col3:
                st.metric("Avg discount %", f"{impact.get('avg_discount_pct', 0):.1f}%")
            
            st.markdown("---")
            
            # By rule breakdown
            st.markdown("#### Discount impact by rule")
            by_rule = report_svc.get_discount_by_rule(shop_id, days=days_lookback)
            
            if by_rule:
                rule_list = []
                for rule_name, data in by_rule.items():
                    rule_list.append({
                        "rule_name": rule_name,
                        "units": data["units"],
                        "revenue_forgone": data["revenue_forgone"],
                        "avg_discount_pct": data["avg_discount_pct"],
                    })
                rule_df = pd.DataFrame(rule_list)
                st.dataframe(
                    rule_df,
                    use_container_width=True,
                    hide_index=True,
                )
                
                # Chart: revenue forgone by rule
                if len(rule_df) > 0 and "revenue_forgone" in rule_df.columns:
                    chart_df = rule_df[["rule_name", "revenue_forgone"]].set_index("rule_name")
                    st.bar_chart(chart_df)
            else:
                st.info("No discounts applied in this period.")
            
            st.markdown("---")
            
            # Expiring vs wasted comparison
            st.markdown("#### Expiring vs Wasted (comparison)")
            expiry_waste = report_svc.get_expiring_vs_wasted(shop_id, days=days_lookback)
            
            if expiry_waste:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Products at risk (expiring)", expiry_waste.get("expiry", {}).get("total_batches", 0))
                with col_b:
                    st.metric("Products wasted", expiry_waste.get("waste", {}).get("total_events", 0))
                
                # Bar chart comparison
                expiring_qty = expiry_waste.get("expiry", {}).get("remaining_qty", 0)
                wasted_qty = expiry_waste.get("waste", {}).get("total_wasted_qty", 0)
                if expiring_qty or wasted_qty:
                    comparison_data = {
                        "Expiring": expiring_qty,
                        "Wasted": wasted_qty,
                    }
                    st.bar_chart(pd.DataFrame([comparison_data]).T)
            else:
                st.info("No expiry/waste data in this period.")
        
        except Exception as e:
            log.exception("Discount report error")
            st.error(f"Failed to generate report: {e}")
