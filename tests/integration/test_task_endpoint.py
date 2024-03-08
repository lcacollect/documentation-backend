import datetime
from typing import Callable

import pytest
from httpx import AsyncClient
from lcacollect_config.email import EmailType
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.commit import Commit
from models.task import Task


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient, reporting_schemas, tasks, get_response: Callable):
    query = """
        query ($reportingSchemaId: String!){
            tasks(reportingSchemaId: $reportingSchemaId, filters: {name: {contains: "0"}}) {
                name
                description
                dueDate
                comments{
                    text
                }
                reportingSchema{
                    id
                }
            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[0].id}"}

    data = await get_response(client, query, variables=variables)
    assert data["tasks"][0] == {
        "name": "Name 0",
        "dueDate": datetime.date.today().strftime("%Y-%m-%d"),
        "description": "Description 0",
        "comments": [],
        "reportingSchema": {"id": f"{reporting_schemas[0].id}"},
    }


@pytest.mark.asyncio
async def test_get_task_filter(client: AsyncClient, reporting_schemas, tasks, get_response: Callable):
    query = """
        query ($reportingSchemaId: String!, $id: String!){
            tasks(reportingSchemaId: $reportingSchemaId, filters: {id: {equal: $id}}) {
                name
                description
                dueDate
                comments{
                    text
                }
                reportingSchema{
                    id
                }
            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[0].id}", "id": f"{tasks[0].id}"}

    data = await get_response(client, query, variables=variables)
    assert data["tasks"][0] == {
        "name": "Name 0",
        "dueDate": datetime.date.today().strftime("%Y-%m-%d"),
        "description": "Description 0",
        "comments": [],
        "reportingSchema": {"id": f"{reporting_schemas[0].id}"},
    }


@pytest.mark.asyncio
async def test_create_task(
    client: AsyncClient,
    reporting_schemas,
    commits,
    schema_elements,
    tasks,
    db,
    member_mocker,
    group_exists_mock,
    get_response: Callable,
    mocker,
):
    users_mock = mocker.patch("schema.task.get_users_from_azure")
    users_mock.return_value = [{"email": "test"}]
    email_mock = mocker.patch("schema.task.send_email")
    task_item = f"""{{id: "{schema_elements[0].id}", type: Element}}"""
    assignee = f"""{{id: "0dfa3-43234-23sdfd", type: PROJECT_MEMBER}}"""
    mutation = f"""
        mutation {{
            addTask(reportingSchemaId: "{reporting_schemas[0].id}", name: "test", dueDate: 
            "{datetime.date.today().strftime("%Y-%m-%d")}",  item: {task_item}, description: "do it", 
            status: APPROVED, assignee: {assignee}) {{
                id
                name
                description
                dueDate
                status
                item {{
                        ... on GraphQLSchemaElement {{
                            id
                            quantity
                            }}
                        ... on GraphQLSchemaCategory {{
                            id
                    }}
                }}
            }}
        }}
    """
    data = await get_response(client, mutation)
    assert data["addTask"] == {
        "name": data["addTask"]["name"],
        "description": "do it",
        "dueDate": datetime.date.today().strftime("%Y-%m-%d"),
        "id": data["addTask"]["id"],
        "status": "APPROVED",
        "item": {"id": f"{schema_elements[0].id}", "quantity": 0.0},
    }
    async with AsyncSession(db) as session:
        query = select(Task)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()
    assert len(commits_after) > len(tasks)

    assert len(users_mock.mock_calls) == 1
    assert users_mock.mock_calls[0][1] == ("0dfa3-43234-23sdfd",)

    assert len(email_mock.mock_calls) == 1
    assert email_mock.mock_calls[0][1] == ("test", EmailType.TASK_ASSIGN)
    assert email_mock.mock_calls[0][2] == {"task": "test"}


@pytest.mark.asyncio
async def test_create_task_category(
    client: AsyncClient,
    reporting_schemas,
    commits,
    schema_categories,
    tasks,
    db,
    member_mocker,
    group_exists_mock,
    get_response: Callable,
    mocker,
):
    users_mock = mocker.patch("schema.task.get_users_from_azure")
    email_mock = mocker.patch("schema.task.send_email")

    assignee = f"""{{id: "0dfa3-43234-23sdfd", type: USER}}"""
    task_item = f"""{{id: "{schema_categories[0].id}", type: Category}}"""
    mutation = f"""
        mutation {{
            addTask(reportingSchemaId: "{reporting_schemas[0].id}", name: "test", dueDate: 
            "{datetime.date.today().strftime("%Y-%m-%d")}",  item: {task_item}, description: "do it", 
            status: PENDING, assignee: {assignee}) {{
                id
                name
                description
                dueDate
                status
                item {{
                        ... on GraphQLSchemaElement {{
                            id
                            quantity
                            }}
                        ... on GraphQLSchemaCategory {{
                            id
                            typeCodeElement {{
                                name
                            }}
                    }}
                }}
            }}
        }}
    """
    data = await get_response(client, mutation)
    assert data["addTask"] == {
        "name": data["addTask"]["name"],
        "description": "do it",
        "dueDate": datetime.date.today().strftime("%Y-%m-%d"),
        "id": data["addTask"]["id"],
        "status": "PENDING",
        "item": {"id": f"{schema_categories[0].id}", "typeCodeElement": {"name": "Name 1"}},
    }
    async with AsyncSession(db) as session:
        query = select(Task)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()
    assert len(commits_after) > len(tasks)

    assert len(users_mock.mock_calls) == 0
    assert len(email_mock.mock_calls) == 0


@pytest.mark.asyncio
async def test_update_task(
    client: AsyncClient,
    tasks,
    db,
    schema_categories,
    reporting_schemas,
    commits,
    member_mocker,
    group_exists_mock,
    get_response: Callable,
    mocker,
):
    users_mock = mocker.patch("schema.task.get_users_from_azure")
    users_mock.return_value = [{"email": "test"}]
    email_mock = mocker.patch("schema.task.send_email")

    task_item = f"""{{id: "{schema_categories[1].id}", type: Category}}"""
    assignee = f"""{{id: "0dfa3-43234-23sdfd", type: PROJECT_MEMBER}}"""
    mutation = f"""
        mutation {{
            updateTask(id: "{tasks[0].id}", name: "update", dueDate: 
            "{datetime.date.today().strftime("%Y-%m-%d")}",  item: {task_item}, description: "updated", 
            status: PENDING, assignee: {assignee}) {{
                id
                name
                description
                dueDate
                status
                item {{
                        ... on GraphQLSchemaElement {{
                            id
                            quantity
                            }}
                        ... on GraphQLSchemaCategory {{
                            id
                            typeCodeElement {{
                                name
                            }}
                    }}
                }}
            }}
        }}
    """

    data = await get_response(client, mutation)
    assert data["updateTask"] == {
        "name": data["updateTask"]["name"],
        "description": "updated",
        "dueDate": datetime.date.today().strftime("%Y-%m-%d"),
        "id": tasks[0].id,
        "status": "PENDING",
        "item": {"id": f"{schema_categories[1].id}", "typeCodeElement": {"name": "Name 2"}},
    }

    assert len(users_mock.mock_calls) == 1
    assert users_mock.mock_calls[0][1] == ("0dfa3-43234-23sdfd",)

    assert len(email_mock.mock_calls) == 1
    assert email_mock.mock_calls[0][1] == ("test", EmailType.TASK_ASSIGN)
    assert email_mock.mock_calls[0][2] == {"task": "update"}


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, tasks, commits, db, member_mocker, get_response: Callable):
    mutation = f"""
        mutation {{
            deleteTask(id: "{tasks[0].id}")
        }}
    """
    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    assert await get_response(client, mutation)

    async with AsyncSession(db) as session:
        query = select(Task)
        _tasks = await session.exec(query)
        _tasks = _tasks.all()

    assert len(_tasks) == len(tasks) - 1
    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)
    print(commits_after)
