import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str
    environment: str

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", environment=os.getenv("APP_ENV", "local"))
