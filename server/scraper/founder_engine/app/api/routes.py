from fastapi import APIRouter, HTTPException
from app.models.founder import FounderInput, FounderProfile
from app.services.pipeline import run_pipeline

router = APIRouter()


@router.post("/collect", response_model=FounderProfile)
async def collect_founder(payload: FounderInput) -> FounderProfile:
    try:
        profile = await run_pipeline(payload)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok"}
