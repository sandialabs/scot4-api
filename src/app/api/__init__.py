from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.endpoints import router
from app.core.config import settings
from app.db.session import SessionLocal


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
        swagger_ui_parameters={
            "filter": True
        }
    )

    app.include_router(router.api_router, prefix=settings.API_V1_STR)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # Remember we need to
        allow_origin_regex=r"moz-extension:\/\/.*",  # Needed to make the Plugin function properly in Firefox, works fine in Chrome/Edge... no idea why
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(BaseHTTPMiddleware, dispatch=db_middleware)

    if not app.openapi_schema:
        # will need to update all links for open source stuff
        openapi_schema = get_openapi(
            title="SCOT",
            version="4.2.0",
            summary="Sandia Cyber Omni Tracker Server",
            description="The Sandia Cyber Omni Tracker (SCOT) is a cyber security incident response management system and knowledge base. Designed by cyber security incident responders, SCOT provides a new approach to manage security alerts, analyze data for deeper patterns, coordinate team efforts, and capture team knowledge. SCOT integrates with existing security applications to provide a consistent, easy to use interface that enhances analyst effectiveness.",
            routes=app.routes,
            # terms_of_service?
            contact={
                "name": "SCOT Development Team",
                "url": "http://getscot.sandia.gov",
                "email": "scot-dev@sandia.gov"
            },
            license_info={
                "name": "LICENSE",
                "identifier": "Apache-2.0",
            },
        )
        openapi_schema["info"]["x-logo"] = {
            "url": "https://sandialabs.github.io/scot4-docs/images/scot.png"
        }
        app.openapi_schema = openapi_schema

    return app
