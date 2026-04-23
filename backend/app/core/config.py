from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "qr-saas"
    APP_ENV: str = "development"
    APP_SECRET: str = "change-me"

    DATABASE_URL: str = "postgresql+psycopg2://qr:qr@localhost:5432/qrsaas"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    CORS_ORIGINS: str = "http://localhost:5173"


settings = Settings()
