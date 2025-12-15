# Yellow Sticker System - Ready to Use! ✅

## Database Setup Complete

Your database now has:
- ✅ **8 sample products** with expiry dates (1-7 days from today)
- ✅ **5 discount rules** (50% off last day, 40% for 2 days, etc.)
- ✅ **Expiry tracking** for all products
- ✅ **Schema compatibility** fixed

## Products Ready for Yellow Stickers

| Product | SKU | Price | Expires | Days Left | Expected Discount |
|---------|-----|-------|---------|-----------|-------------------|
| Fresh Whole Milk 2L | MILK001 | £2.50 | Tomorrow | 1 day | 50% OFF → £1.25 |
| Salmon Fillet 400g | FISH001 | £9.99 | Tomorrow | 1 day | 50% OFF → £5.00 |
| White Bread | BREAD001 | £1.20 | In 2 days | 2 days | 40% OFF → £0.72 |
| Fresh Chicken Breast 1kg | CHICKEN001 | £7.99 | In 2 days | 2 days | 40% OFF → £4.79 |
| Greek Yogurt 500g | YOGURT001 | £2.00 | In 3 days | 3 days | 30% OFF → £1.40 |
| Mixed Salad Leaves | SALAD001 | £1.50 | In 3 days | 3 days | 30% OFF → £1.05 |
| Cheddar Cheese 400g | CHEESE001 | £4.50 | In 5 days | 5 days | 20% OFF → £3.60 |
| Orange Juice 1L | JUICE001 | £2.50 | In 7 days | 7 days | 10% OFF → £2.25 |

## How to Generate Labels

### Option 1: Using the UI

1. **Start the app**:
   ```bash
   streamlit run app.py
   ```

2. **Navigate to Yellow Stickers tab**:
   - Look for "Yellow Stickers 🏷️" in the sidebar

3. **Generate Labels**:
   - Go to "Generate Labels" subtab
   - Set threshold: **7 days** (to see all products)
   - Click "Preview Products & Discounts"
   - You'll see all 8 products with calculated discounts

4. **Print Labels**:
   - Go to "Print Queue" subtab
   - Review all labels
   - Click "Print All Labels"
   - Use browser print (Cmd+P) or download as images

### Option 2: Barcode Scanner

1. Go to "Barcode Scanner" subtab
2. Enter any SKU (e.g., `MILK001`)
3. Click "Check Discount"
4. System shows:
   - Original price: £2.50
   - Discounted price: £1.25
   - Discount: 50% OFF
   - Days left: 1
5. Option to print single label

## Discount Rules Active

| Days Until Expiry | Discount | New Price Example (£5.00) |
|-------------------|----------|---------------------------|
| 0-1 days          | 50% OFF  | £2.50 |
| 2 days            | 40% OFF  | £3.00 |
| 3-4 days          | 30% OFF  | £3.50 |
| 5-6 days          | 20% OFF  | £4.00 |
| 7+ days           | 10% OFF  | £4.50 |

## Testing the System

### Test 1: Generate Labels for All Products
```
1. Set threshold: 7 days
2. Click "Preview Products & Discounts"
3. Expected: 8 products shown with discounts
```

### Test 2: Scan Individual Product
```
1. Go to Barcode Scanner
2. Enter: MILK001
3. Expected: 50% discount (expires tomorrow)
```

### Test 3: Print Labels
```
1. Generate labels (Test 1)
2. Go to Print Queue
3. See 8 label previews
4. Download or print
```

## Troubleshooting

### "No products expiring within X days"

**Solution**: Increase the days threshold slider:
- Try **7 days** to see all products
- Try **14 days** if you want to include more

### "Product not found for barcode"

**Solution**: Use exact SKU:
- ✅ `MILK001` (correct)
- ❌ `milk001` (wrong - case sensitive)
- ❌ `MILK` (wrong - need full SKU)

Valid SKUs:
- MILK001, BREAD001, YOGURT001, CHEESE001
- CHICKEN001, FISH001, SALAD001, JUICE001

### Labels not generating

**Check**:
1. Database connection active
2. Shop selected in sidebar
3. Products exist for selected shop (shop_id = 1)

## What's Next

### Add More Products
```sql
INSERT INTO products (shop_id, sku, name, default_cost, default_price, is_active)
VALUES (1, 'NEWPROD001', 'New Product', 1.00, 2.00, 1);

INSERT INTO expiry_records (product_id, batch_number, quantity_received, quantity_remaining, expiry_date, received_date, days_left, status)
VALUES (
  (SELECT id FROM products WHERE sku = 'NEWPROD001'),
  'BATCH001',
  10,
  10,
  DATE_ADD(CURDATE(), INTERVAL 3 DAY),
  CURDATE(),
  3,
  'active'
);
```

### Modify Discount Rules
```sql
-- Change 50% off to 60% off for last day
UPDATE discount_rules 
SET discount_percent = 60 
WHERE days_left_max = 1 AND shop_id = 1;
```

### Add More Shops
All products are currently for shop_id = 1. To add shop 2:
```sql
INSERT INTO products (shop_id, sku, name, default_price, is_active)
SELECT 2, sku, name, default_price, is_active 
FROM products WHERE shop_id = 1;
```

## Files Created

- ✅ `services/label_service.py` - Label generation logic
- ✅ `ui/tabs/yellow_sticker_tab.py` - UI interface
- ✅ `quick_setup.sql` - Database setup (already run)
- ✅ `test_discount_standalone.py` - Discount calculation tests
- ✅ `YELLOW_STICKER_GUIDE.md` - Full documentation
- ✅ `YELLOW_STICKER_READY.md` - This file

## System Status

🟢 **READY TO USE**

All components operational:
- Database tables created
- Sample data loaded
- Discount rules configured
- UI integrated
- Schema compatibility fixed

**Start using now**: `streamlit run app.py` → Yellow Stickers 🏷️ tab
