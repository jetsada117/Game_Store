# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ---------------------------
    # Application Config
    # ---------------------------
    APP_NAME: str = "Game Store API"
    DEBUG: bool = True

    # ---------------------------
    # MySQL Database
    # ---------------------------
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "game_store"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    # ---------------------------
    # Supabase Config
    # ---------------------------
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None

    # ---------------------------
    # Pydantic Config
    # ---------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

# สร้าง instance เดียวใช้ทั่วระบบ
settings = Settings()
