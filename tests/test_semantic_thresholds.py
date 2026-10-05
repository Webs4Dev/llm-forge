import json

from sentence_transformers import SentenceTransformer
import numpy as np


DATASET_PATH = "data/workloads/semantic-cache-eval.jsonl"

THRESHOLDS = [
    0.70,
    0.75,
    0.80,
    0.82,
    0.85,
    0.88,
    0.90,
    0.92,
    0.95,
]


def load_dataset():
    rows = []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def cosine_similarity(a, b):
    return float(np.dot(a, b))


def main():
    rows = load_dataset()

    print("Loading embedding model...")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Computing embeddings...")

    texts = []

    for row in rows:
        texts.append(row["text_a"])
        texts.append(row["text_b"])

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
    )

    embeddings = embeddings / np.linalg.norm(
        embeddings,
        axis=1,
        keepdims=True,
    )

    similarities = []

    for i, row in enumerate(rows):
        embedding_a = embeddings[i * 2]
        embedding_b = embeddings[i * 2 + 1]

        similarity = cosine_similarity(
            embedding_a,
            embedding_b,
        )

        similarities.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "expected_match": row["expected_match"],
                "similarity": similarity,
            }
        )

    print()
    print("=" * 80)
    print("SEMANTIC CACHE THRESHOLD EXPERIMENT")
    print("=" * 80)

    print(
        f"{'Threshold':<12}"
        f"{'TP':<6}"
        f"{'FP':<6}"
        f"{'TN':<6}"
        f"{'FN':<6}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
        f"{'FPR':<12}"
    )

    print("-" * 80)

    for threshold in THRESHOLDS:

        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for item in similarities:

            predicted_match = (
                item["similarity"] >= threshold
            )

            expected_match = item["expected_match"]

            if predicted_match and expected_match:
                tp += 1

            elif predicted_match and not expected_match:
                fp += 1

            elif not predicted_match and not expected_match:
                tn += 1

            elif not predicted_match and expected_match:
                fn += 1

        precision = (
            tp / (tp + fp)
            if (tp + fp) > 0
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if (tp + fn) > 0
            else 0.0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        false_positive_rate = (
            fp / (fp + tn)
            if (fp + tn) > 0
            else 0.0
        )

        print(
            f"{threshold:<12.2f}"
            f"{tp:<6}"
            f"{fp:<6}"
            f"{tn:<6}"
            f"{fn:<6}"
            f"{precision:<12.4f}"
            f"{recall:<12.4f}"
            f"{f1:<12.4f}"
            f"{false_positive_rate:<12.4f}"
        )


if __name__ == "__main__":
    main()