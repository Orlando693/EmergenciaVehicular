"""
Fuerza un nuevo hash bcrypt para un usuario (p. ej. admin en Aiven si el
password no coincide con un hash antiguo o importado a mano).

Uso (misma URL que en Railway, en una sola línea):
  set DATABASE_URL=postgresql+asyncpg://...
  python reset_admin_password.py
"""
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings
from app.core.security import hash_password
from app.models.usuario import Usuario

EMAIL = os.environ.get("RESET_EMAIL", "admin@emergencia.com")
NEW_PASSWORD = os.environ.get("RESET_PASSWORD", "Admin1234")


async def main() -> None:
    if not settings.DATABASE_URL:
        print("Falta DATABASE_URL")
        return

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    h = hash_password(NEW_PASSWORD)

    async with Session() as db:
        e = (EMAIL or "").strip().lower()
        result = await db.execute(
            select(Usuario).where(func.lower(Usuario.email) == e)
        )
        u = result.scalar_one_or_none()
        if not u:
            print(f'No hay usuario con ese email. Crea el admin con: python crear_admin.py')
            await engine.dispose()
            return
        await db.execute(
            update(Usuario)
            .where(Usuario.id_usuario == u.id_usuario)
            .values(password_hash=h)
        )
        await db.commit()
        print(f"Contraseña actualizada para: {EMAIL}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
