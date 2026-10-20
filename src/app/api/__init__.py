import logging
import socket
import time
from logging.config import dictConfig

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.exception_handlers import http_exception_handler
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html
)
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from starlette.exceptions import HTTPException
from sqlalchemy.exc import TimeoutError, OperationalError
import nats
from contextlib import asynccontextmanager

from app.api.endpoints import router
from app.core.config import settings
from app.core.publisher import NatsPublisher
from app.db.session import SessionLocal

request_log = logging.getLogger("app.request")


async def request_debug_middleware(request: Request, call_next):
    start = time.perf_counter()
    pod_name = socket.gethostname()
    request_id = f"{id(request)}"
    request_log.info(
        "request start id=%s pod=%s method=%s path=%s query=%s",
        request_id,
        pod_name,
        request.method,
        request.url.path,
        request.url.query,
    )
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        request_log.exception(
            "request exception id=%s pod=%s method=%s path=%s latency_ms=%s",
            request_id,
            pod_name,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    request_log.info(
        "request finish id=%s pod=%s method=%s path=%s status=%s latency_ms=%s",
        request_id,
        pod_name,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


async def db_middleware(request: Request, call_next) -> None:
    """
    Middleware that wraps each API call in a transaction
    """
    ROUTE_PREFIX_WHITELIST = ("/api/v1/firehose", "/api/v1/health")
    if request.url.path.startswith(ROUTE_PREFIX_WHITELIST):
        try:
            return await call_next(request)
        except HTTPException as e:
            return await http_exception_handler(request, e)
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
        except OperationalError:
            return PlainTextResponse("Error when connecting to database", status_code=500)

    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    nats_server = f"{settings.NATS_PROTOCOL}://{settings.NATS_HOST}:{settings.NATS_PORT}"
    app.state.publisher = NatsPublisher(
        servers=[nats_server],
        name="scot-api",
        max_reconnect_attempts=-1,
        reconnect_time_wait=2,
        connect_timeout=5,
        enabled=settings.NATS_HOST is not None,  # could be settings.NATS_ENABLED
    )
    await app.state.publisher.start()
    try:
        yield
    finally:
        await app.state.publisher.stop()


def create_app() -> FastAPI:
    """
    :return:
    """
    # Set up logging format
    dictConfig({
       "version": 1,
       "disable_existing_loggers": False,
       "formatters": {
           "default": {
               "format": "%(levelname)s:%(name)s:%(message)s",
           },
           "access": {
               "()": "uvicorn.logging.AccessFormatter",
               "fmt": "%(levelprefix)s %(asctime)s.%(msecs)03d - %(client_addr)s - \"%(request_line)s\" %(status_code)s",
               "datefmt": "%Y-%m-%dT%H:%M:%S",
               "use_colors": True
           },
       },
       "handlers": {
           "default": {
               "formatter": "default",
               "class": "logging.StreamHandler",
               "stream": "ext://sys.stdout",
           },
           "access": {
               "formatter": "access",
               "class": "logging.StreamHandler",
               "stream": "ext://sys.stdout",
           },
       },
       "loggers": {
           "uvicorn.access": {
               "handlers": ["access"],
               "level": "INFO",
               "propagate": False
           },
           "app.request": {
               "handlers": ["default"],
               "level": "INFO",
               "propagate": False,
           },
       },
    })

    base_app = FastAPI(
        debug=settings.DEBUG,
        docs_url=None,
        redoc_url=None,
        openapi_url=settings.OPENAPI_URL,
        lifespan=lifespan,
    )

    base_app.mount('/api/static', StaticFiles(packages=[('app.api', 'static')]), name='static')

    base_app.include_router(router.api_router, prefix=settings.API_V1_STR)

    base_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],  # Remember we need to
        allow_origin_regex=r"moz-extension:\/\/.*",  # Needed to make the Plugin function properly in Firefox, works fine in Chrome/Edge... no idea why
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],  # allows for frontend to get download file names
    )

    base_app.add_middleware(
        GZipMiddleware,
        minimum_size=500,
        compresslevel=5)

    if settings.ENV == "Development":
        base_app.add_middleware(BaseHTTPMiddleware, dispatch=request_debug_middleware)

    base_app.add_middleware(BaseHTTPMiddleware, dispatch=db_middleware)

    def custom_openapi():
        if not base_app.openapi_schema:
            # will need to update all links for open source stuff
            openapi_schema = get_openapi(
                title="SCOT",
                version="4.7.3",
                summary="Sandia Cyber Omni Tracker Server",
                description="The Sandia Cyber Omni Tracker (SCOT) is a cyber security incident response management system and knowledge base. Designed by cyber security incident responders, SCOT provides a new approach to manage security alerts, analyze data for deeper patterns, coordinate team efforts, and capture team knowledge. SCOT integrates with existing security applications to provide a consistent, easy to use interface that enhances analyst effectiveness.",
                routes=base_app.routes,
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
            base_app.openapi_schema = openapi_schema
        return base_app.openapi_schema

    base_app.openapi = custom_openapi

    @base_app.get(settings.DOCS_URL, include_in_schema=False)
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

    @base_app.get(settings.REDOC_URL, include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=settings.OPENAPI_URL,
            title=settings.TITLE,
            redoc_js_url=settings.REDOC_JS_URL,
        )

    # Merge the MCP server and the regular API into one application if it's enabled
    if settings.MCP_SERVER_ENABLED:
        try:
            import fastmcp
        except ImportError:
            logging.warning("FastMCP not installed, not starting MCP server")
            app = base_app
        else:
            from app.api.mcp import create_mcp_server

            mcp_app = create_mcp_server(base_app)

            # Dummy lifespan combiner because it's not in fastmcp until version 3
            @asynccontextmanager
            async def combined_lifespan(app: FastAPI):
                # Note that you have to pass base_app. Change this if we move
                # away from sub-application mount later
                async with lifespan(base_app):
                    async with mcp_app.lifespan(app):
                        yield

            mcp_routes = [
                route for route in mcp_app.routes
                if getattr(route, "name", None) not in {
                    "openapi",
                    "swagger_ui_html",
                    "swagger_ui_redirect",
                    "redoc_html",
                }
                and getattr(route, "path", None) not in {
                    settings.OPENAPI_URL,
                    settings.DOCS_URL,
                    settings.REDOC_URL,
                    "/openapi.json",
                    "/docs",
                    "/redoc",
                }
            ]
            app = FastAPI(
                debug=settings.DEBUG,
                docs_url=None,
                redoc_url=None,
                openapi_url=None,
                routes=mcp_routes,
                lifespan=combined_lifespan,
                middleware=mcp_app.user_middleware
            )

            @app.get(settings.OPENAPI_URL, include_in_schema=False)
            async def outer_openapi():
                return base_app.openapi()

            @app.get(settings.DOCS_URL, include_in_schema=False)
            async def outer_custom_swagger_ui_html():
                return await custom_swagger_ui_html()

            @app.get(settings.REDOC_URL, include_in_schema=False)
            async def outer_redoc_html():
                return await redoc_html()

            # Note that original application is mounted as a sub-application
            app.mount("/", base_app)
    else:
        app = base_app

    return app
