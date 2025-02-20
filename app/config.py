from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: Optional[str] = "Provider Roster"
    PAYER: Optional[str] = "aetna"
   
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()