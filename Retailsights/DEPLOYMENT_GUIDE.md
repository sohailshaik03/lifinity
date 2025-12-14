# 🚀 Deployment Guide - Streamlit Cloud

## Quick Deployment Steps

### 1. Prerequisites
- ✅ GitHub account
- ✅ Neon PostgreSQL database (you already have this)
- ✅ Streamlit Cloud account (free at https://share.streamlit.io)

### 2. Push to GitHub

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Production ready deployment"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/lifinity.git

# Push to GitHub
git push -u origin main
```

### 3. Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io
2. **Sign in** with GitHub
3. **Click**: "New app"
4. **Configure**:
   - Repository: `yourusername/lifinity`
   - Branch: `main`
   - Main file path: `Retailsights/app.py`
5. **Click**: "Advanced settings"
6. **Set Python version**: `3.11` (recommended)
7. **Add secrets** (click "Secrets"):

```toml
# Paste this in the secrets section:
DATABASE_URL = "postgresql://neondb_owner:npg_OVIhKZvEk14c@ep-little-water-ab0pwzo6-pooler.eu-west-2.aws.neon.tech/lifinity?sslmode=require"

# Add any other API keys if needed:
# OPENAI_API_KEY = "sk-..."
# SENDGRID_API_KEY = "SG..."
```

8. **Click**: "Deploy!"

### 4. Your App Will Be Live At:
```
https://yourusername-lifinity-retailsightsapp-xxxxx.streamlit.app
```

---

## Important Notes

### ⚠️ Secrets Management
- **NEVER** commit `.env` or `secrets.toml` to GitHub (already in .gitignore)
- All sensitive data goes in Streamlit Cloud's "Secrets" section
- The app will read from `st.secrets` in production

### 📊 Performance for 50-100 Users
Your app is now optimized with:
- ✅ Database query caching (5 min TTL)
- ✅ Connection pooling (5 connections + 10 overflow)
- ✅ Optimized Streamlit config
- ✅ PostgreSQL with Neon (serverless, auto-scales)

**Expected Performance:**
- ✅ 50 users: Excellent performance
- ✅ 100 users: Good performance (might need to upgrade Neon plan)
- ⚠️ 150+ users: Consider upgrading to paid Streamlit tier or self-hosting

### 💰 Cost Breakdown

**FREE Tier (Current Setup):**
- Streamlit Cloud: Free (1 private app, 3 public apps)
- Neon PostgreSQL: Free (0.5GB storage, 3GB transfer/month)
- Total: **$0/month** for up to ~50 users

**If You Need More:**
- Streamlit Cloud Pro: $20/month (more resources, priority support)
- Neon Scale Plan: $19/month (3GB storage, better performance)
- Total: **$39/month** for 100+ users comfortably

---

## Alternative: Railway.app Deployment

If you prefer Railway:

1. **Go to**: https://railway.app
2. **Create new project** → "Deploy from GitHub"
3. **Select**: Your repository
4. **Add PostgreSQL** database (Railway provides one)
5. **Set environment variables**:
   - `DATABASE_URL` (auto-filled by Railway's PostgreSQL)
6. **Set start command**:
   ```bash
   streamlit run Retailsights/app.py --server.port $PORT
   ```
7. **Deploy!**

**Railway Pricing:**
- $5/month for hobby plan
- PostgreSQL included
- Better for 100+ users

---

## Monitoring & Maintenance

### Check App Health
- Streamlit Cloud dashboard shows: CPU, Memory, Users online
- Set up alerts for errors

### Clear Cache Manually
If data seems stale, clear cache:
```python
# Add a button in admin panel:
if st.button("Clear All Cache"):
    st.cache_data.clear()
    st.success("Cache cleared!")
```

### Database Backups
- Neon auto-backups (restore from dashboard)
- Or manual: `pg_dump` → save to S3/Google Drive

---

## Troubleshooting

### "ModuleNotFoundError"
- Check `requirements.txt` is in the repo root or `Retailsights/` folder
- Streamlit Cloud looks for it automatically

### "Database connection failed"
- Verify `DATABASE_URL` in Streamlit secrets
- Check Neon database is running (may sleep on free tier after inactivity)

### "App is slow"
- Check Streamlit Cloud metrics (CPU/Memory usage)
- Verify caching is working (check logs)
- Consider upgrading Neon plan for better DB performance

---

## Next Steps

1. ✅ Push to GitHub
2. ✅ Deploy to Streamlit Cloud
3. ✅ Test with multiple users
4. ✅ Monitor performance
5. ✅ Upgrade plans if needed for 100+ users

---

## Questions?

- Streamlit Docs: https://docs.streamlit.io/streamlit-cloud
- Neon Docs: https://neon.tech/docs
- Community: https://discuss.streamlit.io

**Your app is production-ready! 🎉**
