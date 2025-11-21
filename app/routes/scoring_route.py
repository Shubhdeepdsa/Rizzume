
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,status
)
from app.schemas.jd_questions_schema import JDQuestions
from app.schemas.rag_scoring import ResumeRagResult
from app.service.jd_question_generator import generate_jd_questions
from app.service.resume_rag_scorer import score_resume_with_rag
from app.validator.normalize import normalize_score_input
from app.helper.text_extracter import _read_text_from_upload
from app.schemas.score_input_schema import NormalizedScoreInput
from app.validator.scoring_validators import _ensure_exactly_one

router = APIRouter()


@router.get("/score/health")
async def score_root():
    return {"status": "scoring running"}

@router.post("/score")
async def score_resume(payload: NormalizedScoreInput = Depends(normalize_score_input)):
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
        jd_questions: JDQuestions = generate_jd_questions(jd_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate JD questions: {e}",
        )

    try:
        rag_result: ResumeRagResult = score_resume_with_rag(
            jd_questions, resume_text, top_k=3
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to score resume with RAG: {e}",
        )


    return {
        "success": True,
        "score": rag_result,
        "jd_text_length": len(jd_text),
        "resume_text_length": len(resume_text),
        "questions":jd_questions,
        "message": "Scoring placeholder — plug your LLM logic here.",
    }
