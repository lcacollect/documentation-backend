import asyncio
import datetime
import json

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.comment import Comment
from models.commit import Commit
from models.reporting_schema import ReportingSchema
from models.repository import Repository
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement
from models.schema_template import SchemaTemplate
from models.source import ProjectSource
from models.tag import Tag
from models.task import Task
from models.typecode import TypeCode, TypeCodeElement


@pytest.fixture
async def schema_templates(db) -> list[SchemaTemplate]:
    templates = []
    async with AsyncSession(db) as session:
        for i in range(3):
            schema = ReportingSchema(name=f"Reporting Schema {i}")
            type_code_element = TypeCodeElement(code="11", name="Part", level=1)
            category = SchemaCategory(
                name=f"Category {i}", project_id="Test Project", type_code_element=type_code_element
            )
            schema.categories.append(category)
            session.add(category)
            session.add(schema)
            await session.commit()
            await session.refresh(schema)

            template = SchemaTemplate(name=f"Template {i}", original_id=schema.id, domain=f"test {i}")
            schema.template_id = template.id
            session.add(template)
            session.add(schema)
            templates.append(template)
            await session.commit()
        [await session.refresh(tmplt) for tmplt in templates]

    yield templates


@pytest.fixture
async def reporting_schemas(db, project_id) -> list[ReportingSchema]:
    schemas = []
    async with AsyncSession(db) as session:
        for i in range(4):
            schema = ReportingSchema(name=f"Reporting Schema {i}", project_id=project_id)
            session.add(schema)
            schemas.append(schema)
        await session.commit()
        [await session.refresh(schema) for schema in schemas]

    yield schemas


@pytest.fixture
async def repositories(db, reporting_schemas) -> list[Repository]:
    repositories = []
    async with AsyncSession(db) as session:
        for i in range(4):
            repository = Repository(reporting_schema=reporting_schemas[i])
            session.add(repository)
            repositories.append(repository)
        await session.commit()
        [await session.refresh(repository) for repository in repositories]
        [await session.refresh(reporting_schema) for reporting_schema in reporting_schemas]
    yield repositories


@pytest.fixture
async def schema_categories(db, reporting_schemas, type_code_elements) -> list[SchemaCategory]:
    categories = []
    async with AsyncSession(db) as session:
        for i in range(4):
            category = SchemaCategory(
                type_code_element=type_code_elements[i],
                description=f"description {i}",
                reporting_schema=reporting_schemas[i],
            )
            session.add(category)
            categories.append(category)
        await session.commit()
        [await session.refresh(category) for category in categories]
        [await session.refresh(reporting_schema) for reporting_schema in reporting_schemas]
    yield categories


@pytest.fixture
async def project_sources(db, project_id) -> list[ProjectSource]:
    sources = []
    csv_data_id = "test/39/92/3ce5233dbf3400bb9905fdec8fd2355ab15b1ef242b2ef1d2756192d64a0"
    csv_interpretation = {"interpretationName": "name", "description": "description", "m2": "area"}

    async with AsyncSession(db) as session:
        for i in range(4):
            source = ProjectSource(
                type="SPECKLE" if i < 3 else "csv",
                data_id="21b253d478" if i < 3 else csv_data_id,
                name=f"Source {i}",
                project_id=project_id,
                meta_fields=dict(speckle_url="speckle.arkitema.com"),
                interpretation={
                    "name": "family",
                    "classification": "family",
                    "subclassification": "",
                    "unit": "_units.name",
                    "description": "type",
                    "quantity": "parameters.HOSTED_AREA_COMPUTED.value",
                }
                if i < 3
                else csv_interpretation,
                author_id="some_user",
            )
            session.add(source)
            sources.append(source)

        await session.commit()
        [await session.refresh(source) for source in sources]

    yield sources


@pytest.fixture
async def xlsx_source(db, project_id) -> list[ProjectSource]:
    sources = []
    xlsx_data_id = "test/39/92/3ce5233dbf3400bb9905fdec8fd2355ab15b1ef242b2ef1d2756192d64a1"
    xlsx_interpretation = {"interpretationName": "name", "description": "description", "m2": "area"}

    async with AsyncSession(db) as session:
        xlsx_source = ProjectSource(
            type="xlsx",
            data_id=xlsx_data_id,
            name=f"Source 0",
            project_id=project_id,
            meta_fields=dict(speckle_url="speckle.arkitema.com"),
            interpretation=xlsx_interpretation,
            author_id="some_user",
        )
        session.add(xlsx_source)
        sources.append(xlsx_source)

        await session.commit()
        [await session.refresh(source) for source in sources]

    yield sources


@pytest.fixture
async def tasks(db, reporting_schemas, schema_categories) -> list[Task]:
    tasks = []
    async with AsyncSession(db) as session:
        for i in range(4):
            task = Task(
                name=f"Name {i}",
                due_date=datetime.date.today().strftime("%Y-%m-%d"),
                description=f"Description {i}",
                category=schema_categories[i],
                reporting_schema=reporting_schemas[i],
                status=f"Pending",
            )
            session.add(task)
            tasks.append(task)
        await session.commit()
        [await session.refresh(task) for task in tasks]
        [await session.refresh(reporting_schema) for reporting_schema in reporting_schemas]

    yield tasks


@pytest.fixture
async def schema_elements(db, schema_categories, project_sources) -> list[SchemaElement]:
    elements = []
    async with AsyncSession(db) as session:
        for i in range(4):
            element = SchemaElement(
                name=f"Schema Element {i}",
                classification=f"Class {i}",
                unit=f"m2",
                quantity=i,
                description=f"Description {i}",
                schema_category=schema_categories[i],
                source=project_sources[i],
            )
            session.add(element)
            elements.append(element)
        await session.commit()
        [await session.refresh(element) for element in elements]
        [await session.refresh(category) for category in schema_categories]

    yield elements


@pytest.fixture
async def commits(db, repositories, schema_categories, schema_elements, tasks) -> list[Commit]:
    commits = []
    async with AsyncSession(db) as session:
        for i in range(4):
            commit = Commit(
                project_id=f"{i}",
                repository=repositories[i],
                schema_elements=[schema_elements[i]],
                schema_categories=[schema_categories[i]],
                tasks=[tasks[i]],
                short_id=f"Path {i}",
            )
            session.add(commit)
            commits.append(commit)
        await session.commit()
        [await session.refresh(commit) for commit in commits]
        [await session.refresh(repository) for repository in repositories]
        [await session.refresh(schema_category) for schema_category in schema_categories]
        [await session.refresh(schema_element) for schema_element in schema_elements]
        [await session.refresh(task) for task in tasks]

    yield commits


@pytest.fixture
async def tags(db, commits) -> list[Tag]:
    tags = []
    async with AsyncSession(db) as session:
        for i in range(3):
            tag = Tag(
                project_id=f"{i}",
                name=f"Release {i}.0",
                author_id=f"test_author_{i}",
                commit_id=commits[i].id,
            )
            session.add(tag)
            tags.append(tag)
        await session.commit()
        [await session.refresh(tag) for tag in tags]

    yield tags


@pytest.fixture
async def comments(db, tasks) -> list[Comment]:
    comments = []
    async with AsyncSession(db) as session:
        for i in range(4):
            comment = Comment(
                text=f"Comment Text {i}",
                task=tasks[i],
            )
            session.add(comment)
            comments.append(comment)
        await session.commit()
        [await session.refresh(comment) for comment in comments]
        [await session.refresh(task) for task in tasks]

    yield comments


@pytest.fixture
async def type_code(db) -> TypeCode:
    async with AsyncSession(db) as session:
        type_code = TypeCode(name="Type Code 0")
        session.add(type_code)
        await session.commit()
        await session.refresh(type_code)

    yield type_code


@pytest.fixture
async def type_code_elements(db, type_code) -> list[TypeCodeElement]:
    type_code_elements = []
    async with AsyncSession(db) as session:
        type_code_element1 = TypeCodeElement(
            name="Name 1",
            code="1",
            level=1,
            parent_path="/",
            typecode_id=type_code.id,
        )
        session.add(type_code_element1)
        type_code_elements.append(type_code_element1)

        type_code_element2 = TypeCodeElement(
            name="Name 2",
            code="11",
            level=2,
            parent_path=f"/{type_code_element1.id}",
            typecode_id=type_code.id,
        )
        session.add(type_code_element2)
        type_code_elements.append(type_code_element2)

        type_code_element3 = TypeCodeElement(
            name="Name 3",
            code="3",
            level=1,
            parent_path=f"/",
            typecode_id=type_code.id,
        )
        session.add(type_code_element3)
        type_code_elements.append(type_code_element3)

        type_code_element4 = TypeCodeElement(
            name="Name 4",
            code="34",
            level=3,
            parent_path=f"/{type_code_element3.id}",
            typecode_id=type_code.id,
        )
        session.add(type_code_element4)
        type_code_elements.append(type_code_element4)

        await session.commit()
        [await session.refresh(type_code_elem) for type_code_elem in type_code_elements]

    yield type_code_elements


@pytest.fixture
def csv_file(datafix_dir):
    yield open(datafix_dir / "project_source.csv", "rb")


@pytest.fixture
def project_exists_mock(mocker):
    mocker.patch("lcacollect_config.validate.project_exists", return_value=True)


@pytest.fixture
def is_admin_mock(mocker):
    mocker.patch("core.permissions.IsAdmin.has_permission", return_value=True)


@pytest.fixture
def project_doesnt_exists_mock(httpx_mock):
    httpx_mock.add_response(url=f"{settings.ROUTER_URL}/graphql", json={"errors": "User not authenticated"})


@pytest.fixture
def group_exists_mock(mocker):
    mocker.patch("lcacollect_config.validate.group_exists", return_value=True)


@pytest.fixture
def group_doesnt_exist_mock(mocker):
    mocker.patch("lcacollect_config.validate.group_exists", return_value=False)


@pytest.fixture
def query_project_for_export_mock(httpx_mock, datafix_dir, reporting_schemas):
    project_mock = json.loads((datafix_dir / "project_export.json").read_text())
    project_id = reporting_schemas[0].project_id
    query = (
        b'{"query": "\\n        query($id: String!) {\\n            projects(filters: {id: {equal: $id}}) {\\n                id\\n                name\\n                country\\n                stages {\\n                    phase\\n                }\\n                metaFields\\n            }\\n        }\\n    ", "variables": {"id": "'
        + project_id.encode()
        + b'"}}'
    )
    httpx_mock.add_response(url=f"{settings.ROUTER_URL}/graphql", json=project_mock, match_content=query)
    yield
    httpx_mock.reset(assert_all_responses_were_requested=True)


@pytest.fixture
def query_assemblies_for_export_mock(httpx_mock, datafix_dir, reporting_schemas):
    assembly_mock = json.loads((datafix_dir / "assembly_export.json").read_text())
    project_id = reporting_schemas[0].project_id
    query = (
        b'{"query": "\\n        query($projectId: String!) {\\n            projectAssemblies(projectId: $projectId) {\\n                id\\n                name\\n                lifeTime\\n                unit\\n                conversionFactor\\n                description\\n                layers {\\n                    id\\n                    name\\n                    description\\n                    conversionFactor\\n                    referenceServiceLife\\n                    transportEpd {\\n                        id\\n                        name\\n                    }\\n                    transportDistance\\n                    transportConversionFactor\\n                    epd {\\n                        id\\n                        name\\n                        declaredUnit\\n                        version\\n                        validUntil\\n                        publishedDate\\n                        source\\n                        location\\n                        subtype\\n                        referenceServiceLife\\n                        comment\\n                        conversions {\\n                            to\\n                            value\\n                        }\\n                        gwp {\\n                            a1a3\\n                            c3\\n                            c4\\n                            d\\n                        }\\n                    }\\n                }\\n            }\\n        }\\n    ", "variables": {"projectId": "'
        + project_id.encode()
        + b'"}}'
    )
    httpx_mock.add_response(
        url=f"{settings.ROUTER_URL}/graphql",
        json=assembly_mock,
        match_content=query,
    )

    yield
    httpx_mock.reset(assert_all_responses_were_requested=False)


@pytest.fixture
def blob_client_mock_xlsx(mocker, datafix_dir):
    class FakeBlob:
        def upload_blob(self, data):
            return None

        def download_blob(self):
            return MockObject()

    data = (datafix_dir / "source_data.xlsx").read_bytes()

    class MockObject:
        def readall(self):
            return data

    mocker.patch("azure.storage.blob.BlobClient.__init__", return_value=None)
    mocker.patch("azure.storage.blob.BlobClient.__enter__", return_value=FakeBlob())
    mocker.patch("azure.storage.blob.BlobClient.__exit__", return_value=None)


@pytest.fixture
def blob_client_mock(mocker, datafix_dir):
    class FakeBlob:
        def upload_blob(self, data):
            return None

        def download_blob(self):
            return MockObject()

    data = (datafix_dir / "source_data.csv").read_bytes()

    class MockObject:
        def readall(self):
            return data

    mocker.patch("azure.storage.blob.BlobClient.__init__", return_value=None)
    mocker.patch("azure.storage.blob.BlobClient.__enter__", return_value=FakeBlob())
    mocker.patch("azure.storage.blob.BlobClient.__exit__", return_value=None)


@pytest.fixture
def blob_client_mock_async(mocker, datafix_dir):
    class FakeBlob:
        async def upload_blob(self, data):
            return asyncio.Future()

        async def download_blob(self):
            return MockObject()

    data = (datafix_dir / "source_data.csv").read_bytes()

    class MockObject:
        def readall(self):
            return data

    mocker.patch("azure.storage.blob.aio.BlobClient.__init__", return_value=None)
    mocker.patch("azure.storage.blob.aio.BlobClient.__aenter__", return_value=FakeBlob())
    mocker.patch("azure.storage.blob.aio.BlobClient.__aexit__", return_value=None)


@pytest.fixture
async def member_mock(httpx_mock):
    httpx_mock.add_response(
        url=f"{settings.ROUTER_URL}/graphql",
        json={
            "data": {
                "projectMembers": [
                    {
                        "id": "5005-43234-23sdfd",
                        "email": "testtest@cowi.com",
                        "userId": "someid0",
                    },
                    {
                        "id": "1010-43234-23sdfd",
                        "email": "test2test@cowi.com",
                        "userId": "someid1",
                    },
                ]
            }
        },
    )


@pytest.fixture
async def project_exists_mock(httpx_mock, datafix_dir, project_id):
    project_mock = json.loads((datafix_dir / "project_exists.json").read_text())
    content = (
        b'{"query": "\\n        query($id: String!) {\\n            projects(filters: {id: {equal: $id}}) {\\n                id\\n                public\\n            }\\n        }\\n    ", "variables": {"id": "'
        + project_id.encode()
        + b'"}}'
    )
    httpx_mock.add_response(
        url=f"{settings.ROUTER_URL}/graphql",
        json=project_mock,
        match_content=content,
    )
