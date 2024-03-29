import httpx
from aiocache import cached
from lcacollect_config.exceptions import MicroServiceResponseError

from core.config import settings


@cached(ttl=60)
async def query_project_for_export(project_id: str, token: str) -> dict | None:
    query = """
        query($id: String!) {
            projects(filters: {id: {equal: $id}}) {
                id
                name
                country
                stages {
                    phase
                }
            }
        }
    """

    async with httpx.AsyncClient(
        headers={"authorization": f"Bearer {token}"},
    ) as client:
        response = await client.post(
            f"{settings.ROUTER_URL}/graphql",
            json={
                "query": query,
                "variables": {"id": project_id},
            },
        )

        data = response.json()
        if response.is_error or data.get("errors"):
            return None
        return data.get("data", {}).get("projects", [])[0]


@cached(ttl=60)
async def query_assemblies_for_export(project_id: str, token: str) -> dict | None:
    query = """
        query($projectId: String!) {
            projectAssemblies(projectId: $projectId) {
                id
                name
                lifeTime
                unit
                conversionFactor
                description
                layers {
                    id
                    name
                    description
                    conversionFactor
                    referenceServiceLife
                    transportEpd {
                        id
                        name
                    }
                    transportDistance
                    transportConversionFactor
                    epd {
                        id
                        name
                        declaredUnit
                        version
                        validUntil
                        publishedDate
                        source
                        location
                        subtype
                        referenceServiceLife
                        comment
                        conversions {
                            to
                            value
                        }
                        gwp {
                            a1a3
                            c3
                            c4
                            d
                        }
                    }
                }
            }
        }
    """

    async with httpx.AsyncClient(
        headers={"authorization": f"Bearer {token}"},
    ) as client:
        try:
            response = await client.post(
                f"{settings.ROUTER_URL}/graphql",
                json={
                    "query": query,
                    "variables": {"projectId": project_id},
                },
            )
        except Exception as e:
            print(e)
        data = response.json()
        if response.is_error or data.get("errors"):
            raise MicroServiceResponseError(data.get("errors"))
        return data.get("data").get("projectAssemblies")
