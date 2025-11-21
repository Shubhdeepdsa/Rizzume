import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

_EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME")

_model = SentenceTransformer(_EMBED_MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Return a 2D numpy array of shape (len(texts), dim).
    """
    if not texts:
        return np.zeros((0, 768), dtype="float32")  # safe default
    return _model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def cosine_sim_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between each row of a and each row of b.
    a: (n, d)
    b: (m, d)
    returns: (n, m)
    """
    if a.size == 0 or b.size == 0:
        return np.zeros((a.shape[0], b.shape[0]), dtype="float32")
    return np.matmul(a, b.T)
