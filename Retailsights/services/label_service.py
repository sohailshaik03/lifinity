"""
Yellow Sticker Label Generation Service
Generates printable barcode labels for products expiring soon with discounts.
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
from datetime import datetime
import io
from ..repositories.products_repo import get_expiring_products, get_discount_rules
from ..logger import logger

try:
    from barcode import Code128
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    logger.warning("python-barcode not installed. Barcode generation will be limited.")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed. Image generation will be limited.")

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    logger.warning("qrcode not installed. QR code generation unavailable.")


class LabelService:
    """Service for generating yellow sticker labels with barcodes."""

    @staticmethod
    def calculate_discount_for_product(
        product: Dict[str, Any],
        days_left: int,
        discount_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate the applicable discount for a product based on days to expiry.
        
        Args:
            product: Product dict with selling_price, current_stock
            days_left: Number of days until expiry
            discount_rules: List of discount rules with days_left_min, days_left_max, discount_percent
        
        Returns:
            Dict with: discount_percent, discounted_price, original_price, discount_amount, rule_name, rule_id
        """
        applicable_rule = None
        max_discount = 0

        # Sort rules by discount_percent descending to prioritize higher discounts
        sorted_rules = sorted(
            discount_rules,
            key=lambda r: r.get("discount_percent", 0),
            reverse=True
        )

        for rule in sorted_rules:
            if not rule.get("active", True):
                continue
            
            days_min = rule.get("days_left_min", 0)
            days_max = rule.get("days_left_max", 999)
            quantity_min = rule.get("quantity_min", 0)  # Fixed: was qty_min
            discount = float(rule.get("discount_percent", 0))

            # Check if days_left falls within rule range
            if days_min <= days_left <= days_max:
                # Check quantity requirement if specified
                current_stock = product.get("current_stock", 0)
                if current_stock >= quantity_min:
                    # Apply highest discount rule that matches
                    if discount > max_discount:
                        max_discount = discount
                        applicable_rule = rule
                        break  # Stop at first matching rule (already sorted by discount)

        if applicable_rule:
            original_price = float(product.get("selling_price", 0))
            discount_amount = original_price * (max_discount / 100)
            discounted_price = original_price - discount_amount

            return {
                "discount_percent": int(max_discount),
                "original_price": original_price,
                "discounted_price": round(discounted_price, 2),
                "discount_amount": round(discount_amount, 2),
                "rule_name": applicable_rule.get("name", "Discount"),
                "rule_id": applicable_rule.get("id"),
            }
        
        # No discount applicable
        original_price = float(product.get("selling_price", 0))
        return {
            "discount_percent": 0,
            "original_price": original_price,
            "discounted_price": original_price,
            "discount_amount": 0.0,
            "rule_name": None,
            "rule_id": None,
        }

    @staticmethod
    def generate_barcode_image(barcode_data: str, writer_options: Optional[Dict] = None) -> Optional[io.BytesIO]:
        """
        Generate a barcode image as BytesIO object.
        
        Args:
            barcode_data: String to encode (e.g., SKU or product ID)
            writer_options: Options for barcode writer (width, height, etc.)
        
        Returns:
            BytesIO object containing PNG image or None if unavailable
        """
        if not BARCODE_AVAILABLE:
            logger.error("python-barcode not available")
            return None

    @staticmethod
    def generate_qr_code(data: str, box_size: int = 10, border: int = 2) -> Optional[io.BytesIO]:
        """Generate a QR code PNG for provided data."""
        if not QR_AVAILABLE:
            logger.error("qrcode package not available")
            return None
        try:
            qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf
        except Exception as e:
            logger.exception(f"QR code generation error: {e}")
            return None

        try:
            options = writer_options or {
                'module_width': 0.3,
                'module_height': 10,
                'quiet_zone': 2,
                'font_size': 10,
                'text_distance': 3,
            }

            output = io.BytesIO()
            code = Code128(barcode_data, writer=ImageWriter())
            code.write(output, options=options)
            output.seek(0)
            
            return output

        except Exception as e:
            logger.exception(f"Barcode generation error: {e}")
            return None

    @staticmethod
    def generate_yellow_sticker_label(
        product: Dict[str, Any],
        expiry_record: Dict[str, Any],
        discount_info: Dict[str, Any],
        include_barcode: bool = True
    ) -> Optional[io.BytesIO]:
        """
        Generate a complete yellow sticker label image.
        
        Label includes:
        - Product name and SKU
        - Original price (crossed out)
        - New discounted price (large, bold)
        - Discount percentage in badge
        - Expiry date
        - Barcode
        
        Args:
            product: Product dict with name, sku, selling_price
            expiry_record: Expiry record with expiry_date, days_left
            discount_info: Output from calculate_discount_for_product
            include_barcode: Whether to include barcode (default True)
        
        Returns:
            BytesIO object containing label image (PNG)
        """
        if not PIL_AVAILABLE:
            logger.error("Pillow not available for label generation")
            return None

        try:
            # Label dimensions (standard retail label: 62mm x 29mm at 300 DPI)
            width, height = 730, 340
            
            # Create yellow background
            img = Image.new('RGB', (width, height), color='#FFD700')
            draw = ImageDraw.Draw(img)

            # Try to load fonts (fallback to default if not available)
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
                font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
                font_bold = ImageFont.load_default()

            y_offset = 10

            # Product name (truncate if too long)
            product_name = product.get("name", "Unknown Product")[:30]
            draw.text((10, y_offset), product_name, fill='black', font=font_medium)
            y_offset += 40

            # SKU
            sku = product.get("sku", "N/A")
            draw.text((10, y_offset), f"SKU: {sku}", fill='black', font=font_small)
            y_offset += 30

            # Original price (crossed out)
            original_price = discount_info.get("original_price", 0)
            original_text = f"Was: £{original_price:.2f}"
            draw.text((10, y_offset), original_text, fill='red', font=font_medium)
            # Draw strikethrough line
            text_bbox = draw.textbbox((10, y_offset), original_text, font=font_medium)
            draw.line([(text_bbox[0], y_offset + 15), (text_bbox[2], y_offset + 15)], fill='red', width=3)
            y_offset += 40

            # New price (large and bold)
            discounted_price = discount_info.get("discounted_price", 0)
            draw.text((10, y_offset), f"NOW: £{discounted_price:.2f}", fill='darkgreen', font=font_large)

            # Discount badge (top right)
            discount_pct = discount_info.get("discount_percent", 0)
            if discount_pct > 0:
                badge_text = f"{int(discount_pct)}% OFF"
                badge_bbox = draw.textbbox((0, 0), badge_text, font=font_bold)
                badge_width = badge_bbox[2] - badge_bbox[0] + 20
                badge_height = badge_bbox[3] - badge_bbox[1] + 20
                badge_x = width - badge_width - 10
                badge_y = 10
                
                # Red circle background
                draw.ellipse(
                    [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
                    fill='red',
                    outline='darkred',
                    width=2
                )
                # White text
                text_x = badge_x + 10
                text_y = badge_y + 10
                draw.text((text_x, text_y), badge_text, fill='white', font=font_bold)

            y_offset += 70

            # Expiry date
            expiry_date = expiry_record.get("expiry_date")
            days_left = expiry_record.get("days_left", 0)
            if expiry_date:
                if isinstance(expiry_date, str):
                    expiry_str = expiry_date
                else:
                    expiry_str = expiry_date.strftime("%d/%m/%Y")
                draw.text((10, y_offset), f"Use by: {expiry_str} ({days_left} days)", fill='black', font=font_small)
                y_offset += 25

            # Barcode at bottom
            if include_barcode and BARCODE_AVAILABLE:
                barcode_data = f"{sku}"
                barcode_img_io = LabelService.generate_barcode_image(
                    barcode_data,
                    writer_options={
                        'module_width': 0.25,
                        'module_height': 40,
                        'quiet_zone': 1,
                        'font_size': 8,
                        'text_distance': 2,
                    }
                )
                
                if barcode_img_io:
                    barcode_img = Image.open(barcode_img_io)
                    # Resize to fit label
                    barcode_img = barcode_img.resize((width - 20, 60))
                    img.paste(barcode_img, (10, height - 70))

            # Save to BytesIO
            output = io.BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            return output

        except Exception as e:
            logger.exception(f"Label generation error: {e}")
            return None

    @staticmethod
    def generate_batch_labels(shop_id: int, days_threshold: int = 7) -> List[Dict[str, Any]]:
        """
        Generate labels for all products expiring within threshold.
        
        Args:
            shop_id: Shop ID
            days_threshold: Generate labels for products expiring within N days
        
        Returns:
            List of dicts with product info and label image data
        """
        try:
            # Get expiring products
            expiring = get_expiring_products(shop_id, days_threshold=days_threshold)
            if not expiring:
                return []

            # Get discount rules
            discount_rules = get_discount_rules(shop_id)

            labels = []
            for item in expiring:
                # Calculate discount
                days_left = item.get("days_left", 0)
                discount_info = LabelService.calculate_discount_for_product(
                    item,
                    days_left,
                    discount_rules
                )

                # Generate label image
                label_img = LabelService.generate_yellow_sticker_label(
                    item,
                    item,  # expiry_record fields are in the same dict
                    discount_info,
                    include_barcode=True
                )

                labels.append({
                    "product_id": item.get("product_id"),
                    "sku": item.get("sku"),
                    "name": item.get("name"),
                    "expiry_date": item.get("expiry_date"),
                    "days_left": days_left,
                    "original_price": discount_info["original_price"],
                    "discounted_price": discount_info["discounted_price"],
                    "discount_percent": discount_info["discount_percent"],
                    "rule_name": discount_info["rule_name"],
                    "label_image": label_img,
                })

            logger.info(f"Generated {len(labels)} yellow sticker labels for shop {shop_id}")
            return labels

        except Exception as e:
            logger.exception(f"Batch label generation error: {e}")
            return []

    @staticmethod
    def scan_barcode_and_get_discount(barcode_data: str, shop_id: int) -> Optional[Dict[str, Any]]:
        """
        Scan a barcode (SKU) and return discount information if product is expiring.
        
        This simulates a barcode scanner at POS.
        
        Args:
            barcode_data: Scanned barcode (typically SKU)
            shop_id: Shop ID
        
        Returns:
            Dict with product info and discount, or None if not found/not expiring
        """
        try:
            from repositories.products_repo import get_products_by_shop

            # Find product by SKU
            products = get_products_by_shop(shop_id)
            product = None
            for p in products:
                if p.get("sku") == barcode_data:
                    product = p
                    break

            if not product:
                logger.warning(f"Product not found for barcode: {barcode_data}")
                return None

            # Get expiry records for this product
            expiring = get_expiring_products(shop_id, days_threshold=30)
            expiry_record = None
            for exp in expiring:
                if exp.get("product_id") == product.get("id"):
                    expiry_record = exp
                    break

            if not expiry_record:
                # Product not expiring soon
                return {
                    "product_id": product.get("id"),
                    "sku": product.get("sku"),
                    "name": product.get("name"),
                    "price": product.get("selling_price"),
                    "discounted_price": product.get("selling_price"),
                    "discount_percent": 0,
                    "expiring": False,
                    "message": "No discount - product not expiring soon"
                }

            # Calculate discount
            discount_rules = get_discount_rules(shop_id)
            days_left = expiry_record.get("days_left", 0)
            discount_info = LabelService.calculate_discount_for_product(
                product,
                days_left,
                discount_rules
            )

            return {
                "product_id": product.get("id"),
                "sku": product.get("sku"),
                "name": product.get("name"),
                "expiry_date": expiry_record.get("expiry_date"),
                "days_left": days_left,
                "batch_number": expiry_record.get("batch_number"),
                "original_price": discount_info["original_price"],
                "discounted_price": discount_info["discounted_price"],
                "discount_percent": discount_info["discount_percent"],
                "discount_amount": discount_info["discount_amount"],
                "rule_name": discount_info["rule_name"],
                "expiring": True,
                "message": f"{discount_info['discount_percent']}% discount applied - {days_left} days until expiry"
            }

        except Exception as e:
            logger.exception(f"Barcode scan error: {e}")
            return None
