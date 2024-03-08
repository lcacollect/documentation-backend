import asyncio
import json
from pathlib import Path

from lcacollect_config.connection import create_postgres_engine
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.comment import Comment
from models.commit import Commit
from models.repository import Repository
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement
from models.task import Task
from models.typecode import TypeCodeElement


async def load_comments(path: Path):
    print("Loading Comments!")
    data = json.loads(path.read_text())
    comments = []
    async with AsyncSession(create_postgres_engine()) as session:
        for comment_data in data:
            comment = await session.get(Comment, comment_data.get("id"))
            if not comment:
                comment = Comment(**comment_data)
                session.add(comment)
                await session.commit()
                await session.refresh(comment)
            comments.append(comment)
    return comments


async def load_task(path: Path):
    print("Loading Tasks!")
    data = json.loads(path.read_text())
    tasks = []
    async with AsyncSession(create_postgres_engine()) as session:
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
        commit = Commit.copy_from_parent(
            await session.get(Commit, repo.head.id),
            author_id="60067d80-3bd0-42b7-8b17-2b9c0c8aaff3",
        )
        for task_data in data:
            task = await session.get(Task, task_data.get("id"))
            if not task:
                if name := task_data.pop("category_name", None):
                    category = (
                        await session.exec(
                            select(SchemaCategory).join(TypeCodeElement).where(TypeCodeElement.name == name)
                        )
                    ).first()
                    if not category:
                        continue
                    task_data.update(category_id=category.id)
                elif name := task_data.pop("element_name", None):
                    element = (await session.exec(select(SchemaElement).where(SchemaElement.name == name))).first()
                    if not element:
                        continue
                    task_data.update(element_id=element.id)
                task = Task(**task_data)
                session.add(task)
                commit.tasks.append(task)
                await session.commit()
                await session.refresh(task)
            tasks.append(task)
        session.add(commit)
        await session.commit()
    return tasks


async def load_tasks(path: Path):
    await load_task(path / "tasks.json")
    await load_comments(path / "comments.json")


if __name__ == "__main__":
    p = Path(__file__).parent

    asyncio.run(load_tasks(p))
