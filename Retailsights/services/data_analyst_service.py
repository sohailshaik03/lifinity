# services/data_analyst_service.py
"""
Senior Data Analyst Service - Automatically handles messy data uploads
like a professional data analyst would.

This service:
1. Detects data quality issues
2. Automatically cleans and fixes common problems
3. Generates insights and recommendations
4. Provides detailed quality reports
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import re
from ..logger import logger


class DataAnalystService:
    """
    Professional-grade data analysis and cleaning service.
    Handles messy business data uploads intelligently.
    """

    # ================================================================
    # 1. DATA QUALITY ASSESSMENT
    # ================================================================

    @staticmethod
    def assess_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive data quality assessment.
        Returns detailed report like a senior analyst would provide.
        """
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "issues_found": [],
            "warnings": [],
            "recommendations": [],
            "data_types": {},
            "missing_data": {},
            "duplicates": 0,
            "quality_score": 100.0,  # Start at 100%, deduct for issues
        }

        # Check for empty data
        if df.empty:
            report["issues_found"].append("Dataset is completely empty")
            report["quality_score"] = 0
            return report

        # Analyze each column
        for col in df.columns:
            # Data type detection
            report["data_types"][col] = str(df[col].dtype)

            # Missing data analysis
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            report["missing_data"][col] = {
                "count": int(missing_count),
                "percentage": round(missing_pct, 2),
            }

            if missing_pct > 0:
                if missing_pct > 50:
                    report["issues_found"].append(
                        f"Column '{col}' has {missing_pct:.1f}% missing data (critical)"
                    )
                    report["quality_score"] -= 10
                elif missing_pct > 20:
                    report["warnings"].append(
                        f"Column '{col}' has {missing_pct:.1f}% missing data (moderate)"
                    )
                    report["quality_score"] -= 5

        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            report["duplicates"] = int(duplicates)
            report["warnings"].append(
                f"Found {duplicates} duplicate rows ({(duplicates/len(df)*100):.1f}%)"
            )
            report["quality_score"] -= 5

        # Generate recommendations
        if report["quality_score"] >= 90:
            report["recommendations"].append("✅ Data quality is excellent!")
        elif report["quality_score"] >= 70:
            report["recommendations"].append(
                "⚠️ Data quality is good but could be improved"
            )
        else:
            report["recommendations"].append(
                "🔴 Data quality needs attention before analysis"
            )

        report["quality_score"] = max(0, report["quality_score"])

        return report

    # ================================================================
    # 2. INTELLIGENT COLUMN DETECTION
    # ================================================================

    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        Intelligently detect what each column represents.
        Goes beyond simple names to analyze actual data patterns.
        """
        column_map = {}

        for col in df.columns:
            col_lower = col.strip().lower()
            sample_data = df[col].dropna().head(100)

            # Date/Time detection
            if DataAnalystService._is_date_column(col_lower, sample_data):
                if "time" in col_lower and "date" not in col_lower:
                    column_map[col] = "time"
                else:
                    column_map[col] = "date"

            # Product/Item detection
            elif DataAnalystService._is_product_column(col_lower, sample_data):
                column_map[col] = "product"

            # Quantity detection
            elif DataAnalystService._is_quantity_column(col_lower, sample_data):
                column_map[col] = "quantity"

            # Price/Amount detection
            elif DataAnalystService._is_price_column(col_lower, sample_data):
                column_map[col] = "price"

            # Category detection
            elif DataAnalystService._is_category_column(col_lower, sample_data):
                column_map[col] = "category"

            # SKU/Barcode detection
            elif DataAnalystService._is_sku_column(col_lower, sample_data):
                column_map[col] = "sku"

            # Customer detection
            elif DataAnalystService._is_customer_column(col_lower, sample_data):
                column_map[col] = "customer"

            # Store/Location detection
            elif DataAnalystService._is_location_column(col_lower, sample_data):
                column_map[col] = "location"

        return column_map

    @staticmethod
    def _is_date_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains dates"""
        date_keywords = ["date", "day", "dt", "timestamp", "when", "created", "updated"]
        if any(kw in col_name for kw in date_keywords):
            return True

        # Try parsing sample data
        try:
            pd.to_datetime(sample_data.iloc[:5], errors="coerce")
            return True
        except (ValueError, TypeError, AttributeError):
            return False

    @staticmethod
    def _is_product_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains product names"""
        product_keywords = [
            "product",
            "item",
            "name",
            "description",
            "article",
            "goods",
        ]
        return any(kw in col_name for kw in product_keywords)

    @staticmethod
    def _is_quantity_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains quantities"""
        qty_keywords = ["qty", "quantity", "units", "count", "amount", "pcs", "pieces"]
        if any(kw in col_name for kw in qty_keywords):
            return True

        # Check if numeric and looks like quantities (integers)
        try:
            numeric_data = pd.to_numeric(sample_data, errors="coerce")
            if numeric_data.notna().sum() > 0:
                # Quantities are usually small integers
                return (numeric_data >= 0).all() and (numeric_data < 10000).all()
        except (ValueError, TypeError):
            pass
        return False

    @staticmethod
    def _is_price_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains prices"""
        price_keywords = [
            "price",
            "amount",
            "cost",
            "value",
            "revenue",
            "total",
            "subtotal",
        ]
        if any(kw in col_name for kw in price_keywords):
            return True

        # Check if numeric with decimal places (typical for money)
        try:
            numeric_data = pd.to_numeric(sample_data, errors="coerce")
            if numeric_data.notna().sum() > 0:
                # Prices usually have decimals
                has_decimals = (numeric_data % 1 != 0).any()
                return has_decimals and (numeric_data >= 0).all()
        except (ValueError, TypeError):
            pass
        return False

    @staticmethod
    def _is_category_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains categories"""
        cat_keywords = [
            "category",
            "dept",
            "department",
            "section",
            "type",
            "class",
            "group",
        ]
        if any(kw in col_name for kw in cat_keywords):
            return True

        # Categories typically have limited unique values (< 50)
        try:
            unique_count = sample_data.nunique()
            return 2 <= unique_count <= 50
        except (ValueError, TypeError):
            pass
        return False

    @staticmethod
    def _is_sku_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains SKUs or barcodes"""
        sku_keywords = ["sku", "code", "barcode", "upc", "ean", "id"]
        return any(kw in col_name for kw in sku_keywords)

    @staticmethod
    def _is_customer_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains customer data"""
        customer_keywords = ["customer", "client", "user", "member"]
        return any(kw in col_name for kw in customer_keywords)

    @staticmethod
    def _is_location_column(col_name: str, sample_data: pd.Series) -> bool:
        """Check if column contains location/store data"""
        location_keywords = ["store", "shop", "location", "branch", "site", "outlet"]
        return any(kw in col_name for kw in location_keywords)

    # ================================================================
    # 3. AUTOMATIC DATA CLEANING
    # ================================================================

    @staticmethod
    def auto_clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Automatically clean messy data like a senior analyst would.
        Returns cleaned dataframe and list of actions taken.
        """
        df = df.copy()
        actions = []

        # 1. Remove completely empty rows and columns
        initial_rows = len(df)
        df = df.dropna(how="all")
        removed_rows = initial_rows - len(df)
        if removed_rows > 0:
            actions.append(f"✓ Removed {removed_rows} completely empty rows")

        initial_cols = len(df.columns)
        df = df.dropna(axis=1, how="all")
        removed_cols = initial_cols - len(df.columns)
        if removed_cols > 0:
            actions.append(f"✓ Removed {removed_cols} completely empty columns")

        # 2. Clean column names
        original_cols = df.columns.tolist()
        df.columns = [
            col.strip().lower().replace(" ", "_").replace("-", "_")
            for col in df.columns
        ]
        if df.columns.tolist() != original_cols:
            actions.append("✓ Standardized column names (lowercase, underscores)")

        # 3. Remove duplicate rows
        initial_rows = len(df)
        df = df.drop_duplicates()
        removed_dups = initial_rows - len(df)
        if removed_dups > 0:
            actions.append(f"✓ Removed {removed_dups} duplicate rows")

        # 4. Clean text fields (trim whitespace)
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["nan", "NaN", "None", ""], np.nan)

        actions.append("✓ Cleaned text fields (removed extra spaces)")

        # 5. Fix common data entry errors
        df = DataAnalystService._fix_common_errors(df, actions)

        # 6. Handle negative values in quantities/prices
        for col in df.columns:
            if "quantity" in col.lower() or "qty" in col.lower():
                if pd.api.types.is_numeric_dtype(df[col]):
                    negatives = (df[col] < 0).sum()
                    if negatives > 0:
                        df[col] = df[col].abs()
                        actions.append(
                            f"✓ Converted {negatives} negative quantities to positive"
                        )

            if "price" in col.lower() or "cost" in col.lower():
                if pd.api.types.is_numeric_dtype(df[col]):
                    negatives = (df[col] < 0).sum()
                    if negatives > 0:
                        df[col] = df[col].abs()
                        actions.append(
                            f"✓ Converted {negatives} negative prices to positive"
                        )

        return df, actions

    @staticmethod
    def _fix_common_errors(df: pd.DataFrame, actions: List[str]) -> pd.DataFrame:
        """Fix common data entry errors"""

        # Fix price formatting (remove currency symbols, commas)
        for col in df.columns:
            if "price" in col.lower() or "amount" in col.lower():
                if df[col].dtype == "object":
                    # Remove common currency symbols
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace("$", "", regex=False)
                        .str.replace("£", "", regex=False)
                        .str.replace("€", "", regex=False)
                        .str.replace("¥", "", regex=False)
                        .str.replace(",", "", regex=False)
                        .str.strip()
                    )
                    actions.append(f"✓ Cleaned currency formatting in '{col}'")

        # Fix date formats - robust multi-pass parser
        for col in df.columns:
            if "date" in col.lower():
                try:
                    # Strategy: Parse each value individually with multiple formats
                    def parse_flexible_date(val):
                        if pd.isna(val) or str(val).strip().lower() == 'nan':
                            return pd.NaT
                        
                        val_str = str(val).strip()
                        
                        # Try common formats in order of likelihood
                        formats = [
                            '%Y-%m-%d',      # 2024-11-23
                            '%d-%m-%Y',      # 23-11-2024
                            '%m/%d/%Y',      # 11/23/2024
                            '%d/%m/%Y',      # 23/11/2024
                            '%Y/%m/%d',      # 2024/11/23
                            '%d-%b-%y',      # 20-May-24
                            '%d-%B-%y',      # 20-May-24
                            '%m/%d/%y',      # 11/23/24
                            '%d/%m/%y',      # 23/11/24
                            '%d.%m.%Y',      # 23.11.2024
                            '%Y.%m.%d',      # 2024.11.23
                            '%B %d %Y',      # January 13 2024
                            '%B %d, %Y',     # January 13, 2024
                            '%b %d, %Y',     # Oct 06, 2024
                            '%d %B %Y',      # 23 November 2024
                            '%d %b %Y',      # 23 Nov 2024
                        ]
                        
                        for fmt in formats:
                            try:
                                return pd.to_datetime(val_str, format=fmt)
                            except:
                                continue
                        
                        # Last resort: let pandas figure it out
                        try:
                            return pd.to_datetime(val_str, dayfirst=True)
                        except:
                            return pd.NaT
                    
                    df[col] = df[col].apply(parse_flexible_date)
                    actions.append(f"✓ Standardized date format in '{col}'")
                except Exception as e:
                    pass

        return df

    # ================================================================
    # 4. BUSINESS INSIGHTS GENERATION
    # ================================================================

    @staticmethod
    def generate_insights(df: pd.DataFrame, column_map: Dict[str, str]) -> List[str]:
        """
        Generate business insights like a senior analyst would.
        """
        insights = []

        # Revenue insights
        if "price" in column_map.values() and "quantity" in column_map.values():
            price_col = [k for k, v in column_map.items() if v == "price"][0]
            qty_col = [k for k, v in column_map.items() if v == "quantity"][0]

            try:
                price_data = pd.to_numeric(df[price_col], errors="coerce")
                qty_data = pd.to_numeric(df[qty_col], errors="coerce")

                revenue = (price_data * qty_data).sum()
                avg_transaction = (price_data * qty_data).mean()

                insights.append(
                    f"💰 **Total Revenue**: ${revenue:,.2f} from {len(df):,} transactions"
                )
                insights.append(
                    f"📊 **Average Transaction Value**: ${avg_transaction:,.2f}"
                )
            except:
                pass

        # Product insights
        if "product" in column_map.values():
            product_col = [k for k, v in column_map.items() if v == "product"][0]
            unique_products = df[product_col].nunique()
            insights.append(f"🛒 **Unique Products**: {unique_products:,}")

        # Category insights
        if "category" in column_map.values():
            cat_col = [k for k, v in column_map.items() if v == "category"][0]
            unique_categories = df[cat_col].nunique()
            insights.append(f"📂 **Product Categories**: {unique_categories}")

        # Date range insights
        if "date" in column_map.values():
            date_col = [k for k, v in column_map.items() if v == "date"][0]
            try:
                dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
                if len(dates) > 0:
                    date_range = (dates.max() - dates.min()).days
                    insights.append(
                        f"📅 **Date Range**: {date_range} days ({dates.min().date()} to {dates.max().date()})"
                    )
            except:
                pass

        # Volume insights
        total_rows = len(df)
        if total_rows > 10000:
            insights.append(f"🔥 **Large Dataset**: {total_rows:,} records (excellent!)")
        elif total_rows > 1000:
            insights.append(f"✅ **Good Sample Size**: {total_rows:,} records")
        else:
            insights.append(f"⚠️ **Small Dataset**: {total_rows:,} records (limited analysis)")

        return insights

    # ================================================================
    # 5. SMART RECOMMENDATIONS
    # ================================================================

    @staticmethod
    def generate_recommendations(
        df: pd.DataFrame, quality_report: Dict[str, Any], column_map: Dict[str, str]
    ) -> List[str]:
        """
        Generate actionable recommendations like a business analyst would.
        """
        recommendations = []

        # Data quality recommendations
        if quality_report["quality_score"] < 70:
            recommendations.append(
                "🔴 **Urgent**: Improve data quality by addressing missing values and duplicates"
            )

        # Column recommendations
        required_cols = ["date", "product", "quantity", "price"]
        missing_cols = [col for col in required_cols if col not in column_map.values()]

        if missing_cols:
            recommendations.append(
                f"⚠️ **Missing Data**: Add {', '.join(missing_cols)} columns for complete analysis"
            )

        # Business recommendations
        if "category" not in column_map.values():
            recommendations.append(
                "💡 **Tip**: Add product categories to unlock category-level analytics"
            )

        if "date" in column_map.values():
            date_col = [k for k, v in column_map.items() if v == "date"][0]
            try:
                dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
                if len(dates) > 0:
                    date_range = (dates.max() - dates.min()).days
                    if date_range > 365:
                        recommendations.append(
                            "📈 **Opportunity**: Long historical data enables trend analysis and forecasting"
                        )
                    elif date_range < 30:
                        recommendations.append(
                            "⏰ **Note**: Upload more historical data for better insights"
                        )
            except:
                pass

        # Performance recommendations
        if len(df) > 50000:
            recommendations.append(
                "⚡ **Performance**: Large dataset detected. Consider filtering or aggregating for faster analysis"
            )

        if not recommendations:
            recommendations.append(
                "✅ **Excellent**: Your data is clean and ready for analysis!"
            )

        return recommendations

    # ================================================================
    # 6. MASTER ANALYSIS FUNCTION
    # ================================================================

    @staticmethod
    def analyze_and_clean(
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Master function: Analyze, clean, and report on data like a senior analyst.

        Returns:
            - Cleaned dataframe
            - Comprehensive analysis report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "original_shape": df.shape,
            "quality_assessment": {},
            "column_detection": {},
            "cleaning_actions": [],
            "insights": [],
            "recommendations": [],
            "final_shape": None,
        }

        logger.info("🔍 Starting intelligent data analysis...")

        # Step 1: Assess data quality
        report["quality_assessment"] = DataAnalystService.assess_data_quality(df)

        # Step 2: Auto-clean
        df_cleaned, cleaning_actions = DataAnalystService.auto_clean(df)
        report["cleaning_actions"] = cleaning_actions

        # Step 3: Detect column types
        column_map = DataAnalystService.detect_column_types(df_cleaned)
        report["column_detection"] = column_map

        # Step 4: Generate insights
        insights = DataAnalystService.generate_insights(df_cleaned, column_map)
        report["insights"] = insights

        # Step 5: Generate recommendations
        recommendations = DataAnalystService.generate_recommendations(
            df_cleaned, report["quality_assessment"], column_map
        )
        report["recommendations"] = recommendations

        report["final_shape"] = df_cleaned.shape

        logger.info(
            f"✅ Analysis complete: {df.shape} → {df_cleaned.shape} (Quality: {report['quality_assessment']['quality_score']:.1f}%)"
        )

        return df_cleaned, report
