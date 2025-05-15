from typing import List
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://chenter404:c3Futureapps@zynx-auth.yxarrsu.mongodb.net/?retryWrites=true&w=majority&appName=zynx-auth")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "auth")
    PROJECT_NAME: str = "INTELLINEX SOFT"
    VERSION: str = "1.0.0"

    PORT: int = os.getenv("PORT", 8000) 
    HOST: str = os.getenv("HOST", "0.0.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 43200))
    ALLOWED_HOSTS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        extra = "allow" 

settings = Settings()