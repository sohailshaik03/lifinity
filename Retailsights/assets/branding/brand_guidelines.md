# RetailSight - Enterprise Branding Guidelines

## 🎨 Brand Identity

### Company Overview
**RetailSight** is a future-level, pro enterprise retail management platform that combines AI, machine learning, blockchain, and IoT technologies to revolutionize retail operations.

### Mission Statement
"Empowering retailers with intelligent insights and cutting-edge technology to minimize waste, maximize profits, and deliver exceptional customer experiences."

---

## 🎯 Brand Values

1. **Innovation** - Leading-edge AI/ML technology
2. **Efficiency** - Streamlined operations and automation
3. **Sustainability** - Waste reduction and environmental responsibility
4. **Intelligence** - Data-driven decision making
5. **Trust** - Enterprise-grade security and reliability
6. **Excellence** - Professional, polished user experience

---

## 🌈 Color Palette

### Primary Colors
```
- **Brand Blue**: #1E40AF (rgb(30, 64, 175))
  Usage: Primary buttons, headers, key CTAs
  
- **Tech Cyan**: #06B6D4 (rgb(6, 182, 212))
  Usage: Accent elements, links, highlights
  
- **Success Green**: #10B981 (rgb(16, 185, 129))
  Usage: Positive metrics, confirmations, success states
```

### Secondary Colors
```
- **Warning Amber**: #F59E0B (rgb(245, 158, 11))
  Usage: Alerts, yellow sticker features, warnings
  
- **Danger Red**: #EF4444 (rgb(239, 68, 68))
  Usage: Errors, critical alerts, waste indicators
  
- **Enterprise Purple**: #8B5CF6 (rgb(139, 92, 246))
  Usage: Premium features, AI/ML indicators
```

### Neutral Colors
```
- **Dark Slate**: #1E293B (rgb(30, 41, 59))
  Usage: Text, backgrounds, containers
  
- **Medium Gray**: #64748B (rgb(100, 116, 139))
  Usage: Secondary text, borders, disabled states
  
- **Light Gray**: #F1F5F9 (rgb(241, 245, 249))
  Usage: Backgrounds, cards, subtle dividers
  
- **White**: #FFFFFF (rgb(255, 255, 255))
  Usage: Main backgrounds, cards, contrast elements
```

---

## 🔤 Typography

### Font Families

**Primary Font: Inter**
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```
- Usage: Body text, UI elements, data tables
- Weights: 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)

**Display Font: SF Pro Display (Apple-grade)**
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'SF Pro Display', sans-serif;
```
- Usage: Headlines, dashboard titles, hero text
- Weights: 600 (SemiBold), 700 (Bold), 800 (Heavy)

**Monospace Font: JetBrains Mono**
```css
font-family: 'JetBrains Mono', 'Courier New', monospace;
```
- Usage: Code snippets, API responses, technical data

### Font Scale
```
- Display: 48px / 3rem (Dashboard headers)
- H1: 36px / 2.25rem (Page titles)
- H2: 30px / 1.875rem (Section headers)
- H3: 24px / 1.5rem (Card titles)
- H4: 20px / 1.25rem (Subsection titles)
- Body Large: 18px / 1.125rem (Important text)
- Body: 16px / 1rem (Default text)
- Body Small: 14px / 0.875rem (Labels, captions)
- Caption: 12px / 0.75rem (Metadata, timestamps)
```

---

## 📐 Logo Specifications

### Logo Variations

**Primary Logo** (Full Color)
- Filename: `retailsight-logo-primary.svg`
- Usage: Headers, login page, marketing materials
- Minimum width: 180px
- Clear space: 20px on all sides

**Icon Logo** (Symbol Only)
- Filename: `retailsight-icon.svg`
- Usage: Favicon, app icon, mobile navigation
- Size: 64x64px minimum
- Format: Square (1:1 ratio)

**White Logo** (Knockout)
- Filename: `retailsight-logo-white.svg`
- Usage: Dark backgrounds, footer, hero sections
- Usage: On backgrounds darker than 50% gray

**Black Logo** (Monochrome)
- Filename: `retailsight-logo-black.svg`
- Usage: Print materials, invoices, documents

### Logo Construction
```
┌─────────────────────────────────┐
│  🛒  RetailSight                │
│     Intelligent Retail Platform │
└─────────────────────────────────┘

Icon: Shopping cart with AI brain overlay
Wordmark: "RetailSight" in bold SF Pro Display
Tagline: "Intelligent Retail Platform" (optional)
```

---

## 🖼️ Imagery Style

### Photography Guidelines

**Product Photos**
- High-resolution (min 1920x1080px)
- Clean, minimalist backgrounds
- Bright, natural lighting
- Sharp focus on products
- Professional color correction

**Store/Retail Environment**
- Modern retail spaces
- Clean, organized shelves
- Technology integration visible
- Diverse people using technology
- Bright, inviting atmosphere

**Technology/Interface**
- Dashboard screenshots
- Data visualization close-ups
- Hands using tablets/scanners
- QR codes and barcodes
- IoT sensor devices

### Illustration Style
- Flat design with subtle gradients
- Geometric shapes
- Technology-focused iconography
- Consistent line weights (2-3px)
- Color palette adherence

---

## 🎨 UI Component Styles

### Buttons

**Primary Button**
```css
background: linear-gradient(135deg, #1E40AF 0%, #06B6D4 100%);
color: #FFFFFF;
padding: 12px 24px;
border-radius: 8px;
font-weight: 600;
box-shadow: 0 4px 6px rgba(30, 64, 175, 0.25);
transition: all 0.3s ease;
```

**Secondary Button**
```css
background: transparent;
color: #1E40AF;
border: 2px solid #1E40AF;
padding: 12px 24px;
border-radius: 8px;
font-weight: 600;
```

### Cards
```css
background: #FFFFFF;
border-radius: 12px;
padding: 24px;
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1),
            0 1px 2px rgba(0, 0, 0, 0.06);
border: 1px solid #E2E8F0;
```

### Data Tables
```css
border: 1px solid #E2E8F0;
border-radius: 8px;
overflow: hidden;

/* Header */
background: #F8FAFC;
font-weight: 600;
color: #1E293B;

/* Rows */
hover: background: #F1F5F9;
stripe: alternate rows #FAFAFA / #FFFFFF;
```

---

## 📊 Data Visualization

### Chart Colors (Ordered by importance)
1. **Primary**: #1E40AF (Brand Blue)
2. **Secondary**: #06B6D4 (Tech Cyan)
3. **Accent 1**: #10B981 (Success Green)
4. **Accent 2**: #8B5CF6 (Enterprise Purple)
5. **Accent 3**: #F59E0B (Warning Amber)
6. **Accent 4**: #EF4444 (Danger Red)

### Chart Types
- **Line Charts**: Temporal data, sales trends
- **Bar Charts**: Comparisons, category performance
- **Pie Charts**: Proportions, category distribution
- **Heatmaps**: Multi-store comparisons
- **Gauges**: KPI metrics, goal progress

---

## 🏆 Badge System

### Status Badges
```
✅ Active    - Green background, white text
⚠️ Warning   - Amber background, black text
❌ Error     - Red background, white text
🔵 Info      - Blue background, white text
⭐ Premium   - Purple gradient, white text
```

### Feature Badges
```
🤖 AI Powered
🔒 Blockchain Verified
📡 IoT Connected
🎯 ML Optimized
⚡ Real-time
🔐 Enterprise Grade
```

---

## 📱 Responsive Design

### Breakpoints
```
- Mobile: 0-640px
- Tablet: 641-1024px
- Desktop: 1025-1440px
- Large Desktop: 1441px+
```

### Mobile-First Principles
- Touch-friendly targets (min 44x44px)
- Simplified navigation
- Collapsible sections
- Optimized images
- Reduced animations

---

## 🎭 Animation & Motion

### Timing Functions
```
ease-out: Fast start, slow end (buttons, menus)
ease-in-out: Smooth, balanced (page transitions)
spring: Bouncy, energetic (success animations)
```

### Duration Scale
```
- Instant: 100ms (hover states)
- Fast: 200ms (button clicks)
- Normal: 300ms (panel slides)
- Slow: 500ms (page transitions)
```

---

## 📸 Asset Requirements

### Required Images

1. **Hero Background**
   - Filename: `hero-bg.jpg`
   - Size: 1920x1080px
   - Subject: Modern retail store with technology

2. **Dashboard Preview**
   - Filename: `dashboard-preview.png`
   - Size: 1440x900px
   - Subject: RetailSight dashboard in use

3. **Product Scanning**
   - Filename: `product-scanning.jpg`
   - Size: 800x600px
   - Subject: Hand scanning product barcode

4. **Analytics Visualization**
   - Filename: `analytics-visual.png`
   - Size: 1200x800px
   - Subject: Charts and graphs on screen

5. **Team Collaboration**
   - Filename: `team-collab.jpg`
   - Size: 1200x800px
   - Subject: Store staff using tablets

6. **IoT Sensors**
   - Filename: `iot-sensors.jpg`
   - Size: 800x600px
   - Subject: Temperature sensors in store

7. **AI/ML Concept**
   - Filename: `ai-ml-concept.jpg`
   - Size: 1000x800px
   - Subject: Abstract AI visualization

---

## 🚀 Implementation Checklist

### Phase 1: Core Branding
- [ ] Create primary logo (SVG)
- [ ] Create icon/favicon (PNG, ICO)
- [ ] Update color scheme in `assets/theme.css`
- [ ] Add custom fonts (Google Fonts CDN)

### Phase 2: Visual Assets
- [ ] Hero background image
- [ ] Dashboard screenshots
- [ ] Product photos (5-10 samples)
- [ ] Icon library (Feather/Heroicons)

### Phase 3: UI Polish
- [ ] Gradient buttons
- [ ] Card shadows and borders
- [ ] Table styling
- [ ] Badge components
- [ ] Loading animations

### Phase 4: Marketing Materials
- [ ] Landing page content
- [ ] Feature highlights
- [ ] Customer testimonials
- [ ] Pricing page design

---

## 🎓 Usage Examples

### Login Page Header
```html
<div class="hero-section">
  <img src="assets/branding/retailsight-logo-primary.svg" alt="RetailSight" />
  <h1>Intelligent Retail Platform</h1>
  <p>AI-powered inventory management and waste reduction</p>
</div>
```

### Dashboard Metric Card
```html
<div class="metric-card">
  <div class="metric-icon">📊</div>
  <h3>Total Sales</h3>
  <p class="metric-value">$127,543</p>
  <span class="metric-change positive">+12.5%</span>
</div>
```

### Feature Badge
```html
<span class="badge badge-premium">
  🤖 AI Powered
</span>
```

---

## 📞 Brand Contacts

**Design Questions**: design@retailsight.com  
**Marketing Assets**: marketing@retailsight.com  
**Brand Guidelines**: brand@retailsight.com

---

**Last Updated**: December 2025  
**Version**: 1.0.0  
**Approved By**: RetailSight Design Team
