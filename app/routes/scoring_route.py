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


@router.post(
    "/dummy", dependencies=[Depends(rate_limiter)]
)
async def dummy(
    payload: NormalizedScoreInput = Depends(normalize_score_input),
) :
    return {
        "success": True,
        "result": {
            "questions": [
                {
                    "category": "experience",
                    "question": "Has the candidate performed employee orientation and training logistics and recordkeeping?",
                    "answer": "No",
                    "score": 0.0,
                    "reasoning": "None of the provided resume chunks explicitly mention performing employee orientation and training logistics or recordkeeping.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 9,
                            "start": 4950,
                            "end": 5650,
                            "similarity": 0.4953435957431793,
                            "text": "te workforces. Created staffing models and\nrecruiting strategies to meet each client’s unique requirements.\nSCANLON INVESTMENT CORPORATION | Chicago, IL | Financial services venture 2000 – 2001\nStaffing & Recruitment Associate\nHired to manage recruitment and staffing for start-up venture. Helped to build company from an empty suite of offices into a full-\nscale operation with 35 employees (29 staff and 6 management/executive personnel). Created and implemented hiring policies,\nprocedures, systems, and technologies to support company’s long-term growth and expansion.\nDRG FOOD SERVICE, INC. | Chicago, IL | Regional food products supplier to retail and hospitality 1998 – 2000\nHuman Resources As",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.4875645339488983,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.47618359327316284,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                    ],
                },
                {
                    "category": "experience",
                    "question": "Has the candidate facilitated or participated in company-wide committees?",
                    "answer": "No direct evidence provided.",
                    "score": 0.0,
                    "reasoning": "The resume does not mention any involvement in company-wide committees or similar roles.",
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
                    "question": "Has the candidate assisted with employee safety, welfare, wellness, and health reporting?",
                    "answer": "No clear evidence provided.",
                    "score": 0.0,
                    "reasoning": "The resume chunks do not mention any specific experience or role related to employee safety, welfare, wellness, or health reporting.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.548376202583313,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.5014790892601013,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 9,
                            "start": 4950,
                            "end": 5650,
                            "similarity": 0.4996330142021179,
                            "text": "te workforces. Created staffing models and\nrecruiting strategies to meet each client’s unique requirements.\nSCANLON INVESTMENT CORPORATION | Chicago, IL | Financial services venture 2000 – 2001\nStaffing & Recruitment Associate\nHired to manage recruitment and staffing for start-up venture. Helped to build company from an empty suite of offices into a full-\nscale operation with 35 employees (29 staff and 6 management/executive personnel). Created and implemented hiring policies,\nprocedures, systems, and technologies to support company’s long-term growth and expansion.\nDRG FOOD SERVICE, INC. | Chicago, IL | Regional food products supplier to retail and hospitality 1998 – 2000\nHuman Resources As",
                        },
                    ],
                },
                {
                    "category": "experience",
                    "question": "Has the candidate provided direct support to employees during the implementation of HR services, policies, and programs?",
                    "answer": "No direct support provided to employees during implementation of HR services, policies, and programs.",
                    "score": 0.0,
                    "reasoning": "The resume chunks do not mention any direct involvement or support given by the candidate to employees during the implementation of specific HR services, policies, or programs. The focus is mainly on leadership roles, strategic initiatives, and organizational changes.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.555396556854248,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.5260741710662842,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.5176365375518799,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                    ],
                },
                {
                    "category": "technical_skills",
                    "question": "Is the candidate proficient with Microsoft Word and Excel?",
                    "answer": "Not explicitly mentioned",
                    "score": 0.0,
                    "reasoning": "The provided resume chunks do not mention any proficiency with Microsoft Word or Excel.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.3642454147338867,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.3561018109321594,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.3487577438354492,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                    ],
                },
                {
                    "category": "technical_skills",
                    "question": "Can the candidate apply Human Resources Information System (HRIS) database management and record keeping skills?",
                    "answer": "Yes",
                    "score": 9.0,
                    "reasoning": "The candidate's resume explicitly mentions 'HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.' This indicates they have applied HRIS database management and record keeping skills in a previous role.",
                    "evidence_chars": 1613,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.47866660356521606,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.41643771529197693,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 11,
                            "start": 6050,
                            "end": 6249,
                            "similarity": 0.41091257333755493,
                            "text": "man Resources Management Senior Certified Professional (SHRM-SCP)\nPROFESSIONAL HR AFFILIATIONS\nMember – Society of Human Resources Management (SHRM)\nMember & Education Committee Chair – World at Work",
                        },
                    ],
                },
                {
                    "category": "technical_skills",
                    "question": "Does the candidate have knowledge of HR law and compliance with governmental regulations?",
                    "answer": "Yes",
                    "score": 8.0,
                    "reasoning": "The candidate's experience at Donovan Corporation involved 'regulatory compliance' and leading HR change and transformation programs, which likely include governmental regulations and compliance requirements. However, there is no explicit mention of knowledge in HR law.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.5316390991210938,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.518385112285614,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.45360082387924194,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                    ],
                },
                {
                    "category": "soft_skills",
                    "question": "Is the candidate able to maintain a high level of confidentiality?",
                    "answer": "No clear evidence provided.",
                    "score": 0.0,
                    "reasoning": "The resume does not provide any specific information about maintaining confidentiality or handling sensitive information.",
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
                    "question": "Can the candidate engage professionally in HR meetings and seminars with other HR professionals in the region?",
                    "answer": "No strong evidence provided.",
                    "score": 1.0,
                    "reasoning": "The resume does not explicitly mention engaging in HR meetings or seminars with other professionals in the region. The provided information focuses more on internal HR transformation and management tasks, without clear references to external interactions.",
                    "evidence_chars": 2114,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 3,
                            "start": 1650,
                            "end": 2350,
                            "similarity": 0.5072564482688904,
                            "text": " directing 4 HR professionals in staffing,\nrecruitment, benefits, executive compensation, training, leadership development, succession planning, HRIS, and\nregulatory compliance. Heavy emphasis on leading Donovan through rapid HR change and transformation programs.\n International HR Launch: Created HR organization – recruitment, staffing, onboarding, training – for both\nexpatriates and local national hires in Brazil, Mexico, and Spain.\n Organization Transformation: Enabled operational change essential to a $5M reduction in HR costs. Helped to\nfacilitate redesign of core business operations, including 2 site closures and 1 fast-track expansion.\n Post-Acquisition HR Integration: Streamlined ",
                        },
                        {
                            "chunk_id": 5,
                            "start": 2750,
                            "end": 3450,
                            "similarity": 0.49474483728408813,
                            "text": "h by assessing HR cultural compatibility and talent impacts.\nUNDERWRITERS LABORATORIES | Indianapolis, IN | Privately owned product testing & certification laboratory 2005 – 2007\nDirector – Human Resources\nTransformed HR into a true strategic business partner in the aftermath of an end-to-end HR restructuring. Championed HR\nvision while forging sustainable HR infrastructure, systems, processes, and practices. Oversaw budget and a staff of 2.\n HRIS Technology: Drove transition from outdated HR systems into a fully integrated HRIS platform from Oracle.\nInstantly improved analysis, reporting, and planning capabilities while streamlining daily HR functions.\n Employee Relations: Introduced proa",
                        },
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.4511191248893738,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                    ],
                },
                {
                    "category": "soft_skills",
                    "question": "Does the candidate have effective oral and written management communication skills?",
                    "answer": "No explicit evidence.",
                    "score": 0.0,
                    "reasoning": "The provided resume chunks do not mention any specific experience or achievements related to oral and written management communication skills.",
                    "evidence_chars": 1613,
                    "retrieved_chunks": [
                        {
                            "chunk_id": 1,
                            "start": 550,
                            "end": 1250,
                            "similarity": 0.4715936481952667,
                            "text": "l is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, value-added goals.\nSignature HR Qualifications\nHR Best Practices Organizational Development Change Management\nEmployee Relations & Diversity Employee Performance Improvement Workforce Planning & Development\nTalent Acquisition Leadership Development M&A Strategies & Due Diligence\nStaff Coaching & Mentoring HR Policy, Process & Systems Design Organization-Wide Consensus Building\nDisciplined and flexible problem-solving approach that balances business goals with employee needs.\nPROFESSIONAL EXPERIENCE\nDONOVAN CORPORATION | Chicago, IL | $200M commun",
                        },
                        {
                            "chunk_id": 0,
                            "start": 0,
                            "end": 700,
                            "similarity": 0.4366610050201416,
                            "text": "LORETTA DANIELSON, MBA, SPHR, SHRM-SCP\n312-555-5555 | lorettadanielson@gmail.com\nLinkedIn.com/in/lorettadanielson\nHUMA N R E SO UR C ES D IR EC TOR\nStart-ups | Acquisitions | Turnarounds | High-Growth Organizations\nPositioning HR as a Business Partner for Excellence\nStrategic and innovative HR Executive who translates business vision into HR initiatives that improve performance, profitability,\ngrowth, and employee engagement. Empowering leader who supports companies and top executives with a unique perspective\nand appreciation that human capital is every organization’s greatest asset. Genuine influencer who thrives on tough challenges\nand translates visions and strategies into actionable, va",
                        },
                        {
                            "chunk_id": 11,
                            "start": 6050,
                            "end": 6249,
                            "similarity": 0.4023181200027466,
                            "text": "man Resources Management Senior Certified Professional (SHRM-SCP)\nPROFESSIONAL HR AFFILIATIONS\nMember – Society of Human Resources Management (SHRM)\nMember & Education Committee Chair – World at Work",
                        },
                    ],
                },
            ],
            "average_score": 1.8,
        },
        "jd_text_length": 1524,
        "resume_text_length": 6249,
        "questions": {
            "education": [],
            "experience": [
                {
                    "question": "Has the candidate performed employee orientation and training logistics and recordkeeping?"
                },
                {
                    "question": "Has the candidate facilitated or participated in company-wide committees?"
                },
                {
                    "question": "Has the candidate assisted with employee safety, welfare, wellness, and health reporting?"
                },
                {
                    "question": "Has the candidate provided direct support to employees during the implementation of HR services, policies, and programs?"
                },
            ],
            "technical_skills": [
                {
                    "question": "Is the candidate proficient with Microsoft Word and Excel?"
                },
                {
                    "question": "Can the candidate apply Human Resources Information System (HRIS) database management and record keeping skills?"
                },
                {
                    "question": "Does the candidate have knowledge of HR law and compliance with governmental regulations?"
                },
            ],
            "soft_skills": [
                {
                    "question": "Is the candidate able to maintain a high level of confidentiality?"
                },
                {
                    "question": "Can the candidate engage professionally in HR meetings and seminars with other HR professionals in the region?"
                },
                {
                    "question": "Does the candidate have effective oral and written management communication skills?"
                },
            ],
        },
        "message": "Resume scored successfully.",
    }
