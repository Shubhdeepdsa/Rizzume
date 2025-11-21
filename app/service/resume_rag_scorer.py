
import json
from typing import Any, Dict, List, Tuple

import numpy as np

from app.config import get_settings
from app.errors import ValidationAppError
from app.helper.prompt_builder import build_rag_question_scoring_user_prompt
from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import RetrievedChunk, ResumeRagResult, ScoredQuestion
from app.service.chunking import TextChunk, chunk_text
from app.service.embedding_service import cosine_sim_matrix, embed_texts
from app.service.ollama_client import call_ollama_chat
from app.prompts.jd_prompts import RAG_QUESTION_SCORING_SYSTEM_PROMPT


def _build_resume_index(resume_text: str) -> Tuple[List[TextChunk], np.ndarray]:
    """
    Chunk the resume and create an embedding index.
    """
    chunks = chunk_text(resume_text, max_chars=700, overlap=150)
    chunk_texts = [c.text for c in chunks]
    embeddings = embed_texts(chunk_texts)
    return chunks, embeddings


def _retrieve_chunks_for_question(
    question: str,
    chunks: List[TextChunk],
    chunk_embeddings: np.ndarray,
    top_k: int = 3,
) -> List[RetrievedChunk]:
    """
    Retrieve top_k chunks most relevant to the question.
    """
    question_emb = embed_texts([question])  # shape (1, d)
    sims = cosine_sim_matrix(question_emb, chunk_embeddings)[0]  # shape (num_chunks,)

    # top_k indices
    if len(sims) == 0:
        return []

    top_k = min(top_k, len(sims))
    top_indices = np.argsort(-sims)[:top_k]

    retrieved: List[RetrievedChunk] = []
    for idx in top_indices:
        c = chunks[int(idx)]
        retrieved.append(
            RetrievedChunk(
                chunk_id=c.id,
                start=c.start,
                end=c.end,
                similarity=float(sims[idx]),
                text=c.text,
            )
        )

    return retrieved


def _extract_content_from_ollama_response(response: Dict[str, Any]) -> str:
    message = response.get("message") or {}
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"Ollama response missing 'message.content': {response!r}")
    return content


def _parse_scoring_json(content: str) -> Dict[str, Any]:
    """
    Parse the scoring JSON from the LLM output.
    Handles ```json ... ``` wrapping if present.
    """
    text = content.strip()

    if text.startswith("```"):
        text = text.lstrip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    return json.loads(text)


def _score_single_question_with_rag(
    category: str,
    question: str,
    retrieved_chunks: List[RetrievedChunk],
) -> ScoredQuestion:
    """
    Call Ollama with question + evidence, parse JSON, and build ScoredQuestion.
    """
    if not retrieved_chunks:
        evidence_text = ""
    else:
        evidence_text = "\n\n---\n\n".join(c.text for c in retrieved_chunks)

    evidence_chars = len(evidence_text)

    messages = [
        {"role": "system", "content": RAG_QUESTION_SCORING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_rag_question_scoring_user_prompt(
                question, evidence_text
            ),
        },
    ]

    response = call_ollama_chat(messages)
    content = _extract_content_from_ollama_response(response)

    try:
        parsed = _parse_scoring_json(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse scoring JSON for question '{question}': {e}\nContent: {content[:500]}"
        )

    answer = str(parsed.get("answer", "")).strip()
    score_raw = parsed.get("score", 0)
    reasoning = str(parsed.get("reasoning", "")).strip()

    try:
        score = float(score_raw)
    except (TypeError, ValueError):
        score = 0.0

    score = max(0.0, min(10.0, score))

    return ScoredQuestion(
        category=category,
        question=question,
        answer=answer,
        score=score,
        reasoning=reasoning,
        evidence_chars=evidence_chars,
        retrieved_chunks=retrieved_chunks,
    )


def score_resume_with_rag(
    jd_questions: JDQuestions,
    resume_text: str,
    top_k: int = 3,
) -> ResumeRagResult:
    """
    Main high-level API:

    - Build RAG index over resume.
    - For each JD question (4 categories), retrieve top_k chunks.
    - Call LLM to answer + score each question.
    - Return a ResumeRagResult with full audit trail.
    """
    settings = get_settings()

    if len(resume_text) > settings.max_resume_chars:
        raise ValidationAppError(
            f"Resume text is too long (>{settings.max_resume_chars} characters) "
            "for processing."
        )

    chunks, chunk_embeddings = _build_resume_index(resume_text)

    all_scored: list[ScoredQuestion] = []

    def process_category(category_name: str, questions: list) -> None:
        for q in questions:
            q_text = q.question
            retrieved = _retrieve_chunks_for_question(
                q_text, chunks, chunk_embeddings, top_k=top_k
            )
            scored = _score_single_question_with_rag(
                category=category_name,
                question=q_text,
                retrieved_chunks=retrieved,
            )
            all_scored.append(scored)

    max_q = settings.max_questions_per_category

    process_category("education", jd_questions.education[:max_q])
    process_category("experience", jd_questions.experience[:max_q])
    process_category("technical_skills", jd_questions.technical_skills[:max_q])
    process_category("soft_skills", jd_questions.soft_skills[:max_q])

    if all_scored:
        avg_score = sum(q.score for q in all_scored) / len(all_scored)
    else:
        avg_score = 0.0

    return ResumeRagResult(
        questions=all_scored,
        average_score=avg_score,
    )
