from logging.config import dictConfig
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html
)
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from sqlalchemy.exc import TimeoutError, DatabaseError

from app.api.endpoints import router
from app.core.config import settings
from app.db.session import SessionLocal


async def db_middleware(request: Request, call_next) -> None:
    """
    Middleware that wraps each API call in a transaction
    """
    ROUTE_PREFIX_WHITELIST = ("/api/v1/firehose")
    if request.url.path.startswith(ROUTE_PREFIX_WHITELIST):
        return await call_next(request)
    else:
        try:
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
        except TimeoutError:
            return PlainTextResponse("Timeout when connecting to database", status_code=503)
        except DatabaseError:
            raise

    return response


def create_app() -> FastAPI:
    """
    :return:
    """
    # Set up logging format
    # dictConfig({
    #    "version": 1,
    #    "disable_existing_loggers": False,
    #    "formatters": {
    #        "access": {
    #            "()": "uvicorn.logging.AccessFormatter",
    #            "fmt": '%(asctime)s - %(levelprefix)s %(client_addr)s - \"%(request_line)s\" %(status_code)s',
    #            "use_colors": True
    #        },
    #    },
    #    "handlers": {
    #        "access": {
    #            "formatter": "access",
    #            "class": "logging.StreamHandler",
    #            "stream": "ext://sys.stdout",
    #        },
    #    },
    #    "loggers": {
    #        "uvicorn.access": {
    #            "handlers": ["access"],
    #            "level": "INFO",
    #            "propagate": False
    #        },
    #    },
    # })

    app = FastAPI(
        debug=settings.DEBUG,
        docs_url=None,
        redoc_url=None,
        openapi_url=settings.OPENAPI_URL
    )

    app.mount('/api/static', StaticFiles(packages=[('app.api', 'static')]), name='static')

    app.include_router(router.api_router, prefix=settings.API_V1_STR)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # Remember we need to
        allow_origin_regex=r"moz-extension:\/\/.*",  # Needed to make the Plugin function properly in Firefox, works fine in Chrome/Edge... no idea why
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        GZipMiddleware,
        minimum_size=500,
        compresslevel=5)

    app.add_middleware(BaseHTTPMiddleware, dispatch=db_middleware)

    if not app.openapi_schema:
        # will need to update all links for open source stuff
        openapi_schema = get_openapi(
            title="SCOT",
            version="4.4.0",
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

    @app.get(settings.DOCS_URL, include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=settings.OPENAPI_URL,
            title=settings.TITLE,
            swagger_js_url=settings.SWAGGER_JS_URL,
            swagger_css_url=settings.SWAGGER_CSS_URL,
            swagger_ui_parameters={
                "filter": True
            }
        )

    @app.get(settings.REDOC_URL, include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=settings.OPENAPI_URL,
            title=settings.TITLE,
            redoc_js_url=settings.REDOC_JS_URL,
        )

    return app
