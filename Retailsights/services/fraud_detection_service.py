"""
Fraud Detection Service
Detect and prevent pricing abuse, staff fraud, and anomalies.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from ..db import get_connection
from ..logger import logger


class FraudDetectionService:
    """Enterprise-grade fraud detection and prevention."""
    
    @staticmethod
    def detect_staff_discount_abuse(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Detect staff members applying excessive discounts.
        Red flags:
        - Discounts >70% (outside policy)
        - Buying discounted items themselves
        - Unusual patterns (only work when discounts happen)
        """
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            
            # Analyze markdown patterns by staff
            cur.execute("""
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.role,
                    COUNT(ms.id) as markdown_count,
                    AVG(ms.discount_percent) as avg_discount,
                    MAX(ms.discount_percent) as max_discount,
                    SUM(ms.discount_amount * ms.quantity_sold) as total_discount_given,
                    SUM(ms.discounted_price * ms.quantity_sold) as revenue_from_markdowns
                FROM users u
                JOIN markdown_sales ms ON u.id = ms.sold_by
                WHERE u.shop_id = %s
                  AND ms.sold_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY u.id, u.username, u.role
                HAVING max_discount > 70 OR avg_discount > 50
                ORDER BY total_discount_given DESC
            """, (shop_id, days))
            
            suspicious_staff = cur.fetchall()
            
            alerts = []
            for staff in suspicious_staff:
                risk_score = 0
                flags = []
                
                # Flag 1: Excessive average discount
                if staff['avg_discount'] > 50:
                    risk_score += 30
                    flags.append(f"Avg discount {staff['avg_discount']:.1f}% (policy max: 50%)")
                
                # Flag 2: Individual discounts over 70%
                if staff['max_discount'] > 70:
                    risk_score += 40
                    flags.append(f"Applied {staff['max_discount']:.0f}% discount (policy max: 70%)")
                
                # Flag 3: High volume of markdowns
                if staff['markdown_count'] > 100:
                    risk_score += 20
                    flags.append(f"High volume: {staff['markdown_count']} markdowns in {days} days")
                
                # Flag 4: Large discount amount
                if staff['total_discount_given'] > 1000:
                    risk_score += 10
                    flags.append(f"£{staff['total_discount_given']:.2f} total discount given")
                
                alerts.append({
                    "user_id": staff['user_id'],
                    "username": staff['username'],
                    "role": staff['role'],
                    "risk_score": min(100, risk_score),
                    "severity": "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 40 else "LOW",
                    "flags": flags,
                    "statistics": {
                        "markdown_count": staff['markdown_count'],
                        "avg_discount": round(staff['avg_discount'], 1),
                        "max_discount": staff['max_discount'],
                        "total_discount_given": staff['total_discount_given']
                    },
                    "recommendation": "Review discount authorization and transaction logs"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"detect_staff_discount_abuse error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def detect_barcode_tampering(shop_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """
        Detect potential barcode switching or tampering.
        Red flags:
        - Same barcode scanned for different products
        - Invalid barcodes with successful lookups
        - Price mismatches
        """
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            
            # Check for same barcode mapped to multiple products
            cur.execute("""
                SELECT 
                    sh.code as barcode,
                    COUNT(DISTINCT sh.product_id) as different_products,
                    GROUP_CONCAT(DISTINCT p.name) as product_names,
                    COUNT(*) as scan_count,
                    MAX(sh.scanned_at) as last_scan
                FROM scan_history sh
                JOIN products p ON sh.product_id = p.id
                WHERE sh.shop_id = %s
                  AND sh.code_type = 'barcode'
                  AND sh.scanned_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY sh.code
                HAVING different_products > 1
                ORDER BY scan_count DESC
            """, (shop_id, days))
            
            suspicious_barcodes = cur.fetchall()
            
            alerts = []
            for record in suspicious_barcodes:
                alerts.append({
                    "type": "BARCODE_REUSE",
                    "severity": "HIGH",
                    "barcode": record['barcode'],
                    "issue": f"Barcode used for {record['different_products']} different products",
                    "products": record['product_names'],
                    "scan_count": record['scan_count'],
                    "last_scan": record['last_scan'],
                    "recommendation": "Investigate: possible barcode tampering or system error"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"detect_barcode_tampering error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def detect_unusual_transaction_patterns(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Detect unusual sales patterns that may indicate fraud.
        """
        conn = get_connection()
        alerts = []
        
        try:
            cur = conn.cursor(dictionary=True)
            
            # Pattern 1: Transactions at unusual hours
            cur.execute("""
                SELECT 
                    DATE(created_at) as date,
                    HOUR(created_at) as hour,
                    COUNT(*) as transaction_count,
                    SUM(total_amount) as total_value
                FROM sales
                WHERE shop_id = %s
                  AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                  AND (HOUR(created_at) < 6 OR HOUR(created_at) > 23)
                GROUP BY DATE(created_at), HOUR(created_at)
                HAVING transaction_count > 5
                ORDER BY date DESC, hour DESC
            """, (shop_id, days))
            
            unusual_hours = cur.fetchall()
            
            if unusual_hours:
                for record in unusual_hours:
                    alerts.append({
                        "type": "UNUSUAL_HOURS",
                        "severity": "MEDIUM",
                        "date": record['date'],
                        "hour": record['hour'],
                        "transaction_count": record['transaction_count'],
                        "total_value": record['total_value'],
                        "recommendation": "Review: transactions outside normal business hours"
                    })
            
            # Pattern 2: Same customer/staff buying heavily discounted items
            cur.execute("""
                SELECT 
                    ms.sold_by as user_id,
                    u.username,
                    COUNT(DISTINCT ms.id) as purchase_count,
                    SUM(ms.quantity_sold) as total_items,
                    AVG(ms.discount_percent) as avg_discount,
                    SUM(ms.discounted_price * ms.quantity_sold) as total_spent
                FROM markdown_sales ms
                JOIN users u ON ms.sold_by = u.id
                WHERE ms.shop_id = %s
                  AND ms.sold_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY ms.sold_by, u.username
                HAVING purchase_count > 20 AND avg_discount > 40
                ORDER BY purchase_count DESC
            """, (shop_id, days))
            
            heavy_discounters = cur.fetchall()
            
            for record in heavy_discounters:
                alerts.append({
                    "type": "DISCOUNT_BUYER",
                    "severity": "MEDIUM",
                    "user_id": record['user_id'],
                    "username": record['username'],
                    "purchase_count": record['purchase_count'],
                    "total_items": record['total_items'],
                    "avg_discount": round(record['avg_discount'], 1),
                    "total_spent": record['total_spent'],
                    "recommendation": "Verify: same person consistently buying discounted items"
                })
            
        except Exception as e:
            logger.error(f"detect_unusual_transaction_patterns error: {e}")
        finally:
            conn.close()
        
        return alerts
    
    @staticmethod
    def generate_fraud_report(shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Comprehensive fraud detection report."""
        
        staff_abuse = FraudDetectionService.detect_staff_discount_abuse(shop_id, days)
        barcode_tampering = FraudDetectionService.detect_barcode_tampering(shop_id, days)
        unusual_patterns = FraudDetectionService.detect_unusual_transaction_patterns(shop_id, days)
        
        all_alerts = staff_abuse + barcode_tampering + unusual_patterns
        
        # Count by severity
        high_severity = len([a for a in all_alerts if a.get('severity') == 'HIGH'])
        medium_severity = len([a for a in all_alerts if a.get('severity') == 'MEDIUM'])
        low_severity = len([a for a in all_alerts if a.get('severity') == 'LOW'])
        
        # Overall risk score
        risk_score = (high_severity * 10) + (medium_severity * 5) + (low_severity * 2)
        risk_level = "CRITICAL" if risk_score >= 50 else "HIGH" if risk_score >= 30 else "MEDIUM" if risk_score >= 10 else "LOW"
        
        return {
            "shop_id": shop_id,
            "analysis_period_days": days,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_alerts": len(all_alerts),
                "high_severity": high_severity,
                "medium_severity": medium_severity,
                "low_severity": low_severity,
                "risk_score": risk_score,
                "risk_level": risk_level
            },
            "alerts": {
                "staff_discount_abuse": staff_abuse,
                "barcode_tampering": barcode_tampering,
                "unusual_patterns": unusual_patterns
            },
            "recommendations": [
                "Review high-risk alerts immediately",
                "Implement stricter discount approval workflow",
                "Enable video surveillance correlation",
                "Regular staff training on discount policy"
            ] if risk_score >= 30 else ["Continue monitoring - no critical issues detected"]
        }
    
    @staticmethod
    def get_transaction_audit_trail(
        transaction_id: Optional[int] = None,
        user_id: Optional[int] = None,
        product_sku: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get detailed audit trail for investigations.
        """
        conn = get_connection()
        try:
            conditions = ["ms.sold_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"]
            params = [days]
            
            if transaction_id:
                conditions.append("ms.id = %s")
                params.append(transaction_id)
            
            if user_id:
                conditions.append("ms.sold_by = %s")
                params.append(user_id)
            
            if product_sku:
                conditions.append("ms.sku = %s")
                params.append(product_sku)
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT 
                    ms.id,
                    ms.sku,
                    p.name as product_name,
                    ms.quantity_sold,
                    ms.original_price,
                    ms.discounted_price,
                    ms.discount_percent,
                    ms.discount_amount,
                    ms.rule_name,
                    ms.sold_by,
                    u.username as sold_by_user,
                    u.role as user_role,
                    ms.sold_at,
                    s.name as shop_name
                FROM markdown_sales ms
                JOIN products p ON ms.product_id = p.id
                JOIN users u ON ms.sold_by = u.id
                JOIN shops s ON ms.shop_id = s.id
                WHERE {where_clause}
                ORDER BY ms.sold_at DESC
                LIMIT 100
            """
            
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params)
            return cur.fetchall()
            
        except Exception as e:
            logger.error(f"get_transaction_audit_trail error: {e}")
            return []
        finally:
            conn.close()
