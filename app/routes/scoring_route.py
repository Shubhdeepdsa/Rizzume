
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.errors import AppError, app_error_to_http
from app.helper.token_utils import estimate_tokens
from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import ResumeRagResult
from app.schemas.score_input_schema import NormalizedScoreInput
from app.schemas.score_response_schema import (
    ScoreResponse,
    TokenEstimateResponse,
)
from app.security import rate_limiter
from app.service.jd_question_generator import generate_jd_questions
from app.service.resume_rag_scorer import score_resume_with_rag
from app.validator.normalize import normalize_score_input

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/score/health")
async def score_root():
    return {"status": "scoring running"}


@router.post("/score", response_model=ScoreResponse, dependencies=[Depends(rate_limiter)])
async def score_resume(
    payload: NormalizedScoreInput = Depends(normalize_score_input),
) -> ScoreResponse:
    """
    JD and Resume are BOTH REQUIRED.

    Contract (multipart/form-data):

      - To send files:
            jd_file: UploadFile (PDF / text)
            resume_file: UploadFile (PDF / text)

      - To send raw text:
            jd_text: string
            resume_text: string

    Exactly one of *_text or *_file must be provided for each of JD and Resume.
    """

    jd_text = payload.jd
    resume_text = payload.resume
    try:
        jd_questions: JDQuestions = await run_in_threadpool(
            generate_jd_questions, jd_text
        )
    except AppError as exc:
        logger.exception("Failed to generate JD questions (AppError)")
        raise app_error_to_http(exc)
    except Exception:
        logger.exception("Failed to generate JD questions (unexpected)")
        raise HTTPException(status_code=500, detail="Internal server error.")

    try:
        rag_result: ResumeRagResult = await run_in_threadpool(
            score_resume_with_rag,
            jd_questions,
            resume_text,
            3,
        )
    except AppError as exc:
        logger.exception("Failed to score resume with RAG (AppError)")
        raise app_error_to_http(exc)
    except Exception:
        logger.exception("Failed to score resume with RAG (unexpected)")
        raise HTTPException(status_code=500, detail="Internal server error.")

    jd_tokens = estimate_tokens(jd_text)
    resume_tokens = estimate_tokens(resume_text)

    return ScoreResponse(
        success=True,
        result=rag_result,
        jd_text_length=len(jd_text),
        resume_text_length=len(resume_text),
        jd_token_estimate=jd_tokens,
        resume_token_estimate=resume_tokens,
        jd_text=jd_text,
        resume_text=resume_text,
        questions=jd_questions,
        message="Resume scored successfully.",
    )


@router.post(
    "/score/estimate",
    response_model=TokenEstimateResponse,
    dependencies=[Depends(rate_limiter)],
)
async def estimate_tokens_endpoint(
    payload: NormalizedScoreInput = Depends(normalize_score_input),
) -> TokenEstimateResponse:
    """
    Estimate token usage for JD and Resume without running full scoring.

    This uses the same normalization pipeline as /score, so it supports
    both raw text and file uploads. The estimates are approximate and
    intended for UX only (e.g. progress bars and warnings).
    """
    jd_text = payload.jd
    resume_text = payload.resume

    jd_tokens = estimate_tokens(jd_text)
    resume_tokens = estimate_tokens(resume_text)

    return TokenEstimateResponse(
        jd_text_length=len(jd_text),
        resume_text_length=len(resume_text),
        jd_token_estimate=jd_tokens,
        resume_token_estimate=resume_tokens,
    )
