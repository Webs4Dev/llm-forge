import redis


class RedisExactCache:
    """Exact-match cache in Redis.

    Keys are stored under `<namespace>:` so that two experiments sharing one
    Redis database cannot wipe each other's entries: clear() only deletes this
    namespace (earlier versions called FLUSHDB, which invalidated a run when
    OpenAI and Anthropic experiments ran at the same time).
    """

    def __init__(
        self,
        url: str,
        ttl: int = 3600,
        namespace: str = "llmforge",
    ):
        self.client = redis.Redis.from_url(
            url,
            decode_responses=True,
        )

        self.ttl = ttl
        self.namespace = namespace
        self.hits = 0
        self.misses = 0

    def _key(self, key):
        return f"{self.namespace}:{key}"

    def get(self, key):
        value = self.client.get(self._key(key))

        if value is not None:
            self.hits += 1
            return value

        self.misses += 1
        return None

    def set(self, key, value):
        self.client.set(
            self._key(key),
            value,
            ex=self.ttl,
        )

    def delete(self, key):
        self.client.delete(self._key(key))

    def clear(self):
        keys = list(
            self.client.scan_iter(
                match=f"{self.namespace}:*"
            )
        )

        if keys:
            self.client.delete(*keys)

        self.hits = 0
        self.misses = 0
