from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # --- APP SETTINGS ---
    APP_NAME: str = "OunceAI Dashboard"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # --- POSTGRES (LOCAL DOCKER) ---
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_SSLMODE: str = "disable"

    # --- MONGODB ---
    MONGO_URL: str
    MONGO_DB_NAME: str = "Oncinha"
    MONGO_COLLECTION_NAME: str = "ofertas_ia"

    # --- AI & EXTERNAL APIS ---
    GEMINI_KEY: str = ""
    WEATHER_KEY: str = ""

    # Configuração para ler o arquivo .env automaticamente
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instância global para ser importada no projeto todo
settings = Settings()