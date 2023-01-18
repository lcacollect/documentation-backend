import httpx
import strawberry
from lcacollect_config.context import get_token
from strawberry.types import Info

from core.config import settings
from exceptions import MicroServiceConnectionError, MicroServiceResponseError


@strawberry.federation.type(keys=["id"])
class GraphQLProjectMember:
    id: strawberry.ID
    email: str = strawberry.federation.field(shareable=True)
    user_id: str = strawberry.federation.field(shareable=True)

    @classmethod
    async def resolve_reference(cls, info: Info, project_id: str):
        return await get_members(project_id, get_token(info))


async def get_members(project_id: str, token: str) -> list[GraphQLProjectMember]:
    query = """
        query getMembers($projectId: String!){
            projectMembers(projectId: $projectId) {
                id
                email
                userId
            }
        }
    """

    data = {}
    members = []
    async with httpx.AsyncClient(
        headers={"authorization": f"Bearer {token}"},
    ) as client:
        response = await client.post(
            f"{settings.ROUTER_URL}/graphql",
            json={
                "query": query,
                "variables": {"projectId": project_id},
            },
        )
        if response.is_error:
            raise MicroServiceConnectionError(f"Could not receive data from {settings.ROUTER_URL}. Got {response.text}")
        data = response.json()
        if errors := data.get("errors"):
            raise MicroServiceResponseError(f"Got error from {settings.ROUTER_URL}: {errors}")

    project_members = data["data"]["projectMembers"]
    for member in project_members:
        members.append(
            GraphQLProjectMember(
                id=member.get("id"),
                email=member.get("email"),
                user_id=member.get("userId"),
            )
        )

    return members
