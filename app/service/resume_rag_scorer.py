import json
import logging
from typing import Any, Dict, List, Tuple, Optional

import numpy as np

from app.config import get_settings
from app.errors import ValidationAppError
from app.helper.prompt_builder import build_rag_question_scoring_user_prompt
from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import RetrievedChunk, ResumeRagResult, ScoredQuestion
from app.service.chunking import TextChunk, chunk_text
from app.service.embedding_service import cosine_sim_matrix, embed_texts
from app.service.llm_client import call_llm_chat
from app.prompts.jd_prompts import RAG_QUESTION_SCORING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def build_resume_index(resume_text: str) -> Tuple[List[TextChunk], np.ndarray]:
    """
    Chunk the resume and create an embedding index.
    """
    settings = get_settings()
    logger.info(
        "📊 [Embeddings] Building resume index using model: '%s'",
        settings.embed_model_name
    )
    chunks = chunk_text(resume_text, max_chars=700, overlap=150)
    chunk_texts = [c.text for c in chunks]
    embeddings = embed_texts(chunk_texts)
    logger.info("✅ [Embeddings] Created %d chunks from resume", len(chunks))
    return chunks, embeddings

def score_resume_with_rag(
    jd_questions: JDQuestions,
    resume_text: str,
    top_k: int = 3,
    precomputed_index: Optional[Tuple[List[TextChunk], np.ndarray]] = None,
) -> ResumeRagResult:
    """
    Main high-level API:

    - Build RAG index over resume (or use precomputed).
    - For each JD question (4 categories), retrieve top_k chunks.
    - Call LLM to answer + score each question.
    - Return a ResumeRagResult with full audit trail.
    """
    settings = get_settings()

    if not precomputed_index and len(resume_text) > settings.max_resume_chars:
        raise ValidationAppError(
            f"Resume text is too long (>{settings.max_resume_chars} characters) "
            "for processing."
        )

    if precomputed_index:
        chunks, chunk_embeddings = precomputed_index
        logger.info("📊 [Embeddings] Using precomputed index from DB")
    else:
        chunks, chunk_embeddings = build_resume_index(resume_text)

    all_scored: list[ScoredQuestion] = []

    # Log which LLM provider is being used for scoring
    logger.info(
        "🎯 [Scoring] Starting resume scoring using LLM provider: '%s' (model: '%s')",
        settings.llm_provider,
        settings.groq_model if settings.llm_provider.lower() == "groq" else settings.ollama_default_model
    )

    def process_category(category_name: str, questions: list) -> None:
        if not questions:
            logger.info("⏭️  [Scoring] Skipping category '%s' - no questions", category_name)
            return
        logger.info(
            "📋 [Scoring] Processing category '%s' - %d questions",
            category_name, len(questions)
        )
        for idx, q in enumerate(questions, 1):
            q_text = q.question
            q_mandatory = q.is_mandatory
            mandatory_tag = "[MANDATORY]" if q_mandatory else "[OPTIONAL]"
            logger.info(
                "  → [Scoring] %s Question %d/%d %s",
                category_name, idx, len(questions), mandatory_tag
            )
            retrieved = _retrieve_chunks_for_question(
                q_text, chunks, chunk_embeddings, top_k=top_k
            )
            scored = _score_single_question_with_rag(
                category=category_name,
                question=q_text,
                is_mandatory=q_mandatory,
                retrieved_chunks=retrieved,
            )
            all_scored.append(scored)
        logger.info(
            "✅ [Scoring] Completed category '%s'",
            category_name
        )

    max_q = settings.max_questions_per_category

    process_category("education", jd_questions.education[:max_q])
    process_category("experience", jd_questions.experience[:max_q])
    process_category("technical_skills", jd_questions.technical_skills[:max_q])
    process_category("soft_skills", jd_questions.soft_skills[:max_q])

    # Compute final score using weighted average with mandatory cap
    avg_score = _compute_final_score(
        all_scored,
        settings.mandatory_question_weight,
        settings.optional_question_weight,
        settings.mandatory_cap_weight,
    )

    return ResumeRagResult(
        questions=all_scored,
        average_score=avg_score,
    )


def _retrieve_chunks_for_question(
    question_text: str,
    chunks: List[TextChunk],
    chunk_embeddings: np.ndarray,
    top_k: int = 3
) -> List[RetrievedChunk]:
    """
    Search for top_k most similar chunks to the question.
    """
    # 1. Embed question (single string)
    q_emb = embed_texts([question_text])[0]  # shape (dim,)
    
    # 2. Cosine similarity
    q_emb_matrix = np.array([q_emb], dtype=np.float32)
    
    # helper returns (N, M) matrix -> (N, 1)
    sims = cosine_sim_matrix(chunk_embeddings, q_emb_matrix)
    # sims is (N, 1). Flatten to (N,)
    sims = sims.flatten()
    
    # 3. Top-K
    # sort descending
    top_indices = np.argsort(sims)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        c = chunks[idx]
        score = float(sims[idx])
        # Use existing ID if available and valid int, else use index
        cid = int(c.id) if c.id is not None and str(c.id).isdigit() else idx
        
        results.append(RetrievedChunk(
            chunk_id=cid,
            start=c.start,
            end=c.end,
            similarity=score,
            text=c.text
        ))
        
    return results


def _score_single_question_with_rag(
    category: str,
    question: str,
    is_mandatory: bool,
    retrieved_chunks: List[RetrievedChunk]
) -> ScoredQuestion:
    """
    Call LLM to answer 'question' given 'retrieved_chunks'.
    Expects LLM to return JSON with {score, answer, reasoning}.
    """
    
    # 1. Build context string
    context_text = "\n\n".join([
        f"--- Chunk {rc.chunk_id} (sim={rc.similarity:.2f}) ---\n{rc.text}"
        for rc in retrieved_chunks
    ])
    
    # 2. Build Prompt
    user_prompt = build_rag_question_scoring_user_prompt(
        category=category,
        question=question,
        context=context_text,
        is_mandatory=is_mandatory
    )
    
    # 3. Call LLM
    try:
        llm_output = call_llm_chat(
            messages=[
                {"role": "system", "content": RAG_QUESTION_SCORING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0 # Strict for scoring
        )
        
        # Extract content string from dict response
        # call_llm_chat returns {"message": {"role": "assistant", "content": "..."}}
        if isinstance(llm_output, dict):
            response_text = llm_output.get("message", {}).get("content", "")
        else:
            response_text = str(llm_output)
        
        # Clean potential markdown code blocks
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Validate/Extract fields with fallbacks
        score = float(data.get("score", 0))
        answer = data.get("answer", "No answer provided.")
        reasoning = data.get("reasoning", "No reasoning provided.")
        
    except Exception as e:
        logger.error(f"Failed to score question '{question}': {e}")
        score = 0.0
        answer = "Error during scoring."
        reasoning = f"LLM error: {str(e)}"

    return ScoredQuestion(
        category=category,
        question=question,
        is_mandatory=is_mandatory,
        answer=answer,
        score=score,
        reasoning=reasoning,
        evidence_chars=sum(len(rc.text) for rc in retrieved_chunks),
        retrieved_chunks=retrieved_chunks
    )


def _compute_final_score(
    questions: List[ScoredQuestion],
    mandatory_weight: float,
    optional_weight: float,
    mandatory_cap_weight: float
) -> float:
    """
    Compute weighted average.
    """
    if not questions:
        return 0.0
        
    total_weighted_score = 0.0
    total_weight = 0.0
    
    mandatory_scores = []
    
    for q in questions:
        w = mandatory_weight if q.is_mandatory else optional_weight
        total_weighted_score += q.score * w
        total_weight += w
        
        if q.is_mandatory:
            mandatory_scores.append(q.score)
            
    if total_weight == 0:
        return 0.0
        
    final_score = total_weighted_score / total_weight
    
    if mandatory_scores:
        avg_mandatory = sum(mandatory_scores) / len(mandatory_scores)
        if avg_mandatory < 5.0:
            final_score *= mandatory_cap_weight
            
    return round(final_score, 2)
