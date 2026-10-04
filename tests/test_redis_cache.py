import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.optimization.cache.redis_cache import RedisExactCache


def main():
    cache = RedisExactCache(
        url="redis://localhost:6380/0",
        ttl=3600,
    )

    cache.clear()

    key = "llmforge-test-key"
    value = "test-value"

    print("Setting Redis key...")
    cache.set(key, value)

    print("Reading Redis key...")
    result = cache.get(key)

    print(f"Result: {result}")
    print(f"Hits: {cache.hits}")
    print(f"Misses: {cache.misses}")

    if result == value:
        print("\nRedis SET/GET test PASSED.")
    else:
        print("\nRedis SET/GET test FAILED.")

    cache.delete(key)


if __name__ == "__main__":
    main()