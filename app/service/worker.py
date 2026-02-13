import asyncio
import json
import logging
from typing import List

import numpy as np
from fastapi.concurrency import run_in_threadpool

from app.service.pocketbase import get_pocketbase_service
from app.service.resume_rag_scorer import score_resume_with_rag
from app.service.chunking import TextChunk
from app.schemas.jd_questions_schema import JDQuestions

logger = logging.getLogger(__name__)

# Global state for worker
_worker_token = None

async def process_scoring_queue():
    """
    Background task to process queued scoring jobs.
    Uses cached token to avoid re-authenticating every cycle.
    """
    global _worker_token
    pb = get_pocketbase_service()
    
    from app.config import get_settings
    import os
    # Use environment variables for Admin Auth
    admin_email = os.getenv("PB_ADMIN_EMAIL", "shubhdeepdas0@gmail.com") 
    admin_pass = os.getenv("PB_ADMIN_PASSWORD", "030301@Deepdas")
    
    # 1. Authenticate (if needed)
    if not _worker_token:
        try:
            # logger.info(f"🔑 [Worker] Authenticating as {admin_email}...")
            _worker_token = await pb.admin_auth_with_email(admin_email, admin_pass)
        except Exception as e:
            logger.warning(f"Worker failed to authenticate ({admin_email}): {e}. Worker skipping cycle.")
            return

    token = _worker_token

    # 2. Fetch queued jobs
    try:
        # We fetch list. Expanding resume and jd is crucial.
        records = await pb.client.get(
            "/api/collections/scoring_results/records",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "filter": 'status="queued"',
                "sort": "created",
                "expand": "resume,jd",
                "perPage": 5 # Batch size
            }
        )
        
        # Handle Token Expiry (401)
        if records.status_code == 401:
            logger.warning("⚠️ [Worker] Token expired. clearing cache and retrying next cycle.")
            _worker_token = None
            return

        if records.status_code != 200:
            # Silent fail for 404 (Missing collection) to avoid log spam, 
            # BUT we want to know if startup setup failed.
            if records.status_code == 404:
                return 
            logger.error(f"Worker failed to list jobs: {records.text}")
            return
            
        items = records.json().get("items", [])
    except Exception as e:
        logger.error(f"Worker exception listing jobs: {e}")
        return

    if not items:
        # Silent when no jobs
        return

    logger.info(f"👷 [Worker] Processing {len(items)} queued jobs...")

    for job in items:
        job_id = job["id"]
        expand = job.get("expand", {})
        resume_record = expand.get("resume")
        jd_record = expand.get("jd")

        if not resume_record or not jd_record:
            logger.error(f"Job {job_id} missing expand data. Marking failed.")
            await pb.update_job_status(token, job_id, "failed")
            continue

        # Mark Processing
        await pb.update_job_status(token, job_id, "processing")

        try:
            # 2. Rehydrate Data
            # Resume Index
            # Resume Index
            chunks_data = resume_record.get("embeddings")
            if isinstance(chunks_data, str):
                chunks_data = json.loads(chunks_data)
            if not chunks_data:
                chunks_data = []
            
            # Reconstruct TextChunk list and Numpy Array
            chunks: List[TextChunk] = []
            vectors_list = []
            
            for c in chunks_data:
                chunks.append(TextChunk(
                    text=c["text"],
                    start=c["start"],
                    end=c["end"],
                    id=c.get("id")
                ))
                vectors_list.append(c["vector"])
            
            precomputed = None
            if chunks and vectors_list:
                precomputed = (chunks, np.array(vectors_list, dtype=np.float32))

            # JD Questions
            q_json = jd_record.get("generated_questions") or {}
            
            if isinstance(q_json, str):
                q_json = json.loads(q_json)
                
            jd_questions = JDQuestions.model_validate(q_json)

            # Fetch JD's scoring config (if assigned)
            scoring_config = None
            config_id = jd_record.get("scoring_config")
            if config_id:
                try:
                    scoring_config = await pb.get_scoring_config(token, config_id)
                except Exception:
                    logger.warning(f"[Worker] Could not fetch scoring_config {config_id} for job {job_id}. Using defaults.")
            
            # 3. Score
            result = await run_in_threadpool(
                score_resume_with_rag,
                jd_questions,
                resume_record.get("original_text", ""),
                3,
                precomputed,
                scoring_config,
            )
            
            # 4. Save
            analysis_dict = result.dict()
            await pb.update_job_status(
                token, 
                job_id, 
                "completed", 
                score=result.average_score, 
                analysis=analysis_dict
            )

            # 5. Record config history (audit trail)
            if scoring_config and config_id:
                try:
                    config_snapshot = {
                        k: scoring_config.get(k) for k in [
                            "name", "education_weight", "experience_weight",
                            "technical_weight", "soft_skills_weight",
                            "mandatory_question_weight", "optional_question_weight",
                            "mandatory_cap_weight",
                        ]
                    }
                    await pb.create_score_config_history(
                        token, job_id, config_id, config_snapshot
                    )
                except Exception as e:
                    logger.warning(f"[Worker] Failed to record config history for {job_id}: {e}")

            logger.info(f"✅ [Worker] Job {job_id} completed. Score: {result.average_score}")

        except Exception as e:
            logger.exception(f"❌ [Worker] Job {job_id} failed: {e}")
            await pb.update_job_status(token, job_id, "failed")


async def ensure_pb_setup():
    """
    Called by main.py on startup to ensure collections exist.
    """
    pb = get_pocketbase_service()
    import os
    admin_email = os.getenv("PB_ADMIN_EMAIL", "shubhdeepdas0@gmail.com") 
    admin_pass = os.getenv("PB_ADMIN_PASSWORD", "030301@Deepdas")
    
    try:
        logger.info("🔧 [Startup] ensuring Pocketbase collections exist...")
        token = await pb.admin_auth_with_email(admin_email, admin_pass)
        await pb.ensure_collections_exist(token)
        logger.info("✅ [Startup] Pocketbase setup complete.")
    except Exception as e:
        logger.error(f"❌ [Startup] Failed to setup PB collections: {e}")
