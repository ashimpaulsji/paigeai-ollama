from fastapi import FastAPI, Request, HTTPException
from fastapi.openapi.utils import get_openapi
from app.api.endpoints import router
from app.api.api_key_management import router as api_key_router
from app.core.config import settings
from app.core.logging_config import *
from app.services.api_key_utils import verify_api_key
from app.models.mongodb import mongodb  # fixed import
from fastapi.responses import JSONResponse
from fastapi import status

app = FastAPI(title="Invoice Extractor", version="1.0.0")

@app.middleware("http")
async def apiKeyMiddleware(request: Request, call_next):
    try:
        await verify_api_key(request)
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    response = await call_next(request)
    return response

def customOpenapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Add x-api-key header globally
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            parameters = method.setdefault("parameters", [])
            parameters.append({
                "name": "x-api-key",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "API Key required to access the endpoints"
            })
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = customOpenapi

app.include_router(router, prefix="/api/v1")
app.include_router(api_key_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)