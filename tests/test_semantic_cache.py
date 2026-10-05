from src.optimization.cache.semantic import SemanticCache


cache = SemanticCache(
    threshold=0.80
)


response = (
    '{"category":"delivery",'
    '"urgency":"medium",'
    '"summary":"Order has not arrived.",'
    '"suggested_reply":"Please check the delivery status.",'
    '"needs_escalation":false}'
)


original_ticket = (
    "My package still hasn't arrived "
    "even though the expected delivery date passed yesterday."
)

similar_ticket = (
    "My order was supposed to arrive yesterday, "
    "but it still hasn't been delivered."
)

different_ticket = (
    "My card was stolen and I am worried "
    "someone could use it."
)


print("=" * 70)
print("ADDING ORIGINAL REQUEST")
print("=" * 70)

cache.set(
    text=original_ticket,
    response=response,
    model="fake",
    temperature=0.0,
    max_tokens=500,
)

print("Cache entries:", len(cache.entries))


print()
print("=" * 70)
print("SIMILAR REQUEST")
print("=" * 70)

result = cache.get(
    text=similar_ticket,
    model="fake",
    temperature=0.0,
    max_tokens=500,
)

print("Hit:", result["hit"])
print(
    "Similarity:",
    f"{result['similarity']:.4f}",
)
print("Response:", result["response"])


print()
print("=" * 70)
print("DIFFERENT REQUEST")
print("=" * 70)

result = cache.get(
    text=different_ticket,
    model="fake",
    temperature=0.0,
    max_tokens=500,
)

print("Hit:", result["hit"])
print(
    "Similarity:",
    f"{result['similarity']:.4f}",
)
print("Response:", result["response"])


print()
print("=" * 70)
print("CACHE METRICS")
print("=" * 70)

print("Hits:", cache.hits)
print("Misses:", cache.misses)
print(
    "Hit rate:",
    f"{cache.hit_rate():.2%}",
)