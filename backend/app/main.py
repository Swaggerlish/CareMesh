from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.app_debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, 'http://localhost:5173', 'https://localhost:5173', 'http://localhost:5174', 'https://localhost:5174'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    Base.metadata.create_all(bind=engine)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get('/')
    def root() -> dict[str, str]:
        return {'message': 'CareMesh API is running'}

    return app


app = create_app()
