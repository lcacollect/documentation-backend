import pytest

from core.federation import GraphQLProjectMember, get_members


@pytest.mark.asyncio
async def test_get_members(member_mocker):
    members = await get_members("0", "mytoken")

    assert members
    assert isinstance(members[0], GraphQLProjectMember)
