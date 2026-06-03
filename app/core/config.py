from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_URL: str
    SMTP_PASSWORD: str
    EMAIL: str
    EMAIL_FROM: str
    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    model_config = {
        "env_file": ".env"
    }


    # class Config:
    #     case_sensitive = True

settings = Settings()