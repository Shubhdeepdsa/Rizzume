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


@router.post(
    "/score", response_model=ScoreResponse, dependencies=[Depends(rate_limiter)]
)
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


@router.post("/dummy", dependencies=[Depends(rate_limiter)])
async def dummy(
    payload: NormalizedScoreInput = Depends(normalize_score_input),
):
    return {
        "success": True,
        "result": {
            "questions": [
                {
                    "category": "experience",
                    "question": "Has the candidate provided direct support to employees during implementation of HR services, policies and programs?",
                    "answer": "No direct support provided.",
                    "score": 0.0,
                    "reasoning": "The resume does not mention any specific instances of providing direct support to employees during the implementation of HR services, policies, or programs.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.5778658986091614,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.5443827509880066,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.5404036641120911,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                    ],
                },
                {
                    "category": "experience",
                    "question": "Has the candidate facilitated or participated in company-wide committees?",
                    "answer": "No",
                    "score": 0.0,
                    "reasoning": "The provided resume chunks do not mention any involvement in company-wide committees or similar roles. The candidate's experience focuses on HR management, recruitment, and organizational development but does not indicate participation or facilitation of company-wide committees.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.42593079805374146,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 9,
                            "start": 4950,
                            "end": 5650,
                            "similarity": 0.4164401590824127,
                            "text": "te workforces. Created staffing models and\nrecruiting strategies to meet each client’s unique requirements.\nSCANLON INVESTMENT CORPORATION | Chicago, IL | Financial services venture 2000 – 2001\nStaffing & Recruitment Associate\nHired to manage recruitment and staffing for start-up venture. Helped to build company from an empty suite of offices into a full-\nscale operation with 35 employees (29 staff and 6 management/executive personnel). Created and implemented hiring policies,\nprocedures, systems, and technologies to support company’s long-term growth and expansion.\nDRG FOOD SERVICE, INC. | Chicago, IL | Regional food products supplier to retail and hospitality 1998 – 2000\nHuman Resources As",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.3708838224411011,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                    ],
                },
                {
                    "category": "experience",
                    "question": "Has the candidate assisted with employee orientation and training logistics and recordkeeping?",
                    "answer": "No clear evidence.",
                    "score": 0.0,
                    "reasoning": "None of the provided resume chunks mention anything related to employee orientation or training logistics and recordkeeping.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 9,
                            "start": 4950,
                            "end": 5650,
                            "similarity": 0.5913759469985962,
                            "text": "te workforces. Created staffing models and\nrecruiting strategies to meet each client’s unique requirements.\nSCANLON INVESTMENT CORPORATION | Chicago, IL | Financial services venture 2000 – 2001\nStaffing & Recruitment Associate\nHired to manage recruitment and staffing for start-up venture. Helped to build company from an empty suite of offices into a full-\nscale operation with 35 employees (29 staff and 6 management/executive personnel). Created and implemented hiring policies,\nprocedures, systems, and technologies to support company’s long-term growth and expansion.\nDRG FOOD SERVICE, INC. | Chicago, IL | Regional food products supplier to retail and hospitality 1998 – 2000\nHuman Resources As",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.5377292633056641,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.532929003238678,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                    ],
                },
                {
                    "category": "experience",
                    "question": "Does the candidate have general knowledge of employment law and practices?",
                    "answer": "No clear direct evidence provided.",
                    "score": 0.0,
                    "reasoning": "The provided resume chunks do not mention any specific knowledge or experience related to employment law and practices.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.45125293731689453,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.4383193850517273,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 9,
                            "start": 4950,
                            "end": 5650,
                            "similarity": 0.40383437275886536,
                            "text": "te workforces. Created staffing models and\nrecruiting strategies to meet each client’s unique requirements.\nSCANLON INVESTMENT CORPORATION | Chicago, IL | Financial services venture 2000 – 2001\nStaffing & Recruitment Associate\nHired to manage recruitment and staffing for start-up venture. Helped to build company from an empty suite of offices into a full-\nscale operation with 35 employees (29 staff and 6 management/executive personnel). Created and implemented hiring policies,\nprocedures, systems, and technologies to support company’s long-term growth and expansion.\nDRG FOOD SERVICE, INC. | Chicago, IL | Regional food products supplier to retail and hospitality 1998 – 2000\nHuman Resources As",
                        },
                    ],
                },
                {
                    "category": "technical_skills",
                    "question": "Is the candidate proficient with Microsoft Word?",
                    "answer": "Not explicitly mentioned",
                    "score": 0.0,
                    "reasoning": "There is no mention of Microsoft Word or any word processing software in the provided resume chunks.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.36247560381889343,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.33812350034713745,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.3112446069717407,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                    ],
                },
                {
                    "category": "technical_skills",
                    "question": "Is the candidate proficient with Microsoft Excel?",
                    "answer": "No direct evidence.",
                    "score": 0.0,
                    "reasoning": "The provided resume chunks do not mention any proficiency or experience with Microsoft Excel.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.37177592515945435,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.3517298996448517,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.34527209401130676,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                    ],
                },
                {
                    "category": "technical_skills",
                    "question": "Can the candidate manage a Human Resources Information System (HRIS) database and maintain records?",
                    "answer": "Yes",
                    "score": 9.0,
                    "reasoning": "The candidate has strong evidence of managing an HRIS database and maintaining records through their experience at Underwriters Laboratories, where they drove the transition from outdated systems into a fully integrated HRIS platform using Oracle. This directly addresses the ability to manage an HRIS database and maintain records.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.4722427725791931,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.4703872799873352,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.4542731046676636,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                    ],
                },
                {
                    "category": "soft_skills",
                    "question": "Does the candidate have effective oral communication skills?",
                    "answer": "No direct evidence",
                    "score": 0.0,
                    "reasoning": "The resume does not mention any specific skills related to oral communication.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.31035125255584717,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.30176928639411926,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.2881636619567871,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                    ],
                },
                {
                    "category": "soft_skills",
                    "question": "Does the candidate have effective written communication skills?",
                    "answer": "No strong evidence.",
                    "score": 3.0,
                    "reasoning": "The provided resume chunks do not explicitly mention effective written communication skills. The candidate describes their strategic and leadership roles but does not provide specific examples or statements about written communication.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.35196253657341003,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.3204391598701477,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.2903811037540436,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                    ],
                },
                {
                    "category": "soft_skills",
                    "question": "Is the candidate able to maintain a high level of confidentiality?",
                    "answer": "Not clearly demonstrated",
                    "score": 0.0,
                    "reasoning": "None of the provided resume chunks explicitly mention maintaining confidentiality or handling sensitive information.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.33328527212142944,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.33066046237945557,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.29127413034439087,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                    ],
                },
                {
                    "category": "soft_skills",
                    "question": "Has the candidate engaged professionally in HR meetings and seminars with other HR professionals in the region?",
                    "answer": "No",
                    "score": 0.0,
                    "reasoning": "The resume does not mention any participation in HR meetings or seminars with other HR professionals in the region.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.5690034031867981,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.5265144109725952,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.4996493458747864,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                    ],
                },
            ],
            "average_score": 1.0909090909090908,
        },
        "jd_text_length": 1524,
        "resume_text_length": 6249,
        "jd_token_estimate": 381,
        "resume_token_estimate": 1563,
        "jd_text": "Sample Job Description\nJob Title: Human Resources Assistant\nJob Description: This position reports to the Human Resources (HR) director and\ninterfaces with company managers and HR staff. Company XYZ is\ncommitted to an employee-orientated, high performance culture that\nemphasizes empowerment, quality, continuous improvement, and the\nrecruitment and ongoing development of a superior workforce.\nThe intern will gain exposure\nto these functional areas: HR Information Systems; Employee relations; Training and development;\nBenefits; Compensation; Organization development; Employment\nSpecific responsibilities: - Employee orientation and training logistics and recordkeeping\n- Company-wide committee facilitation and participation\n- Employee safety, welfare, wellness and health reporting\n- Provide direct support to employees during implementation of HR\nservices, policies and programs\nWhat skills will the\nintern learn: - Active participation in strategic planning process, including\ndeveloping goals, objectives and processes\n- How to engage professionally in HR meetings and seminars with\nother HR professionals in the region\n- Gain experience with Human Resources Information system (HRIS)\ndatabase management and record keeping\n- Application of HR law and compliance with governmental regulations\nQualifications: - Proficient with Microsoft Word and Excel\n- General knowledge of employment law and practices\n- Able to maintain a high level of confidentiality\n- Effective oral and written management communication skills",
        "resume_text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M communications & technology services provider 2008 – Present\nDirector – US & International Human Resources\nRecruited to direct HR for US and newly launched international operations. Partner with other directors and senior executives to\ndevelop new business initiatives, foster employee engagement, and mobilize talent. Manage $135K budget.\n HR Organization Leadership: Most senior HR executive in Donovan, directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined integration of VueX Wireless Systems, Donovan’s largest-ever\nacquisition at the time. Ensured strategic alignment of HR with new business objectives and minimized business\ninterruptions through execution of workforce integration plans.\n M&A Due Diligence: Contributed to senior-level M&A decisions, supporting initial analysis through due diligence and\nsubsequent integration. Enabled business growth by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proactive employee relations and communications programs to resolve previous\nlabor and management issues and restore the credibility and employee-centric focus of the HR organization.\n Career Coaching: Rolled out the company’s first HR shared services center for delivery of internal coaching services.\n Workforce Expansion: Ramped up California-based engineering group of 50 new employees in just 3 months,\nLORETTA DANIELSON, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nGRAYSON INDUSTRIES | Indianapolis, IN | Enterprise learning and training company 2003 – 2005\nManager – Human Resources\nJoined new management team tasked with revitalizing Grayson following years of instability, internal change, restructuring, and\nabsent leadership. Supported corporate repositioning, guiding recruitment of 100 technical, professional, and management staff\nfor US HQ.\n Workforce Integration: Integrated 30+ staff in the aftermath of 2 acquisitions, steering flawless workforce\nassimilation into core business operations. Contributed to profitable turnaround with >$1M in first-year savings.\n HR Operations: Consolidated HR functions previously managed by several different departments into a single\nconsolidated organization to manage all generalist affairs. Trained and supervised 2 HR assistants.\nSTANNARD E-COMMERCE, LTD. | Chicago, IL | Management consulting firm to the e-commerce industry 2001 – 2002\nHR Consultant\nConsulted with major online retailers to help them build both on-site and remote workforces. Created staffing models and\nrecruiting strategies to meet each client’s unique requirements.\nSCANLON INVESTMENT CORPORATION | Chicago, IL | Financial services venture 2000 – 2001\nStaffing & Recruitment Associate\nHired to manage recruitment and staffing for start-up venture. Helped to build company from an empty suite of offices into a full-\nscale operation with 35 employees (29 staff and 6 management/executive personnel). Created and implemented hiring policies,\nprocedures, systems, and technologies to support company’s long-term growth and expansion.\nDRG FOOD SERVICE, INC. | Chicago, IL | Regional food products supplier to retail and hospitality 1998 – 2000\nHuman Resources Associate – Staffing\nManaged staffing and onboarding for administrative, customer service, sales, and warehousing personnel.\nEDUCATION & PROFESSIONAL CREDENTIALS\nMBA Degree – Keller Graduate School of Management – 2008\nMS Degree – Organization Development – Loyola University – 2004\nBA Degree – Industrial Relations – Loyola University – 1998\nSenior Professional in Human Resources (SPHR)\nSociety of Human Resources Management Senior Certified Professional (SHRM-SCP)\nPROFESSIONAL HR AFFILIATIONS\nMember – Society of Human Resources Management (SHRM)\nMember & Education Committee Chair – World at Work",
        "questions": {
            "education": [],
            "experience": [
                {
                    "question": "Has the candidate provided direct support to employees during implementation of HR services, policies and programs?"
                },
                {
                    "question": "Has the candidate facilitated or participated in company-wide committees?"
                },
                {
                    "question": "Has the candidate assisted with employee orientation and training logistics and recordkeeping?"
                },
                {
                    "question": "Does the candidate have general knowledge of employment law and practices?"
                },
            ],
            "technical_skills": [
                {"question": "Is the candidate proficient with Microsoft Word?"},
                {"question": "Is the candidate proficient with Microsoft Excel?"},
                {
                    "question": "Can the candidate manage a Human Resources Information System (HRIS) database and maintain records?"
                },
            ],
            "soft_skills": [
                {
                    "question": "Does the candidate have effective oral communication skills?"
                },
                {
                    "question": "Does the candidate have effective written communication skills?"
                },
                {
                    "question": "Is the candidate able to maintain a high level of confidentiality?"
                },
                {
                    "question": "Has the candidate engaged professionally in HR meetings and seminars with other HR professionals in the region?"
                },
            ],
        },
        "message": "Resume scored successfully.",
    }
