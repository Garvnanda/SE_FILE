import hashlib, secrets, time
from collections import defaultdict, deque
from datetime import timedelta, datetime
from decimal import Decimal
from typing import Literal
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, model_validator
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from .db import Session, settings
from .models import *
from . import trading as engine

app = FastAPI(title="TradeSphere", version="1.0.0")
ph = PasswordHasher()
API = "/api/v1"


def row(obj):
    return {
        c.name: str(v)
        if isinstance(v, Decimal)
        else v.isoformat()
        if isinstance(v, datetime)
        else v
        for c in obj.__table__.columns
        if c.name != "password_hash"
        for v in [getattr(obj, c.name)]
    }


def db_session():
    with Session.begin() as db:
        yield db


DB = Depends(db_session, scope="function")


@app.exception_handler(HTTPException)
def http_error(request, exc):
    return JSONResponse({"error": {"message": exc.detail}}, status_code=exc.status_code)


@app.exception_handler(IntegrityError)
def integrity_error(request, exc):
    return JSONResponse(
        {"error": {"message": "Record conflicts with existing data or constraints"}},
        status_code=409,
    )


@app.middleware("http")
async def headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def current(request: Request, db=DB):
    token = request.cookies.get("session", "")
    session = db.get(AuthSession, hashlib.sha256(token.encode()).hexdigest())
    if not session or session.expires_at < now():
        raise HTTPException(401, "Please sign in")
    u = db.get(User, session.user_id)
    if not u.active:
        raise HTTPException(403, "Account disabled")
    if request.method not in ("GET", "HEAD", "OPTIONS") and not secrets.compare_digest(
        request.headers.get("X-CSRF-Token", ""), session.csrf
    ):
        raise HTTPException(403, "Invalid CSRF token; sign in again")
    request.state.auth_session = session
    return u


def role(name):
    def check(u=Depends(current)):
        if u.role != name:
            raise HTTPException(403, "This action is not permitted for your role")
        return u

    return Depends(check)


Trader = role("TRADER")
Admin = role("ADMIN")
Operator = role("MARKET_OPERATOR")


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class OrderInput(BaseModel):
    stock_id: int
    side: Literal["BUY", "SELL"]
    type: Literal["MARKET", "LIMIT"]
    quantity: int = Field(gt=0, le=2147483647, strict=True)
    limit_price: Decimal | None = Field(
        default=None, gt=0, max_digits=18, decimal_places=4
    )
    idempotency_key: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def price_rule(self):
        if (self.type == "LIMIT") != (self.limit_price is not None):
            raise ValueError("Limit price is required only for LIMIT orders")
        return self


class StockInput(BaseModel):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9]{0,15}$")
    name: str = Field(min_length=1, max_length=100)
    sector: str = Field(default="Technology", max_length=100)
    active: bool = True


class TickInput(BaseModel):
    stock_id: int
    price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    event_key: str = Field(min_length=8, max_length=100)


class SessionInput(BaseModel):
    is_open: bool


class ActiveInput(BaseModel):
    active: bool


class NameInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)


attempts = defaultdict(deque)


def throttle(request):
    key = request.client.host
    queue = attempts[key]
    cutoff = time.monotonic() - 60
    while queue and queue[0] < cutoff:
        queue.popleft()
    if len(queue) >= 30:
        raise HTTPException(429, "Too many attempts. Try again in one minute.")
    queue.append(time.monotonic())


def create_user(db, email, password, role="TRADER"):
    u = User(email=email.lower(), password_hash=ph.hash(password), role=role)
    db.add(u)
    db.flush()
    if role == "TRADER":
        p = Portfolio(user_id=u.id)
        db.add(p)
        db.flush()
        w = Wallet(portfolio_id=p.id, cash_total=settings.initial_cash, cash_reserved=0)
        db.add(w)
        db.flush()
        db.add(
            Ledger(
                wallet_id=w.id,
                amount_signed=settings.initial_cash,
                event_type="INITIAL_CREDIT",
            )
        )
        db.add(Watchlist(user_id=u.id, name="Favorites"))
    engine.record(db, u.id, "ACCOUNT_CREATED", "user", u.id, after={"role": role})
    return u


@app.get("/health")
def health(db=DB):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql", "quotes": "SIMULATED"}


@app.post(API + "/auth/register", status_code=201)
def register(data: Credentials, request: Request, db=DB):
    throttle(request)
    return row(create_user(db, str(data.email), data.password))


@app.post(API + "/auth/login")
def login(data: Credentials, request: Request, response: Response, db=DB):
    throttle(request)
    u = db.scalar(select(User).where(User.email == str(data.email).lower()))
    try:
        if not u or not u.active:
            raise ValueError()
        ph.verify(u.password_hash, data.password)
    except (ValueError, VerificationError):
        raise HTTPException(401, "Email or password is incorrect")
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            user_id=u.id,
            csrf=csrf,
            expires_at=now() + timedelta(hours=8),
        )
    )
    response.set_cookie(
        "session",
        token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        max_age=28800,
    )
    return {"user": row(u), "csrf": csrf}


@app.get(API + "/auth/me")
def me(request: Request, u=Depends(current)):
    return {"user": row(u), "csrf": request.state.auth_session.csrf}


@app.post(API + "/auth/logout")
def logout(request: Request, response: Response, u=Depends(current), db=DB):
    db.delete(request.state.auth_session)
    response.delete_cookie("session")
    return {"ok": True}


@app.get(API + "/stocks")
def stocks(u=Depends(current), db=DB):
    return [
        dict(row(s), quote=row(t) if (t := engine.quote(db, s.id)) else None)
        for s in db.scalars(select(Stock).where(Stock.active).order_by(Stock.symbol))
    ]


@app.get(API + "/stocks/{symbol}/history")
def history(
    symbol: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    u=Depends(current),
    db=DB,
):
    s = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if not s:
        raise HTTPException(404, "Instrument not found")
    return [
        row(t)
        for t in db.scalars(
            select(PriceTick)
            .where(PriceTick.stock_id == s.id)
            .order_by(PriceTick.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ]


@app.get(API + "/market-status")
@app.get(API + "/operator/market-status")
def status(u=Depends(current), db=DB):
    return {
        "is_open": engine.market_open(db),
        "source": "SIMULATED",
        "quote_max_age_seconds": settings.quote_max_age_seconds,
    }


@app.post(API + "/orders")
def place(data: OrderInput, u=Trader, db=DB):
    return row(engine.place(db, u, data))


@app.post(API + "/orders/{ident}/cancel")
def cancel(ident: int, u=Trader, db=DB):
    return row(engine.cancel(db, u, ident))


def records(model, db, u, symbol, side, status, since, until, offset, limit):
    q = select(model).where(model.user_id == u.id)
    if symbol:
        q = q.join(Stock, Stock.id == model.stock_id).where(Stock.symbol == symbol)
    if side:
        q = q.where(model.side == side)
    if status and model == Order:
        q = q.where(Order.status == status)
    date = model.created_at if model == Order else model.executed_at
    if since:
        q = q.where(date >= since)
    if until:
        q = q.where(date <= until)
    return [
        dict(row(o), symbol=db.get(Stock, o.stock_id).symbol)
        for o in db.scalars(q.order_by(model.id.desc()).offset(offset).limit(limit))
    ]


@app.get(API + "/orders")
def orders(
    symbol: str | None = None,
    side: str | None = None,
    status: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    u=Trader,
    db=DB,
):
    return records(Order, db, u, symbol, side, status, since, until, offset, limit)


@app.get(API + "/trades")
def trades(
    symbol: str | None = None,
    side: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    u=Trader,
    db=DB,
):
    return records(Trade, db, u, symbol, side, None, since, until, offset, limit)


@app.get(API + "/orders/{ident}")
def order(ident: int, u=Trader, db=DB):
    o = db.get(Order, ident)
    if not o or o.user_id != u.id:
        raise HTTPException(404, "Order not found")
    return row(o)


@app.get(API + "/wallet")
def wallet(u=Trader, db=DB):
    w = engine.wallet_for(db, u.id)
    return dict(row(w), available=str(w.cash_total - w.cash_reserved), currency="INR")


@app.get(API + "/wallet/ledger")
def ledger(
    offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), u=Trader, db=DB
):
    w = engine.wallet_for(db, u.id)
    return [
        row(x)
        for x in db.scalars(
            select(Ledger)
            .where(Ledger.wallet_id == w.id)
            .order_by(Ledger.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ]


@app.get(API + "/portfolio")
@app.get(API + "/portfolio/performance")
def portfolio(u=Trader, db=DB):
    w = engine.wallet_for(db, u.id)
    positions = []
    value = Decimal(0)
    realized = Decimal(0)
    unrealized = Decimal(0)
    for h in db.scalars(
        select(Holding)
        .where(Holding.portfolio_id == w.portfolio_id)
        .order_by(Holding.id)
    ):
        t = engine.quote(db, h.stock_id)
        price = t.price if t else Decimal(0)
        mv = h.qty * price
        up = h.qty * (price - h.avg_cost)
        value += mv
        realized += h.realized_pnl
        unrealized += up
        positions.append(
            dict(
                row(h),
                symbol=db.get(Stock, h.stock_id).symbol,
                price=str(price),
                market_value=str(mv),
                unrealized_pnl=str(up),
                available_qty=h.qty - h.reserved_qty,
                quote_time=t.recorded_at.isoformat() if t else None,
                stale=not engine.usable(t),
            )
        )
    return {
        "positions": positions,
        "cash": str(w.cash_total),
        "reserved": str(w.cash_reserved),
        "market_value": str(value),
        "equity": str(w.cash_total + value),
        "realized_pnl": str(realized),
        "unrealized_pnl": str(unrealized),
        "net_pnl": str(w.cash_total + value - settings.initial_cash),
    }


@app.get(API + "/watchlists")
def watchlists(u=Trader, db=DB):
    return [
        dict(
            row(w),
            items=[
                dict(row(i), symbol=db.get(Stock, i.stock_id).symbol)
                for i in db.scalars(
                    select(WatchlistItem).where(WatchlistItem.watchlist_id == w.id)
                )
            ],
        )
        for w in db.scalars(select(Watchlist).where(Watchlist.user_id == u.id))
    ]


@app.post(API + "/watchlists")
def new_watchlist(data: NameInput, u=Trader, db=DB):
    w = Watchlist(user_id=u.id, name=data.name)
    db.add(w)
    db.flush()
    return row(w)


@app.post(
    API + "/watchlists/{ident}/items/{stock_id}", operation_id="add_watchlist_item"
)
@app.delete(
    API + "/watchlists/{ident}/items/{stock_id}", operation_id="remove_watchlist_item"
)
def watch_item(ident: int, stock_id: int, request: Request, u=Trader, db=DB):
    engine.lock_market(db)
    w = db.get(Watchlist, ident)
    if not w or w.user_id != u.id:
        raise HTTPException(404, "Watchlist not found")
    if not db.get(Stock, stock_id):
        raise HTTPException(404, "Instrument not found")
    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == ident, WatchlistItem.stock_id == stock_id
        )
    )
    if request.method == "POST" and not item:
        db.add(WatchlistItem(watchlist_id=ident, stock_id=stock_id))
    if request.method == "DELETE" and item:
        db.delete(item)
    return {"ok": True}


@app.get(API + "/notifications")
def notifications(
    offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), u=Trader, db=DB
):
    return [
        row(n)
        for n in db.scalars(
            select(Notification)
            .where(Notification.user_id == u.id)
            .order_by(Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ]


@app.patch(API + "/notifications/{ident}")
def read_notification(ident: int, u=Trader, db=DB):
    n = db.get(Notification, ident)
    if not n or n.user_id != u.id:
        raise HTTPException(404, "Notification not found")
    n.read_at = now()
    return row(n)


@app.get(API + "/admin/stocks")
def admin_stocks(u=Admin, db=DB):
    return [row(s) for s in db.scalars(select(Stock).order_by(Stock.id))]


@app.post(API + "/admin/stocks")
def add_stock(data: StockInput, u=Admin, db=DB):
    engine.lock_market(db)
    s = Stock(**data.model_dump())
    db.add(s)
    db.flush()
    engine.record(db, u.id, "STOCK_CREATED", "stock", s.id, after=row(s))
    return row(s)


@app.patch(API + "/admin/stocks/{ident}")
def edit_stock(ident: int, data: StockInput, u=Admin, db=DB):
    engine.lock_market(db)
    s = db.get(Stock, ident)
    if not s:
        raise HTTPException(404, "Instrument not found")
    before = row(s)
    for k, v in data.model_dump().items():
        setattr(s, k, v)
    engine.record(db, u.id, "STOCK_UPDATED", "stock", s.id, before, row(s))
    return row(s)


@app.post(API + "/operator/ticks")
def tick(data: TickInput, u=Operator, db=DB):
    engine.lock_market(db)
    existing = db.scalar(select(PriceTick).where(PriceTick.event_key == data.event_key))
    if existing:
        if existing.stock_id != data.stock_id or existing.price != data.price:
            raise HTTPException(409, "Event key already used")
        return row(existing)
    s = db.get(Stock, data.stock_id)
    if not s or not s.active:
        raise HTTPException(404, "Active instrument not found")
    t = PriceTick(**data.model_dump())
    db.add(t)
    db.flush()
    engine.record(
        db, u.id, "QUOTE_PUBLISHED", "stock", s.id, after={"price": str(t.price)}
    )
    engine.process_pending(db, s.id)
    return row(t)


@app.post(API + "/operator/market-session")
def change_session(data: SessionInput, u=Operator, db=DB):
    engine.lock_market(db)
    s = MarketSession(is_open=data.is_open, updated_by=u.id)
    db.add(s)
    db.flush()
    engine.record(
        db,
        u.id,
        "SESSION_CHANGED",
        "market_session",
        s.id,
        after={"is_open": s.is_open},
    )
    engine.process_pending(db)
    return row(s)


@app.get(API + "/admin/users")
def users(
    offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), u=Admin, db=DB
):
    return [
        row(x)
        for x in db.scalars(select(User).order_by(User.id).offset(offset).limit(limit))
    ]


@app.patch(API + "/admin/users/{ident}")
def edit_user(ident: int, data: ActiveInput, u=Admin, db=DB):
    engine.lock_market(db)
    target = db.get(User, ident)
    if not target:
        raise HTTPException(404, "Account not found")
    if target.role == "ADMIN":
        raise HTTPException(
            409, "Administrator accounts cannot be disabled through this interface"
        )
    if not data.active:
        for o in db.scalars(
            select(Order).where(Order.user_id == ident, Order.status == "PENDING")
        ).all():
            engine.cancel(db, target, o.id)
    before = {"active": target.active}
    target.active = data.active
    engine.record(
        db, u.id, "ACCOUNT_UPDATED", "user", ident, before, {"active": target.active}
    )
    return row(target)


@app.get(API + "/admin/audit")
def audit(
    action: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    u=Admin,
    db=DB,
):
    q = select(Audit)
    if action:
        q = q.where(Audit.action.ilike("%" + action + "%"))
    return [
        row(x)
        for x in db.scalars(q.order_by(Audit.id.desc()).offset(offset).limit(limit))
    ]


@app.get(API + "/admin/summary")
def summary(u=Admin, db=DB):
    return {
        m.__tablename__: db.scalar(select(func.count()).select_from(m))
        for m in [User, Stock, Order, Trade]
    }


static = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if static.exists():
    app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")
