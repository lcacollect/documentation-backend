import asyncio
import json
from pathlib import Path

from lcaconfig.connection import create_postgres_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from models.source import ProjectSource


async def load_source(path: Path):
    print("Loading Project Sources!")
    data = json.loads(path.read_text())
    sources = []
    async with AsyncSession(create_postgres_engine()) as session:
        for source_data in data:
            source = await session.get(ProjectSource, source_data.get("id"))
            if not source:
                source = ProjectSource(**source_data)
                session.add(source)
                await session.commit()
                await session.refresh(source)
            sources.append(source)
    return sources


if __name__ == "__main__":
    p = Path(__file__).parent / "source.json"

    asyncio.run(load_source(p))
