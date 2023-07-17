import time
from typing import Callable, Iterator

import docker
import lcacollect_config.security
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from lcacollect_config.connection import create_postgres_engine
from lcacollect_config.formatting import string_uuid
from sqlmodel import SQLModel

from core.config import settings


@pytest.fixture(scope="session")
def docker_client():
    yield docker.from_env()


@pytest.fixture(scope="session")
def postgres(docker_client):
    container = docker_client.containers.run(
        "postgres:13.1-alpine",
        ports={"5432": settings.POSTGRES_PORT},
        environment={
            "POSTGRES_DB": settings.POSTGRES_DB,
            "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
            "POSTGRES_USER": settings.POSTGRES_USER,
        },
        detach=True,
        auto_remove=True,
    )

    time.sleep(3)
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture()
async def db(postgres) -> None:
    from main import app

    engine = create_postgres_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="session")
def mock_azure_scheme(session_mocker):
    class ConfigClass:
        def __init__(self):
            pass

        async def load_config(self):
            pass

    class AzureScheme:
        openid_config = ConfigClass()
        # fake user object fields
        claims = {"oid": "someid0"}
        access_token = f"Bearer eydlhjaflkjadh"
        roles = []

    session_mocker.patch.object(
        lcacollect_config.security,
        "azure_scheme",
        AzureScheme,
    )


@pytest.fixture()
async def app(db, mock_azure_scheme) -> FastAPI:
    from main import app

    async with LifespanManager(app):
        yield app


@pytest.fixture()
async def client(app: FastAPI, httpx_mock) -> Iterator[AsyncClient]:
    """Async server (authenticated) client that handles lifespan and teardown"""

    async with AsyncClient(
        app=app,
        base_url=settings.SERVER_HOST,
        headers={"authorization": f"Bearer eydlhjaflkjadh"},
    ) as _client:
        try:
            yield _client
        except Exception as exc:
            print(exc)


@pytest.fixture
def project_id() -> str:
    yield string_uuid()


@pytest.fixture
def non_mocked_hosts() -> list:
    return ["test.com"]


@pytest.fixture
async def member_mocker(httpx_mock):
    mock_data = {
        "data": {
            "projectMembers": [
                {
                    "id": "580aadba-0758-48dd-a78f-4103aaf15908",
                    "email": "member1@email.com",
                    "userId": "someid0",
                },
                {
                    "id": "1d8c3625-269f-4e98-87f0-a780b1b7a7f2",
                    "email": "member2@cowi.com",
                    "userId": "someid1",
                },
                {
                    "id": "98a3180b-4857-49a1-809d-3e8ad9472415",
                    "email": "member3@cowi.com",
                    "userId": "someid2",
                },
            ]
        }
    }

    httpx_mock.add_response(url=f"{settings.ROUTER_URL}/graphql", json=mock_data)


@pytest.fixture
@pytest.mark.asyncio
async def get_response() -> Callable:
    """Helper function."""

    async def _get_response(client: AsyncClient, query: str, variables: dict = None) -> dict:
        """Send a GraphQL query, check for errors and return the response if no errors."""

        response = await client.post(
            f"{settings.API_STR}/graphql",
            json={"query": query, "variables": variables},
        )
        assert response.status_code == 200

        data = response.json()
        if data.get("errors") is not None:
            raise AssertionError(
                f"The query returned a non-empty error field. The error field contains:\n {data['errors']}"
            )

        return data["data"]

    return _get_response
