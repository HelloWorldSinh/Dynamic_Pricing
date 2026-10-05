from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "Dynamic Pricing System API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./dynamic_pricing.db"
    DEBOUNCE_SECONDS: int = 30

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
