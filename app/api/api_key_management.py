from fastapi import APIRouter, HTTPException
from app.services.api_key_utils import create_api_key, delete_api_key

router = APIRouter(prefix="/api-key", tags=["API Key Management"])

@router.post("/create")
async def createKey(key: str):
    await create_api_key(key)
    return {"message": "API key created", "key": key}

@router.delete("/delete")
async def deleteKey(key: str):
    await delete_api_key(key)
    return {"message": "API key deleted", "key": key}
