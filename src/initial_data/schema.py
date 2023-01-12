import asyncio
from pathlib import Path

from lcaconfig.connection import create_postgres_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.commit import Commit
from models.reporting_schema import ReportingSchema
from models.repository import Repository
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement
from models.schema_template import SchemaTemplate


def load_bim7aa(path: Path):
    data = path.read_text().split("\n")

    return [row.split("\t") for row in data]


async def create_reporting(rows: list):
    async with AsyncSession(create_postgres_engine()) as session:
        schema = await create_schema(session)
        if schema is not None:
            await create_categories(rows, schema, session)


async def create_categories(rows: list, schema, session):
    categories = []
    print("Creating categories!")

    for row in rows:
        name = f"{row[0]} | {row[1]}"
        if len(row[0]) == 1:
            category = SchemaCategory(path="/", name=name, reporting_schema_id=schema.id, description="")
        elif len(row[0]) == 2:
            parent = [cat for cat in categories if cat.name.startswith(f"{row[0][0]} ")][0]
            category = SchemaCategory(
                path=f"/{parent.id}",
                name=name,
                reporting_schema_id=schema.id,
                description="",
            )
        else:
            parent = [cat for cat in categories if cat.name.startswith(f"{row[0][:2]} ")][0]
            category = SchemaCategory(
                path=f"{parent.path}/{parent.id}",
                name=name,
                reporting_schema_id=schema.id,
                description="",
            )
        session.add(category)
        categories.append(category)

    await session.commit()
    [await session.refresh(category) for category in categories]
    await session.refresh(schema)
    return categories


async def create_schema(session):
    query = select(SchemaTemplate).where(SchemaTemplate.name == "BIM7AA")
    _templates = (await session.exec(query)).all()
    if _templates:
        return None

    schema = ReportingSchema(name="BIM7AA")
    template = SchemaTemplate(name="BIM7AA", original_id=schema.id)
    schema.template_id = template.id
    session.add(schema)
    await session.commit()

    session.add(template)

    await session.commit()
    await session.refresh(schema)
    await session.refresh(template)

    print(f"Added reporting schema: {schema}")
    print(f"Added template: {template}")
    return schema


async def load_reporting(path: Path):
    rows = load_bim7aa(path)
    await create_reporting(rows)
    await assign_reporting()
    await create_elements()


async def create_elements():
    print("Loading Elements!")
    async with AsyncSession(create_postgres_engine()) as session:
        if (await session.exec(select(SchemaElement))).all():
            return

        query = select(SchemaCategory).where(
            func.length(SchemaCategory.path) == 74,
            SchemaCategory.reporting_schema_id == "5cf97040-ddf0-4759-af30-aa0e8857ee2f",
        )

        categories = (await session.exec(query)).all()
        repo = (
            await session.exec(
                select(Repository)
                .where(Repository.id == "4c6854c7-c1a3-41e7-bf5c-d7a6b7aff04b")
                .options(
                    selectinload(Repository.commits)
                    .options(selectinload(Commit.tasks))
                    .options(selectinload(Commit.schema_elements))
                    .options(selectinload(Commit.schema_categories))
                )
            )
        ).one()

        i = 0
        commit = Commit.copy_from_parent(
            await session.get(Commit, repo.head.id),
            author_id="60067d80-3bd0-42b7-8b17-2b9c0c8aaff3",
        )
        for category in categories:
            for _ in range(3):
                element = SchemaElement(
                    schema_category_id=category.id,
                    name=f"Wall {i}",
                    quantity=i * 3 + 2,
                    unit="m2",
                    description=f"This is my wall {i}",
                )
                session.add(element)
                commit.schema_elements.append(element)
                i += 1
        session.add(commit)
        await session.commit()


async def assign_reporting():
    print("Assigned Reporting Schema")
    project_id = "91604a3c-f30a-40af-8951-a738db49171d"
    schema_id = "5cf97040-ddf0-4759-af30-aa0e8857ee2f"
    async with AsyncSession(create_postgres_engine()) as session:
        schema = await session.get(ReportingSchema, schema_id)
        if schema:
            return

        query = (
            select(ReportingSchema)
            .join(SchemaTemplate)
            .where(
                SchemaTemplate.name == "BIM7AA",
                ReportingSchema.project_id == None,
            )
            .options(selectinload(ReportingSchema.categories))
        )
        template_schema = (await session.exec(query)).one()

        reporting_schema = ReportingSchema(id=schema_id, name=template_schema.name, project_id=project_id)
        reporting_schema.template_id = template_schema.template_id
        repository = Repository(
            id="4c6854c7-c1a3-41e7-bf5c-d7a6b7aff04b",
            reporting_schema=reporting_schema,
            reporting_schema_id=reporting_schema.id,
        )
        commit = Commit(author_id="60067d80-3bd0-42b7-8b17-2b9c0c8aaff3")
        repository.commits.append(commit)

        path_map = {}
        categories = []
        for old_category in template_schema.categories:
            new_category = SchemaCategory(
                **old_category.dict(exclude={"id", "project_id", "reporting_schema_id"}),
                project_id=project_id,
            )
            path_map[old_category.id] = new_category.id
            categories.append(new_category)

        for category in categories:
            if category.path and category.path != "/":
                path_parts = category.path.split("/")[1:]
                category.path = "/" + "/".join([path_map[part] for part in path_parts])
            session.add(category)

        reporting_schema.categories = categories
        commit.schema_categories = categories

        session.add(commit)
        session.add(reporting_schema)
        session.add(repository)

        await session.commit()
        await session.refresh(reporting_schema)
        await session.refresh(repository)

    return reporting_schema


if __name__ == "__main__":
    p = Path(__file__).parent / "bim7aa.txt"
    r = load_bim7aa(p)
    asyncio.run(create_reporting(r))
