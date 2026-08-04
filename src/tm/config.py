# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import Field, HttpUrl, PositiveInt

class PolygonConfig(BaseSettings):
    DB_HOST: str = Field(..., description="DB host name of ip-address")
    DB_PORT: int = Field(..., description="DB port ")
    DB_NAME: str = Field(..., description="DB name")
    DB_USER: str = Field(..., description="DB user login")
    DB_PASSWORD:str = Field(..., description="DB user password")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


config = PolygonConfig()

