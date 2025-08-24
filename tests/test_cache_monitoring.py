#!/usr/bin/env python3
"""
Test script to generate cache activity and monitor Redis
"""
import sys
sys.path.append('src')
import time
from utils.redis_cache import cached_opensanctions_request, cache

def test_cache_monitoring():
    print("🧪 Testing cache monitoring...")
    print("🔍 Run 'docker exec -it aml-redis redis-cli monitor' in another terminal to see live activity")
    print("="*60)
    
    # Test URLs
    test_urls = [
        'https://httpbin.org/json',
        'https://httpbin.org/uuid',
        'https://httpbin.org/delay/1'
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📡 Test {i}: {url}")
        
        # First call - cache MISS
        print("   First call (cache MISS)...")
        start = time.time()
        try:
            result1 = cached_opensanctions_request(url, ttl=30)
            duration1 = time.time() - start
            print(f"   ⏱️  Duration: {duration1:.3f}s")
            
            # Second call - cache HIT
            print("   Second call (cache HIT)...")
            start = time.time()
            result2 = cached_opensanctions_request(url, ttl=30)
            duration2 = time.time() - start
            print(f"   ⏱️  Duration: {duration2:.3f}s")
            
            if duration1 > 0 and duration2 > 0:
                speedup = duration1 / duration2
                print(f"   🚀 Speedup: {speedup:.1f}x")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between tests
    
    # Show current cache contents
    print(f"\n📊 Current cache keys:")
    try:
        import redis
        r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
        keys = r.keys('*')
        for key in keys:
            ttl = r.ttl(key)
            print(f"   🔑 {key} (TTL: {ttl}s)")
        
        print(f"\n📈 Total cached items: {len(keys)}")
        
    except Exception as e:
        print(f"❌ Error checking cache: {e}")

if __name__ == "__main__":
    test_cache_monitoring()