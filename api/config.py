from pydantic import BaseSettings, SecretStr, Field


class Settings(BaseSettings):
    github_client_id: str = Field(..., env="GITHUB_CLIENT_ID")
    github_client_secret: SecretStr = Field(..., env="GITHUB_CLIENT_SECRET")
    secret_key: SecretStr = Field(..., env="SECRET_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
