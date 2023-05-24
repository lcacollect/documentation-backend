import datetime
from typing import Callable

import pytest
from httpx import AsyncClient
from lcacollect_config.email import EmailType
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

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
async def test_create_comment(client: AsyncClient, tasks, member_mock, get_response: Callable, mocker):
    users_mock = mocker.patch("schema.comment.get_users_from_azure")
    users_mock.return_value = [{"email": "test"}]
    email_mock = mocker.patch("schema.comment.send_email")
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

    assert len(users_mock.mock_calls) == 1
    assert users_mock.mock_calls[0][0] == ""

    assert len(email_mock.mock_calls) == 1
    assert email_mock.mock_calls[0][1] == ("test", EmailType.TASK_COMMENT)
    assert email_mock.mock_calls[0][2] == {"task": "Name 0", "comment": "lovely"}


@pytest.mark.asyncio
async def test_update_comment(client: AsyncClient, comments, member_mock, get_response: Callable, mocker):
    users_mock = mocker.patch("schema.comment.get_users_from_azure")
    users_mock.return_value = [{"email": "test"}]
    email_mock = mocker.patch("schema.comment.send_email")
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

    assert len(users_mock.mock_calls) == 1
    assert users_mock.mock_calls[0][0] == ""

    assert len(email_mock.mock_calls) == 1
    assert email_mock.mock_calls[0][1] == ("test", EmailType.TASK_COMMENT)
    assert email_mock.mock_calls[0][2] == {"task": "Name 0", "comment": "updated"}


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
