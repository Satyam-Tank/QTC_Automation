from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    CLIENT_ID: str
    TENANT_ID: str
    CLIENT_SECRET: Optional[str] = None
    GRAPH_USER_IDENTIFIER: str
    MAILBOX_UPN: str
    WEBHOOK_NOTIFICATION_URL: str
    CLIENT_STATE_SECRET: str
    GOOGLE_API_KEY: str
    AUTH_JSON_PATH: Path = Path("/app/auth.json")
    TOKEN_CACHE_FILE: Path = Path("/app/user_tokens.json")
    
    # --- THIS IS THE MISSING LINE ---
    HARDCODED_ACCESS_TOKEN: Optional[str] = None

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()
