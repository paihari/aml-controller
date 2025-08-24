#!/usr/bin/env python3
"""
Real-time Redis cache monitoring
"""
import redis
import time
import json

def monitor_redis_cache():
    try:
        r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
        
        print("🔍 Redis Cache Monitor")
        print("=" * 50)
        
        while True:
            # Get all keys
            keys = r.keys('*')
            
            # Clear screen (optional)
            print("\033[2J\033[H", end="")  
            
            print(f"🕐 {time.strftime('%H:%M:%S')} - Redis Cache Status")
            print("=" * 50)
            print(f"📊 Total cached items: {len(keys)}")
            print("")
            
            if keys:
                print("🔑 Cached Keys:")
                for key in keys:
                    ttl = r.ttl(key)
                    try:
                        value = r.get(key)
                        if value:
                            data = json.loads(value)
                            size = len(str(data))
                            print(f"   {key} (TTL: {ttl}s, Size: {size} chars)")
                    except:
                        print(f"   {key} (TTL: {ttl}s)")
            else:
                print("💭 No cached items")
                
            print("\nPress Ctrl+C to exit...")
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    monitor_redis_cache()