# repositories/sales_repo.py
from __future__ import annotations

from typing import Any, Dict, List

from ..db_orm import get_session
from ..models import SalesTransaction, SalesLine
from ..logger import log
from typing import Any, Dict, List
from datetime import datetime
from sqlalchemy import func


class SalesRepository:
    """
    Data access layer for sales-related tables.
    Handles:
    - uploaded_files
    - sales_transactions
    - sales_lines
    """

    # ------------------------------------------------------
    # INSERTS
    # ------------------------------------------------------
    @staticmethod
    def insert_uploaded_file(
        shop_id: int, user_id: int, filename: str, rows: int
    ) -> int:
        """
        Inserts a row into uploaded_files table and returns the ID.
        """
        session = get_session()
        try:
            # uploaded_files table not modeled; use raw insert
            session.execute(
                "INSERT INTO uploaded_files (shop_id, user_id, original_name, rows_imported) VALUES (:s, :u, :n, :r)",
                {"s": shop_id, "u": user_id, "n": filename, "r": rows},
            )
            session.commit()
            # cannot get lastrowid easily here; return 0 as placeholder
            return 0
        except Exception as e:
            log.exception("Failed to insert uploaded file: %s", e)
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def insert_transactions(
        shop_id: int, upload_id: int, tx_rows: List[Dict[str, Any]]
    ) -> None:
        """
        Bulk inserts the header-level transactions.
        tx_rows: [{transaction_dt, total_revenue, total_items}, ...]
        """
        if not tx_rows:
            return

        if not tx_rows:
            return
        session = get_session()
        try:
            for r in tx_rows:
                st = SalesTransaction(
                    shop_id=shop_id,
                    transaction_dt=r.get("transaction_dt", datetime.utcnow()),
                    total_amount=r.get("total_revenue", 0.0),
                )
                session.add(st)
            session.commit()
        except Exception as e:
            log.exception("Failed to bulk insert transactions: %s", e)
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def insert_sales_lines(line_rows: List[Dict[str, Any]]) -> None:
        """
        Bulk inserts line-level rows.
        line_rows: [{transaction_id, product_name_raw, quantity, unit_price, line_revenue, category_name_raw}, ...]
        """
        if not line_rows:
            return

        if not line_rows:
            return
        session = get_session()
        try:
            for r in line_rows:
                sl = SalesLine(
                    transaction_id=r.get("transaction_id"),
                    product_id=r.get("product_id", None),
                    quantity=r.get("quantity", 0),
                    unit_price=r.get("unit_price", 0.0),
                )
                session.add(sl)
            session.commit()
        except Exception as e:
            log.exception("Failed to bulk insert sales lines: %s", e)
            session.rollback()
            raise
        finally:
            session.close()

    # ------------------------------------------------------
    # READS (used by analytics_service)
    # ------------------------------------------------------
    @staticmethod
    def get_transactions_for_upload(
        shop_id: int, upload_id: int
    ) -> List[Dict[str, Any]]:
        """
        Returns all transactions for a given shop + source_file_id.
        Used to map tx_key → transaction_id after bulk insert.
        """
        session = get_session()
        try:
            rows = (
                session.query(SalesTransaction)
                .filter(SalesTransaction.shop_id == shop_id)
                .all()
            )
            return [{"id": r.id, "transaction_dt": r.transaction_dt} for r in rows]
        except Exception as e:
            log.exception("Failed to fetch transactions for upload: %s", e)
            raise
        finally:
            session.close()

    @staticmethod
    def get_sales_lines_for_period(
        shop_id: int, start_dt, end_dt
    ) -> List[Dict[str, Any]]:
        """
        Reads sales lines for a given shop and date range.
        Used for History & Manager dashboards.
        """
        session = get_session()
        try:
            rows = (
                session.query(SalesLine, SalesTransaction)
                .join(SalesTransaction, SalesLine.transaction_id == SalesTransaction.id)
                .filter(SalesTransaction.shop_id == shop_id)
                .filter(SalesTransaction.transaction_dt >= start_dt)
                .filter(SalesTransaction.transaction_dt < end_dt)
                .order_by(SalesTransaction.transaction_dt.asc())
                .all()
            )
            result: List[Dict[str, Any]] = []
            for sl, st in rows:
                result.append({
                    "line_id": sl.id,
                    "datetime": st.transaction_dt,
                    "product": getattr(sl, 'product_name_raw', None) or sl.product_id,
                    "quantity": sl.quantity,
                    "price": sl.unit_price,
                    "revenue": sl.quantity * sl.unit_price,
                    "category": getattr(sl, 'category_name_raw', None),
                })
            return result
        except Exception as e:
            log.exception("Failed to fetch sales lines for period: %s", e)
            raise
        finally:
            session.close()
