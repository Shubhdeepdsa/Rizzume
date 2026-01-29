from __future__ import annotations

import logging
try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)

def estimate_tokens(text: str) -> int:
    """
    Estimate tokens using tiktoken (cl100k_base) if available.
    Otherwise fall back to character count heuristic.
    """
    if not text:
        return 0
        
    if tiktoken:
        try:
            # cl100k_base is used by GPT-4 and is a good approximation for modern LLMs
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Tiktoken encoding failed: {e}. Using fallback.")
            
    # Fallback: ~4 chars per token
    return len(text) // 4

