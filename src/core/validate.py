from lcaconfig.context import get_token, get_user
from lcaconfig.exceptions import AuthenticationError, DatabaseItemNotFound
from lcaconfig.validate import group_exists, is_super_admin, project_exists
from strawberry.types import Info

from core.federation import get_members


def is_project_member(info: Info, members) -> bool:
    user = get_user(info)
    if is_super_admin(user):
        return True
    for member in members:
        if member.user_id == user.claims.get("oid"):
            return True

    return False


async def authenticate(info: Info, project_id: str):
    members = await get_members(project_id, get_token(info))
    if not is_project_member(info, members):
        raise AuthenticationError("User is not authenticated")
    return members


async def authenticate_project(info: Info, project_id: str):
    project = await project_exists(project_id=project_id, token=get_token(info))
    if not project:
        raise DatabaseItemNotFound(f"Project with id: {project_id} does not exist")
    return project


async def authenticate_group(info: Info, group_id: str, project_id: str):
    group = await group_exists(project_id=project_id, group_id=group_id, token=get_token(info))
    if not group:
        raise DatabaseItemNotFound(f"Project group with id: {group_id} does not exist")
    return group
