# Streamlit Configuration

This folder contains Streamlit-specific configuration files.

## Files:

### `config.toml` ✅
Production configuration for the Streamlit app.
- **Committed to git**: YES
- **Purpose**: Performance and security settings
- **Modify**: Only if you need to change app behavior

### `secrets.toml` 🔒
Contains sensitive data like database credentials and API keys.
- **Committed to git**: ❌ NO (in .gitignore)
- **Purpose**: Store secrets locally
- **On Streamlit Cloud**: Use the web dashboard "Secrets" section instead

## Local Development

Your `secrets.toml` should contain:
```toml
DATABASE_URL = "postgresql://user:pass@host:5432/db"
# Add other secrets as needed
```

## Production (Streamlit Cloud)

1. Don't commit `secrets.toml` to git
2. Instead, add secrets in the Streamlit Cloud dashboard:
   - Go to your app settings
   - Click "Secrets"
   - Paste the same content from `secrets.toml`
   - Save

## Security

⚠️ **Never commit secrets.toml to git!**
- It's already in `.gitignore`
- Always verify with `git status` before pushing
- If accidentally committed, rotate all credentials immediately
