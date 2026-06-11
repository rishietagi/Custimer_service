from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartCare API"
    API_V1_STR: str = "/api/v1"
    
    GROQ_API_KEY: str | None = None
    HUGGINGFACE_API_KEY: str | None = None
    SARVAM_API_KEY: str | None = None
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
