from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.routes.websocket import router as ws_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FujiFood — White-Label Restaurant Commerce SaaS Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket routes (no prefix — ws://host/ws/...)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
