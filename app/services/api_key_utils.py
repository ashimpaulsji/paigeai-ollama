from fastapi import HTTPException, Request
from app.models.mongodb import mongodb

async def verify_api_key(request: Request):
    if request.url.path.startswith("/api/v1/"):
        api_key = request.headers.get("x-api-key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key.")
        key_doc = await mongodb.get_db().api_keys.find_one({"key": api_key})
        if not key_doc:
            raise HTTPException(status_code=401, detail="Invalid API key.")

def get_api_key_collection():
    return mongodb.get_db().api_keys

async def create_api_key(key: str, meta: dict = None):
    col = get_api_key_collection()
    # Check if key already exists
    existing = await col.find_one({"key": key})
    if existing:
        raise HTTPException(status_code=409, detail="API key already exists.")
    doc = {"key": key}
    if meta:
        doc.update(meta)
    await col.insert_one(doc)

async def delete_api_key(key: str):
    col = get_api_key_collection()
    result = await col.delete_one({"key": key})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found.")

async def list_api_keys():
    col = get_api_key_collection()
    return await col.find().to_list(length=100)
