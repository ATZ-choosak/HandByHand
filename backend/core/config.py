from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_URI: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5 * 60
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAILS_FROM_EMAIL: str
    EMAILS_FROM_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env", validate_assignment=True, extra="allow"
    )

def get_settings():
    return Settings()
