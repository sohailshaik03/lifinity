# services/subscription_service.py
"""
Enterprise Subscription Management Service
Handles Basic, Premium, and Ultra Premium tier features
"""
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime, timedelta


class SubscriptionTier(Enum):
    """Subscription tiers with feature access levels"""
    BASIC = "basic"
    PREMIUM = "premium"
    ULTRA_PREMIUM = "ultra_premium"


class SubscriptionFeatures:
    """
    Define what features are available at each tier.
    Professional enterprise-level feature gating.
    """
    
    TIER_FEATURES = {
        SubscriptionTier.BASIC: {
            "name": "Basic Plan",
            "price": "£25 one-time",
            "price_amount": 25,
            "currency": "GBP",
            "billing_type": "one-time",
            "trial_days": 7,
            "trial_features_only": True,
            "max_file_size_mb": 10,
            "max_rows": 5000,
            "max_columns": 50,
            "file_types": ["csv", "xlsx"],
            "analysis_types": ["orders"],
            "features": [
                "7-day FREE trial (basic features only)",
                "Basic data upload (CSV/Excel)",
                "Simple sales analytics",
                "Basic charts & visualizations",
                "Up to 5,000 rows per file",
                "Standard cleaning & validation",
                "Single file analysis",
                "Basic reports (PDF)",
                "30-day data retention",
                "£25 one-time payment after trial"
            ],
            "advanced_analytics": False,
            "multi_file_analysis": False,
            "power_bi_export": False,
            "api_access": False,
            "custom_reports": False,
            "ml_predictions": False,
            "anomaly_detection": False,
            "data_profiling": False,
            "cross_file_joins": False
        },
        
        SubscriptionTier.PREMIUM: {
            "name": "Premium Plan",
            "price": "£49/month",
            "price_amount": 49,
            "currency": "GBP",
            "billing_type": "monthly",
            "trial_days": 0,
            "trial_features_only": False,
            "max_file_size_mb": 100,
            "max_rows": 100000,
            "max_columns": 200,
            "file_types": ["csv", "xlsx", "json", "parquet"],
            "analysis_types": ["orders", "returns", "inventory", "customers"],
            "features": [
                "All Basic features",
                "Advanced data upload (CSV/Excel/JSON/Parquet)",
                "Multi-file analysis (Orders + Returns + Inventory)",
                "Up to 100,000 rows per file",
                "Advanced data profiling",
                "Statistical analysis & correlations",
                "Cohort analysis",
                "Customer segmentation",
                "Trend analysis & forecasting",
                "Custom business insights",
                "Advanced visualizations (Plotly)",
                "Scheduled reports",
                "30-day data retention",
                "Power BI export",
                "API access (Basic)"
            ],
            "advanced_analytics": True,
            "multi_file_analysis": True,
            "power_bi_export": True,
            "api_access": True,
            "custom_reports": True,
            "ml_predictions": False,
            "anomaly_detection": True,
            "data_profiling": True,
            "cross_file_joins": True
        },
        
        SubscriptionTier.ULTRA_PREMIUM: {
            "name": "Ultra Premium Plan",
            "price": "£199/month",
            "price_amount": 199,
            "currency": "GBP",
            "billing_type": "monthly",
            "trial_days": 0,
            "trial_features_only": False,
            "max_file_size_mb": 1000,
            "max_rows": 10000000,
            "max_columns": 1000,
            "file_types": ["csv", "xlsx", "json", "parquet", "xml", "sql"],
            "analysis_types": [
                "orders", "returns", "inventory", "customers", 
                "reviews", "products", "categories", "suppliers",
                "shipments", "payments"
            ],
            "features": [
                "All Premium features",
                "Unlimited file types & formats",
                "Enterprise-scale data (10M+ rows)",
                "Real-time data processing",
                "ML-powered predictions",
                "AI-driven insights & recommendations",
                "Automated anomaly detection",
                "Advanced statistical modeling",
                "RFM analysis & CLV prediction",
                "Market basket analysis",
                "Churn prediction",
                "Demand forecasting",
                "Price optimization",
                "Multi-source data integration",
                "Power BI/Tableau connectors",
                "Custom dashboard builder",
                "White-label reports",
                "Unlimited data retention",
                "Full API access with webhooks",
                "Priority support (24/7)",
                "Custom ML model training",
                "Blockchain audit trail"
            ],
            "advanced_analytics": True,
            "multi_file_analysis": True,
            "power_bi_export": True,
            "api_access": True,
            "custom_reports": True,
            "ml_predictions": True,
            "anomaly_detection": True,
            "data_profiling": True,
            "cross_file_joins": True,
            "real_time_processing": True,
            "custom_ml_models": True,
            "white_label": True
        }
    }
    
    @staticmethod
    def get_features(tier: SubscriptionTier) -> Dict[str, Any]:
        """Get all features for a subscription tier"""
        return SubscriptionFeatures.TIER_FEATURES.get(tier, {})
    
    @staticmethod
    def can_access_feature(tier: SubscriptionTier, feature: str) -> bool:
        """Check if a tier has access to a specific feature"""
        tier_features = SubscriptionFeatures.TIER_FEATURES.get(tier, {})
        return tier_features.get(feature, False)
    
    @staticmethod
    def get_file_limits(tier: SubscriptionTier) -> Dict[str, Any]:
        """Get file size and row limits for a tier"""
        features = SubscriptionFeatures.TIER_FEATURES.get(tier, {})
        return {
            "max_file_size_mb": features.get("max_file_size_mb", 10),
            "max_rows": features.get("max_rows", 1000),
            "max_columns": features.get("max_columns", 50)
        }
    
    @staticmethod
    def get_allowed_file_types(tier: SubscriptionTier) -> List[str]:
        """Get allowed file types for a tier"""
        features = SubscriptionFeatures.TIER_FEATURES.get(tier, {})
        return features.get("file_types", ["csv"])
    
    @staticmethod
    def get_allowed_analysis_types(tier: SubscriptionTier) -> List[str]:
        """Get allowed analysis types for a tier"""
        features = SubscriptionFeatures.TIER_FEATURES.get(tier, {})
        return features.get("analysis_types", ["orders"])


class SubscriptionService:
    """
    Manage user subscriptions and enforce tier limits.
    Professional enterprise subscription management.
    """
    
    @staticmethod
    def get_user_tier(user_id: int) -> SubscriptionTier:
        """
        Get subscription tier for a user.
        TODO: Integrate with database to fetch actual subscription.
        For now, returns ULTRA_PREMIUM for testing.
        """
        # TODO: Query database for user's subscription
        # subscription = db.query(Subscription).filter_by(user_id=user_id).first()
        # return SubscriptionTier(subscription.tier)
        
        # For now, return ULTRA_PREMIUM to enable all features during development
        return SubscriptionTier.ULTRA_PREMIUM
    
    @staticmethod
    def validate_file_upload(
        tier: SubscriptionTier, 
        file_size_mb: float, 
        file_type: str,
        num_rows: int,
        num_columns: int
    ) -> tuple[bool, str]:
        """
        Validate if file upload is allowed for the user's tier.
        Returns (is_valid, error_message)
        """
        limits = SubscriptionFeatures.get_file_limits(tier)
        allowed_types = SubscriptionFeatures.get_allowed_file_types(tier)
        
        # Check file size
        if file_size_mb > limits["max_file_size_mb"]:
            return False, f"File size ({file_size_mb:.1f}MB) exceeds {tier.value} plan limit ({limits['max_file_size_mb']}MB). Upgrade to process larger files."
        
        # Check file type
        if file_type not in allowed_types:
            return False, f"File type '.{file_type}' not supported in {tier.value} plan. Allowed: {', '.join(allowed_types)}. Upgrade for more formats."
        
        # Check row count
        if num_rows > limits["max_rows"]:
            return False, f"File has {num_rows:,} rows, exceeding {tier.value} plan limit ({limits['max_rows']:,}). Upgrade to process larger datasets."
        
        # Check column count
        if num_columns > limits["max_columns"]:
            return False, f"File has {num_columns} columns, exceeding {tier.value} plan limit ({limits['max_columns']}). Upgrade for more columns."
        
        return True, ""
    
    @staticmethod
    def get_upgrade_prompt(current_tier: SubscriptionTier, required_feature: str) -> str:
        """Generate upgrade prompt message"""
        tier_names = {
            SubscriptionTier.BASIC: "Premium",
            SubscriptionTier.PREMIUM: "Ultra Premium"
        }
        
        next_tier = tier_names.get(current_tier, "Premium")
        
        return f"""
🔒 **{required_feature}** is not available in your current plan.

**Upgrade to {next_tier}** to unlock:
{chr(10).join('  ✨ ' + f for f in SubscriptionFeatures.TIER_FEATURES[SubscriptionTier.PREMIUM if current_tier == SubscriptionTier.BASIC else SubscriptionTier.ULTRA_PREMIUM]["features"][:5])}
  ... and much more!

[**Upgrade Now**](#) to access enterprise features.
"""
    
    @staticmethod
    def get_tier_limits(tier: str) -> Dict[str, Any]:
        """Get limits and features for a given tier"""
        tier_enum = SubscriptionTier.BASIC
        if tier == 'premium':
            tier_enum = SubscriptionTier.PREMIUM
        elif tier == 'ultra_premium':
            tier_enum = SubscriptionTier.ULTRA_PREMIUM
        
        return SubscriptionFeatures.TIER_FEATURES[tier_enum]
