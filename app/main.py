from fastapi import FastAPI
from app.routes.scoring_route import router
app = FastAPI()
app.include_router(router)

@app.get("/health")
async def root():
    return {"status": "healthy and running"}
