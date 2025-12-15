# check_redis.py
"""
Test Redis connection and display cache statistics
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("❌ Redis package not installed")
    print("   Install with: pip install redis hiredis")
    exit(1)

def test_redis_connection():
    """Test Redis connection and display info"""
    print("🔍 Testing Redis Connection...\n")
    
    redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_HOST")
    
    if not redis_url:
        print("⚠️  No Redis configuration found in .env")
        print("\nAdd one of these to your .env file:")
        print("  REDIS_URL=redis://default:password@host:6379")
        print("  or")
        print("  REDIS_HOST=localhost:6379")
        print("  REDIS_PASSWORD=your-password")
        return False
    
    print(f"📍 Connecting to: {redis_url[:20]}...")
    
    try:
        # Try to connect
        if redis_url.startswith("redis://") or redis_url.startswith("rediss://"):
            client = redis.from_url(redis_url, socket_connect_timeout=5)
        else:
            host = redis_url.split(":")[0] if ":" in redis_url else redis_url
            port = int(redis_url.split(":")[1]) if ":" in redis_url else 6379
            password = os.getenv("REDIS_PASSWORD")
            
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_connect_timeout=5
            )
        
        # Test connection
        response = client.ping()
        if response:
            print("✅ Successfully connected to Redis!\n")
            
            # Get server info
            info = client.info()
            print("📊 Redis Server Info:")
            print(f"   Version: {info.get('redis_version', 'N/A')}")
            print(f"   Mode: {info.get('redis_mode', 'N/A')}")
            print(f"   Connected Clients: {info.get('connected_clients', 0)}")
            print(f"   Used Memory: {info.get('used_memory_human', 'N/A')}")
            print(f"   Total Keys: {client.dbsize()}")
            
            # Calculate hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0
            print(f"   Cache Hit Rate: {hit_rate:.1f}%")
            
            # Test read/write
            print("\n🧪 Testing Read/Write:")
            test_key = "test:connection"
            test_value = "Hello Redis!"
            
            client.setex(test_key, 10, test_value)
            retrieved = client.get(test_key).decode('utf-8')
            
            if retrieved == test_value:
                print(f"   ✅ Write/Read successful")
                client.delete(test_key)
            else:
                print(f"   ❌ Write/Read test failed")
            
            return True
        else:
            print("❌ Connection failed - no response from Redis")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if Redis server is running")
        print("   2. Verify host and port are correct")
        print("   3. Check firewall/network settings")
        print("   4. Verify password (if required)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    
    if success:
        print("\n✅ Redis is ready to use!")
        print("\nYour application will now use Redis for caching.")
    else:
        print("\n⚠️  Redis connection failed.")
        print("Application will fallback to Streamlit cache.")
