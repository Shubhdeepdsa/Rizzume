import json
import logging
import time
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

from app.service.pocketbase import get_pocketbase_service, PocketBaseService
from app.service.embedding_service import embed_texts, cosine_sim_matrix
from app.service.llm_client import call_llm_chat
from app.prompts.tag_extraction_prompt import TAG_EXTRACTION_SYSTEM_PROMPT, build_tag_extraction_user_prompt
from app.schemas.tag_schema import JDExtractionResult, JobMetadata
from app.config import get_settings

logger = logging.getLogger(__name__)

# TTL for cache refresh in seconds (5 minutes)
CACHE_TTL = 300

class TagManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TagManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.cache: Dict[str, Dict[str, Any]] = {
            "role_family": {"ids": [], "vectors": [], "labels": []},
            "skills": {"ids": [], "vectors": [], "labels": []},
            "seniority": {"ids": [], "vectors": [], "labels": []},
            "domain": {"ids": [], "vectors": [], "labels": []}
        }
        self.last_refresh_time = 0
        self.initialized = True
        self.settings = get_settings()

    async def _ensure_cache(self, pb: PocketBaseService, token: str, user_id: str):
        """Check TTL and refresh cache if needed."""
        now = time.time()
        if now - self.last_refresh_time > CACHE_TTL:
            logger.info("🔄 [TagManager] Cache expired. Refreshing from DB...")
            await self._refresh_cache(pb, token, user_id)

    async def _refresh_cache(self, pb: PocketBaseService, token: str, user_id: str):
        try:
            items = await pb.get_all_tags_with_vectors(token, user_id)
            
            # Reset buckets
            new_cache = {
                "role_family": {"ids": [], "vectors": [], "labels": []},
                "skills": {"ids": [], "vectors": [], "labels": []},
                "seniority": {"ids": [], "vectors": [], "labels": []},
                "domain": {"ids": [], "vectors": [], "labels": []}
            }

            for item in items:
                cat = item.get("category")
                if cat in new_cache:
                    vec_store = item.get("vector")
                    # Vector might be stored as list string or raw json list
                    if isinstance(vec_store, str):
                        try:
                            vec = json.loads(vec_store)
                        except:
                            vec = []
                    else:
                        vec = vec_store or []

                    if vec and len(vec) > 0:
                        new_cache[cat]["ids"].append(item["id"])
                        new_cache[cat]["vectors"].append(vec)
                        new_cache[cat]["labels"].append(item["label"])

            # Convert lists to numpy arrays
            for cat in new_cache:
                if new_cache[cat]["vectors"]:
                    new_cache[cat]["vectors"] = np.array(new_cache[cat]["vectors"], dtype="float32")
                else:
                    new_cache[cat]["vectors"] = np.zeros((0, 768), dtype="float32") # Default dim, adjustable?

            self.cache = new_cache
            self.last_refresh_time = time.time()
            logger.info(f"✅ [TagManager] Cache refreshed. Loaded {len(items)} tags.")
        except Exception as e:
            logger.error(f"❌ [TagManager] Failed to refresh cache: {e}")

    def find_similar_tag(self, category: str, vector: np.ndarray, threshold: float = 0.85) -> Optional[str]:
        """
        Find a similar tag in the given category.
        Returns Tag ID if match found, else None.
        """
        if category not in self.cache:
            return None
        
        cat_data = self.cache[category]
        target_matrix = cat_data["vectors"]
        
        if target_matrix.size == 0 or len(target_matrix) == 0:
            return None

        # vector is (dim,), make it (1, dim)
        query = vector.reshape(1, -1)
        
        # Sim matrix: (1, N)
        sims = cosine_sim_matrix(query, target_matrix)
        
        # Get best match
        best_idx = np.argmax(sims)
        best_score = sims[0][best_idx]
        
        if best_score >= threshold:
            logger.info(f"🔍 [TagManager] Found similar tag '{cat_data['labels'][best_idx]}' (score: {best_score:.2f})")
            return cat_data["ids"][best_idx]
        
        return None

    async def create_tag(self, pb, token, user_id, label, category, vector_list) -> str:
        """Create tag in DB and update cache immediately."""
        try:
            record = await pb.create_jd_tag(token, user_id, label, category, vector_list)
            new_id = record["id"]
            
            # Update cache
            if category in self.cache:
                self.cache[category]["ids"].append(new_id)
                self.cache[category]["labels"].append(label)
                
                # Append to numpy array
                current_vecs = self.cache[category]["vectors"]
                new_vec = np.array([vector_list], dtype="float32")
                
                if current_vecs.size == 0:
                     self.cache[category]["vectors"] = new_vec
                else:
                     self.cache[category]["vectors"] = np.vstack([current_vecs, new_vec])
            
            return new_id
        except Exception as e:
            # PocketBase might error on unique constraint.
            # In that case, force strict match?
            # For now, let's treat it as failure or try to find by label?
            # If unique constraint fails, it means we have exact match.
            if "UNIQUE constraint failed" in str(e) or "400" in str(e):
                 # Try to find existing tag by label in cache?
                 # Or just return None/Error. 
                 # Given we did similarity search, this shouldn't happen often unless race condition.
                 logger.warning(f"⚠️ [TagManager] Create tag '{label}' failed (duplicate): {e}")
                 # Fallback: In next refresh it will appear. For now, rely on similarity (which missed it?)
                 # or exact string match if we wanted.
                 pass
            raise e

    async def update_tag_vector(self, pb, token, tag_id, category, new_label):
        """Re-compute vector and update DB."""
        new_vec = embed_texts([new_label])[0]
        await pb.update_jd_tag(token, tag_id, {
            "label": new_label,
            "vector": json.dumps(new_vec.tolist())
        })
        # Force cache refresh next time (simpler than inplace update for now)
        self.last_refresh_time = 0

def get_tag_manager() -> TagManager:
    return TagManager()

async def extract_tags_and_metadata(text: str) -> JDExtractionResult:
    """Call LLM to extract tags and metadata."""
    messages = [
        {"role": "system", "content": TAG_EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": build_tag_extraction_user_prompt(text)},
    ]
    
    response = call_llm_chat(messages)
    
    # helper from jd_question_generator (needs refactor to shared? or copy)
    # i'll copy logic briefly for robustness or import if i can.
    # jd_question_generator has _extract_content_from_ollama_response
    # let's duplicate the simple extraction logic here to avoid circulars or deep deps
    
    content = response.get("message", {}).get("content", "")
    if not content:
        raise ValueError("Empty LLM response")
        
    # Robust JSON extraction: Find first '{' and last '}'
    start_idx = content.find("{")
    end_idx = content.rfind("}")
    
    if start_idx != -1 and end_idx != -1:
        clean_content = content[start_idx : end_idx + 1]
    else:
        # Fallback to stripping if braces not found (unlikely for valid JSON)
        clean_content = content.strip()
        
    try:
        data = json.loads(clean_content)
        return JDExtractionResult.model_validate(data)
    except Exception as e:
        logger.error(f"Failed to parse JD extraction: {e}. Content: {content}")
        raise e

async def process_jd_tags(
    pb: PocketBaseService, 
    token: str, 
    user_id: str, 
    jd_text: str
) -> Tuple[List[str], JobMetadata]:
    """
    Main entry point.
    1. Extract Tags & Metadata
    2. Normalize & Embed Tags
    3. Resolve Tags (Find Existing or Create New)
    4. Return Tag IDs and Metadata
    """
    manager = get_tag_manager()
    await manager._ensure_cache(pb, token, user_id)
    
    # 1. Extraction
    try:
        extraction = await extract_tags_and_metadata(jd_text)
    except Exception as e:
        logger.error(f"JD Extraction failed: {e}")
        # Return empty tags and generic metadata if failed? 
        # Or raise? Better to raise to inform user extraction failed.
        raise e
        
    tag_ids = []
    
    # 2. Processing Tags
    # Collect all text tags flattened with category
    # extraction.tags is JobTags object
    
    tags_to_process = []
    for cat in ["role_family", "skills", "seniority", "domain"]:
        labels = getattr(extraction.tags, cat, [])
        for label in labels:
             tags_to_process.append((cat, label.lower().strip()))
             
    if not tags_to_process:
        return [], extraction.metadata

    # Batch embedding? Default embedding service takes list.
    # So lets embed all labels at once.
    all_labels = [t[1] for t in tags_to_process]
    all_vectors = embed_texts(all_labels) # numpy array
    
    # 3. Resolve
    for i, (cat, label) in enumerate(tags_to_process):
        vector = all_vectors[i] # 1D array
        
        # Check similarity
        found_id = manager.find_similar_tag(cat, vector)
        
        if found_id:
            tag_ids.append(found_id)
        else:
            # Create new
            try:
                logger.info(f"🆕 [TagManager] Creating new tag: {label} ({cat})")
                new_id = await manager.create_tag(pb, token, user_id, label, cat, vector.tolist())
                tag_ids.append(new_id)
            except Exception as e:
                logger.error(f"Failed to create tag {label}: {e}")
    
    return list(set(tag_ids)), extraction.metadata
