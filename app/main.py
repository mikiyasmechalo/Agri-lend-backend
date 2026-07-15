from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine
from app.routers.v1 import auth, farmers, banks, loans, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AgriLend backend — environment: %s", settings.environment)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.seed import seed_roles
    await seed_roles()
    yield
    await engine.dispose()


app = FastAPI(
    title="AgriLend API",
    description="Agricultural Credit Intelligence Platform — Backend API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(farmers.router, prefix="/api/v1")
app.include_router(loans.router, prefix="/api/v1")
app.include_router(banks.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
