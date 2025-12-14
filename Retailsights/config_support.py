"""
Support Configuration
Centralized configuration for customer support settings.
"""

# Support Contact Information
SUPPORT_EMAIL = "support@retailsight.com"
SUPPORT_PHONE = "+44 (0) 20 1234 5678"
SUPPORT_HOURS = "Mon-Fri: 9:00 AM - 6:00 PM GMT"
RESPONSE_TIME_EMAIL = "Within 24 hours"
RESPONSE_TIME_URGENT = "Within 4 hours"

# Support Team
SUPPORT_TEAM = {
    "general": "support@retailsight.com",
    "technical": "tech@retailsight.com",
    "billing": "billing@retailsight.com",
    "enterprise": "enterprise@retailsight.com",
}

# Social Media & Resources
SOCIAL_LINKS = {
    "twitter": "https://twitter.com/retailsight",
    "linkedin": "https://linkedin.com/company/retailsight",
    "youtube": "https://youtube.com/@retailsight",
    "documentation": "https://docs.retailsight.com",
}

# System Status
STATUS_PAGE = "https://status.retailsight.com"

# Feature Flags
ENABLE_CHATBOT = True
ENABLE_LIVE_CHAT = False  # Set to True when live chat service is integrated
ENABLE_PHONE_SUPPORT = False  # Set to True when phone support is available
