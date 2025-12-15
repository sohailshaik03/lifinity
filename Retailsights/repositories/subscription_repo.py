# repositories/subscription_repo.py
"""
Subscription Repository - Database operations for subscription management
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text
from ..db import get_connection
from ..logger import log
import json


class SubscriptionRepo:
    """Handle all subscription-related database operations"""
    
    @staticmethod
    def get_user_subscription(user_id: int) -> Optional[Dict[str, Any]]:
        """Get active subscription for a user"""
        conn = get_connection()
        try:
            result = conn.execute(text("""
                SELECT 
                    us.id,
                    us.user_id,
                    us.plan_id,
                    us.status,
                    us.start_date,
                    us.end_date,
                    us.trial_ends_at,
                    us.auto_renew,
                    us.payment_method,
                    us.next_billing_date,
                    sp.tier,
                    sp.name as plan_name,
                    sp.price,
                    sp.billing_cycle,
                    sp.max_file_size_mb,
                    sp.max_rows,
                    sp.max_columns,
                    (us.status = 'trial') as is_trial,
                    us.end_date as subscription_ends_at
                FROM user_subscriptions us
                JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE us.user_id = :user_id
                ORDER BY us.created_at DESC
                LIMIT 1
            """), {"user_id": user_id})
            
            row = result.fetchone()
            if row:
                result_dict = dict(row._mapping)
                if result_dict.get('is_trial'):
                    result_dict['is_trial'] = bool(result_dict['is_trial'])
                return result_dict
            return None
        except Exception as e:
            log.error(f"Error getting user subscription: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_user_tier(user_id: int) -> str:
        """Get user's subscription tier (returns 'basic' if no active subscription)"""
        subscription = SubscriptionRepo.get_user_subscription(user_id)
        return subscription['tier'] if subscription else 'basic'
    
    @staticmethod
    def create_subscription(
        user_id: int,
        plan_tier: str = 'basic',
        trial_days: int = 30
    ) -> Optional[int]:
        """Create a new subscription for a user"""
        conn = get_connection()
        
        try:
            # Get plan ID
            result = conn.execute(
                text("SELECT id FROM subscription_plans WHERE tier = :tier LIMIT 1"),
                {"tier": plan_tier}
            )
            row = result.fetchone()
            
            if not row:
                log.error(f"Plan tier '{plan_tier}' not found")
                return None
            
            plan = dict(row._mapping)
            
            # Calculate dates
            start_date = datetime.now()
            status = 'trial' if trial_days > 0 else 'active'
            trial_ends_at = start_date + timedelta(days=trial_days) if trial_days > 0 else None
            next_billing_date = trial_ends_at if trial_ends_at else start_date + timedelta(days=30)
            
            result = conn.execute(text("""
                INSERT INTO user_subscriptions 
                    (user_id, plan_id, status, start_date, trial_ends_at, next_billing_date)
                VALUES (:user_id, :plan_id, :status, :start_date, :trial_ends_at, :next_billing_date)
            """), {
                "user_id": user_id,
                "plan_id": plan['id'],
                "status": status,
                "start_date": start_date,
                "trial_ends_at": trial_ends_at,
                "next_billing_date": next_billing_date
            })
            
            conn.commit()
            return result.lastrowid
            
        except Exception as e:
            log.error(f"Error creating subscription: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    @staticmethod
    def upgrade_subscription(user_id: int, new_tier: str, payment_method: str = None) -> bool:
        """Upgrade user to a new tier"""
        conn = get_connection()
        
        try:
            # Deactivate current subscription
            conn.execute(text("""
                UPDATE user_subscriptions 
                SET status = 'upgraded', end_date = NOW() 
                WHERE user_id = :user_id AND status IN ('active', 'trial')
            """), {"user_id": user_id})
            
            conn.commit()
            
            # Create new subscription (no trial for upgrades)
            return SubscriptionRepo.create_subscription(user_id, new_tier, trial_days=0) is not None
            
        except Exception as e:
            log.error(f"Error upgrading subscription: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def cancel_subscription(user_id: int) -> bool:
        """Cancel user subscription"""
        conn = get_connection()
        
        try:
            conn.execute(text("""
                UPDATE user_subscriptions 
                SET status = 'cancelled', end_date = NOW() 
                WHERE user_id = :user_id AND status IN ('active', 'trial')
            """), {"user_id": user_id})
            
            conn.commit()
            return True
            
        except Exception as e:
            log.error(f"Error cancelling subscription: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def track_usage(user_id: int, metric_name: str, value: int) -> bool:
        """Track usage metric"""
        conn = get_connection()
        
        try:
            # Get current month period
            now = datetime.now()
            period_start = now.replace(day=1)
            if now.month == 12:
                period_end = now.replace(year=now.year + 1, month=1, day=1)
            else:
                period_end = now.replace(month=now.month + 1, day=1)
            
            conn.execute(text("""
                INSERT INTO subscription_usage 
                    (user_id, metric_name, metric_value, period_start, period_end)
                VALUES (:user_id, :metric_name, :value, :period_start, :period_end)
                ON DUPLICATE KEY UPDATE 
                    metric_value = metric_value + VALUES(metric_value)
            """), {
                "user_id": user_id,
                "metric_name": metric_name,
                "value": value,
                "period_start": period_start,
                "period_end": period_end
            })
            
            conn.commit()
            return True
            
        except Exception as e:
            log.error(f"Error tracking usage: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_usage_stats(user_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        conn = get_connection()
        
        try:
            date_from = datetime.now() - timedelta(days=period_days)
            
            # Get file uploads count
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as files_uploaded,
                    COALESCE(SUM(row_count), 0) as total_rows_processed,
                    COALESCE(SUM(file_size_mb), 0) as storage_used_mb
                FROM file_uploads
                WHERE user_id = :user_id AND uploaded_at >= :date_from
            """), {"user_id": user_id, "date_from": date_from})
            
            row = result.fetchone()
            stats = dict(row._mapping) if row else {}
            
            # Get feature usage count
            result = conn.execute(text("""
                SELECT COUNT(DISTINCT feature_name) as features_accessed
                FROM feature_usage
                WHERE user_id = :user_id AND last_used_at >= :date_from
            """), {"user_id": user_id, "date_from": date_from})
            
            row = result.fetchone()
            if row:
                feature_stats = dict(row._mapping)
                stats['features_accessed'] = feature_stats['features_accessed']
            
            return stats
            
        except Exception as e:
            log.error(f"Error getting usage stats: {e}")
            return {
                'files_uploaded': 0,
                'total_rows_processed': 0,
                'storage_used_mb': 0,
                'features_accessed': 0
            }
        finally:
            conn.close()
    
    @staticmethod
    def get_payment_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get payment history for a user"""
        conn = get_connection()
        
        try:
            result = conn.execute(text("""
                SELECT 
                    id,
                    amount,
                    currency,
                    payment_status,
                    payment_method,
                    transaction_id,
                    billing_period_start,
                    billing_period_end,
                    created_at
                FROM subscription_payments
                WHERE user_subscription_id IN (
                    SELECT id FROM user_subscriptions WHERE user_id = :user_id
                )
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"user_id": user_id, "limit": limit})
            
            return [dict(row._mapping) for row in result.fetchall()] or []
            
        except Exception as e:
            log.error(f"Error getting payment history: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_user_payments(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Alias for get_payment_history - get payment records for a user"""
        return SubscriptionRepo.get_payment_history(user_id, limit)
