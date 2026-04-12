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

    # Orígenes permitidos para CORS (separados por coma si son varios)
    CORS_ORIGINS: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
