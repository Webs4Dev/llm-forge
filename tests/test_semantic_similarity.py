from src.optimization.cache.semantic import SemanticCache


cache = SemanticCache(
    threshold=0.90
)


pairs = [
    (
        "My package still hasn't arrived even though the expected delivery date passed yesterday.",
        "My order was supposed to arrive yesterday, but it still hasn't been delivered.",
    ),
    (
        "I don't recognize a card transaction from this morning. I did not make this purchase.",
        "There is a card transaction I don't recognize. I never made this purchase.",
    ),
    (
        "I want my money back for the subscription I purchased.",
        "How can I request a refund for my subscription?",
    ),
    (
        "My package still hasn't arrived.",
        "My card was stolen and I am worried someone could use it.",
    ),
    (
        "I don't recognize this transaction.",
        "I want to update the email address on my account.",
    ),
]


for index, (text_a, text_b) in enumerate(pairs, start=1):
    embedding_a = cache._embed(text_a)
    embedding_b = cache._embed(text_b)

    similarity = cache._similarity(
        embedding_a,
        embedding_b,
    )

    print("=" * 70)
    print(f"PAIR {index}")
    print("=" * 70)
    print(f"A: {text_a}")
    print(f"B: {text_b}")
    print(f"Similarity: {similarity:.4f}")
    print()