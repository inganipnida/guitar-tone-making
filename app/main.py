from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import APP_DIR, settings
from app.db.database import init_db
from app.routes.api import router as api_router
from app.routes.ui import router as ui_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, debug=settings.debug)
    application.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
    application.include_router(ui_router)
    application.include_router(api_router)

    @application.on_event("startup")
    def on_startup() -> None:
        init_db()

    return application


app = create_app()
