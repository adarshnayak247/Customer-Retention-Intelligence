import numpy as np

def cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors."""
    a, b = np.array(vec_a), np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def semantic_similarity_pct(text_a: str, text_b: str, embeddings) -> float:
    """Compute cosine similarity between two texts as a 0-100 percentage.

    Args:
        text_a: First text to compare.
        text_b: Second text to compare.
        embeddings: An embeddings client with an `embed_query` method.

    Returns:
        Cosine similarity as a percentage (0-100), rounded to 1 decimal.
    """
    emb_a = embeddings.embed_query(text_a)
    emb_b = embeddings.embed_query(text_b)
    return round(cosine_similarity(emb_a, emb_b) * 100, 1)
