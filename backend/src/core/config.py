from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "streaming_platform"

    SECRET_KEY: str = "your-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    APP_NAME: str = "Streaming_Platform"
    debug: bool = True
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def URL_DATABASE(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Config()