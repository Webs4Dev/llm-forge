import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def cosine_similarity(vector_a, vector_b):
    vector_a = np.array(vector_a)
    vector_b = np.array(vector_b)

    denominator = (
        np.linalg.norm(vector_a)
        * np.linalg.norm(vector_b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(vector_a, vector_b)
        / denominator
    )


def calculate_summary_similarity(
    reference_summary,
    generated_summary,
):
    model = get_model()

    embeddings = model.encode(
        [
            reference_summary,
            generated_summary,
        ]
    )

    return cosine_similarity(
        embeddings[0],
        embeddings[1],
    )


def calculate_average_similarity(
    reference_summaries,
    generated_summaries,
):
    if not reference_summaries:
        return 0.0

    scores = []

    for reference, generated in zip(
        reference_summaries,
        generated_summaries,
    ):
        score = calculate_summary_similarity(
            reference,
            generated,
        )

        scores.append(score)

    return float(np.mean(scores))


def calculate_similarity_percentile(
    reference_summaries,
    generated_summaries,
    percentile,
):
    if not reference_summaries:
        return 0.0

    scores = []

    for reference, generated in zip(
        reference_summaries,
        generated_summaries,
    ):
        score = calculate_summary_similarity(
            reference,
            generated,
        )

        scores.append(score)

    return float(
        np.percentile(scores, percentile)
    )