"""
Bootstrap de base de datos para Railway.

Railway ejecuta este script antes de arrancar Uvicorn. Para bases ya existentes
usa Alembic normalmente. Para una base Aiven nueva, donde las migraciones
historicas esperan tablas legacy, crea el esquema actual desde los modelos y
marca Alembic en head.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base, engine  # noqa: E402
import app.models  # noqa: F401,E402


CORE_TABLES = {"usuarios", "clientes", "incidentes"}


def _alembic_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


async def _prepare_database() -> bool:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        tables = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))

    has_core_schema = CORE_TABLES.issubset(tables)
    has_alembic_history = "alembic_version" in tables
    if not has_core_schema:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    return has_core_schema and has_alembic_history


def main() -> None:
    can_upgrade_with_alembic = asyncio.run(_prepare_database())
    if can_upgrade_with_alembic:
        command.upgrade(_alembic_config(), "head")
    else:
        command.stamp(_alembic_config(), "head")
    asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
