from decimal import Decimal
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
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)
