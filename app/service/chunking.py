from dataclasses import dataclass
from typing import List


@dataclass
class TextChunk:
    id: int
    start: int
    end: int
    text: str


def chunk_text(
    text: str,
    max_chars: int = 600,
    overlap: int = 100,
) -> List[TextChunk]:
    """
    Simple character-based chunking with overlap.
    Not perfect, but good enough for a first RAG pass.

    Returns a list of TextChunk(id, start, end, text)
    """
    text = text.strip()
    n = len(text)
    chunks: List[TextChunk] = []
    if n == 0:
        return chunks

    chunk_id = 0
    start = 0

    while start < n:
        end = min(start + max_chars, n)
        chunk_text = text[start:end]

        chunks.append(
            TextChunk(
                id=chunk_id,
                start=start,
                end=end,
                text=chunk_text,
            )
        )
        chunk_id += 1

        if end == n:
            break

        start = end - overlap  # overlap into next chunk

    return chunks
