# 🎧 Customer Support System

## Overview

RetailSight now includes a comprehensive customer support system with:

- **📧 Email Support**: Direct contact via support@retailsight.com
- **💬 AI Chatbot**: Instant answers to common questions
- **📝 Support Tickets**: Submit detailed support requests
- **❓ FAQ Section**: Searchable frequently asked questions
- **📚 Resources**: Documentation, training, and troubleshooting guides

## Features

### 1. AI-Powered Chatbot 🤖

The intelligent support assistant can help with:

- Login and access issues
- Data upload and import
- Expiry tracking and alerts
- Barcode scanning
- Reports and analytics
- AI and enterprise features
- General troubleshooting

**Quick Topics Available:**
- 🔐 Login Issues
- 📊 Upload Data
- ⚠️ Expiry Alerts

The chatbot maintains conversation history and provides contextual responses based on keywords.

### 2. Support Ticket System 📧

Submit detailed support requests with:

- **Priority levels**: Low, Medium, High, Urgent
- **Categories**: 
  - Login & Access
  - Data Upload
  - Expiry Tracking
  - Barcode Scanning
  - Reports & Analytics
  - Enterprise Features
  - Billing & Subscription
  - Technical Issue
  - Feature Request
  - Other

- **File attachments**: Screenshots, CSV, Excel, PDF
- **Ticket tracking**: Unique reference numbers
- **Email confirmation**: Automatic confirmation emails

### 3. FAQ Section ❓

Comprehensive answers to 12+ frequently asked questions covering:

- Password resets
- File formats
- Expiry alerts
- Barcode scanning
- Discount rules
- Report exports
- Dashboard differences
- AI predictions
- Data security
- Multi-store features
- IoT sensors
- Browser compatibility

### 4. Resource Center 📚

Quick access to:

- **Documentation**: Quick start, user manual, admin guide, API docs
- **Training**: Onboarding courses, advanced features, certifications
- **Troubleshooting**: Common issues, browser setup, performance tips
- **System Status**: Real-time operational status

### 5. Sidebar Support Widget

Quick access from any page:

- Support email
- Business hours
- Response times
- Quick help links
- Direct navigation to Support Center

## Configuration

### Email Settings

Edit `config_support.py` to customize:

```python
SUPPORT_EMAIL = "support@retailsight.com"
SUPPORT_HOURS = "Mon-Fri: 9:00 AM - 6:00 PM GMT"
RESPONSE_TIME_EMAIL = "Within 24 hours"

SUPPORT_TEAM = {
    "general": "support@retailsight.com",
    "technical": "tech@retailsight.com",
    "billing": "billing@retailsight.com",
    "enterprise": "enterprise@retailsight.com",
}
```

### Feature Flags

Enable/disable features:

```python
ENABLE_CHATBOT = True          # AI chatbot
ENABLE_LIVE_CHAT = False       # Live chat with agents
ENABLE_PHONE_SUPPORT = False   # Phone support
```

## Usage

### Accessing Support

1. **From Navigation**: Click "🎧 Support" in the sidebar menu
2. **Quick Widget**: Expand the support widget at bottom of sidebar
3. **In-App**: Support options available throughout the application

### Using the Chatbot

1. Navigate to Support → Live Chat
2. Type your question in the message box
3. Click "Send" or press Enter
4. Use quick topic buttons for common questions
5. Clear chat history with "Clear Chat" button

### Submitting a Ticket

1. Go to Support → Contact Us
2. Fill in required fields:
   - Name
   - Email
   - Category
   - Priority
   - Subject
   - Detailed message
3. Optionally attach files
4. Click "Submit Ticket"
5. Save your ticket reference number

### Browsing FAQ

1. Go to Support → FAQ
2. Browse through expandable questions
3. Click any question to view the answer
4. Use browser search (Ctrl+F) to find specific topics

## Chatbot Intelligence

The chatbot uses keyword matching to provide contextual responses:

- **Login keywords**: login, password, access, sign in
- **Upload keywords**: upload, import, csv, excel, file
- **Expiry keywords**: expiry, expire, alert, notification, yellow sticker
- **Scanning keywords**: scan, barcode, qr, camera, webcam
- **Analytics keywords**: report, analytics, dashboard, sales, revenue
- **AI keywords**: ai, prediction, forecast, machine learning
- **Blockchain keywords**: blockchain, traceability, ledger
- **Support keywords**: email, contact, phone, call, support

### Extending Chatbot Responses

Edit `ui/tabs/support_tab.py` → `get_bot_response()` function to add new responses:

```python
elif any(word in message_lower for word in ["your", "keywords"]):
    return """Your custom response here"""
```

## Support Metrics

The system tracks:

- Ticket submission timestamps
- User contact information
- Issue categories and priorities
- Attachment files
- Chat conversation history
- Quick topic usage

## Best Practices

### For Users

1. **Search FAQ first**: Most questions already answered
2. **Use chatbot**: Get instant help for common issues
3. **Include details**: Provide screenshots, error messages, steps to reproduce
4. **Choose correct category**: Helps route to right team
5. **Set appropriate priority**: Reserve "Urgent" for critical issues

### For Administrators

1. **Monitor support email**: Check support@retailsight.com regularly
2. **Update FAQ**: Add new questions based on ticket trends
3. **Train chatbot**: Add responses for recurring questions
4. **Review metrics**: Analyze support patterns
5. **Update contact info**: Keep hours and response times current

## Integration Opportunities

The support system can be integrated with:

- **Email services**: SendGrid, Mailgun, AWS SES
- **Ticketing systems**: Zendesk, Freshdesk, Help Scout
- **Live chat**: Intercom, Drift, LiveChat
- **Knowledge base**: Notion, Confluence, GitBook
- **Analytics**: Google Analytics, Mixpanel, Amplitude

## Troubleshooting

### Chatbot not responding

- Check if `ENABLE_CHATBOT = True` in config
- Verify session state is initialized
- Clear browser cache and reload

### Ticket submission fails

- Validate all required fields filled
- Check email format
- Verify file size < 10MB
- Check browser console for errors

### Support widget not showing

- Ensure `show_support_widget()` called in app.py
- Check sidebar visibility
- Refresh the page

## Future Enhancements

Planned features:

- 🔴 Live agent chat
- 📞 Phone support integration
- 🎫 Ticket tracking dashboard
- 📊 Support analytics
- 🌐 Multi-language support
- 🔔 Push notifications
- 📱 Mobile app support
- 🤝 Community forum
- 📹 Video call support
- 🎓 Interactive tutorials

## Contact Information

- **General Support**: support@retailsight.com
- **Technical Support**: tech@retailsight.com
- **Billing**: billing@retailsight.com
- **Enterprise**: enterprise@retailsight.com

**Hours**: Monday - Friday, 9:00 AM - 6:00 PM GMT  
**Response Time**: Within 24 hours (4 hours for urgent issues)

---

**Version**: 2.5  
**Last Updated**: December 2025  
**Maintained By**: RetailSight Support Team
