import asyncio
import json
import logging
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _firebase_ready() -> bool:
    try:
        from firebase_admin import credentials, get_app, initialize_app
    except Exception as exc:
        logger.info("Firebase Admin SDK no instalado: %s", exc)
        return False

    try:
        get_app()
        return True
    except ValueError:
        pass

    try:
        if settings.FIREBASE_CREDENTIALS_JSON:
            info = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(info)
        elif settings.FIREBASE_CREDENTIALS_PATH:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        else:
            logger.info("Firebase push desactivado: no hay credenciales configuradas")
            return False

        initialize_app(cred)
        return True
    except Exception as exc:
        logger.warning("No se pudo inicializar Firebase Admin: %s", exc)
        return False


async def enviar_push_token(
    token: str,
    titulo: str,
    mensaje: str,
    data: dict[str, str] | None = None,
) -> bool:
    if not _firebase_ready():
        return False

    from firebase_admin import messaging

    payload = messaging.Message(
        token=token,
        notification=messaging.Notification(title=titulo, body=mensaje),
        data=data or {},
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="emergencia_high_importance",
                priority="max",
            ),
        ),
    )

    try:
        await asyncio.to_thread(messaging.send, payload)
        return True
    except Exception as exc:
        logger.warning("FCM push fallido: %s", exc)
        return False
