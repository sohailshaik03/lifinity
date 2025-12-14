# Yellow Sticker Label System Guide

## Overview

The Yellow Sticker Label System automatically generates professional discount labels for products approaching expiry. This is similar to systems used by major UK retailers like M&S, Tesco, and Sainsbury's.

## Features

✅ **Automatic Discount Calculation**: Applies discount rules based on days until expiry  
✅ **Professional Label Design**: Yellow background, barcode, pricing comparison  
✅ **Barcode Scanner Integration**: POS-ready barcode scanning for quick checkout  
✅ **Batch Label Generation**: Print labels for all expiring products at once  
✅ **Label Queue Management**: Review, edit, and print labels in batches  

## Installation

### 1. Install Dependencies

```bash
pip install python-barcode[images] Pillow
```

Or if already in requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```python
# Test in Python
import barcode
from PIL import Image

print("✅ Dependencies installed successfully")
```

## Label Specifications

- **Size**: 62mm × 29mm (standard retail label)
- **Resolution**: 300 DPI (730 × 340 pixels)
- **Barcode Format**: Code128 (industry standard)
- **File Format**: PNG (transparent background option)

## Label Design

```
┌────────────────────────────────────────────────────┐
│  SKU: PROD001                      [30% OFF]       │
│                                                     │
│  Product Name (truncated to 30 chars)             │
│                                                     │
│  Was: £5.99 ──────                                 │
│  NOW: £4.19                                        │
│                                                     │
│  Use by: 25/12/2024 (3 days)                      │
│                                                     │
│  ||||||||||||||||||||||||||||                      │
│  PROD001                                           │
└────────────────────────────────────────────────────┘
```

### Design Elements

- **Yellow Background**: #FFD700 (gold)
- **Original Price**: Red, 32pt, strikethrough
- **Discounted Price**: Dark green, 60pt bold
- **Discount Badge**: Red circle, white text, top-right corner
- **Barcode**: Code128 at bottom with SKU text

## Usage

### Generate Labels for Expiring Products

1. Navigate to **"Yellow Stickers 🏷️"** tab
2. Go to **"Generate Labels"** subtab
3. Select days threshold (e.g., 7 days)
4. Click **"Preview Products & Discounts"**
5. Review discount calculations in table
6. Labels automatically added to Print Queue

### Barcode Scanner

1. Navigate to **"Barcode Scanner"** subtab
2. Scan or manually enter product SKU
3. Click **"Check Discount"**
4. System shows:
   - Original price
   - Discounted price (if expiring)
   - Days until expiry
   - Applicable discount rule
5. Option to print single label

### Print Queue

1. Navigate to **"Print Queue"** subtab
2. Review all labels in queue
3. Click **"Print All Labels"**
4. Use browser print dialog (Ctrl+P / Cmd+P)
5. Select printer or "Save as PDF"

**Tip**: For best results, use a thermal label printer with 62mm × 29mm labels.

## Discount Logic

The system automatically applies discounts based on configured rules:

| Days Until Expiry | Discount |
|-------------------|----------|
| 7 days            | 10% OFF  |
| 5 days            | 20% OFF  |
| 3 days            | 30% OFF  |
| 2 days            | 40% OFF  |
| 1 day             | 50% OFF  |

**Note**: Discount rules can be configured in Admin tab under "Discount Rules".

## Integration with POS Systems

### Method 1: Manual Barcode Scanning

1. Print labels and attach to products
2. At checkout, scan barcode with standard barcode scanner
3. Use "Barcode Scanner" tab to look up discount
4. Manually apply discount at POS

### Method 2: POS Integration (Advanced)

```python
from services.label_service import LabelService

# In your POS system
label_svc = LabelService()
result = label_svc.scan_barcode_and_get_discount(
    barcode_data="PROD001",
    shop_id=1
)

if result and result["expiring"]:
    apply_discount(
        product_id=result["product_id"],
        discount_percent=result["discount_percent"],
        discounted_price=result["discounted_price"]
    )
```

## API Reference

### LabelService Methods

#### `calculate_discount_for_product(product, days_left, discount_rules)`
Calculates applicable discount for a product based on days until expiry.

**Parameters**:
- `product` (dict): Product record with id, sku, name, price
- `days_left` (int): Days until expiry
- `discount_rules` (list): List of discount rule dicts

**Returns**:
```python
{
    "discount_percent": 30,
    "discounted_price": 4.19,
    "original_price": 5.99,
    "discount_amount": 1.80,
    "rule_name": "30% off - 3 days",
    "applied": True
}
```

#### `generate_yellow_sticker_label(product, expiry_record, discount_info, include_barcode=True)`
Generates a single yellow sticker label image.

**Returns**: BytesIO object containing PNG image

#### `generate_batch_labels(shop_id, days_threshold=7)`
Generates labels for all expiring products in a shop.

**Returns**: List of label dicts with `label_image` BytesIO objects

#### `scan_barcode_and_get_discount(barcode_data, shop_id)`
Simulates POS barcode scanner - looks up product and calculates discount.

**Returns**:
```python
{
    "product_id": 123,
    "sku": "PROD001",
    "name": "Milk",
    "price": 5.99,
    "expiring": True,
    "days_left": 3,
    "discount_percent": 30,
    "original_price": 5.99,
    "discounted_price": 4.19,
    "discount_amount": 1.80,
    "expiry_date": "2024-12-25",
    "message": "30% discount applied (expires in 3 days)"
}
```

## Troubleshooting

### Dependencies Not Installed

**Error**: `ModuleNotFoundError: No module named 'barcode'`

**Solution**:
```bash
pip install python-barcode[images] Pillow
```

### Labels Not Generating

**Error**: "No products expiring within X days"

**Checklist**:
- ✅ Products exist in database
- ✅ Products have expiry dates set
- ✅ Expiry dates are within threshold
- ✅ Shop ID is correct

### Barcode Scanner Not Working

**Checklist**:
- ✅ SKU exists in products table
- ✅ Product is assigned to current shop
- ✅ Barcode input is exact match (case-sensitive)

### Labels Print Too Small/Large

**Solution**: Adjust printer settings:
- Set paper size to 62mm × 29mm
- Use "Actual Size" or "100% scale"
- Disable "Fit to Page"

### Low Image Quality

**Solution**: Labels are 300 DPI by default. To increase:

```python
# In label_service.py, modify:
width_px = int(62 * 300 / 25.4)  # Change 300 to 600 for higher DPI
height_px = int(29 * 300 / 25.4)
```

## Best Practices

### Daily Workflow

1. **Morning**: Generate labels for products expiring in next 7 days
2. **Midday**: Re-scan and generate additional labels for faster-moving items
3. **Evening**: Generate aggressive discount labels (50% off) for next-day expiry

### Label Application

- Apply labels to **front** of product packaging
- Ensure barcode is visible and not wrinkled
- Replace old labels when discount increases
- Remove labels if product sold or waste recorded

### Inventory Management

- Generate labels in batches to save time
- Export label data as CSV for records
- Cross-reference with waste reports
- Monitor discount effectiveness in Reports tab

## Example Workflows

### Workflow 1: Daily Morning Label Run

```
1. Login → Select Shop
2. Navigate to "Yellow Stickers 🏷️"
3. Set threshold: 7 days
4. Click "Preview Products & Discounts"
5. Review list of 23 products
6. Go to "Print Queue"
7. Click "Print All Labels"
8. Print to PDF → Send to thermal printer
9. Apply labels to products on shelf
```

### Workflow 2: Quick Single Product Label

```
1. Customer asks about discount on milk
2. Navigate to "Barcode Scanner"
3. Enter SKU: "MILK001"
4. Click "Check Discount"
5. Shows: 30% OFF, £1.99 → £1.39
6. Click "Print Label for this Product"
7. Download PNG
8. Print and apply to product
```

### Workflow 3: End-of-Day Clearance

```
1. Filter for products expiring tomorrow (1 day)
2. Generate labels with 50% discount
3. Review 8 products in queue
4. Print all labels
5. Apply to products
6. Move to clearance section of store
```

## Integration with Other Modules

### Expiry & Waste Tab
- Links to expiry tracking
- Waste reports show products that didn't sell even with discounts

### Admin Tab
- Configure discount rules
- Set alert thresholds for label generation

### Manager Dashboard
- Track discount effectiveness
- Revenue impact of markdown strategy

## Future Enhancements

- [ ] Webcam barcode scanning
- [ ] Auto-print on label printer
- [ ] Label template customization
- [ ] Multi-language labels
- [ ] QR codes for product info
- [ ] Email labels to store managers
- [ ] Integration with thermal printers (Brother, Zebra, Dymo)

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify dependencies installed correctly
3. Test with sample products
4. Check database connection

## License

Part of RetailSight enterprise retail management system.
