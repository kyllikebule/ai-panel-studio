"""AI Panel Studio — FastAPI 应用入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.guests import router as guest_router
from .api.routes.discussions import router as discussion_router
from .api.ws.studio import router as ws_router
from .db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库。"""
    await init_db()
    yield


app = FastAPI(
    title="AI Panel Studio",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guest_router)
app.include_router(discussion_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
