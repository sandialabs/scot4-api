from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.endpoints import router
from app.core.config import settings
from app.db.session import SessionLocal


def register_cors(app: FastAPI) -> None:
    """ """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # Remember we need to
        allow_origin_regex=r"moz-extension:\/\/.*",  # Needed to make the Plugin function properly in Firefox, works fine in Chrome/Edge... no idea why
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def db_middleware(request: Request, call_next) -> None:
    """
    Middleware that wraps each API call in a transaction
    """
    with SessionLocal() as db_session:
        request.state.db = db_session

        response = await call_next(request)
        if response.status_code >= 500:
            db_session.rollback()
        else:

            db_session.commit()

            if hasattr(request.state, "audit_logger") and request.state.audit_logger:
                request.state.audit_logger.save_audits(db_session)
                db_session.commit()

    return response


def register_router(app: FastAPI) -> None:
    """ """
    app.include_router(router.api_router, prefix=settings.API_V1_STR)


def create_app() -> FastAPI:
    """
    :return:
    """
    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        docs_url=settings.DOCS_URL,
        openapi_url=settings.OPENAPI_URL,
        redoc_url=settings.REDOC_URL,
    )

    register_cors(app)
    register_router(app)
    app.add_middleware(BaseHTTPMiddleware, dispatch=db_middleware)

    return app
