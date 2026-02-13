import asyncio
import json
import logging
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.schemas.scoring_config_schema import ScoringConfigCreate, ScoringConfigUpdate
from app.security import get_current_user, get_current_user_token
from app.service.pocketbase import get_pocketbase_service, PocketBaseService
from app.service.resume_rag_scorer import recalculate_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scoring-configs", tags=["Scoring Configs"])


# ─────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────

@router.get("")
async def list_configs(
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """List all scoring configs for the current user."""
    try:
        configs = await pb.list_scoring_configs(token, user["id"])
        # Attach usage_count to each config
        for cfg in configs:
            jds = await pb.get_jds_using_config(token, user["id"], cfg["id"])
            cfg["usage_count"] = len(jds)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}")
async def get_config(
    config_id: str,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Get a single scoring config with usage count."""
    try:
        cfg = await pb.get_scoring_config(token, config_id)
        jds = await pb.get_jds_using_config(token, user["id"], cfg["id"])
        cfg["usage_count"] = len(jds)
        cfg["used_by_jds"] = jds
        return cfg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_config(
    data: ScoringConfigCreate,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Create a new scoring config."""
    try:
        # Enforce is_default uniqueness
        if data.is_default:
            await pb.clear_default_scoring_configs(token, user["id"])

        payload = data.model_dump()
        config = await pb.create_scoring_config(token, user["id"], payload)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{config_id}")
async def update_config(
    config_id: str,
    data: ScoringConfigUpdate,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Update an existing scoring config."""
    try:
        # Enforce is_default uniqueness
        if data.is_default:
            await pb.clear_default_scoring_configs(token, user["id"])

        payload = data.model_dump(exclude_none=True)
        config = await pb.update_scoring_config(token, config_id, payload)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{config_id}")
async def delete_config(
    config_id: str,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """Delete a scoring config. Unlinks it from all JDs first."""
    try:
        unlinked = await pb.unlink_config_from_jds(token, user["id"], config_id)
        await pb.delete_scoring_config(token, config_id)
        return {"success": True, "unlinked_jds": unlinked}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Assign config to JD + trigger recalculation
# ─────────────────────────────────────────────────────────────

@router.post("/{config_id}/assign/{jd_id}")
async def assign_config_to_jd(
    config_id: str,
    jd_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """
    Assign a scoring config to a JD and trigger async recalculation
    of all completed scores for that JD.
    """
    try:
        # 1. Verify config exists
        config = await pb.get_scoring_config(token, config_id)

        # 2. Update JD's scoring_config relation
        await pb.update_jd(token, jd_id, {"scoring_config": config_id})

        # 3. Trigger async recalculation
        results = await pb.get_completed_results_for_jd(token, jd_id)
        affected_count = len(results)

        if affected_count > 0:
            # Mark all as recalculating
            result_ids = [r["id"] for r in results]
            await pb.bulk_update_status(token, result_ids, "recalculating")

            # Run recalculation in background
            background_tasks.add_task(
                _recalculate_results, token, results, config, config_id, pb
            )

        return {
            "status": "recalculating" if affected_count > 0 else "assigned",
            "affected_count": affected_count,
            "config_id": config_id,
            "jd_id": jd_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Standalone recalculation (e.g., after editing a config)
# ─────────────────────────────────────────────────────────────

@router.post("/recalculate/{jd_id}")
async def recalculate_jd_scores(
    jd_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    token: str = Depends(get_current_user_token),
    pb: PocketBaseService = Depends(get_pocketbase_service),
):
    """
    Recalculate all completed scores for a JD using its current scoring config.
    Pure math — no LLM calls needed.
    """
    try:
        # Get the JD to find its config
        jd = await pb.get_jd(token, jd_id)
        config_id = jd.get("scoring_config")

        if config_id:
            config = await pb.get_scoring_config(token, config_id)
        else:
            # Use default weights
            config = {
                "education_weight": 25,
                "experience_weight": 25,
                "technical_weight": 25,
                "soft_skills_weight": 25,
                "mandatory_question_weight": 2.0,
                "optional_question_weight": 1.0,
                "mandatory_cap_weight": 0.5,
            }

        results = await pb.get_completed_results_for_jd(token, jd_id)
        affected_count = len(results)

        if affected_count > 0:
            result_ids = [r["id"] for r in results]
            await pb.bulk_update_status(token, result_ids, "recalculating")

            background_tasks.add_task(
                _recalculate_results, token, results, config, config_id or "", pb
            )

        return {
            "status": "recalculating" if affected_count > 0 else "no_results",
            "affected_count": affected_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Background recalculation worker
# ─────────────────────────────────────────────────────────────

async def _recalculate_results(
    token: str,
    results: list,
    config: dict,
    config_id: str,
    pb: PocketBaseService,
):
    """
    Background task: recalculate scores for a list of scoring results.
    Pure math — no LLM. Updates each result's score and status.
    """
    for result in results:
        try:
            # Get the stored analysis (question-level scores)
            analysis = result.get("analysis")
            if isinstance(analysis, str):
                analysis = json.loads(analysis)

            if not analysis:
                logger.warning(f"No analysis for result {result['id']}, skipping recalc")
                await pb.update_scoring_result_score(token, result["id"], result.get("score", 0), "completed")
                continue

            # Extract questions from the analysis
            questions = analysis.get("questions", [])
            if not questions:
                await pb.update_scoring_result_score(token, result["id"], result.get("score", 0), "completed")
                continue

            # Recalculate using pure math
            new_score = recalculate_score(questions, config)

            # Update the result
            await pb.update_scoring_result_score(token, result["id"], new_score, "completed")

            # Record config history
            if config_id:
                config_snapshot = {
                    k: config.get(k) for k in [
                        "name", "education_weight", "experience_weight",
                        "technical_weight", "soft_skills_weight",
                        "mandatory_question_weight", "optional_question_weight",
                        "mandatory_cap_weight",
                    ]
                }
                try:
                    await pb.create_score_config_history(
                        token, result["id"], config_id, config_snapshot
                    )
                except Exception:
                    pass  # Non-critical

            logger.info(f"✅ Recalculated {result['id']}: {result.get('score', 0)} → {new_score}")

        except Exception as e:
            logger.error(f"❌ Recalculation failed for {result['id']}: {e}")
            # Mark back to completed to avoid stuck state
            try:
                await pb.update_scoring_result_score(
                    token, result["id"], result.get("score", 0), "completed"
                )
            except Exception:
                pass
