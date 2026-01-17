from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.endpoints import auth, webhooks, admin, kb, test_lab, ai, bi
from app.db.session import engine
from app.db.base import Base

# Setup Logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    
    # Initialize DB (Create tables for DEV mode - in prod use migrations)
    # This will now create tables for User, TestRun, KBDocument etc.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}

# Register Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(kb.router, prefix=f"{settings.API_V1_STR}/kb", tags=["kb"])
app.include_router(test_lab.router, prefix=f"{settings.API_V1_STR}/testlab", tags=["test_lab"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai"])
app.include_router(bi.router, prefix=f"{settings.API_V1_STR}/bi", tags=["bi"])
# P2: Bot Studio Routers
from app.api.v1.endpoints import bot_studio
app.include_router(bot_studio.router, prefix=f"{settings.API_V1_STR}/botstudio", tags=["bot_studio"])
