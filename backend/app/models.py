from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str]
    role: Mapped[str] = mapped_column(String(24), default="TRADER")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("role IN ('TRADER','ADMIN','MARKET_OPERATOR')"),)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    csrf: Mapped[str]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)


class Wallet(Base):
    __tablename__ = "wallets"
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), unique=True)
    cash_total: Mapped[Decimal] = mapped_column(Numeric(24, 4))
    cash_reserved: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=0)
    __table_args__ = (
        CheckConstraint("cash_total >= cash_reserved AND cash_reserved >= 0"),
    )


class Stock(Base):
    __tablename__ = "stocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(100), default="Technology")
    active: Mapped[bool] = mapped_column(default=True)


class PriceTick(Base):
    __tablename__ = "price_ticks"
    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    source: Mapped[str] = mapped_column(default="SIMULATED")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    event_key: Mapped[str | None] = mapped_column(unique=True)
    __table_args__ = (CheckConstraint("price > 0"),)


class MarketSession(Base):
    __tablename__ = "market_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    is_open: Mapped[bool]
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    side: Mapped[str]
    order_type: Mapped[str]
    qty: Mapped[int]
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(default="PENDING", index=True)
    reserved_cash: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=0)
    reserved_qty: Mapped[int] = mapped_column(default=0)
    idempotency_key: Mapped[str]
    rejection_reason: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        CheckConstraint("qty > 0"),
        CheckConstraint("status IN ('PENDING','FILLED','CANCELLED','REJECTED')"),
        CheckConstraint("side IN ('BUY','SELL')"),
        CheckConstraint("order_type IN ('MARKET','LIMIT')"),
    )


class Holding(Base):
    __tablename__ = "holdings"
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    qty: Mapped[int] = mapped_column(default=0)
    reserved_qty: Mapped[int] = mapped_column(default=0)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    __table_args__ = (
        UniqueConstraint("portfolio_id", "stock_id"),
        CheckConstraint("qty >= reserved_qty AND reserved_qty >= 0"),
    )


class Trade(Base):
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    side: Mapped[str]
    qty: Mapped[int]
    execution_price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Ledger(Base):
    __tablename__ = "wallet_ledger"
    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    amount_signed: Mapped[Decimal] = mapped_column(Numeric(24, 4))
    event_type: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Watchlist(Base):
    __tablename__ = "watchlists"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(80))


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id"))
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"))
    __table_args__ = (UniqueConstraint("watchlist_id", "stock_id"),)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    body: Mapped[str]
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Audit(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str]
    entity_type: Mapped[str]
    entity_id: Mapped[int | None]
    before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
