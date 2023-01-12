from typing import Callable

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_tag(
    client: AsyncClient,
    tags,
    commits,
    member_mocker,
    get_response: Callable,
    reporting_schemas,
):
    """Test that a the ``tags`` query returns the expected fields."""
    query = """
        query getTags($reportingSchema: String!){
            tags(reportingSchemaId: $reportingSchema) {
                id
                name
                added
                authorId
                commit {
                    id
                }
            }
        }
    """

    data = await get_response(client, query, {"reportingSchema": reporting_schemas[0].id})

    assert data["tags"] == [
        {
            "id": tags[0].id,
            "name": "Release 0.0",
            "added": tags[0].added.strftime("%Y-%m-%d"),
            "authorId": tags[0].author_id,
            "commit": {"id": commits[0].id},
        },
        {
            "id": tags[1].id,
            "name": "Release 1.0",
            "added": tags[1].added.strftime("%Y-%m-%d"),
            "authorId": tags[1].author_id,
            "commit": {"id": commits[1].id},
        },
        {
            "id": tags[2].id,
            "name": "Release 2.0",
            "added": tags[2].added.strftime("%Y-%m-%d"),
            "authorId": tags[2].author_id,
            "commit": {"id": commits[2].id},
        },
    ]


@pytest.mark.asyncio
async def test_create_tag(
    client: AsyncClient,
    tags,
    commits,
    mock_azure_scheme,
    member_mocker,
    get_response: Callable,
):
    """Test that a tag can be created and that it appears on the parent commit."""

    mutation = """
        mutation ($name: String!, $commitId: String!) {
            createTag(name: $name, commitId: $commitId)  {
                name
                authorId
                commit {
                    id
                }
            }
        }
    """
    variables = {"name": "New tag", "commitId": commits[2].id}
    data = await get_response(client, mutation, variables=variables)

    assert data["createTag"] == {
        "name": "New tag",
        "authorId": "someid0",
        "commit": {"id": commits[2].id},
    }


@pytest.mark.skip("Querying commits messes up the mocker. Nothing was changed and should be working in live version")
@pytest.mark.asyncio
async def test_commit_has_tag(client: AsyncClient, tags, reporting_schemas, member_mocker, get_response: Callable):
    """Assert that the first commit is contains the first tag in the `tags` field."""

    query = """
        query ($reportingSchemaId: String!) {
            commits (reportingSchemaId: $reportingSchemaId){
                tags {
                    id
                }
            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[1].id}"}

    data = await get_response(client, query, variables=variables)
    assert data["commits"][0]["tags"][0] == {"id": tags[1].id}
    assert tags[1].id == data["commits"][0]["tags"][0]["id"]


@pytest.mark.asyncio
async def test_filter_tags_by_author(
    client: AsyncClient,
    tags,
    commits,
    member_mocker,
    reporting_schemas,
    get_response: Callable,
):
    """Test filtering of tags by author."""

    query = """
        query getTags($reportingSchemaId: String!) {
            tags(reportingSchemaId: $reportingSchemaId filters: {authorId: {equal: "test_author_0"}}){
                id
                added
                authorId
            }
        }
    """

    data = await get_response(client, query, {"reportingSchemaId": reporting_schemas[0].id})

    assert data["tags"][0] == {
        "id": tags[0].id,
        "added": tags[0].added.strftime("%Y-%m-%d"),
        "authorId": "test_author_0",
    }


@pytest.mark.asyncio
async def test_update_tag_name(client: AsyncClient, tags, member_mocker, get_response: Callable):
    """Given a tag ID, update the name of that tag."""

    mutation = """
        mutation ($id: String!, $name: String!) {
            updateTag(id: $id, name: $name) {
                id
                name
            }
        }
    """
    variables = {"id": tags[0].id, "name": "Release -3.14"}
    data = await get_response(client, mutation, variables=variables)

    assert data["updateTag"]["id"] == tags[0].id
    assert data["updateTag"]["name"] == "Release -3.14"


@pytest.mark.skip
@pytest.mark.asyncio
async def test_move_tag_to_different_commit(
    client: AsyncClient,
    tags,
    commits,
    reporting_schemas,
    member_mocker,
    get_response: Callable,
):
    """Test that updating a tag's commit moves the tag to the new commit."""

    # Mutate a tag and asssert if its commit changes
    mutation = """
        mutation ($id: String!, $commitId: String!) {
            updateTag(id: $id, commitId: $commitId) {
                id
                commitId
            }
        }
    """
    variables_0 = {"id": tags[0].id, "commitId": commits[1].id}

    data = await get_response(client, mutation, variables=variables_0)
    assert data["updateTag"]["id"] == tags[0].id
    assert data["updateTag"]["commitId"] == commits[1].id

    # Query destination commit to assert if the tag was added
    query = """
        query ($reportingSchemaId: String!) {
            commits (reportingSchemaId: $reportingSchemaId){
                tags {
                    id
                }
            }
        }
    """
    variables_1 = {"reportingSchemaId": reporting_schemas[1].id}

    data = await get_response(client, query, variables=variables_1)
    assert data["commits"][0]["tags"][0]["id"] == tags[1].id
    assert data["commits"][0]["tags"][1]["id"] == tags[0].id

    # Query origin commit to assert if the tag was removed
    variables_2 = {"reportingSchemaId": reporting_schemas[0].id}

    data = await get_response(client, query, variables=variables_2)
    assert data["commits"][0]["tags"] == []


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient, tags, member_mocker, reporting_schemas, get_response: Callable):
    """Test that a tag is properly deleted and that the deletion updates its commit."""

    # Delete 0th tag
    mutation = """
        mutation ($id: String!) {
            deleteTag(id: $id)
        }
    """
    variables = {"id": tags[0].id}

    await get_response(client, mutation, variables=variables)

    query = """
        query getTags($reportingSchemaId: String!) {
            tags(reportingSchemaId: $reportingSchemaId) {
                id
            }
        }
    """
    data = await get_response(client, query, variables={"reportingSchemaId": reporting_schemas[0].id})
    ids = [tag["id"] for tag in data["tags"]]
    assert tags[0].id not in ids
    assert tags[1].id in ids
    assert tags[2].id in ids


@pytest.mark.asyncio
async def test_delete_commit_deletes_tags(client: AsyncClient, tags):
    """Test that deleting a commit deletes its child tags."""
    # Commit deletion not implemented
    pass
