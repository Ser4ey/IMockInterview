from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
from app.db.session import AsyncSessionLocal, engine
from app.db.schema_sync import prepare_database
from app.services.admin_bootstrap import ensure_admin_user

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def create_local_tables() -> None:
    await prepare_database(engine)
    async with AsyncSessionLocal() as db:
        await ensure_admin_user(db)

@app.get("/")
def root():
    return {"message": "IMock API работает"}
