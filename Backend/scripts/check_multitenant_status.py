import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.database import AsyncSessionLocal


TABLES = [
    "usuarios",
    "clientes",
    "talleres",
    "tecnicos",
    "vehiculos",
    "incidentes",
    "incidente_historial",
    "pagos",
    "bitacora",
    "notificaciones",
    "mensajes_chat",
    "dispositivos_push",
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        tenants_exists = (
            await db.execute(text("select to_regclass('public.tenants') is not null"))
        ).scalar_one()
        print(f"tenants_exists={tenants_exists}")

        tenant_demo = (
            await db.execute(
                text("select id_tenant, nombre, slug, estado from tenants where slug = 'tenant-demo'")
            )
        ).mappings().all()
        print(f"tenant_demo={list(tenant_demo)}")

        for table in TABLES:
            row = (
                await db.execute(
                    text(
                        f"""
                        select
                            count(*) as total,
                            count(id_tenant) as with_tenant,
                            count(*) filter (where id_tenant is null) as missing
                        from {table}
                        """
                    )
                )
            ).mappings().one()
            print(
                f"{table}: total={row['total']} "
                f"with_tenant={row['with_tenant']} missing={row['missing']}"
            )


if __name__ == "__main__":
    asyncio.run(main())
