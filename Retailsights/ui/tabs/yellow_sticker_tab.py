"""
Yellow Sticker Labels Tab
UI for generating and printing discount labels for expiring products
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime
from ...services.label_service import LabelService
from ...repositories.scan_history_repo import record_scan_event, get_recent_scans
from ...repositories.products_repo import get_products_by_shop, decrement_expiring_stock, record_waste
from ...logger import log

# Optional barcode/image dependencies
try:
    from PIL import Image
    PIL_IMPORT_OK = True
except Exception:
    PIL_IMPORT_OK = False

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_OK = True
except Exception:
    PYZBAR_OK = False

# Optional webcam streaming
import threading
import time

try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
    WEBRTC_OK = True
    
    class _BarcodeVideoProcessor(VideoProcessorBase):
        """Video frame processor for live barcode decoding."""
        def __init__(self):
            self.last_codes: list[str] = []
            self.last_detect_ts = 0.0
            self.cooldown_sec = 1.0  # limit decode frequency

        def recv(self, frame):  # streamlit-webrtc hook
            if not (PYZBAR_OK and PIL_IMPORT_OK):
                return frame
            img = frame.to_image()
            now = time.time()
            if now - self.last_detect_ts >= self.cooldown_sec:
                try:
                    decoded = _decode_barcodes_from_image(img)
                    if decoded:
                        self.last_codes = decoded
                        self.last_detect_ts = now
                except Exception:
                    pass
            return frame
except Exception:
    WEBRTC_OK = False
    _BarcodeVideoProcessor = None  # placeholder

def _decode_barcodes_from_image(image) -> list[str]:
    """Decode barcodes from a PIL image, returns list of strings."""
    if not (PIL_IMPORT_OK and PYZBAR_OK):
        return []
    try:
        results = pyzbar_decode(image)
        codes = []
        for r in results:
            data = r.data.decode("utf-8").strip()
            if data:
                codes.append(data)
        return codes
    except Exception:
        return []


def render_yellow_sticker_tab(state) -> None:
    """Render yellow sticker label generation and barcode scanning UI."""
    st.title("🏷️ Yellow Sticker Labels")

    user = st.session_state.get("auth_user")
    shop = st.session_state.get("current_shop")

    if not user or not shop:
        st.error("Login and select a shop first.")
        return

    shop_id = shop["id"]

    # Create tabs for different functions
    tabs = st.tabs(["Generate Labels", "Barcode Scanner", "Print Queue"])

    # --- Tab 1: Generate Labels ---
    with tabs[0]:
        st.markdown("### Generate yellow sticker labels")
        st.caption("Automatically generate discount labels for products expiring soon")

        col1, col2 = st.columns(2)
        
        with col1:
            days_threshold = st.slider(
                "Products expiring within (days)",
                min_value=1,
                max_value=30,
                value=7,
                help="Generate labels for products expiring within this many days"
            )
        
        with col2:
            st.markdown("**Label includes:**")
            st.markdown("- Product name & SKU")
            st.markdown("- Original price (crossed out)")
            st.markdown("- Discounted price (bold)")
            st.markdown("- Discount % badge")
            st.markdown("- Expiry date")
            st.markdown("- Barcode")

        st.markdown("---")

        if st.button("🔍 Preview Products & Discounts", type="primary"):
            with st.spinner("Loading expiring products..."):
                try:
                    label_svc = LabelService()
                    labels = label_svc.generate_batch_labels(shop_id, days_threshold=days_threshold)

                    if not labels:
                        st.info(f"No products expiring within {days_threshold} days.")
                    else:
                        st.success(f"Found {len(labels)} products eligible for yellow stickers")

                        # Display as table
                        df_data = []
                        for lbl in labels:
                            df_data.append({
                                "SKU": lbl["sku"],
                                "Product": lbl["name"],
                                "Days Left": lbl["days_left"],
                                "Original Price": f"£{lbl['original_price']:.2f}",
                                "Discount %": f"{lbl['discount_percent']}%",
                                "New Price": f"£{lbl['discounted_price']:.2f}",
                                "Savings": f"£{lbl['original_price'] - lbl['discounted_price']:.2f}",
                                "Rule": lbl["rule_name"] or "No discount",
                            })

                        df = pd.DataFrame(df_data)
                        st.dataframe(df, width="stretch", hide_index=True)

                        # Store in session state for printing
                        st.session_state["label_queue"] = labels

                        st.markdown("---")
                        st.markdown("### 📄 Label Preview")
                        
                        # Show first label as preview
                        if labels[0]["label_image"]:
                            st.image(
                                labels[0]["label_image"],
                                caption=f"Preview: {labels[0]['name']}",
                                width="stretch"
                            )
                            st.caption("Yellow sticker label with barcode, discount, and expiry info")

                except Exception as e:
                    log.exception("Label preview error")
                    st.error(f"Error generating labels: {e}")

    # --- Tab 2: Barcode Scanner ---
    with tabs[1]:
        st.markdown("### 🔍 Barcode Scanner")
        st.caption("Scan a product barcode to check discount eligibility")

        col_a, col_b = st.columns([2, 1])

        with col_a:
            barcode_input = st.text_input(
                "Scan or enter barcode (SKU)",
                placeholder="e.g., PROD001",
                help="Use barcode scanner or type SKU manually"
            )

        with col_b:
            st.markdown("")
            st.markdown("")
            scan_button = st.button("🔎 Check Discount", type="primary")

        if scan_button and barcode_input:
            with st.spinner("Scanning..."):
                try:
                    label_svc = LabelService()
                    result = label_svc.scan_barcode_and_get_discount(barcode_input, shop_id)

                    if not result:
                        st.error(f"❌ Product not found: {barcode_input}")
                        record_scan_event(
                            shop_id=shop_id,
                            code=barcode_input,
                            code_type="barcode",
                            source="manual",
                            product_id=None,
                            discount_applied=False,
                            message="Not found"
                        )
                    else:
                        st.markdown("---")
                        
                        if result["expiring"]:
                            # Product is expiring - show discount
                            st.success(f"✅ Discount available!")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Original Price", f"£{result['original_price']:.2f}")
                            with col2:
                                st.metric(
                                    "Discounted Price",
                                    f"£{result['discounted_price']:.2f}",
                                    delta=f"-{result['discount_percent']}%",
                                    delta_color="inverse"
                                )
                            with col3:
                                st.metric("You Save", f"£{result['discount_amount']:.2f}")

                            st.markdown("---")
                            
                            # Product details
                            st.markdown(f"**Product:** {result['name']}")
                            st.markdown(f"**SKU:** {result['sku']}")
                            st.markdown(f"**Expiry Date:** {result['expiry_date']} ({result['days_left']} days left)")
                            if result.get("batch_number"):
                                st.markdown(f"**Batch:** {result['batch_number']}")
                            if result.get("rule_name"):
                                st.markdown(f"**Discount Rule:** {result['rule_name']}")

                            st.info(f"💡 {result['message']}")
                            # Actions: Apply Discount & Print, Record Waste
                            qty_col, actions_col = st.columns([1, 3])
                            with qty_col:
                                qty = st.number_input("Qty", min_value=1, max_value=50, value=1)
                            with actions_col:
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button("✅ Apply Discount & Print"):
                                        # Decrement stock by qty and generate label
                                        try:
                                            from Retailsights.repositories.markdown_sales_repo import record_markdown_sale
                                            products = get_products_by_shop(shop_id)
                                            product = next((p for p in products if p["sku"] == barcode_input), None)
                                            if product and decrement_expiring_stock(product["id"], qty):
                                                st.success(f"Reduced stock by {qty}")
                                                # Generate label
                                                from Retailsights.repositories.products_repo import get_expiring_products
                                                expiring = get_expiring_products(shop_id, days_threshold=30)
                                                expiry_record = next((e for e in expiring if e["product_id"] == product["id"]), None)
                                                if expiry_record:
                                                    discount_info = {
                                                        "discount_percent": result["discount_percent"],
                                                        "original_price": result["original_price"],
                                                        "discounted_price": result["discounted_price"],
                                                        "discount_amount": result["discount_amount"],
                                                        "rule_name": result["rule_name"],
                                                    }
                                                    # Record markdown sale
                                                    record_markdown_sale(
                                                        shop_id=shop_id,
                                                        product_id=product["id"],
                                                        sku=barcode_input,
                                                        quantity_sold=qty,
                                                        original_price=result["original_price"],
                                                        discounted_price=result["discounted_price"],
                                                        discount_percent=result["discount_percent"],
                                                        discount_amount=result["discount_amount"],
                                                        rule_id=result.get("rule_id"),
                                                        rule_name=result.get("rule_name"),
                                                        expiry_record_id=expiry_record["id"],
                                                        sold_by=user.get("id"),
                                                    )
                                                    label_img = label_svc.generate_yellow_sticker_label(product, expiry_record, discount_info, include_barcode=True)
                                                    if label_img:
                                                        st.image(label_img, caption="Yellow Sticker Label", width="stretch")
                                                        st.download_button(label="💾 Download Label (PNG)", data=label_img, file_name=f"label_{barcode_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png", mime="image/png")
                                            else:
                                                st.error("Could not reduce stock (no active expiry record)")
                                        except Exception as e:
                                            log.exception("Apply discount & print error")
                                            st.error(f"Error: {e}")
                                with c2:
                                    default_reason = "expired"
                                    reason = st.text_input("Waste reason", value=default_reason, help="Default is 'expired'; you can customize")
                                    if st.button("🗑️ Record Waste"):
                                        try:
                                            products = get_products_by_shop(shop_id)
                                            product = next((p for p in products if p["sku"] == barcode_input), None)
                                            if product and record_waste(product["id"], qty, reason, recorded_by=user.get("id")):
                                                st.success(f"Waste recorded: {qty} ({reason}) and stock reduced")
                                            else:
                                                st.error("Could not record waste (no active expiry record)")
                                        except Exception as e:
                                            log.exception("Record waste error")
                                            st.error(f"Error: {e}")
                            record_scan_event(
                                shop_id=shop_id,
                                code=barcode_input,
                                code_type="barcode",
                                source="manual",
                                product_id=result.get("product_id"),
                                discount_applied=True,
                                discount_percent=result.get("discount_percent", 0),
                                original_price=result.get("original_price"),
                                discounted_price=result.get("discounted_price"),
                                message=result.get("message")
                            )

                            # Generate single label
                            if st.button("🖨️ Print Label for this Product"):
                                with st.spinner("Generating label..."):
                                    try:
                                        # Get full product details
                                        products = get_products_by_shop(shop_id)
                                        product = next((p for p in products if p["sku"] == barcode_input), None)
                                        
                                        if product:
                                            from Retailsights.repositories.products_repo import get_expiring_products
                                            expiring = get_expiring_products(shop_id, days_threshold=30)
                                            expiry_record = next(
                                                (e for e in expiring if e["product_id"] == product["id"]),
                                                None
                                            )
                                            
                                            if expiry_record:
                                                discount_info = {
                                                    "discount_percent": result["discount_percent"],
                                                    "original_price": result["original_price"],
                                                    "discounted_price": result["discounted_price"],
                                                    "discount_amount": result["discount_amount"],
                                                    "rule_name": result["rule_name"],
                                                }
                                                
                                                label_img = label_svc.generate_yellow_sticker_label(
                                                    product,
                                                    expiry_record,
                                                    discount_info,
                                                    include_barcode=True
                                                )
                                                
                                                if label_img:
                                                    st.image(label_img, caption="Yellow Sticker Label", width="stretch")
                                                    
                                                    # Download button
                                                    st.download_button(
                                                        label="💾 Download Label (PNG)",
                                                        data=label_img,
                                                        file_name=f"label_{barcode_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                                        mime="image/png"
                                                    )
                                    except Exception as e:
                                        log.exception("Single label print error")
                                        st.error(f"Error generating label: {e}")

                        else:
                            # Product not expiring - no discount
                            st.info(f"ℹ️ No discount available")
                            st.markdown(f"**Product:** {result['name']}")
                            st.markdown(f"**SKU:** {result['sku']}")
                            st.markdown(f"**Price:** £{result['price']:.2f}")
                            st.caption(result["message"])
                            record_scan_event(
                                shop_id=shop_id,
                                code=barcode_input,
                                code_type="barcode",
                                source="manual",
                                product_id=result.get("product_id"),
                                discount_applied=False,
                                original_price=result.get("price"),
                                message=result.get("message")
                            )

                except Exception as e:
                    log.exception("Barcode scan error")
                    st.error(f"Scan error: {e}")

        st.markdown("---")
        st.markdown("#### 🖼️ Image / Photo Barcode Scan")
        st.caption("Upload a photo or screenshot of a product barcode to decode it.")

        if not PIL_IMPORT_OK or not PYZBAR_OK:
            st.warning("Image barcode scanning needs Pillow and pyzbar. Run: pip install Pillow pyzbar")
        else:
            uploaded_img = st.file_uploader(
                "Upload barcode image (PNG/JPG)",
                type=["png", "jpg", "jpeg"],
                help="Clear, well-lit barcode images work best"
            )
            if uploaded_img:
                try:
                    pil_img = Image.open(uploaded_img)
                    st.image(pil_img, caption="Uploaded image", width="stretch")
                    codes = _decode_barcodes_from_image(pil_img)
                    if not codes:
                        st.error("No barcodes detected. Try a clearer image.")
                    else:
                        st.success(f"Detected {len(codes)} barcode(s)")
                        for code in codes:
                            st.markdown(f"**Decoded:** `{code}`")
                            if st.button(f"Lookup {code}", key=f"lookup_{code}"):
                                with st.spinner("Looking up product..."):
                                    label_svc = LabelService()
                                    result = label_svc.scan_barcode_and_get_discount(code, shop_id)
                                    if not result:
                                        st.error(f"❌ Product not found: {code}")
                                        record_scan_event(shop_id, code, "barcode", "image", None, False, message="Not found")
                                    else:
                                        if result["expiring"]:
                                            st.success(f"Discount: {result['discount_percent']}% → £{result['discounted_price']:.2f}")
                                            record_scan_event(
                                                shop_id, code, "barcode", "image", result.get("product_id"), True,
                                                result.get("discount_percent", 0), result.get("original_price"), result.get("discounted_price"), result.get("message")
                                            )
                                        else:
                                            st.info("No discount (not expiring soon)")
                                            record_scan_event(
                                                shop_id, code, "barcode", "image", result.get("product_id"), False,
                                                0, result.get("price"), None, result.get("message")
                                            )
                                        st.markdown(f"SKU: `{result['sku']}` | Name: **{result['name']}**")
                                        st.markdown(f"Price: £{result.get('original_price', result.get('price', 0)):.2f}")
                except Exception as e:
                    st.error(f"Image processing error: {e}")
                    log.exception("Image barcode decode error")

        st.markdown("---")
        st.markdown("#### 📷 Live Webcam Scan (Beta)")
        if not WEBRTC_OK:
            st.info("Install live scan dependency: pip install streamlit-webrtc")
        elif not (PYZBAR_OK and PIL_IMPORT_OK):
            st.warning("Requires Pillow + pyzbar. Run: pip install Pillow pyzbar")
        else:
            st.caption("Allow camera access. Hold barcode ~20–30cm from camera, align horizontally.")
            live_placeholder = st.empty()
            codes_holder = st.empty()

            if 'live_barcode_codes' not in st.session_state:
                st.session_state['live_barcode_codes'] = []

            def _update_codes_loop():
                while 'webrtc_active' in st.session_state and st.session_state['webrtc_active']:
                    processor = st.session_state.get('barcode_processor')
                    if processor and processor.last_codes:
                        st.session_state['live_barcode_codes'] = processor.last_codes
                        codes_holder.markdown("**Detected:** " + ", ".join(f'`{c}`' for c in processor.last_codes))
                    time.sleep(0.5)

            start_live = st.checkbox("Enable live barcode scanning")
            if start_live:
                st.session_state['webrtc_active'] = True
                webrtc_ctx = webrtc_streamer(
                    key="barcode-live",
                    video_processor_factory=_BarcodeVideoProcessor,
                    media_stream_constraints={"video": True, "audio": False},
                )
                st.session_state['barcode_processor'] = webrtc_ctx.video_processor
                threading.Thread(target=_update_codes_loop, daemon=True).start()

                # Lookup controls
                if st.session_state['live_barcode_codes']:
                    for code in st.session_state['live_barcode_codes'][:5]:
                        if st.button(f"Lookup {code}", key=f"live_lookup_{code}"):
                            with st.spinner("Looking up product..."):
                                label_svc = LabelService()
                                result = label_svc.scan_barcode_and_get_discount(code, shop_id)
                                if not result:
                                    st.error(f"❌ Product not found: {code}")
                                    record_scan_event(shop_id, code, "barcode", "webcam", None, False, message="Not found")
                                else:
                                    if result["expiring"]:
                                        st.success(f"Discount: {result['discount_percent']}% → £{result['discounted_price']:.2f}")
                                        record_scan_event(
                                            shop_id, code, "barcode", "webcam", result.get("product_id"), True,
                                            result.get("discount_percent", 0), result.get("original_price"), result.get("discounted_price"), result.get("message")
                                        )
                                    else:
                                        st.info("No discount (not expiring soon)")
                                        record_scan_event(
                                            shop_id, code, "barcode", "webcam", result.get("product_id"), False,
                                            0, result.get("price"), None, result.get("message")
                                        )
                                    st.markdown(f"SKU: `{result['sku']}` | Name: **{result['name']}**")
                                    st.markdown(f"Price: £{result.get('original_price', result.get('price', 0)):.2f}")
            else:
                st.session_state['webrtc_active'] = False

        # QR Code Generation Utility
        st.markdown("---")
        st.markdown("#### 🧾 QR Code Tools")
        st.caption("Generate a QR code for a product SKU (encodes SKU + current discount if any).")
        with st.form("qr_form"):
            qr_sku = st.text_input("SKU", placeholder="e.g., MILK001")
            include_discount = st.checkbox("Include discount data if expiring", value=True)
            submitted_qr = st.form_submit_button("Generate QR")
        if submitted_qr and qr_sku:
            label_svc = LabelService()
            # Lookup product discount status
            result = label_svc.scan_barcode_and_get_discount(qr_sku, shop_id)
            payload = {"sku": qr_sku}
            if include_discount and result and result.get("expiring"):
                payload.update({
                    "discount_percent": result.get("discount_percent"),
                    "discounted_price": result.get("discounted_price"),
                    "days_left": result.get("days_left")
                })
            import json
            qr_data_str = json.dumps(payload)
            qr_img = label_svc.generate_qr_code(qr_data_str)
            if qr_img:
                st.image(qr_img, caption=f"QR for {qr_sku}")
                st.download_button(
                    label="Download QR PNG",
                    data=qr_img,
                    file_name=f"qr_{qr_sku}.png",
                    mime="image/png"
                )

        # Scan History Display
        st.markdown("---")
        st.markdown("#### 📜 Scan History (Latest 25)")
        history = get_recent_scans(shop_id, limit=25)
        if not history:
            st.caption("No scans recorded yet.")
        else:
            hist_rows = []
            for h in history:
                hist_rows.append({
                    "Time": h["scanned_at"],
                    "Code": h["code"],
                    "Type": h["code_type"],
                    "Source": h["source"],
                    "Discount?": "Yes" if h["discount_applied"] else "No",
                    "%": h["discount_percent"],
                    "Orig £": h["original_price"],
                    "Disc £": h["discounted_price"],
                    "Msg": h.get("message")
                })
            st.dataframe(pd.DataFrame(hist_rows), width="stretch", hide_index=True)

    # --- Tab 3: Print Queue ---
    with tabs[2]:
        st.markdown("### 🖨️ Print Queue")
        st.caption("Batch print labels generated in 'Generate Labels' tab")

        if "label_queue" not in st.session_state or not st.session_state["label_queue"]:
            st.info("No labels in queue. Go to 'Generate Labels' tab to create labels.")
        else:
            labels = st.session_state["label_queue"]
            st.success(f"📋 {len(labels)} labels in queue")

            # Show summary
            total_discount = sum(
                lbl["original_price"] - lbl["discounted_price"]
                for lbl in labels
            )
            st.metric("Total Customer Savings", f"£{total_discount:.2f}")

            st.markdown("---")

            # Display all labels for printing
            cols = st.columns(2)
            for idx, label in enumerate(labels):
                col = cols[idx % 2]
                
                with col:
                    with st.container():
                        st.markdown(f"**{label['name']}**")
                        st.caption(f"SKU: {label['sku']} | {label['discount_percent']}% OFF")
                        
                        if label["label_image"]:
                            st.image(
                                label["label_image"],
                                caption=f"£{label['discounted_price']:.2f} (was £{label['original_price']:.2f})",
                                width="stretch"
                            )

            st.markdown("---")

            col_x, col_y = st.columns(2)
            
            with col_x:
                if st.button("🖨️ Print All Labels", type="primary"):
                    st.info("💡 Send to printer: Use browser print dialog (Ctrl+P / Cmd+P)")
                    st.caption("Tip: Select 'Save as PDF' to create printable file")

            with col_y:
                if st.button("🗑️ Clear Queue"):
                    st.session_state["label_queue"] = []
                    st.rerun()

            # Export option
            st.markdown("---")
            st.markdown("### 📥 Export Labels")
            
            # Create CSV export
            export_data = []
            for lbl in labels:
                export_data.append({
                    "SKU": lbl["sku"],
                    "Product Name": lbl["name"],
                    "Expiry Date": lbl["expiry_date"],
                    "Days Left": lbl["days_left"],
                    "Original Price": lbl["original_price"],
                    "Discounted Price": lbl["discounted_price"],
                    "Discount %": lbl["discount_percent"],
                    "Discount Rule": lbl["rule_name"],
                })

            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)

            st.download_button(
                label="📄 Download Label Data (CSV)",
                data=csv,
                file_name=f"yellow_stickers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
