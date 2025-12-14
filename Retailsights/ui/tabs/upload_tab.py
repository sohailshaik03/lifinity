# ui/tabs/upload_tab.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ...logger import log
from ...services.analytics_service import AnalyticsService, load_sales_for_period
from ...services.data_analyst_service import DataAnalystService
from ...services.storage_service import Storage
from ...services.celery_app import celery_app
from ...services import report_tasks
from ...services.subscription_service import SubscriptionService
from ...repositories.subscription_repo import SubscriptionRepo
from io import BytesIO
import time


def _render_file_preview(df: pd.DataFrame) -> None:
    """
    Small helper: show a preview + simple analytics for the uploaded file only.
    This is intentionally lightweight – full history/manager analytics happen
    via the DB + other tabs.
    """
    st.markdown("### 📄 Cleaned data preview")
    st.dataframe(df.head(50), use_container_width=True)

    # Guard: need datetime + revenue for charts
    if "datetime" not in df.columns or "revenue" not in df.columns:
        st.info("Not enough fields for charts (datetime / revenue missing).")
        return

    df = df.copy()
    df["date_only"] = df["datetime"].dt.date

    # 🔹 Daily revenue
    st.markdown("### 📈 Daily revenue (this file only)")
    by_day = df.groupby("date_only")["revenue"].sum().reset_index()
    if not by_day.empty:
        fig = px.line(
            by_day,
            x="date_only",
            y="revenue",
            title="Daily revenue from this upload",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No revenue data to plot.")

    # 🔹 Top products
    st.markdown("### 🏆 Top products in this file")
    top_products = (
        df.groupby("product")
        .agg(units_sold=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    if not top_products.empty:
        st.dataframe(top_products, use_container_width=True)
        fig_top = px.bar(
            top_products,
            x="product",
            y="revenue",
            title="Top 10 products (this upload)",
        )
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("No product breakdown available.")


def render_upload_tab(state) -> None:
    """
    Upload & Analyse tab.

    Flow:
    1. Check user + shop context
    2. Check subscription tier and enforce limits
    3. Upload CSV / Excel
    4. Normalise + preprocess via AnalyticsService
    5. Show preview + quick charts
    6. Save to DB (uploaded_files, sales_transactions, sales_lines)
    """
    st.title("📤 Upload & Analyse")

    # ------------------------------------------------------------------
    # 1) Ensure auth + shop context exist
    # ------------------------------------------------------------------
    user = st.session_state.get("auth_user")
    current_shop = st.session_state.get("current_shop")

    if not user:
        st.error("You are not logged in. Please log in again.")
        return

    if not current_shop:
        st.warning("No shop selected. Please choose a shop from the sidebar.")
        return

    shop_id = current_shop["id"]
    user_id = user["id"]
    
    # ------------------------------------------------------------------
    # 1.5) Check subscription tier and display badge
    # ------------------------------------------------------------------
    subscription_service = SubscriptionService()
    subscription_repo = SubscriptionRepo()
    
    try:
        current_sub = subscription_repo.get_user_subscription(user_id)
        if not current_sub:
            # Create default BASIC subscription with 30-day trial
            subscription_repo.create_subscription(user_id, 'basic', trial_days=30)
            current_sub = subscription_repo.get_user_subscription(user_id)
        
        current_tier = current_sub['tier'] if current_sub else 'basic'
        tier_limits = subscription_service.get_tier_limits(current_tier)
        
        # Display tier badge
        tier_badges = {
            'basic': '🆓 BASIC (Free)',
            'premium': '⭐ PREMIUM',
            'ultra_premium': '💎 ULTRA PREMIUM'
        }
        tier_display = tier_badges.get(current_tier, current_tier.upper())
        
        st.markdown(f"**Current Plan**: {tier_display}")
        
        # Show limits
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"📁 Max file size: {tier_limits['max_file_size_mb']} MB")
        with col2:
            st.caption(f"📊 Max rows: {tier_limits['max_rows']:,}")
        with col3:
            if st.button("🚀 Upgrade Plan", key="upgrade_from_upload"):
                st.switch_page("pages/subscription.py")
        
        st.markdown("---")
        
    except Exception as e:
        log.exception("Error checking subscription")
        st.warning("Unable to verify subscription status. Using BASIC tier limits.")
        current_tier = 'basic'
        tier_limits = subscription_service.get_tier_limits('basic')

    # Keep track of already-saved uploads in this session to avoid
    # accidental double-imports.
    if "saved_upload_keys" not in st.session_state:
        st.session_state["saved_upload_keys"] = set()

    # ------------------------------------------------------------------
    # 2) File upload with tier-based validation
    # ------------------------------------------------------------------
    st.markdown("### 📤 Upload Your Data")
    st.info(f"💡 Your plan allows files up to **{tier_limits['max_file_size_mb']} MB** with up to **{tier_limits['max_rows']:,} rows**")
    
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel export from your POS",
        type=["csv", "xlsx", "xls"],
        key="upload_file",
        help="Supported: CSV, XLSX, XLS. "
        "Columns like date/time/product/quantity/price/category will be auto-detected.",
    )

    if not uploaded_file:
        st.info("Drag a file here or click **Browse files** to get started.")
        
        # Show what's possible with upgrade
        if current_tier == 'basic':
            st.markdown("---")
            st.markdown("### 🚀 Want More?")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **Premium Plan** ($49/mo)
                - ✅ 100 MB file size
                - ✅ 100,000 rows per file
                - ✅ Multi-file analysis
                - ✅ Advanced analytics
                - ✅ Power BI export
                """)
            with col2:
                st.markdown("""
                **Ultra Premium** ($199/mo)
                - ✅ 1 GB file size
                - ✅ 10M rows per file
                - ✅ AI-powered predictions
                - ✅ Custom ML models
                - ✅ Real-time processing
                """)
            
            if st.button("View All Plans", type="primary"):
                st.switch_page("pages/subscription.py")
        
        return
    
    # ------------------------------------------------------------------
    # 2.5) Validate file size against tier limits
    # ------------------------------------------------------------------
    file_size_mb = uploaded_file.size / (1024 * 1024)
    
    if file_size_mb > tier_limits['max_file_size_mb']:
        st.error(f"❌ **File too large!** Your file is {file_size_mb:.1f} MB but your plan allows max {tier_limits['max_file_size_mb']} MB")
        
        # Show upgrade prompt
        st.markdown("### 🚀 Upgrade to Process Larger Files")
        
        if current_tier == 'basic':
            st.info(f"✅ **Premium Plan** allows up to 100 MB files - only $49/month")
        elif current_tier == 'premium':
            st.info(f"✅ **Ultra Premium Plan** allows up to 1 GB files - only $199/month")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🚀 Upgrade Now", type="primary", use_container_width=True):
                st.switch_page("pages/subscription.py")
        with col2:
            st.caption("Upgrade instantly - no credit card required for trial")
        
        return

    # ------------------------------------------------------------------
    # 3) INTELLIGENT DATA ANALYSIS & CLEANING (Like a Senior Analyst)
    # ------------------------------------------------------------------
    st.markdown("### 🧠 Intelligent Data Analysis")
    st.info("📊 **AI-Powered Analysis**: Our system automatically detects data quality issues, cleans messy data, and provides professional insights like a senior data analyst would.")

    try:
        raw_df = AnalyticsService.load_file(uploaded_file)
    except ValueError as e:
        st.error(str(e))
        return
    except Exception as e:
        log.exception("Unexpected error while loading file")
        st.error(
            "Unexpected error while reading the file. Please check the logs or contact support."
        )
        return

    if raw_df.empty:
        st.error("The uploaded file appears to be empty.")
        return

    st.write(f"📄 **Original file**: {len(raw_df):,} rows × {len(raw_df.columns)} columns")
    
    # ------------------------------------------------------------------
    # 3.5) Validate row count against tier limits
    # ------------------------------------------------------------------
    if len(raw_df) > tier_limits['max_rows']:
        st.error(f"❌ **Too many rows!** Your file has {len(raw_df):,} rows but your plan allows max {tier_limits['max_rows']:,} rows")
        
        # Show upgrade prompt
        st.markdown("### 🚀 Upgrade to Process More Data")
        
        if current_tier == 'basic':
            st.info(f"✅ **Premium Plan** allows up to 100,000 rows - only $49/month")
        elif current_tier == 'premium':
            st.info(f"✅ **Ultra Premium Plan** allows up to 10 million rows - only $199/month")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🚀 Upgrade Now", type="primary", use_container_width=True, key="upgrade_rows"):
                st.switch_page("pages/subscription.py")
        with col2:
            st.caption("Process unlimited data with our enterprise plans")
        
        return

    # ------------------------------------------------------------------
    # 🧠 SENIOR ANALYST MODE: Automatic analysis and cleaning
    # ------------------------------------------------------------------
    with st.spinner("🔍 Analyzing data quality and cleaning messy data..."):
        cleaned_df, analyst_report = DataAnalystService.analyze_and_clean(raw_df)

    # Show professional analysis report
    st.markdown("---")
    st.markdown("### 📋 Data Quality Report")
    
    # Quality score with color coding
    quality_score = analyst_report["quality_assessment"]["quality_score"]
    if quality_score >= 90:
        score_color = "green"
        score_emoji = "🟢"
    elif quality_score >= 70:
        score_color = "orange"
        score_emoji = "🟡"
    else:
        score_color = "red"
        score_emoji = "🔴"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Quality Score", f"{score_emoji} {quality_score:.1f}%")
    with col2:
        st.metric("Rows Processed", f"{len(cleaned_df):,}")
    with col3:
        duplicates = analyst_report["quality_assessment"]["duplicates"]
        st.metric("Duplicates Removed", f"{duplicates:,}")

    # Cleaning actions taken
    if analyst_report["cleaning_actions"]:
        with st.expander("🧹 Automatic Cleaning Actions", expanded=True):
            for action in analyst_report["cleaning_actions"]:
                st.write(f"- {action}")

    # Column detection
    if analyst_report["column_detection"]:
        with st.expander("🎯 Intelligent Column Detection"):
            st.write("**Detected column types:**")
            col_map = analyst_report["column_detection"]
            for col, col_type in col_map.items():
                st.write(f"- `{col}` → **{col_type}**")

    # Business insights
    if analyst_report["insights"]:
        st.markdown("### 💡 Business Insights")
        for insight in analyst_report["insights"]:
            st.markdown(insight)

    # Recommendations
    if analyst_report["recommendations"]:
        st.markdown("### 🎯 Analyst Recommendations")
        for rec in analyst_report["recommendations"]:
            st.markdown(rec)

    st.markdown("---")

    # Check if this is retail sales data or just general business data
    # Detect if we have the core retail columns needed for sales analysis
    cleaned_cols = [col.lower().strip() for col in cleaned_df.columns]
    has_retail_columns = (
        any("date" in col for col in cleaned_cols) and
        any(x in col for col in cleaned_cols for x in ["product", "item", "sku"]) and
        any(x in col for col in cleaned_cols for x in ["qty", "quantity", "units"]) and
        any(x in col for col in cleaned_cols for x in ["price", "amount", "revenue"])
    )

    if has_retail_columns:
        # This looks like retail sales data - proceed with standard normalization
        st.info("🏪 Detected retail sales data format - preparing for sales analysis...")
        norm_df = AnalyticsService.normalize(cleaned_df)
        df = AnalyticsService.preprocess(norm_df)

        if df.empty:
            st.error(
                "No usable rows after cleaning. Check your file format and required columns."
            )
            return

        st.success(f"✅ **Data ready for analysis**: {len(df):,} clean rows with all required fields!")

        # Preview & quick analytics for this upload only
        _render_file_preview(df)
    else:
        # This is general business data - show cleaned version only
        st.info("📊 General business data detected - showing cleaned data preview")
        st.success(f"✅ **Data cleaned successfully**: {len(cleaned_df):,} rows × {len(cleaned_df.columns)} columns")
        
        # Show preview of cleaned data
        st.markdown("### 👁️ Cleaned Data Preview")
        st.dataframe(cleaned_df.head(100), use_container_width=True)
        
        # Offer download of cleaned data
        st.markdown("### 💾 Download Cleaned Data")
        csv_data = cleaned_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv_data,
            file_name=f"cleaned_{uploaded_file.name}",
            mime="text/csv"
        )
        
        st.info("💡 **Note**: This file doesn't contain standard retail sales columns (date, product, quantity, price). Only data quality analysis and cleaning was performed. To use full sales analytics features, upload a file with retail sales data.")
        return

    # ------------------------------------------------------------------
    # 4.5) In-memory analytics, forecasting and exports (before saving)
    # ------------------------------------------------------------------
    st.markdown("### 📊 Analytics & Exports (this upload)")

    # Summary KPIs
    summary = AnalyticsService.compute_summary(df)
    cols = st.columns(4)
    cols[0].metric("Total revenue", f"{summary['total_revenue']:.2f}")
    cols[1].metric("Total items", f"{summary['total_items']:.0f}")
    cols[2].metric("Transactions", f"{summary['num_transactions']}")
    cols[3].metric("Avg basket", f"{summary['avg_basket']:.2f}")

    # Time series plot
    ts = AnalyticsService.aggregate_time_series(df, freq="D")
    if not ts.empty:
        fig = px.line(ts, x="datetime", y="revenue", title="Daily revenue (this upload)")
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # TIER-GATED FEATURES
    # ------------------------------------------------------------------
    
    # Forecast controls - PREMIUM+ only
    st.markdown("#### 🔮 Forecasting")
    
    if current_tier == 'basic':
        st.info("🔒 **Forecasting** is available on Premium and Ultra Premium plans")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🚀 Unlock Forecasting", type="primary", key="unlock_forecast"):
                st.switch_page("pages/subscription.py")
        with col2:
            st.caption("Get 30-day forecasts with Premium ($49/mo)")
    else:
        # Premium: 30 days, Ultra Premium: 365 days
        max_periods = 30 if current_tier == 'premium' else 365
        periods = st.number_input(
            f"Forecast horizon (days) - Max: {max_periods}", 
            min_value=1, 
            max_value=max_periods, 
            value=min(14, max_periods)
        )
        
        if st.button("Run forecast"):
            with st.spinner("Running forecast…"):
                forecast_df = AnalyticsService.forecast_sales(df, periods=periods)
                if not forecast_df.empty:
                    figf = px.line(forecast_df, x="datetime", y="forecast", title="Forecasted daily revenue")
                    st.plotly_chart(figf, use_container_width=True)
                    st.dataframe(forecast_df.head(50), use_container_width=True)
                    
                    # Track usage
                    try:
                        subscription_repo.track_usage(user_id, 'forecast_runs', 1)
                    except:
                        pass

    # Exports
    st.markdown("#### ⤓ Download exports")
    csv_bytes = AnalyticsService.export_csv_bytes(df)
    st.download_button("Download CSV", csv_bytes, file_name=f"upload_{uploaded_file.name}.csv", mime="text/csv")

    pdf_bytes = AnalyticsService.export_pdf_bytes(df, summary=summary)
    st.download_button("Download PDF report", pdf_bytes, file_name=f"upload_{uploaded_file.name}.pdf", mime="application/pdf")

    # Power BI Export - PREMIUM+ only
    st.markdown("#### 📊 Power BI Export")
    
    if current_tier == 'basic':
        st.info("🔒 **Power BI Export** is available on Premium and Ultra Premium plans")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🚀 Unlock Power BI Export", type="primary", key="unlock_powerbi"):
                st.switch_page("pages/subscription.py")
        with col2:
            st.caption("Export optimized data for Power BI dashboards")
    else:
        if st.button("📤 Export for Power BI", type="secondary"):
            with st.spinner("Preparing Power BI export..."):
                try:
                    # Create Power BI optimized export
                    powerbi_csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Power BI File",
                        powerbi_csv,
                        file_name=f"powerbi_{uploaded_file.name}.csv",
                        mime="text/csv",
                        key="download_powerbi"
                    )
                    st.success("✅ Power BI export ready!")
                    
                    # Track usage
                    try:
                        subscription_repo.track_usage(user_id, 'powerbi_exports', 1)
                    except:
                        pass
                        
                    # Ultra Premium gets DAX measures
                    if current_tier == 'ultra_premium':
                        st.markdown("""
                        **📋 Suggested DAX Measures:**
                        ```dax
                        Total Revenue = SUM(Sales[revenue])
                        Average Basket = AVERAGE(Sales[revenue])
                        Total Transactions = DISTINCTCOUNT(Sales[transaction_id])
                        ```
                        """)
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

    # Cloud exports
    st.markdown("#### ☁️ Cloud export")
    if st.button("Upload PDF report to cloud (sync)"):
        try:
            res = Storage.upload_bytes(pdf_bytes, f"report_{uploaded_file.name}.pdf")
            st.success("Uploaded report")
            st.write("URL:", res.get("url"))
            
            # Track usage
            try:
                subscription_repo.track_usage(user_id, 'cloud_uploads', 1)
            except:
                pass
        except Exception as e:
            log.exception("Cloud upload failed")
            st.error("Cloud upload failed. See logs.")

    if st.button("Upload PDF report to cloud (async)"):
        # create CSV bytes to send to task
        csv_bytes = AnalyticsService.export_csv_bytes(df)
        task = report_tasks.generate_and_upload_report.delay(csv_bytes, f"async_report_{uploaded_file.name}")
        st.info(f"Started background job: {task.id}")

        # Poll result for a short time (server-side loop) — in prod prefer webhook/callback
        with st.spinner("Waiting for background job to finish (polling)…"):
            for _ in range(30):
                res = celery_app.AsyncResult(task.id)
                if res.ready():
                    if res.successful():
                        out = res.result
                        st.success("Background upload completed")
                        st.write("URL:", out.get("url"))
                    else:
                        st.error("Background job failed — check worker logs")
                    break
                time.sleep(1)
            else:
                st.warning("Background job is still running — check task id later.")

    st.markdown("---")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 4) Save into MySQL
    # ------------------------------------------------------------------
    # Build a simple key to prevent double-imports during this session.
    upload_key = f"{shop_id}:{user_id}:{uploaded_file.name}:{len(df)}"
    already_saved = upload_key in st.session_state["saved_upload_keys"]

    st.markdown("### 💾 Save into database")

    if already_saved:
        st.info("✅ This upload was already saved in this session.")
        if st.checkbox(
            "I understand and still want to save it again (may duplicate data)",
            value=False,
        ):
            force_save = True
        else:
            force_save = False
    else:
        force_save = True

    save_btn = st.button(
        "Save sales into MySQL",
        type="primary",
        disabled=not force_save,
        help="Writes transactions and line items into the retailsight database.",
    )

    if save_btn and force_save:
        try:
            num_tx, num_lines = AnalyticsService.save_to_db(
                df=df,
                shop_id=shop_id,
                user_id=user_id,
                filename=uploaded_file.name,
            )
            st.session_state["saved_upload_keys"].add(upload_key)

            st.success(
                f"Saved **{num_tx}** transactions and **{num_lines}** line items "
                f"for shop **{current_shop['name']}**."
            )
            st.info(
                "You can now explore this data under **History & Reports** "
                "and the **Manager Dashboard** tabs."
            )

        except Exception as e:
            log.exception("Failed to save upload to DB")
            st.error(
                "❌ Saving this upload into MySQL failed. "
                "Please check the logs (server side) or contact support."
            )
