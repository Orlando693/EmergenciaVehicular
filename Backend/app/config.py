from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/emergencia_vehicular"
    SECRET_KEY: str = "cambia_este_secreto_en_produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_NAME: str = "EmergenciaVehicular API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # SSL para proveedores cloud como Aiven (ponlo en True en producción con Aiven)
    DB_SSL_REQUIRED: bool = False

    # Orígenes permitidos para CORS (separados por coma). Debe incluir el dominio
    # de Firebase Hosting (p. ej. parcial1si2.web.app) o el login fallará en
    # producción. Variable vacía en Railway se trata en main con el mismo listado.
    CORS_ORIGINS: str = (
        "https://parcial1si2.web.app,https://parcial1si2.firebaseapp.com,"
        "http://localhost:4200,http://127.0.0.1:4200,http://localhost:3000,http://127.0.0.1:3000"
    )

    # Google Gemini IA — obtén tu clave en https://aistudio.google.com/app/apikey
    GEMINI_API_KEY: str = ""

    # Carpeta donde se guardan las subidas de imágenes/audio.
    # Local:   "public/uploads"  (default, persiste mientras esté el repo)
    # Railway: "/data/uploads"   (montar un Volume en /data para que persista)
    UPLOAD_DIR: str = "public/uploads"

    # Prefijo URL público bajo el que se sirven los archivos subidos.
    # No cambiarlo salvo que sepas lo que haces (el frontend espera /public/uploads/...)
    UPLOAD_URL_PREFIX: str = "/public/uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
