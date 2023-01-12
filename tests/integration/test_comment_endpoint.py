import datetime
from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from core.federation import GraphQLProjectMember
from models.comment import Comment


@pytest.mark.asyncio
async def test_get_comments(client: AsyncClient, comments, tasks, member_mock, get_response: Callable):
    query = """
        query ($taskId: String!){
            comments(taskId: $taskId, filters: {text: {contains: "0"}}) {
                added
                text
            }
        }
    """
    variables = {"taskId": tasks[0].id}

    data = await get_response(client, query, variables=variables)
    assert data["comments"][0] == {
        "text": "Comment Text 0",
        "added": comments[0].added.strftime("%Y-%m-%d"),
    }


@pytest.mark.asyncio
async def test_create_comment(client: AsyncClient, tasks, member_mock, get_response: Callable):
    mutation = """
        mutation($taskId: String!, $text: String!) {
            addComment(taskId: $taskId, text: $text) {
                id
                added
                text
            }
        }
    """
    variables = {"taskId": tasks[0].id, "text": "lovely"}

    data = await get_response(client, mutation, variables=variables)
    assert data["addComment"] == {
        "id": data["addComment"]["id"],  # FIXME: this is just testing that a value is equal to itself
        "added": datetime.date.today().strftime("%Y-%m-%d"),
        "text": "lovely",
    }


@pytest.mark.asyncio
async def test_update_comment(client: AsyncClient, comments, member_mock, get_response: Callable):
    query = """
        mutation($id: String!, $text: String!) {
            updateComment(id: $id, text: $text) {
                text
            }
        }
    """
    variables = {"id": comments[0].id, "text": "updated"}

    data = await get_response(client, query, variables=variables)
    assert data["updateComment"] == {"text": "updated"}


@pytest.mark.asyncio
async def test_delete_comment(client: AsyncClient, comments, db, member_mock, get_response: Callable):
    query = f"""
        mutation {{
            deleteComment(id: "{comments[0].id}")
        }}
    """

    data = await get_response(client, query)
    async with AsyncSession(db) as session:
        query = select(Comment)
        _comments = await session.exec(query)
        _comments = _comments.all()

    assert len(_comments) == len(comments) - 1
