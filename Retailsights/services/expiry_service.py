from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
import pandas as pd
from ..repositories.products_repo import get_discount_rules
from ..logger import logger


class ExpiryService:
    """Business logic for expiry, waste, and dynamic discount calculation."""

    @staticmethod
    def calculate_discount(
        shop_id: int,
        days_left: int,
        quantity_remaining: int,
        base_price: float,
    ) -> Dict[str, Any]:
        """
        Apply discount rules (M&S style: more aggressive discount as expiry approaches
        and quantity is higher).

        Returns: {discount_percent, discounted_price, reason}
        """
        rules = get_discount_rules(shop_id)

        best_rule = None
        for rule in rules:
            if (
                rule["days_left_min"] <= days_left <= rule["days_left_max"]
                and quantity_remaining >= rule["quantity_min"]
            ):
                if best_rule is None or rule["discount_percent"] > best_rule["discount_percent"]:
                    best_rule = rule

        if best_rule:
            discount_pct = float(best_rule["discount_percent"])
            discounted = base_price * (1 - discount_pct / 100)
            return {
                "discount_percent": discount_pct,
                "discounted_price": round(discounted, 2),
                "reason": best_rule["name"],
            }

        return {
            "discount_percent": 0.0,
            "discounted_price": base_price,
            "reason": "No discount applied",
        }

    @staticmethod
    def get_waste_summary(waste_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize waste records."""
        if not waste_records:
            return {"total_wasted": 0, "total_value": 0, "by_reason": {}}

        df = pd.DataFrame(waste_records)
        total_wasted = int(df["quantity_wasted"].sum())
        by_reason = df.groupby("reason")["quantity_wasted"].sum().to_dict()

        return {
            "total_wasted": total_wasted,
            "by_reason": by_reason,
        }
