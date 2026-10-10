from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    api_key: SecretStr = SecretStr("")
    max_products: int = Field(default=30, ge=1, le=200)
    concurrency: int = Field(default=5, ge=1, le=20)
    request_timeout: float = Field(default=30, gt=0, le=120)
    search_timeout: float = Field(default=180, gt=0, le=600)


def load_settings() -> Settings:
    # Resolve relative to the source checkout, independent of the MCP client's cwd.
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return Settings(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        max_products=os.getenv("SHOPPING_MAX_PRODUCTS", "30"),
        concurrency=os.getenv("SHOPPING_CONCURRENCY", "5"),
        request_timeout=os.getenv("SHOPPING_REQUEST_TIMEOUT", "30"),
        search_timeout=os.getenv("SHOPPING_SEARCH_TIMEOUT", "180"),
    )
