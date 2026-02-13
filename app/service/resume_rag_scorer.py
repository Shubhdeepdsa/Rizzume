import json
import logging
from typing import Any, Dict, List, Tuple, Optional

import numpy as np

from app.config import get_settings
from app.errors import ValidationAppError
from app.helper.prompt_builder import build_rag_question_scoring_user_prompt
from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import RetrievedChunk, ResumeRagResult, ScoredQuestion, ActionPlan
from app.service.chunking import TextChunk, chunk_text
from app.service.embedding_service import cosine_sim_matrix, embed_texts
from app.service.llm_client import call_llm_chat
from app.service.llm_client import call_llm_chat
from app.prompts.jd_prompts import RAG_QUESTION_SCORING_SYSTEM_PROMPT, ACTION_PLAN_PROMPT

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
    scoring_config: Optional[Dict] = None,
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
    # Use scoring_config if provided, otherwise fall back to global settings
    if scoring_config:
        category_weights = {
            "education": scoring_config.get("education_weight", 25),
            "experience": scoring_config.get("experience_weight", 25),
            "technical_skills": scoring_config.get("technical_weight", 25),
            "soft_skills": scoring_config.get("soft_skills_weight", 25),
        }
        avg_score = _compute_final_score(
            all_scored,
            scoring_config.get("mandatory_question_weight", settings.mandatory_question_weight),
            scoring_config.get("optional_question_weight", settings.optional_question_weight),
            scoring_config.get("mandatory_cap_weight", settings.mandatory_cap_weight),
            category_weights,
        )
    else:
        avg_score = _compute_final_score(
            all_scored,
            settings.mandatory_question_weight,
            settings.optional_question_weight,
            settings.mandatory_cap_weight,
        )

    # Generate Action Plan using the scored questions
    action_plan = _generate_action_plan(all_scored)

    return ResumeRagResult(
        questions=all_scored,
        average_score=avg_score,
        action_plan=action_plan
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


def _compute_category_score(
    questions: List[ScoredQuestion],
    mandatory_weight: float,
    optional_weight: float,
    mandatory_cap_weight: float,
) -> float:
    """
    Compute weighted score for a single category's questions.
    Applies mandatory/optional weighting and mandatory cap penalty.
    """
    if not questions:
        return 0.0

    mandatory_weighted_score = 0.0
    mandatory_total_weight = 0.0
    optional_weighted_score = 0.0
    optional_total_weight = 0.0
    mandatory_scores = []

    for q in questions:
        if q.is_mandatory:
            mandatory_weighted_score += q.score * mandatory_weight
            mandatory_total_weight += mandatory_weight
            mandatory_scores.append(q.score)
        else:
            optional_weighted_score += q.score * optional_weight
            optional_total_weight += optional_weight

    # Mandatory average with cap penalty
    if mandatory_total_weight > 0:
        mandatory_avg = mandatory_weighted_score / mandatory_total_weight
        if mandatory_scores:
            avg_mandatory_raw = sum(mandatory_scores) / len(mandatory_scores)
            if avg_mandatory_raw < 5.0:
                mandatory_avg *= mandatory_cap_weight
    else:
        mandatory_avg = 0.0

    # Optional average (no penalty)
    if optional_total_weight > 0:
        optional_avg = optional_weighted_score / optional_total_weight
    else:
        optional_avg = 0.0

    # Combine
    total_weight = mandatory_total_weight + optional_total_weight
    if total_weight == 0:
        return 0.0

    return (mandatory_avg * mandatory_total_weight + optional_avg * optional_total_weight) / total_weight


def _compute_final_score(
    questions: List[ScoredQuestion],
    mandatory_weight: float,
    optional_weight: float,
    mandatory_cap_weight: float,
    category_weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute final score with optional per-category weighting.

    If category_weights is None, falls back to equal weighting (legacy behavior).
    If provided, groups questions by category, computes per-category scores,
    then combines using the category weight percentages.

    Dynamic normalization: if a category has 0 questions, its weight is
    redistributed proportionally to non-empty categories.
    """
    if not questions:
        return 0.0

    # Legacy flat mode: no per-category weights
    if category_weights is None:
        score = _compute_category_score(
            questions, mandatory_weight, optional_weight, mandatory_cap_weight
        )
        return round(score, 2)

    # Group questions by category
    category_groups: Dict[str, List[ScoredQuestion]] = {}
    for q in questions:
        cat = q.category
        if cat not in category_groups:
            category_groups[cat] = []
        category_groups[cat].append(q)

    # Dynamic normalization: only include categories with questions
    active_weights = {
        cat: w for cat, w in category_weights.items()
        if len(category_groups.get(cat, [])) > 0
    }

    if not active_weights:
        return 0.0

    total_active = sum(active_weights.values())
    if total_active == 0:
        return 0.0

    # Compute per-category scores and weighted combination
    final_score = 0.0
    for cat, weight in active_weights.items():
        normalized_weight = weight / total_active  # proportional share
        cat_score = _compute_category_score(
            category_groups[cat],
            mandatory_weight,
            optional_weight,
            mandatory_cap_weight,
        )
        final_score += cat_score * normalized_weight

    return round(final_score, 2)


def recalculate_score(analysis_questions: List[Dict], config: Dict) -> float:
    """
    Pure math recalculation from stored question-level scores.
    No LLM needed — re-applies weights with dynamic normalization.

    Args:
        analysis_questions: list of question dicts from stored analysis JSON
        config: dict with keys: education_weight, experience_weight, technical_weight,
                soft_skills_weight, mandatory_question_weight, optional_question_weight,
                mandatory_cap_weight
    Returns:
        Recalculated average score (0-10)
    """
    if not analysis_questions:
        return 0.0

    # Convert stored dicts back to ScoredQuestion objects
    scored_questions = []
    for q in analysis_questions:
        scored_questions.append(ScoredQuestion(
            category=q.get("category", "unknown"),
            question=q.get("question", ""),
            is_mandatory=q.get("is_mandatory", False),
            answer=q.get("answer", ""),
            score=q.get("score", 0.0),
            reasoning=q.get("reasoning", ""),
            evidence_chars=q.get("evidence_chars", 0),
            retrieved_chunks=[],  # Not needed for score calculation
        ))

    category_weights = {
        "education": config.get("education_weight", 25),
        "experience": config.get("experience_weight", 25),
        "technical_skills": config.get("technical_weight", 25),
        "soft_skills": config.get("soft_skills_weight", 25),
    }

    return _compute_final_score(
        scored_questions,
        config.get("mandatory_question_weight", 2.0),
        config.get("optional_question_weight", 1.0),
        config.get("mandatory_cap_weight", 0.5),
        category_weights,
    )


def _generate_action_plan(scored_questions: List[ScoredQuestion]) -> Optional[ActionPlan]:
    """
    Generate actionable feedback based on scored questions.
    """
    if not scored_questions:
        return None

    missing_items = []
    weak_items = []
    
    for q in scored_questions:
        # Format: "Category: Question (Score/10) - Reasoning"
        item_str = f"- [{q.category.upper()}] {q.question} (Score: {q.score}/10)\n  Reasoning: {q.reasoning}"
        
        if q.score <= 3:
            missing_items.append(item_str)
        elif 4 <= q.score <= 6:
            weak_items.append(item_str)
            
    # If no improvements needed, skip
    if not missing_items and not weak_items:
        return None
        
    missing_text = "\n".join(missing_items) if missing_items else "No critical gaps found."
    weak_text = "\n".join(weak_items) if weak_items else "No weak areas found."
    
    prompt = ACTION_PLAN_PROMPT.format(
        missing_list=missing_text,
        weak_list=weak_text
    )
    
    try:
        settings = get_settings()
        logger.info("📝 [ActionPlan] Generating action plan...")
        
        llm_output = call_llm_chat(
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7 # Slight creativity for advice
        )
        
        if isinstance(llm_output, dict):
            response_text = llm_output.get("message", {}).get("content", "")
        else:
            response_text = str(llm_output)
            
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        return ActionPlan(
            critical_actions=data.get("critical_actions", []),
            improvement_suggestions=data.get("improvement_suggestions", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to generate action plan: {e}")
        # Return fallback empty plan rather than failing the whole request
        return ActionPlan(
            critical_actions=["Failed to generate action plan. Please review individual scores."],
            improvement_suggestions=[]
        )
