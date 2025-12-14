from __future__ import annotations

import io
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from ..repositories.products_repo import create_product, add_expiry_record
from ..logger import logger


class BulkImportService:
    """Service for bulk product and expiry record imports."""

    REQUIRED_COLS = ["sku", "name"]
    OPTIONAL_COLS = ["category", "cost_price", "selling_price"]
    EXPIRY_COLS = ["batch_number", "quantity_received", "expiry_date", "received_date"]

    @staticmethod
    def validate_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate CSV structure. Returns (is_valid, error_messages)."""
        errors = []

        if df.empty:
            errors.append("CSV is empty")
            return False, errors

        # Check required columns
        for col in BulkImportService.REQUIRED_COLS:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        # Check for SKU duplicates within file
        if "sku" in df.columns:
            dups = df[df.duplicated(subset=["sku"], keep=False)]
            if not dups.empty:
                errors.append(f"Duplicate SKUs found: {dups['sku'].unique().tolist()}")

        return len(errors) == 0, errors

    @staticmethod
    def import_products_from_csv(
        csv_bytes: bytes,
        shop_id: int,
        include_expiry: bool = False,
    ) -> Dict[str, Any]:
        """Import products (and optionally expiry records) from CSV bytes.

        Returns: {success: bool, created: int, errors: List[str], warnings: List[str]}
        """
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes))
        except Exception as e:
            logger.error(f"CSV parse error: {e}")
            return {"success": False, "created": 0, "errors": [f"CSV parse error: {e}"], "warnings": []}

        is_valid, validation_errors = BulkImportService.validate_csv(df)
        if not is_valid:
            return {"success": False, "created": 0, "errors": validation_errors, "warnings": []}

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        created = 0
        errors = []
        warnings = []

        for idx, row in df.iterrows():
            try:
                sku = str(row.get("sku", "")).strip()
                name = str(row.get("name", "")).strip()

                if not sku or not name:
                    warnings.append(f"Row {idx + 2}: SKU or name empty, skipped")
                    continue

                # Optional fields
                category = str(row.get("category", "")).strip() or None
                cost_price = None
                selling_price = None

                try:
                    if "cost_price" in row and pd.notna(row["cost_price"]):
                        cost_price = float(row["cost_price"])
                    if "selling_price" in row and pd.notna(row["selling_price"]):
                        selling_price = float(row["selling_price"])
                except ValueError:
                    warnings.append(f"Row {idx + 2}: Invalid price format, using None")

                # Create product
                product_id = create_product(
                    shop_id=shop_id,
                    sku=sku,
                    name=name,
                    category=category,
                    cost_price=cost_price,
                    selling_price=selling_price,
                )

                if not product_id:
                    errors.append(f"Row {idx + 2}: Failed to create product {sku}")
                    continue

                # Optional: add expiry record
                if include_expiry and "expiry_date" in row and pd.notna(row["expiry_date"]):
                    try:
                        qty_received = int(row.get("quantity_received", 0) or 0)
                        expiry_date = pd.to_datetime(row["expiry_date"]).strftime("%Y-%m-%d")
                        batch = str(row.get("batch_number", "")).strip() or None
                        received_date = None
                        if "received_date" in row and pd.notna(row["received_date"]):
                            received_date = pd.to_datetime(row["received_date"]).strftime("%Y-%m-%d")

                        add_expiry_record(
                            product_id=product_id,
                            quantity_received=qty_received,
                            expiry_date=expiry_date,
                            batch_number=batch,
                            received_date=received_date,
                        )
                    except Exception as e:
                        warnings.append(f"Row {idx + 2}: Failed to add expiry record: {e}")

                created += 1

            except Exception as e:
                logger.exception(f"Import row {idx + 2} error")
                errors.append(f"Row {idx + 2}: {str(e)}")

        return {"success": len(errors) == 0, "created": created, "errors": errors, "warnings": warnings}

    @staticmethod
    def generate_csv_template() -> bytes:
        """Generate a CSV template for bulk import."""
        template_data = {
            "sku": ["SKU001", "SKU002"],
            "name": ["Product A", "Product B"],
            "category": ["Dairy", "Frozen"],
            "cost_price": [2.50, 3.00],
            "selling_price": [5.99, 6.99],
            "batch_number": ["BATCH-001", "BATCH-002"],
            "quantity_received": [100, 50],
            "expiry_date": ["2025-12-31", "2025-11-30"],
            "received_date": ["2025-11-01", "2025-11-05"],
        }
        df = pd.DataFrame(template_data)
        return df.to_csv(index=False).encode("utf-8")
