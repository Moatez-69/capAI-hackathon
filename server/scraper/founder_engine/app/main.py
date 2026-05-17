from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Founder Intelligence Aggregation Engine", version="1.0.0")
app.include_router(router, prefix="/api/v1")
