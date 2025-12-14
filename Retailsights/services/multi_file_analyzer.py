# services/multi_file_analyzer.py
"""
Multi-File Analysis Service
Enterprise-level cross-file analysis and insights
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
from .file_type_detector import FileType, FileTypeDetector


class MultiFileAnalyzer:
    """
    Professional multi-file analysis system.
    Joins and analyzes multiple business files together.
    Premium/Ultra Premium feature.
    """
    
    def __init__(self):
        self.loaded_files = {}
        self.file_types = {}
        self.join_history = []
    
    def add_file(self, name: str, df: pd.DataFrame, file_type: FileType = None):
        """Add a file to the multi-file analysis workspace"""
        if file_type is None:
            file_type, confidence, _ = FileTypeDetector.detect_file_type(df, name)
        
        self.loaded_files[name] = df
        self.file_types[name] = file_type
    
    def get_join_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for joining loaded files"""
        file_types_list = list(self.file_types.values())
        return FileTypeDetector.suggest_file_joins(file_types_list)
    
    def cross_file_analysis(self) -> Dict[str, Any]:
        """
        Perform comprehensive cross-file analysis.
        Ultra Premium feature.
        """
        if len(self.loaded_files) < 2:
            return {"error": "Need at least 2 files for cross-file analysis"}
        
        analysis = {
            "files_analyzed": len(self.loaded_files),
            "file_summary": {},
            "cross_file_insights": [],
            "recommended_joins": self.get_join_suggestions(),
            "data_quality_comparison": {}
        }
        
        # Summarize each file
        for name, df in self.loaded_files.items():
            analysis["file_summary"][name] = {
                "type": self.file_types[name].value,
                "rows": len(df),
                "columns": len(df.columns),
                "date_range": self._get_date_range(df),
                "key_metrics": self._get_key_metrics(df, self.file_types[name])
            }
        
        # Generate cross-file insights
        analysis["cross_file_insights"] = self._generate_cross_file_insights()
        
        # Compare data quality
        analysis["data_quality_comparison"] = self._compare_data_quality()
        
        return analysis
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, str]:
        """Extract date range from dataframe"""
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if not date_cols:
            return {}
        
        date_col = date_cols[0]
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            
            return {
                "start": str(min_date.date()) if pd.notna(min_date) else None,
                "end": str(max_date.date()) if pd.notna(max_date) else None,
                "days": int((max_date - min_date).days) if pd.notna(min_date) and pd.notna(max_date) else None
            }
        except:
            return {}
    
    def _get_key_metrics(self, df: pd.DataFrame, file_type: FileType) -> Dict[str, Any]:
        """Get key metrics specific to file type"""
        metrics = {}
        
        if file_type == FileType.ORDERS:
            # Revenue, order count, average order value
            revenue_cols = [col for col in df.columns if any(k in col.lower() for k in ['revenue', 'total', 'amount'])]
            if revenue_cols:
                metrics['total_revenue'] = float(df[revenue_cols[0]].sum())
                metrics['avg_order_value'] = float(df[revenue_cols[0]].mean())
            metrics['total_orders'] = len(df)
        
        elif file_type == FileType.RETURNS:
            # Return count, return rate
            metrics['total_returns'] = len(df)
            refund_cols = [col for col in df.columns if 'refund' in col.lower() or 'amount' in col.lower()]
            if refund_cols:
                metrics['total_refunds'] = float(df[refund_cols[0]].sum())
        
        elif file_type == FileType.INVENTORY:
            # Stock levels, SKU count
            quantity_cols = [col for col in df.columns if any(k in col.lower() for k in ['quantity', 'stock', 'available'])]
            if quantity_cols:
                metrics['total_stock_units'] = float(df[quantity_cols[0]].sum())
            metrics['total_skus'] = len(df)
        
        elif file_type == FileType.CUSTOMERS:
            # Customer count
            metrics['total_customers'] = len(df)
        
        return metrics
    
    def _generate_cross_file_insights(self) -> List[str]:
        """Generate insights from cross-file analysis"""
        insights = []
        
        # Check for orders + returns
        orders_file = self._find_file_by_type(FileType.ORDERS)
        returns_file = self._find_file_by_type(FileType.RETURNS)
        
        if orders_file and returns_file:
            orders_df = self.loaded_files[orders_file]
            returns_df = self.loaded_files[returns_file]
            
            return_rate = (len(returns_df) / len(orders_df)) * 100 if len(orders_df) > 0 else 0
            insights.append(f"📊 Return Rate: {return_rate:.1f}% ({len(returns_df)} returns out of {len(orders_df)} orders)")
        
        # Check for orders + customers
        customers_file = self._find_file_by_type(FileType.CUSTOMERS)
        if orders_file and customers_file:
            orders_df = self.loaded_files[orders_file]
            customers_df = self.loaded_files[customers_file]
            
            orders_per_customer = len(orders_df) / len(customers_df) if len(customers_df) > 0 else 0
            insights.append(f"👥 Average Orders per Customer: {orders_per_customer:.2f}")
        
        # Check for products + inventory
        products_file = self._find_file_by_type(FileType.PRODUCTS)
        inventory_file = self._find_file_by_type(FileType.INVENTORY)
        
        if products_file and inventory_file:
            products_df = self.loaded_files[products_file]
            inventory_df = self.loaded_files[inventory_file]
            
            stock_coverage = (len(inventory_df) / len(products_df)) * 100 if len(products_df) > 0 else 0
            insights.append(f"📦 Inventory Coverage: {stock_coverage:.1f}% of products have stock data")
        
        return insights
    
    def _compare_data_quality(self) -> Dict[str, Any]:
        """Compare data quality across files"""
        comparison = {}
        
        for name, df in self.loaded_files.items():
            total_cells = df.shape[0] * df.shape[1]
            missing_cells = df.isna().sum().sum()
            completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
            
            comparison[name] = {
                "completeness": round(completeness, 2),
                "missing_percentage": round((missing_cells / total_cells * 100), 2) if total_cells > 0 else 0,
                "duplicate_rows": int(df.duplicated().sum())
            }
        
        return comparison
    
    def _find_file_by_type(self, file_type: FileType) -> str:
        """Find first file matching a type"""
        for name, ftype in self.file_types.items():
            if ftype == file_type:
                return name
        return None
    
    def join_files(self, file1: str, file2: str, join_key: str, how: str = "inner") -> pd.DataFrame:
        """
        Join two files for combined analysis.
        Ultra Premium feature.
        """
        if file1 not in self.loaded_files or file2 not in self.loaded_files:
            raise ValueError(f"Files must be loaded first")
        
        df1 = self.loaded_files[file1]
        df2 = self.loaded_files[file2]
        
        # Find join columns
        join_col1 = self._find_column(df1, join_key)
        join_col2 = self._find_column(df2, join_key)
        
        if not join_col1 or not join_col2:
            raise ValueError(f"Join key '{join_key}' not found in both files")
        
        # Perform join
        joined = pd.merge(
            df1, df2,
            left_on=join_col1,
            right_on=join_col2,
            how=how,
            suffixes=('_file1', '_file2')
        )
        
        # Track join history
        self.join_history.append({
            "timestamp": datetime.now().isoformat(),
            "file1": file1,
            "file2": file2,
            "join_key": join_key,
            "how": how,
            "result_rows": len(joined)
        })
        
        return joined
    
    def _find_column(self, df: pd.DataFrame, search_term: str) -> str:
        """Find column matching search term"""
        search_lower = search_term.lower()
        for col in df.columns:
            if search_lower in col.lower():
                return col
        return None


class PowerBIExportService:
    """
    Power BI Export & Integration Service
    Premium/Ultra Premium feature
    """
    
    @staticmethod
    def export_to_powerbi_format(df: pd.DataFrame, filename: str = "export") -> bytes:
        """
        Export dataframe in Power BI compatible format (CSV with UTF-8 BOM).
        Premium/Ultra Premium feature.
        """
        # Add UTF-8 BOM for Excel/Power BI compatibility
        from io import BytesIO
        
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return output.getvalue()
    
    @staticmethod
    def create_powerbi_metadata(df: pd.DataFrame, file_type: FileType) -> Dict[str, Any]:
        """
        Create Power BI data model metadata.
        Ultra Premium feature.
        """
        metadata = {
            "table_name": file_type.value,
            "columns": [],
            "measures": [],
            "relationships": []
        }
        
        # Define columns with data types
        for col in df.columns:
            col_type = "text"
            if pd.api.types.is_numeric_dtype(df[col]):
                col_type = "number"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_type = "datetime"
            elif pd.api.types.is_bool_dtype(df[col]):
                col_type = "boolean"
            
            metadata["columns"].append({
                "name": col,
                "type": col_type,
                "format": "General"
            })
        
        # Suggest DAX measures based on file type
        if file_type == FileType.ORDERS:
            metadata["measures"] = [
                {"name": "Total Revenue", "formula": "SUM([revenue])"},
                {"name": "Total Orders", "formula": "COUNTROWS('orders')"},
                {"name": "Average Order Value", "formula": "DIVIDE([Total Revenue], [Total Orders])"}
            ]
        elif file_type == FileType.RETURNS:
            metadata["measures"] = [
                {"name": "Total Returns", "formula": "COUNTROWS('returns')"},
                {"name": "Return Rate", "formula": "DIVIDE([Total Returns], [Total Orders])"}
            ]
        
        return metadata
    
    @staticmethod
    def generate_powerbi_dashboard_json(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Power BI dashboard configuration JSON.
        Ultra Premium feature.
        """
        dashboard = {
            "name": "RetailSight Analytics Dashboard",
            "pages": [],
            "theme": "corporate"
        }
        
        # Add pages based on available data
        if "revenue" in str(analysis_results).lower():
            dashboard["pages"].append({
                "name": "Revenue Analysis",
                "visuals": [
                    {"type": "lineChart", "title": "Revenue Trend"},
                    {"type": "barChart", "title": "Top Products"},
                    {"type": "card", "title": "Total Revenue"}
                ]
            })
        
        if "customer" in str(analysis_results).lower():
            dashboard["pages"].append({
                "name": "Customer Insights",
                "visuals": [
                    {"type": "pieChart", "title": "Customer Segments"},
                    {"type": "scatterChart", "title": "CLV Analysis"},
                    {"type": "table", "title": "Top Customers"}
                ]
            })
        
        return dashboard
