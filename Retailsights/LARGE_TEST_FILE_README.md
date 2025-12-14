# Large Messy Test Data - 400 Columns

## 📁 File Information

**Filename:** `large_messy_test_data_400cols.csv`  
**Location:** `/Users/shaiksohail/retailsight/large_messy_test_data_400cols.csv`  
**File Size:** 3.2 MB  
**Dimensions:** 1,000 rows × 400 columns

---

## 🎯 Purpose

This comprehensive test file is designed to stress-test the **Intelligent Data Analyst** feature of the RetailSight application. It contains realistic retail/business data with intentionally messy formatting across 400 columns.

---

## 📊 Column Groups (400 Total Columns)

### 1. **Transaction Details** (Columns 1-50)
- Transaction IDs with whitespace issues
- Invoice numbers with missing values
- Order dates in multiple formats
- Delivery dates with inconsistent formatting
- Return dates (sparse data)

### 2. **Product Information** (Columns 51-100)
- Product names with extra spaces
- SKU codes with "MISSING" placeholders
- Categories with whitespace
- Product brands (alphabetical)
- Product descriptions (15% missing)

### 3. **Quantity & Measurements** (Columns 101-150)
- Quantity sold (includes negative values)
- Units in stock (includes negative values)
- Weight in KG (10% missing)

### 4. **Financial Data** (Columns 151-200)
- Unit prices with mixed currency symbols ($, £, €)
- Total revenue with currency formatting
- Cost prices with mixed symbols
- Discount amounts (30% are zero)

### 5. **Customer Information** (Columns 201-250)
- Customer IDs (12% missing)
- Customer names
- Customer emails (10% malformed)
- Customer segments with whitespace

### 6. **Location Data** (Columns 251-300)
- Store locations with extra spaces
- Regions (6 global regions)
- Cities (50 different cities)
- Postal codes (8% missing)

### 7. **Payment & Shipping** (Columns 301-330)
- Payment methods (6 types)
- Shipping costs with currency symbols

### 8. **Performance Metrics** (Columns 331-360)
- Ratings 1-5 (20% missing)
- Review counts

### 9. **Operational Data** (Columns 361-380)
- Supplier IDs
- Lead time in days

### 10. **Custom Business Metrics** (Columns 381-400)
- Conversion rates (percentage format)
- Customer lifetime value with currency symbols

---

## 🔍 Data Quality Issues Included

| Issue Type | Count/Percentage | Description |
|------------|------------------|-------------|
| **Mixed Date Formats** | 9 formats | DD/MM/YYYY, YYYY-MM-DD, MM/DD/YY, DD-MMM-YY, Month DD YYYY, DD.MM.YYYY, YYYY/MM/DD, MMM DD, YYYY, DD-MM-YYYY |
| **Currency Symbols** | 5 types | $, £, €, USD, GBP mixed throughout |
| **Whitespace** | ~30% | Leading/trailing spaces, tabs |
| **Missing Values** | ~120 rows | Empty strings in various critical fields |
| **Empty Rows** | 10 rows | Completely empty rows scattered |
| **Duplicate Rows** | 20 rows | Exact duplicate records |
| **Negative Values** | ~150 | Negative quantities and stock levels |
| **Mixed Case Columns** | All | UPPERCASE, lowercase, Spaces, Underscores |
| **Type Inconsistencies** | Throughout | Numbers stored as strings with symbols |
| **Missing IDs** | ~12% | Customer IDs, Invoices, etc. |

---

## 🧪 How to Test

### Step 1: Start the Application
```bash
cd /Users/shaiksohail/retailsight
streamlit run app.py
```

### Step 2: Navigate to Upload Tab
- Click on **📤 Upload & Analyse** tab
- Login if required

### Step 3: Upload the File
- Click **Browse files**
- Select: `large_messy_test_data_400cols.csv`
- Wait for intelligent analysis to complete

### Step 4: Review Results

**Expected Quality Score:** 75-80%

**Expected Cleaning Actions:**
- ✅ Standardized column names (400 columns)
- ✅ Removed empty rows (10 rows)
- ✅ Removed duplicate rows (20 rows)
- ✅ Cleaned text fields (whitespace removal)
- ✅ Cleaned currency formatting (150+ columns)
- ✅ Standardized date formats (90+ columns)
- ✅ Fixed negative quantities (~150 values)
- ✅ Detected missing values (~120+ instances)

**Expected Insights:**
- Total revenue calculation
- Number of unique products
- Number of categories
- Date range coverage
- Store/location analysis
- Payment method distribution

**Expected Recommendations:**
- Data quality improvement suggestions
- Column standardization advice
- Missing data handling recommendations
- Business process improvements

---

## ⚡ Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| **Upload Time** | 2-5 seconds |
| **Analysis Time** | 5-15 seconds |
| **Quality Assessment** | < 3 seconds |
| **Column Detection** | < 5 seconds |
| **Auto-Cleaning** | 5-10 seconds |
| **Insights Generation** | < 3 seconds |
| **Total Time** | 20-40 seconds |

---

## 📈 What This Tests

### Data Analyst Capabilities
- ✅ Large dataset handling (400 columns, 1000 rows)
- ✅ Complex date format detection (9 formats)
- ✅ Multi-currency processing (5 currency types)
- ✅ Whitespace cleaning at scale
- ✅ Duplicate detection across 400 columns
- ✅ Empty row detection
- ✅ Negative value correction
- ✅ Type conversion (strings to numbers)
- ✅ Column name standardization
- ✅ Missing value identification

### Business Analyst Capabilities
- ✅ Revenue calculation across multiple currencies
- ✅ Product analysis (27 product types)
- ✅ Category analysis (14 categories)
- ✅ Customer segmentation (5 segments)
- ✅ Location analysis (9 stores, 6 regions, 50 cities)
- ✅ Payment method analysis (6 methods)
- ✅ Performance metrics (ratings, reviews)
- ✅ Operational metrics (suppliers, lead times)
- ✅ Business metrics (conversion rates, CLV)

---

## 🎨 Sample Data Patterns

### Messy Date Examples
```
23-11-2024
November 13 2024
13.01.2024
13/01/24
20-May-24
2024/05/05
05.05.2024
```

### Messy Currency Examples
```
$2.50
£1.20
€3.45
USD 12.99
GBP 45.67
```

### Messy Whitespace Examples
```
"  Product_A  "
"   TXN81376        "
"      TXN84238   "
```

### Mixed Column Names
```
Transaction_ID_1
PRODUCT_SKU_65
product_category_71
Product Brand 85
  Product_Name_51  
```

---

## 🚀 Next Steps After Testing

1. **Verify All Cleaning Actions**
   - Check that all 10+ expected actions are logged
   - Verify data quality score is calculated
   - Confirm no errors during processing

2. **Review Business Insights**
   - Verify revenue calculations are accurate
   - Check product and category counts
   - Confirm date range detection

3. **Test Edge Cases**
   - Try filtering by specific columns
   - Test sorting on cleaned data
   - Verify data types after cleaning

4. **Performance Check**
   - Monitor processing time
   - Check memory usage
   - Verify responsive UI during analysis

5. **Export Cleaned Data**
   - Download the cleaned version
   - Verify all transformations applied correctly
   - Compare before/after statistics

---

## 📝 Notes

- **File Generation:** This file is generated using `generate_large_messy_data.py`
- **Reproducibility:** Uses fixed random seed (42) for consistent results
- **Realistic Data:** Based on actual retail/business data patterns
- **Comprehensive:** Tests all 10 column types detected by the system
- **Scalable:** Can be regenerated with different sizes (modify script)

---

## 🔄 Regenerate This File

If you need to create a new version with different parameters:

```bash
cd /Users/shaiksohail/retailsight
python3 generate_large_messy_data.py
```

Modify the script to change:
- Number of rows (currently 1000)
- Number of columns (currently 400)
- Messiness level (percentage of issues)
- Data patterns (products, categories, etc.)

---

## ✅ Success Criteria

The intelligent analyst feature is working correctly if:

1. ✅ File uploads without errors
2. ✅ Quality score is calculated (75-80% expected)
3. ✅ 10+ cleaning actions are identified and executed
4. ✅ All 400 columns are processed
5. ✅ Column types are correctly detected
6. ✅ Business insights are generated
7. ✅ Recommendations are provided
8. ✅ Processing completes within 40 seconds
9. ✅ Cleaned data can be downloaded
10. ✅ No application crashes or errors

---

**Ready to test!** 🎉

Upload `large_messy_test_data_400cols.csv` in the RetailSight app and watch the intelligent analyst work its magic across 400 columns of messy business data!
