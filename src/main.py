import logging.config
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from lcacollect_config.security import azure_scheme

from core.config import settings
from routes import graphql_app

if settings.SERVER_NAME != "LCA Test":
    logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.SERVER_NAME,
    openapi_url=f"{settings.API_STR}/openapi.json",
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.AAD_OPENAPI_CLIENT_ID,
    },
)

app.add_middleware(GZipMiddleware, minimum_size=1024)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(graphql_app, prefix=settings.API_STR)


@app.on_event("startup")
async def app_init():
    """Initialize application services"""

    logger.info("Setting up Azure AD")
    # Setup Azure AD
    await azure_scheme.openid_config.load_config()

    if os.environ.get("RUN_STAGE") == "DEV":
        logger.info(f"Running as DEV. Generating seed data!")
        from initial_data.load import load_all

        await load_all(Path(__file__).parent / "initial_data")
