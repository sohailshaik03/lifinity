# services/file_type_detector.py
"""
Intelligent File Type Detection Service
Automatically identifies what type of business data a file contains
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
from enum import Enum


class FileType(Enum):
    """Business file types we can detect and analyze"""
    ORDERS = "orders"
    RETURNS = "returns"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    CATEGORIES = "categories"
    REVIEWS = "reviews"
    SHIPMENTS = "shipments"
    PAYMENTS = "payments"
    SUPPLIERS = "suppliers"
    EMPLOYEES = "employees"
    UNKNOWN = "unknown"


class FileTypeDetector:
    """
    AI-powered file type detection.
    Analyzes column names and data patterns to identify file purpose.
    """
    
    # Column patterns for each file type
    FILE_PATTERNS = {
        FileType.ORDERS: {
            "required": ["order", "date"],
            "optional": ["product", "quantity", "price", "customer", "amount", "total", "status"],
            "keywords": ["order_id", "order_date", "order_number", "invoice", "purchase", "sale"]
        },
        
        FileType.RETURNS: {
            "required": ["return", "date"],
            "optional": ["order", "product", "reason", "refund", "status", "quantity"],
            "keywords": ["return_id", "return_date", "returned", "refund_amount", "return_reason"]
        },
        
        FileType.INVENTORY: {
            "required": ["product", "quantity"],
            "optional": ["stock", "warehouse", "location", "sku", "available", "reserved"],
            "keywords": ["stock_level", "inventory", "quantity_on_hand", "reorder_point", "warehouse"]
        },
        
        FileType.CUSTOMERS: {
            "required": ["customer"],
            "optional": ["name", "email", "phone", "address", "registration", "segment", "lifetime"],
            "keywords": ["customer_id", "customer_name", "email", "phone", "registration_date", "clv"]
        },
        
        FileType.PRODUCTS: {
            "required": ["product"],
            "optional": ["name", "category", "price", "sku", "description", "brand", "cost"],
            "keywords": ["product_id", "product_name", "sku", "category", "unit_price", "brand"]
        },
        
        FileType.CATEGORIES: {
            "required": ["category"],
            "optional": ["name", "description", "parent", "level", "hierarchy"],
            "keywords": ["category_id", "category_name", "parent_category", "subcategory"]
        },
        
        FileType.REVIEWS: {
            "required": ["review", "rating"],
            "optional": ["product", "customer", "date", "comment", "stars", "verified"],
            "keywords": ["review_id", "rating", "review_text", "review_date", "customer_review"]
        },
        
        FileType.SHIPMENTS: {
            "required": ["shipment", "date"],
            "optional": ["order", "carrier", "tracking", "status", "delivery", "warehouse"],
            "keywords": ["shipment_id", "tracking_number", "carrier", "ship_date", "delivery_date"]
        },
        
        FileType.PAYMENTS: {
            "required": ["payment", "amount"],
            "optional": ["order", "date", "method", "status", "transaction", "customer"],
            "keywords": ["payment_id", "transaction_id", "payment_method", "amount_paid", "payment_date"]
        },
        
        FileType.SUPPLIERS: {
            "required": ["supplier"],
            "optional": ["name", "contact", "product", "lead_time", "rating", "country"],
            "keywords": ["supplier_id", "supplier_name", "vendor", "lead_time", "supplier_rating"]
        },
        
        FileType.EMPLOYEES: {
            "required": ["employee"],
            "optional": ["name", "department", "position", "salary", "hire_date", "manager"],
            "keywords": ["employee_id", "employee_name", "department", "job_title", "hire_date"]
        }
    }
    
    @staticmethod
    def detect_file_type(df: pd.DataFrame, filename: str = "") -> Tuple[FileType, float, Dict[str, any]]:
        """
        Detect what type of business file this is.
        Returns: (file_type, confidence_score, detected_columns)
        """
        
        # Normalize column names
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Score each file type
        scores = {}
        detected_columns = {}
        
        for file_type, patterns in FileTypeDetector.FILE_PATTERNS.items():
            score, cols = FileTypeDetector._calculate_match_score(
                columns_lower, df, patterns
            )
            scores[file_type] = score
            detected_columns[file_type] = cols
        
        # Find best match
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        # If confidence is too low, mark as unknown
        if confidence < 30:
            best_type = FileType.UNKNOWN
        
        return best_type, confidence, detected_columns[best_type]
    
    @staticmethod
    def _calculate_match_score(
        columns: List[str], 
        df: pd.DataFrame,
        patterns: Dict[str, List[str]]
    ) -> Tuple[float, Dict[str, str]]:
        """
        Calculate how well the file matches a specific type.
        Returns score (0-100) and detected column mappings.
        """
        score = 0
        detected = {}
        
        # Check required keywords (must have at least one)
        required_found = 0
        for required in patterns["required"]:
            for col in columns:
                if required in col:
                    required_found += 1
                    detected[required] = col
                    break
        
        if required_found == 0:
            return 0, {}  # No required keywords found
        
        score += required_found * 25  # 25 points per required keyword
        
        # Check optional keywords
        optional_found = 0
        for optional in patterns["optional"]:
            for col in columns:
                if optional in col:
                    optional_found += 1
                    detected[optional] = col
                    break
        
        score += optional_found * 5  # 5 points per optional keyword
        
        # Check specific keywords
        keyword_found = 0
        for keyword in patterns["keywords"]:
            for col in columns:
                if keyword.lower() in col:
                    keyword_found += 1
                    break
        
        score += keyword_found * 10  # 10 points per specific keyword
        
        # Cap at 100
        return min(score, 100), detected
    
    @staticmethod
    def get_file_description(file_type: FileType) -> Dict[str, str]:
        """Get human-readable description of file type"""
        descriptions = {
            FileType.ORDERS: {
                "name": "Sales Orders",
                "description": "Customer purchase orders and transactions",
                "icon": "🛒",
                "analyses": ["Revenue trends", "Product performance", "Customer behavior", "Order patterns"]
            },
            FileType.RETURNS: {
                "name": "Product Returns",
                "description": "Customer return requests and refunds",
                "icon": "↩️",
                "analyses": ["Return rates", "Return reasons", "Product quality issues", "Refund analysis"]
            },
            FileType.INVENTORY: {
                "name": "Inventory Stock",
                "description": "Product stock levels and warehouse data",
                "icon": "📦",
                "analyses": ["Stock levels", "Reorder points", "Warehouse utilization", "SKU performance"]
            },
            FileType.CUSTOMERS: {
                "name": "Customer Database",
                "description": "Customer profiles and contact information",
                "icon": "👥",
                "analyses": ["Customer segmentation", "CLV analysis", "Churn prediction", "Demographics"]
            },
            FileType.PRODUCTS: {
                "name": "Product Catalog",
                "description": "Product master data and specifications",
                "icon": "🏷️",
                "analyses": ["Product performance", "Pricing analysis", "Category insights", "SKU profitability"]
            },
            FileType.CATEGORIES: {
                "name": "Product Categories",
                "description": "Product category hierarchy and taxonomy",
                "icon": "📑",
                "analyses": ["Category performance", "Hierarchy optimization", "Cross-category trends"]
            },
            FileType.REVIEWS: {
                "name": "Customer Reviews",
                "description": "Product reviews and ratings",
                "icon": "⭐",
                "analyses": ["Sentiment analysis", "Rating trends", "Review insights", "Product feedback"]
            },
            FileType.SHIPMENTS: {
                "name": "Shipments & Delivery",
                "description": "Shipping and delivery tracking data",
                "icon": "🚚",
                "analyses": ["Delivery performance", "Carrier analysis", "Shipping costs", "Delivery times"]
            },
            FileType.PAYMENTS: {
                "name": "Payment Transactions",
                "description": "Payment processing and transaction records",
                "icon": "💳",
                "analyses": ["Payment methods", "Transaction success rates", "Payment trends", "Revenue tracking"]
            },
            FileType.SUPPLIERS: {
                "name": "Supplier Data",
                "description": "Supplier and vendor information",
                "icon": "🏭",
                "analyses": ["Supplier performance", "Lead time analysis", "Supplier ratings", "Cost optimization"]
            },
            FileType.EMPLOYEES: {
                "name": "Employee Records",
                "description": "Employee data and HR information",
                "icon": "👔",
                "analyses": ["Headcount analysis", "Department distribution", "Compensation analysis", "Tenure tracking"]
            },
            FileType.UNKNOWN: {
                "name": "Unknown File Type",
                "description": "Could not automatically identify file type",
                "icon": "❓",
                "analyses": ["Basic statistics", "Data profiling"]
            }
        }
        
        return descriptions.get(file_type, descriptions[FileType.UNKNOWN])
    
    @staticmethod
    def suggest_file_joins(file_types: List[FileType]) -> List[Dict[str, any]]:
        """
        Suggest how multiple files can be joined for cross-analysis.
        Ultra Premium feature.
        """
        suggestions = []
        
        # Orders + Returns
        if FileType.ORDERS in file_types and FileType.RETURNS in file_types:
            suggestions.append({
                "files": ["Orders", "Returns"],
                "join_key": "order_id",
                "analyses": ["Return rate by product", "Refund analysis", "Quality issues"],
                "business_value": "Identify products with high return rates"
            })
        
        # Orders + Customers
        if FileType.ORDERS in file_types and FileType.CUSTOMERS in file_types:
            suggestions.append({
                "files": ["Orders", "Customers"],
                "join_key": "customer_id",
                "analyses": ["Customer lifetime value", "Purchase frequency", "Customer segments"],
                "business_value": "Understand customer purchase behavior"
            })
        
        # Orders + Products
        if FileType.ORDERS in file_types and FileType.PRODUCTS in file_types:
            suggestions.append({
                "files": ["Orders", "Products"],
                "join_key": "product_id",
                "analyses": ["Product profitability", "Category performance", "Pricing optimization"],
                "business_value": "Optimize product pricing and inventory"
            })
        
        # Products + Inventory
        if FileType.PRODUCTS in file_types and FileType.INVENTORY in file_types:
            suggestions.append({
                "files": ["Products", "Inventory"],
                "join_key": "product_id / sku",
                "analyses": ["Stock optimization", "Inventory turnover", "Warehouse efficiency"],
                "business_value": "Reduce carrying costs and stockouts"
            })
        
        # Orders + Shipments
        if FileType.ORDERS in file_types and FileType.SHIPMENTS in file_types:
            suggestions.append({
                "files": ["Orders", "Shipments"],
                "join_key": "order_id",
                "analyses": ["Delivery performance", "Shipping cost per order", "Carrier efficiency"],
                "business_value": "Optimize shipping and reduce delivery times"
            })
        
        # Products + Reviews
        if FileType.PRODUCTS in file_types and FileType.REVIEWS in file_types:
            suggestions.append({
                "files": ["Products", "Reviews"],
                "join_key": "product_id",
                "analyses": ["Review sentiment", "Rating impact on sales", "Quality feedback"],
                "business_value": "Improve products based on customer feedback"
            })
        
        return suggestions
