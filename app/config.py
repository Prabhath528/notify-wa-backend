"""
Central configuration for the Notify WA backend.
All values are read from environment variables / the .env file so that
sensitive data (DB password, JWT secret, PayHere keys, WhatsApp token)
never has to be hard-coded.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "admin123"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "notify_wa_db"

    # JWT
    SECRET_KEY: str = "insecure-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # WhatsApp Cloud API
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com/v20.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_DEMO_MODE: bool = True

    # PayHere
    PAYHERE_MERCHANT_ID: str = ""
    PAYHERE_MERCHANT_SECRET: str = ""
    PAYHERE_MODE: str = "sandbox"
    PAYHERE_RETURN_URL: str = "http://localhost:8000/api/subscription/payhere/return"
    PAYHERE_CANCEL_URL: str = "http://localhost:8000/api/subscription/payhere/cancel"
    PAYHERE_NOTIFY_URL: str = "http://localhost:8000/api/subscription/payhere/notify"

    # Bank transfer fallback details
    BANK_NAME: str = "Commercial Bank of Ceylon PLC"
    BANK_ACCOUNT_NAME: str = "Pixel Forge Studio"
    BANK_ACCOUNT_NUMBER: str = "0000000000"
    BANK_BRANCH: str = "Negombo"

    # Plan limits / pricing (LKR)
    FREE_PLAN_MESSAGE_LIMIT: int = 50
    PRO_PLAN_MESSAGE_LIMIT: int = 500
    PRO_PLAN_PRICE_LKR: float = 659
    UNLIMITED_PLAN_PRICE_LKR: float = 1499

    DEVELOPER_INFO_URL: str = "http://pixelforgestudioprabhath.netlify.app/"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def MAINTENANCE_DATABASE_URL(self) -> str:
        """Connects to the default 'postgres' database so we can check/create our real DB."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/postgres"
        )


settings = Settings()
