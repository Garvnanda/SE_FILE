from decimal import Decimal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://tradesphere:tradesphere@127.0.0.1:54329/tradesphere"
    )
    initial_cash: Decimal = Decimal("100000")
    max_order_quantity: int = 10000
    quote_max_age_seconds: int = 86400
    cookie_secure: bool = False
    environment: str = "development"
    public_origin: str = ""
    allow_registration: bool = True

    @model_validator(mode="after")
    def deployment_settings(self):
        if self.database_url.startswith(("postgres://", "postgresql://")):
            self.database_url = (
                "postgresql+psycopg://" + self.database_url.split("://", 1)[1]
            )
        if self.environment == "production":
            if not self.cookie_secure:
                raise ValueError("Production requires COOKIE_SECURE=true")
            if not self.public_origin.startswith(
                "https://"
            ) or self.public_origin.endswith("/"):
                raise ValueError(
                    "PUBLIC_ORIGIN must be the HTTPS site origin without a trailing slash"
                )
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)
