import redis


class RedisExactCache:

    def __init__(self, url: str, ttl: int = 3600):
        self.client = redis.Redis.from_url(
            url,
            decode_responses=True,
        )

        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def get(self, key):
        value = self.client.get(key)

        if value is not None:
            self.hits += 1
            return value

        self.misses += 1
        return None

    def set(self, key, value):
        self.client.set(
            key,
            value,
            ex=self.ttl,
        )

    def delete(self, key):
        self.client.delete(key)

    def clear(self):
        self.client.flushdb()
        self.hits = 0
        self.misses = 0

    def hit_rate(self):
        total = self.hits + self.misses

        if total == 0:
            return 0.0

        return self.hits / total