import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.metrics import record_request, render_metrics_text
from app.routes.scoring_route import router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # add "http://localhost:4173" if you use `npm run preview`
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Log configuration on startup."""
    settings = get_settings()
    llm_model = (
        settings.groq_model 
        if settings.llm_provider.lower() == "groq" 
        else settings.ollama_default_model
    )
    logger.info("═" * 60)
    logger.info("🎯 RIZZUME - Configuration Summary")
    logger.info("═" * 60)
    logger.info("  📦 LLM Provider: %s", settings.llm_provider.upper())
    logger.info("  🤖 LLM Model: %s", llm_model)
    logger.info("  📊 Embedding Model: %s", settings.embed_model_name)
    if settings.llm_provider.lower() == "ollama":
        logger.info("  🔗 Ollama URL: %s", settings.ollama_base_url)
    logger.info("═" * 60)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Simple middleware to record request durations and error counts.
    """
    start = time.time()
    error = False
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            error = True
        return response
    except Exception:
        error = True
        raise
    finally:
        duration = time.time() - start
        # Use route path if available, fallback to raw path.
        path = request.url.path
        method = request.method
        record_request(path, method, duration, error)


@app.get("/health")
async def root():
    return {"status": "healthy and running"}


@app.get("/metrics")
async def metrics():
    """
    Expose basic text metrics.
    """
    return render_metrics_text()
