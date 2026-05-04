from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fitness:fitness@postgres:5432/fitness"
    secret_key: str = "changeme"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    cors_origins: list[str] = ["http://localhost:5173", "https://fitness.maegu.be"]

    class Config:
        env_file = ".env"


settings = Settings()
