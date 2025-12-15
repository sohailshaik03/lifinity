# Quick Stripe Setup Helper
# Run this after you get your Stripe API keys

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "       STRIPE SETUP HELPER - RetailSight" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 STEP 1: Get your Stripe API keys" -ForegroundColor Cyan
Write-Host "   1. Go to: https://dashboard.stripe.com/test/apikeys" -ForegroundColor White
Write-Host "   2. Copy your Publishable key (pk_test_...)" -ForegroundColor White
Write-Host "   3. Copy your Secret key (sk_test_...)" -ForegroundColor White
Write-Host ""

# Prompt for API keys
Write-Host "Enter your Stripe Secret Key (sk_test_...):" -ForegroundColor Yellow
$secretKey = Read-Host

Write-Host "Enter your Stripe Publishable Key (pk_test_...):" -ForegroundColor Yellow
$publishableKey = Read-Host

# Add to .env file
Write-Host ""
Write-Host "Adding Stripe configuration to .env file..." -ForegroundColor Yellow

$stripeConfig = @"

# Stripe Payment Configuration (Added by setup script)
STRIPE_SECRET_KEY=$secretKey
STRIPE_PUBLISHABLE_KEY=$publishableKey
STRIPE_WEBHOOK_SECRET=whsec_placeholder
STRIPE_CURRENCY=gbp
STRIPE_COUNTRY=GB
"@

Add-Content -Path ".env" -Value $stripeConfig

Write-Host "✅ Stripe keys added to .env file" -ForegroundColor Green
Write-Host ""

# Verify
Write-Host "📋 STEP 2: Verify configuration" -ForegroundColor Cyan
$envContent = Get-Content ".env" | Select-String -Pattern "STRIPE"
if ($envContent) {
    Write-Host "✅ Stripe configuration found in .env:" -ForegroundColor Green
    $envContent | ForEach-Object { 
        $line = $_.Line
        if ($line -match "SECRET_KEY=(.+)") {
            Write-Host "   STRIPE_SECRET_KEY=sk_test_****" -ForegroundColor Gray
        } elseif ($line -match "PUBLISHABLE_KEY=(.+)") {
            Write-Host "   STRIPE_PUBLISHABLE_KEY=pk_test_****" -ForegroundColor Gray
        } else {
            Write-Host "   $line" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "❌ Configuration not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 STEP 3: Create products in Stripe Dashboard" -ForegroundColor Cyan
Write-Host "   1. Go to: https://dashboard.stripe.com/test/products" -ForegroundColor White
Write-Host "   2. Create 3 products:" -ForegroundColor White
Write-Host "      🌱 Starter: £29.99/month, £299/year" -ForegroundColor Green
Write-Host "      ⭐ Professional: £79.99/month, £799/year" -ForegroundColor Blue
Write-Host "      🚀 Enterprise: £199.99/month, £1999/year" -ForegroundColor Magenta
Write-Host ""

Write-Host "📋 STEP 4: Test your setup" -ForegroundColor Cyan
Write-Host "   Run: streamlit run app.py" -ForegroundColor White
Write-Host "   Use test card: 4242 4242 4242 4242" -ForegroundColor White
Write-Host ""

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE! See STRIPE_SETUP.txt for full guide" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
