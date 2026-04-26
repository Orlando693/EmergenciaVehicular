import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenData


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        if not plain or not hashed:
            return False
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        logging.getLogger("emergencia.security").warning("verify_password: %s", exc)
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # Entero UTC (recomendación JWT); evita problemas con serialización
    to_encode["exp"] = int(expire.timestamp())
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        id_usuario: int = payload.get("sub")
        email: str = payload.get("email")
        roles: list[str] = payload.get("roles", [])
        if id_usuario is None:
            raise JWTError("Token invalido")
        return TokenData(id_usuario=int(id_usuario), email=email, roles=roles)
    except JWTError:
        raise
