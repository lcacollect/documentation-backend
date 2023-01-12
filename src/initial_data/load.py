import asyncio
import logging
from pathlib import Path

from initial_data.schema import load_reporting
from initial_data.source import load_source
from initial_data.task import load_tasks

logger = logging.getLogger(__name__)


async def load_all(folder: Path):
    await load_reporting(folder / "bim7aa.txt")
    await load_tasks(folder)
    await load_source(folder / "source.json")


if __name__ == "__main__":
    f = Path(__file__).parent

    asyncio.run(load_all(f))
