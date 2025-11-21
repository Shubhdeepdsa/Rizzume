import logging
import time

from fastapi import FastAPI, Request

from app.metrics import record_request, render_metrics_text
from app.routes.scoring_route import router


logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(router)


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
