# services/analytics_service.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from dateutil import parser

from ..logger import log
from ..repositories.sales_repo import SalesRepository
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
import warnings
from .storage_service import Storage

REQUIRED_COLS = ["date", "product", "quantity", "price"]


class AnalyticsService:
    """
    Enterprise analytics layer.

    Responsibilities:
    - Handle POS file ingestion (CSV/XLSX)
    - Normalise & preprocess uploaded data
    - Persist to MySQL via SalesRepository
    - Load historical sales from DB for reports/dashboards
    """

    # ------------------------------------------------------------------
    # 1) FILE LOAD + PREPROCESS FOR UPLOAD
    # ------------------------------------------------------------------
    @staticmethod
    def load_file(file) -> pd.DataFrame:
        """
        Load CSV/XLSX with robust error handling.
        """
        try:
            if file.name.lower().endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            return df

        except Exception as e:
            log.exception("File load error")
            raise ValueError(
                "Unable to read file. The file may be corrupted or invalid."
            ) from e

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise column names across different POS exports.
        Maps date/time/product/quantity/price/category columns
        into a standard schema.
        
        If multiple columns map to the same name (e.g., multiple date columns),
        keep only the first occurrence and drop duplicates.
        """
        col_map: Dict[str, str] = {}
        
        # Track which standard columns we've already found
        found_cols = set()

        for col in df.columns:
            c = col.strip().lower()

            # Only map the FIRST occurrence of each standard column type
            if "date" in c and "date" not in found_cols:
                col_map[col] = "date"
                found_cols.add("date")
            elif "time" in c and "date" not in c and "time" not in found_cols:
                col_map[col] = "time"
                found_cols.add("time")
            elif any(x in c for x in ["product", "item", "sku"]) and "product" not in found_cols:
                col_map[col] = "product"
                found_cols.add("product")
            elif ("qty" in c or "quantity" in c or "units" in c) and "quantity" not in found_cols:
                col_map[col] = "quantity"
                found_cols.add("quantity")
            elif ("price" in c or "amount" in c) and "price" not in found_cols:
                col_map[col] = "price"
                found_cols.add("price")
            elif ("category" in c or "dept" in c) and "category" not in found_cols:
                col_map[col] = "category"
                found_cols.add("category")

        df = df.rename(columns=col_map)

        # Ensure required columns exist (even if empty)
        for req in REQUIRED_COLS:
            if req not in df.columns:
                df[req] = np.nan

        return df

    @staticmethod
    def preprocess(df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess freshly uploaded sales data:
        - validate required fields
        - parse numbers
        - build datetime from date + time columns
        - compute revenue
        - normalise category
        """
        # Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Drop rows missing core fields
        df = df.dropna(subset=["date", "product", "quantity", "price"], how="any")

        # Numeric conversion
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

        # Build datetime
        def parse_dt(row):
            try:
                date_val = row["date"]
                
                # If already a datetime, use it directly
                if isinstance(date_val, (pd.Timestamp, datetime)):
                    return date_val
                
                # Otherwise parse string
                d = str(date_val)
                t = str(row.get("time")) if "time" in row else ""
                return parser.parse(f"{d} {t}".strip())
            except Exception:
                return None

        df["datetime"] = df.apply(parse_dt, axis=1)
        df = df.dropna(subset=["datetime"])
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

        # revenue
        df["revenue"] = df["quantity"] * df["price"]

        # category
        if "category" not in df.columns:
            df["category"] = "Uncategorized"
        else:
            df["category"] = df["category"].fillna("Uncategorized")

        return df

    # ------------------------------------------------------------------
    # 2) SAVE UPLOAD → DB
    # ------------------------------------------------------------------
    @staticmethod
    def save_to_db(
        df: pd.DataFrame,
        shop_id: int,
        user_id: int,
        filename: str,
    ) -> Tuple[int, int]:
        """
        Full DB pipeline:
        - uploaded_files log
        - sales_transactions
        - sales_lines

        Returns: (num_transactions, num_lines)
        """
        if df.empty:
            return 0, 0

        # 1) Log uploaded file
        upload_id = SalesRepository.insert_uploaded_file(
            shop_id, user_id, filename, len(df)
        )

        df = df.copy()
        df["tx_key"] = df["datetime"].dt.floor("min")

        # 2) Build transaction header rows
        tx_rows = (
            df.groupby("tx_key")
            .agg(total_revenue=("revenue", "sum"), total_items=("quantity", "sum"))
            .reset_index()
        )

        tx_payload = []
        for _, r in tx_rows.iterrows():
            tx_payload.append(
                {
                    "transaction_dt": r["tx_key"],
                    "total_revenue": float(r["total_revenue"]),
                    "total_items": float(r["total_items"]),
                }
            )

        SalesRepository.insert_transactions(shop_id, upload_id, tx_payload)

        # 3) Fetch back inserted transactions to map tx_key → transaction_id
        tx_db_rows = SalesRepository.get_transactions_for_upload(shop_id, upload_id)
        tx_map = {row["transaction_dt"]: row["id"] for row in tx_db_rows}

        # 4) Build line items
        line_payload = []
        missing_tx = 0

        for _, row in df.iterrows():
            tx_id = tx_map.get(row["tx_key"])
            if not tx_id:
                missing_tx += 1
                continue
            line_payload.append(
                {
                    "transaction_id": tx_id,
                    "product_name_raw": row["product"],
                    "quantity": float(row["quantity"]),
                    "unit_price": float(row["price"]),
                    "line_revenue": float(row["revenue"]),
                    "category_name_raw": row["category"],
                }
            )

        if missing_tx:
            log.warning(
                "Some rows had no matching transaction_id. Skipped: %s", missing_tx
            )

        SalesRepository.insert_sales_lines(line_payload)

        return len(tx_payload), len(line_payload)

    # ------------------------------------------------------------------
    # 3) LOAD HISTORICAL SALES FROM DB (for History / Manager)
    # ------------------------------------------------------------------
    @staticmethod
    def preprocess_historical(df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess rows loaded from MySQL (sales_lines + transaction_dt):
        - ensure datetime is parsed
        - compute revenue if missing
        - add date_only, hour, day_of_week
        - normalise category
        """
        if df.empty:
            return df

        # datetime
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"])

        # numeric fields
        df["quantity"] = pd.to_numeric(df.get("quantity", 0), errors="coerce").fillna(0)
        df["price"] = pd.to_numeric(df.get("price", 0), errors="coerce").fillna(0)
        if "revenue" in df.columns:
            df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(
                df["quantity"] * df["price"]
            )
        else:
            df["revenue"] = df["quantity"] * df["price"]

        # category
        if "category" not in df.columns:
            df["category"] = "Uncategorized"
        else:
            df["category"] = df["category"].fillna("Uncategorized")

        # derived fields
        df["date_only"] = df["datetime"].dt.date
        df["hour"] = df["datetime"].dt.hour
        df["day_of_week"] = df["datetime"].dt.day_name()

        return df

    @staticmethod
    def load_sales_for_period(
        shop_id: int,
        start_dt: datetime,
        end_dt: datetime,
    ) -> pd.DataFrame:
        """
        Load sales lines for a given shop and date range from DB,
        and preprocess for analytics dashboards.
        """
        rows = SalesRepository.get_sales_lines_for_period(shop_id, start_dt, end_dt)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = AnalyticsService.preprocess_historical(df)
        return df

    # ------------------------------------------------------------------
    # 4) ANALYTICS & EXPORTS
    # ------------------------------------------------------------------
    @staticmethod
    def compute_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Return a small dict with high-level KPIs for the given dataframe."""
        if df.empty:
            return {
                "total_revenue": 0.0,
                "total_items": 0.0,
                "num_transactions": 0,
                "avg_basket": 0.0,
            }

        total_revenue = float(df["revenue"].sum())
        total_items = float(df["quantity"].sum())
        num_transactions = int(df["datetime"].dt.floor("min").nunique())
        avg_basket = float(total_revenue / num_transactions) if num_transactions else 0.0

        return {
            "total_revenue": total_revenue,
            "total_items": total_items,
            "num_transactions": num_transactions,
            "avg_basket": avg_basket,
        }

    @staticmethod
    def aggregate_time_series(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
        """Aggregate revenue and items by time frequency (D=day, H=hour, W=week)."""
        if df.empty:
            return pd.DataFrame()

        s = df.set_index("datetime").resample(freq).agg({"revenue": "sum", "quantity": "sum"})
        s = s.reset_index()
        return s

    @staticmethod
    def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        top = (
            df.groupby("product")
            .agg(units_sold=("quantity", "sum"), revenue=("revenue", "sum"))
            .reset_index()
            .sort_values("revenue", ascending=False)
            .head(n)
        )
        return top

    @staticmethod
    def forecast_sales(df: pd.DataFrame, periods: int = 7) -> pd.DataFrame:
        """Produce a simple forecast for revenue using ExponentialSmoothing.

        Returns a DataFrame with columns: `datetime`, `forecast`.
        """
        return AnalyticsService._forecast_sales_multi(df, periods=periods, method="holt")

    @staticmethod
    def _forecast_sales_multi(df: pd.DataFrame, periods: int = 7, method: str = "holt") -> pd.DataFrame:
        """Run forecasting using different methods: 'holt', 'arima', 'sklearn', 'prophet' (optional).

        Returns DataFrame(datetime, forecast)
        """
        if df.empty:
            return pd.DataFrame(columns=["datetime", "forecast"])

        ts = df.set_index("datetime")["revenue"].resample("D").sum().fillna(0)

        # Ensure enough history
        if len(ts) < 2:
            idx = pd.date_range(start=pd.Timestamp.now(), periods=periods, freq="D")
            return pd.DataFrame({"datetime": idx, "forecast": [0.0] * periods})

        method = method.lower()
        # Holt-Winters
        if method == "holt":
            try:
                seasonal = 7 if len(ts) >= 14 else None
                model = ExponentialSmoothing(
                    ts, trend="add", seasonal=("add" if seasonal else None), seasonal_periods=seasonal
                )
                fit = model.fit(optimized=True)
                pred = fit.forecast(periods)
            except Exception:
                pred = AnalyticsService._naive_forecast(ts, periods)

        elif method == "arima":
            try:
                order = (1, 1, 1)
                model = ARIMA(ts, order=order)
                fit = model.fit()
                pred = fit.forecast(steps=periods)
            except Exception:
                pred = AnalyticsService._naive_forecast(ts, periods)

        elif method == "sklearn":
            # Use a rolling-window regression (RandomForest) on lag features
            try:
                df_feat = pd.DataFrame({"y": ts})
                for lag in range(1, 8):
                    df_feat[f"lag_{lag}"] = df_feat["y"].shift(lag)
                df_feat = df_feat.dropna()
                if df_feat.empty:
                    pred = AnalyticsService._naive_forecast(ts, periods)
                else:
                    X = df_feat.drop(columns=["y"]).values
                    y = df_feat["y"].values
                    model = RandomForestRegressor(n_estimators=50, random_state=42)
                    model.fit(X, y)
                    last_row = df_feat.iloc[-1]
                    preds = []
                    window = last_row[[f"lag_{i}" for i in range(1, 8)]].values.tolist()
                    for _ in range(periods):
                        x_in = [window[-i] for i in range(1, 8)]
                        pred_val = model.predict([x_in])[0]
                        preds.append(pred_val)
                        window.append(pred_val)
                    idx = pd.date_range(start=ts.index[-1] + pd.Timedelta(days=1), periods=periods, freq="D")
                    pred = pd.Series(preds, index=idx)
            except Exception:
                pred = AnalyticsService._naive_forecast(ts, periods)

        elif method == "prophet":
            try:
                from prophet import Prophet

                ds = ts.reset_index()
                ds.columns = ["ds", "y"]
                m = Prophet()
                m.fit(ds)
                future = m.make_future_dataframe(periods=periods)
                fcst = m.predict(future)
                pred = fcst.set_index("ds")["yhat"].tail(periods)
            except Exception:
                pred = AnalyticsService._naive_forecast(ts, periods)

        else:
            pred = AnalyticsService._naive_forecast(ts, periods)

        out = pd.DataFrame({"datetime": pred.index, "forecast": pred.values})
        return out

    @staticmethod
    def _naive_forecast(ts: pd.Series, periods: int):
        last = float(ts.iloc[-1]) if len(ts) else 0.0
        idx = pd.date_range(start=ts.index[-1] + pd.Timedelta(days=1), periods=periods, freq="D")
        return pd.Series([last] * periods, index=idx)

    @staticmethod
    def export_csv_bytes(df: pd.DataFrame) -> bytes:
        """Return CSV bytes for the dataframe (usable for Streamlit download)."""
        return df.to_csv(index=False).encode("utf-8")

    @staticmethod
    def export_pdf_bytes(df: pd.DataFrame, summary: Dict[str, Any] | None = None, logo_path: str | None = None) -> bytes:
        """Create a professional PDF report using ReportLab and return bytes.

        The report contains a cover, KPIs, a timeseries chart image and a top-products table.
        """
        buffer = BytesIO()

        # Build matplotlib chart image for timeseries
        ts = AnalyticsService.aggregate_time_series(df, freq="D")
        chart_buf = BytesIO()
        fig, ax = plt.subplots(figsize=(8, 4))
        if not ts.empty:
            ax.plot(ts["datetime"], ts["revenue"], marker="o")
            ax.set_title("Daily revenue")
            ax.set_xlabel("Date")
            ax.set_ylabel("Revenue")
        else:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        fig.tight_layout()
        fig.savefig(chart_buf, format="png")
        plt.close(fig)
        chart_buf.seek(0)

        # Prepare document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Cover
        story.append(Paragraph("RetailSight - Sales Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 24))

        # KPIs
        kpis = summary or AnalyticsService.compute_summary(df)
        story.append(Paragraph("Key Performance Indicators", styles["Heading2"]))
        for k, v in kpis.items():
            story.append(Paragraph(f"<b>{k}:</b> {v}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Chart image
        story.append(Paragraph("Daily revenue", styles["Heading2"]))
        img = Image(chart_buf, width=450, height=225)
        story.append(img)
        story.append(Spacer(1, 12))

        # Top products
        top = AnalyticsService.top_products(df, n=10)
        if not top.empty:
            story.append(Paragraph("Top Products", styles["Heading2"]))
            data = [list(top.columns)] + top.values.tolist()
            tbl = Table(data, repeatRows=1)
            tbl.setStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
            story.append(tbl)

        doc.build(story)
        buffer.seek(0)
        return buffer.read()


# ----------------------------------------------------------------------
# Convenience function used by UI tabs (e.g. history_tab.py)
# ----------------------------------------------------------------------
def load_sales_for_period(
    shop_id: int, start_dt: datetime, end_dt: datetime
) -> pd.DataFrame:
    """
    Thin wrapper so tabs can simply import:

        from Retailsights.services.analytics_service import load_sales_for_period
    """
    return AnalyticsService.load_sales_for_period(shop_id, start_dt, end_dt)
