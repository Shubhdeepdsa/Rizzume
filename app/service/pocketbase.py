import logging
import json
from typing import Optional, Dict, Any, List, BinaryIO
import httpx
from fastapi import HTTPException, status
from app.config import get_settings

logger = logging.getLogger(__name__)

class PocketBaseError(Exception):
    def __init__(self, status_code: int, message: str, data: Any = None):
        self.status_code = status_code
        self.message = message
        self.data = data
        super().__init__(message)

class PocketBaseService:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.pocketbase_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def close(self):
        await self.client.aclose()

    def _handle_error(self, response: httpx.Response, action: str) -> None:
        if response.is_success:
            return
        
        try:
            error_data = response.json()
            msg = error_data.get("message", response.text)
        except Exception:
            msg = response.text
        
        logger.error(f"PocketBase {action} failed: {response.status_code} - {msg}")
        raise PocketBaseError(response.status_code, f"PocketBase Error: {msg}", data=error_data if 'error_data' in locals() else None)

    # =========================================================================
    # Auth
    # =========================================================================

    async def auth_with_password(self, identity: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return token + record."""
        resp = await self.client.post(
            "/api/collections/users/auth-with-password",
            json={"identity": identity, "password": password}
        )
        if resp.status_code == 400:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        self._handle_error(resp, "auth_with_password")
        return resp.json()

    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user."""
        payload = {
            "email": email,
            "password": password,
            "passwordConfirm": password,
            "name": name,
            "emailVisibility": True
        }
        resp = await self.client.post("/api/collections/users/records", json=payload)
        self._handle_error(resp, "create_user")
        return resp.json()

    async def request_password_reset(self, email: str) -> bool:
        """Trigger password reset email."""
        resp = await self.client.post(
            "/api/collections/users/request-password-reset",
            json={"email": email}
        )
        self._handle_error(resp, "request_password_reset")
        return True

    async def auth_refresh(self, token: str) -> Dict[str, Any]:
        """Validate token and get fresh user data."""
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self.client.post(
            "/api/collections/users/auth-refresh",
            headers=headers
        )
        if resp.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        self._handle_error(resp, "auth_refresh")
        return resp.json()

    # =========================================================================
    # Resumes
    # =========================================================================

    async def create_resume(
        self,
        token: str,
        user_id: str,
        name: str,
        original_text: str,
        file_obj: BinaryIO,
        filename: str,
        tags: List[str] = [],
        embeddings: Optional[List[float]] = None # Serialized or raw? Usually huge.
        # Note: Embeddings are List[List[float]] usually. We will store as JSON.
    ) -> Dict[str, Any]:
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Prepare form fields (non-file)
        data = {
            "user": user_id,
            "name": name,
            "original_text": original_text,
            "tags": json.dumps(tags),
            "embeddings": json.dumps(embeddings) if embeddings else "null"
        }
        
        files = {
            "file": (filename, file_obj, "application/octet-stream")
        }
        
        resp = await self.client.post(
            "/api/collections/resumes/records",
            headers=headers,
            data=data,
            files=files
        )
        self._handle_error(resp, "create_resume")
        return resp.json()

    async def list_resumes(self, token: str, user_id: str) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        # Filter by user
        resp = await self.client.get(
            "/api/collections/resumes/records",
            headers=headers,
            params={"filter": f'user="{user_id}"', "sort": "-created"}
        )
        self._handle_error(resp, "list_resumes")
        return resp.json().get("items", [])
        
    async def get_resume(self, token: str, resume_id: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self.client.get(
            f"/api/collections/resumes/records/{resume_id}",
            headers=headers
        )
        self._handle_error(resp, "get_resume")
        return resp.json()

    async def update_resume_tags(self, token: str, resume_id: str, tags: List[str]) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self.client.patch(
            f"/api/collections/resumes/records/{resume_id}",
            headers=headers,
            json={"tags": json.dumps(tags)}
        )
        self._handle_error(resp, "update_resume_tags")
        return resp.json()

    # =========================================================================
    # Job Descriptions
    # =========================================================================
    
    async def create_jd(
        self,
        token: str,
        user_id: str,
        role_name: str,
        company_name: str,
        original_text: str,
        questions: List[Dict[str, Any]],
        file_obj: Optional[BinaryIO] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        
        data = {
            "user": user_id,
            "role_name": role_name,
            "company_name": company_name,
            "original_text": original_text,
            "generated_questions": json.dumps(questions)
        }
        
        files = {}
        if file_obj and filename:
            files["file"] = (filename, file_obj, "application/octet-stream")
            
        resp = await self.client.post(
            "/api/collections/job_descriptions/records",
            headers=headers,
            data=data,
            files=files if files else None 
        ) # Note: if files is None, httpx sends json if data is dict?
        # Safe way: if files, use 'data' and 'files'. If NO files, use 'json' if we want JSON body, 
        # but PB accepts specific Content-Type. 
        # Httpx: if files param provided, it uses multipart/form-data.
        # If we have no file, PB still accepts multipart, OR we can send JSON.
        
        if not files:
             resp = await self.client.post(
                "/api/collections/job_descriptions/records",
                headers=headers,
                json=data
            )
        else:
             resp = await self.client.post(
                "/api/collections/job_descriptions/records",
                headers=headers,
                data=data,
                files=files
            )
            
        self._handle_error(resp, "create_jd")
        return resp.json()

    async def list_jds(self, token: str, user_id: str) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self.client.get(
            "/api/collections/job_descriptions/records",
            headers=headers,
            params={"filter": f'user="{user_id}"', "sort": "-created"}
        )
        self._handle_error(resp, "list_jds")
        return resp.json().get("items", [])

    async def get_jd(self, token: str, jd_id: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self.client.get(
            f"/api/collections/job_descriptions/records/{jd_id}",
            headers=headers
        )
        self._handle_error(resp, "get_jd")
        return resp.json()

    # =========================================================================
    # Scoring Results
    # =========================================================================

    async def create_scoring_job(
        self,
        token: str,
        user_id: str,
        resume_id: str,
        jd_id: str
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "user": user_id,
            "resume": resume_id,
            "jd": jd_id,
            "status": "queued",
            "score": 0.0,
            "analysis": "{}"
        }
        resp = await self.client.post(
            "/api/collections/scoring_results/records",
            headers=headers,
            json=payload
        )
        self._handle_error(resp, "create_scoring_job")
        return resp.json()

    async def get_scoring_results(
        self, 
        token: str, 
        user_id: str,
        resume_id: Optional[str] = None,
        jd_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Build filter string
        filter_str = f'user="{user_id}"'
        if resume_id:
            filter_str += f' && resume="{resume_id}"'
        if jd_id:
            filter_str += f' && jd="{jd_id}"'
            
        params = {
            "filter": filter_str,
            "sort": "-created",
            "expand": "resume,jd"
        }
        
        resp = await self.client.get(
            "/api/collections/scoring_results/records",
            headers=headers,
            params=params
        )
        self._handle_error(resp, "get_scoring_results")
        return resp.json().get("items", [])

    async def get_scoring_result_detail(self, token: str, record_id: str) -> Dict[str, Any]:
        """Fetch a single result with full details."""
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self.client.get(
            f"/api/collections/scoring_results/records/{record_id}",
            headers=headers,
            params={"expand": "resume,jd"}
        )
        self._handle_error(resp, "get_scoring_result_detail")
        return resp.json()

    # =========================================================================
    # Worker Methods (Admin/System Level - pass known token or use API Key if configured)
    # FOR NOW: Since we don't have Admin Auth flows, we assume the Worker uses a robust token
    # or we handle queue processing slightly differently (stateless?).
    # Ideally, Worker has Admin Access.
    # For MVP: Worker will assume it has access or we rely on user-triggered processing? NO, user wants Async.
    # We need an Admin Client or Admin Login.
    # =========================================================================
    
    async def admin_auth_with_email(self, email: str, password: str) -> str:
        """
        Authenticate as a superuser (Admin) via standard collection auth.
        In PB v0.23+, admins are just users in '_superusers' collection.
        """
        resp = await self.client.post(
            "/api/collections/_superusers/auth-with-password",
            json={"identity": email, "password": password}
        )
        self._handle_error(resp, "admin_auth")
        return resp.json()["token"]

    async def list_queued_jobs(self, admin_token: str) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await self.client.get(
            "/api/collections/scoring_results/records",
            headers=headers,
            params={"filter": 'status="queued"', "sort": "created", "expand": "resume,jd"}
        )
        if not resp.is_success:
             return []
        return resp.json().get("items", [])

    async def ensure_collections_exist(self, admin_token: str) -> None:
        """
        Check if required collections exist, if not create them.
        """
        from app.service.pb_collections import get_resumes_schema, get_jds_schema, get_scoring_results_schema
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. Get existing collections
        try:
             resp = await self.client.get("/api/collections", headers=headers, params={"perPage": 100})
             items = resp.json().get("items", [])
             existing_names = {c["name"]: c["id"] for c in items}
             
             # Locate "users" collection ID dynamically to be safe
             users_col_id = existing_names.get("users")
             if not users_col_id:
                 # Fallback to verify if it has a different name or system ID
                 for c in items:
                     if c["type"] == "auth": # Assuming main auth is users
                         users_col_id = c["id"]
                         break
             if not users_col_id:
                 logger.warning("Could not find 'users' collection. Using default '_pb_users_auth_'.")
                 users_col_id = "_pb_users_auth_"
                 
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return

        # 2. Resumes
        if "resumes" not in existing_names:
            logger.info("🛠 Creating 'resumes' collection...")
            schema = get_resumes_schema(users_col_id)
            try:
                r = await self.client.post("/api/collections", headers=headers, json=schema)
                if r.is_success:
                    existing_names["resumes"] = r.json()["id"]
                else:
                    logger.error(f"Failed to create resumes: {r.text}")
            except Exception as e:
                logger.error(f"Error creating resumes: {e}")
        
        # 3. JDs
        if "job_descriptions" not in existing_names:
            logger.info("🛠 Creating 'job_descriptions' collection...")
            schema = get_jds_schema(users_col_id)
            try:
                r = await self.client.post("/api/collections", headers=headers, json=schema)
                if r.is_success:
                    existing_names["job_descriptions"] = r.json()["id"]
                else:
                     logger.error(f"Failed to create jds: {r.text}")
            except Exception as e:
                logger.error(f"Error creating jds: {e}")

        # 4. Scoring Results (needs IDs)
        if "scoring_results" not in existing_names:
            if "resumes" in existing_names and "job_descriptions" in existing_names:
                logger.info("🛠 Creating 'scoring_results' collection...")
                schema = get_scoring_results_schema(existing_names["resumes"], existing_names["job_descriptions"], users_col_id)
                try:
                    r = await self.client.post("/api/collections", headers=headers, json=schema)
                    if not r.is_success:
                        logger.error(f"Failed to create scoring_results: {r.text}")
                except Exception as e:
                    logger.error(f"Error creating scoring_results: {e}")
            else:
                logger.warning("Skipping 'scoring_results' creation because dependencies missing.")
                
        logger.info("✅ Encured collections exist.")

    async def update_job_status(
        self, 
        admin_token: str, 
        job_id: str, 
        status: str, 
        score: float = 0.0, 
        analysis: Dict = None
    ):
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {"status": status}
        if score > 0:
            payload["score"] = score
        if analysis:
            payload["analysis"] = json.dumps(analysis)
            
        resp = await self.client.patch(
            f"/api/collections/scoring_results/records/{job_id}",
            headers=headers,
            json=payload
        )
        self._handle_error(resp, "update_job_status")




# Singleton
_service: Optional[PocketBaseService] = None

def get_pocketbase_service() -> PocketBaseService:
    global _service
    if _service is None:
        _service = PocketBaseService()
    return _service
