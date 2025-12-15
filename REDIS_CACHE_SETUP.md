# Redis Cache Setup Guide

## Overview

Redis is now integrated for high-performance distributed caching. This provides:

- ✅ **Distributed caching** - Works across multiple app instances
- ✅ **Persistent caching** - Survives app restarts
- ✅ **Better performance** - In-memory key-value store
- ✅ **Advanced features** - Rate limiting, counters, pub/sub
- ✅ **Automatic fallback** - Uses Streamlit cache if Redis unavailable

## Setup Options

### Option 1: Free Redis Cloud (Recommended for Production)

**Upstash Redis** (Free tier: 10,000 commands/day)

1. Sign up at https://upstash.com/
2. Create a new Redis database
3. Get your Redis URL (format: `redis://...`)
4. Add to `.env`:

```env
REDIS_URL=redis://default:your-password@your-endpoint.upstash.io:6379
```

**Redis Cloud** (Free tier: 30MB)

1. Sign up at https://redis.com/try-free/
2. Create database
3. Get connection details
4. Add to `.env`:

```env
REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345
```

### Option 2: Local Redis (Development)

**Install Redis:**

```bash
# Windows (via Chocolatey)
choco install redis-64

# Or download from: https://github.com/microsoftarchive/redis/releases

# macOS
brew install redis

# Linux
sudo apt-get install redis-server
```

**Start Redis:**

```bash
# Windows
redis-server

# macOS/Linux
redis-server
```

**Configure:**

```env
REDIS_HOST=localhost:6379
REDIS_PASSWORD=  # Leave empty for local dev
```

### Option 3: Docker Redis

```bash
# Run Redis in Docker
docker run -d -p 6379:6379 --name redis redis:alpine

# With persistence
docker run -d -p 6379:6379 -v redis-data:/data --name redis redis:alpine redis-server --appendonly yes
```

```env
REDIS_HOST=localhost:6379
```

## Environment Variables

Add to your `.env` file:

```env
# Redis Configuration (choose one method)

# Method 1: Full Redis URL (recommended)
REDIS_URL=redis://default:password@host:6379

# Method 2: Host and Password separately
REDIS_HOST=localhost:6379
REDIS_PASSWORD=your-password-here

# Optional: Redis database number (default: 0)
REDIS_DB=0
```

## Verification

Check if Redis is working:

```python
from Retailsights.utils.cache_manager import cache

# Get cache statistics
stats = cache.get_stats()
print(stats)
```

Expected output with Redis:
```python
{
    "backend": "redis",
    "redis_available": True,
    "redis_connected": True,
    "total_keys": 0,
    "used_memory": "1.2M",
    "connected_clients": 1
}
```

Without Redis (fallback):
```python
{
    "backend": "streamlit",
    "redis_available": False,
    "redis_connected": False
}
```

## Usage Examples

### Basic Caching

```python
from Retailsights.utils.cache_manager import cache

# Cache a function result
@cache.cache_data(ttl=300)  # Cache for 5 minutes
def get_expensive_data(shop_id):
    # ... expensive operation
    return data

# Manual cache operations
cache.set("user:123:profile", user_data, ttl=3600)
profile = cache.get("user:123:profile")
cache.delete("user:123:profile")
```

### Advanced Features

```python
# Rate limiting
visits = cache.increment(f"visits:{user_id}")
if visits > 100:
    st.warning("Rate limit exceeded")

# Pattern-based deletion
cache.clear_pattern("user:*")  # Clear all user keys

# Temporary data with auto-expiry
cache.set_with_expiry("session:abc123", session_data, seconds=1800)
```

### Cache Statistics in Dashboard

Add to your admin dashboard:

```python
import streamlit as st
from Retailsights.utils.cache_manager import cache

st.subheader("Cache Statistics")
stats = cache.get_stats()

if stats["backend"] == "redis":
    st.success(f"✅ Using Redis Cache")
    st.metric("Total Keys", stats.get("total_keys", 0))
    st.metric("Memory Used", stats.get("used_memory", "N/A"))
    st.metric("Hit Rate", f"{stats.get('hit_rate', 0):.1f}%")
else:
    st.info("ℹ️ Using Streamlit Cache (Redis not configured)")

if st.button("Clear All Caches"):
    cache.clear_all_caches()
    st.success("Caches cleared!")
```

## Performance Impact

### Before Redis (Streamlit Cache Only):
- ❌ Cache cleared on every deployment
- ❌ Separate cache per instance (no sharing)
- ❌ Limited cache size
- ⚠️ Not suitable for production with multiple instances

### After Redis:
- ✅ Cache persists across deployments
- ✅ Shared cache across all instances
- ✅ Unlimited cache size (based on Redis plan)
- ✅ Production-ready distributed caching
- ✅ **2-5x faster response times** for cached queries

## Cache Strategy by Data Type

```python
# User sessions - Medium TTL
@cache.cache_data(ttl=cache.TTL_MEDIUM)  # 5 minutes
def get_user_shops(user_id):
    ...

# Products catalog - Long TTL
@cache.cache_data(ttl=cache.TTL_LONG)  # 1 hour
def get_products_by_shop(shop_id):
    ...

# Real-time inventory - Short TTL
@cache.cache_data(ttl=cache.TTL_SHORT)  # 1 minute
def get_current_stock(product_id):
    ...

# Static reference data - Very Long TTL
@cache.cache_data(ttl=cache.TTL_VERY_LONG)  # 24 hours
def get_discount_rules(shop_id):
    ...
```

## Monitoring & Debugging

### Check Redis Connection

```bash
# Install Redis CLI
pip install redis

# Test connection
redis-cli -h your-host -p 6379 -a your-password ping
# Should return: PONG
```

### View Cached Keys

```bash
redis-cli -h your-host -p 6379 -a your-password
> KEYS *
> GET key-name
> TTL key-name
```

### Clear Cache Manually

```bash
redis-cli -h your-host -p 6379 -a your-password FLUSHDB
```

## Troubleshooting

**Issue:** "Redis connection failed"
- Check REDIS_URL format
- Verify Redis server is running
- Check firewall/network settings
- App will automatically fallback to Streamlit cache

**Issue:** "pickle error when caching"
- Ensure cached objects are serializable
- Avoid caching file handles, database connections

**Issue:** "Cache not working"
- Check TTL hasn't expired
- Verify cache key is consistent
- Check Redis memory limits

## Cost Optimization

### Free Tier Limits:

**Upstash:**
- 10,000 commands/day (free)
- ~300 requests/hour sustained
- Good for: Small to medium apps

**Redis Cloud:**
- 30MB storage (free)
- Unlimited requests
- Good for: Development and testing

### Recommendations:

- Use longer TTLs for static data
- Clear old keys regularly
- Monitor usage in Upstash dashboard
- Upgrade when hitting limits

## Production Checklist

- [ ] Redis URL configured in environment variables
- [ ] Redis connection tested and verified
- [ ] Cache TTLs optimized for your data
- [ ] Monitoring set up (Upstash dashboard or Redis Cloud)
- [ ] Backup strategy for critical cached data (if needed)
- [ ] Cache invalidation strategy defined
- [ ] Rate limiting implemented (if public-facing)

## Next Steps

1. **Set up Redis** using one of the options above
2. **Test locally** to verify connection
3. **Deploy to production** with Redis URL in environment
4. **Monitor performance** using cache statistics
5. **Optimize TTLs** based on real usage patterns

---

**No Redis? No Problem!**

The app works fine without Redis using Streamlit's built-in cache. Redis is optional but recommended for production deployments with multiple instances or high traffic.
