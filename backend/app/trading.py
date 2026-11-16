from decimal import Decimal, ROUND_HALF_EVEN
from sqlalchemy import select, text
from fastapi import HTTPException
from .models import *
from .db import settings


def record(db, actor, action, entity, ident=None, before=None, after=None):
    db.add(
        Audit(
            actor_id=actor,
            action=action,
            entity_type=entity,
            entity_id=ident,
            before_json=before or {},
            after_json=after or {},
        )
    )


def notify(db, user, title, body):
    db.add(Notification(user_id=user, title=title, body=body))


def lock_market(db):
    # One transaction-scoped advisory lock serializes demo mutations, including ticks,
    # orders and session transitions. Row locks protect affected financial records too.
    db.execute(text("SELECT pg_advisory_xact_lock(731002)"))


def quote(db, stock):
    return db.scalar(
        select(PriceTick)
        .where(PriceTick.stock_id == stock)
        .order_by(PriceTick.id.desc())
        .limit(1)
    )


def market_open(db):
    row = db.scalar(select(MarketSession).order_by(MarketSession.id.desc()).limit(1))
    return bool(row and row.is_open)


def usable(tick):
    return (
        tick
        and (now() - tick.recorded_at).total_seconds() <= settings.quote_max_age_seconds
    )


def wallet_for(db, user):
    portfolio = db.scalar(select(Portfolio).where(Portfolio.user_id == user))
    return db.scalar(
        select(Wallet).where(Wallet.portfolio_id == portfolio.id).with_for_update()
    )


def holding_for(db, wallet, stock):
    h = db.scalar(
        select(Holding)
        .where(Holding.portfolio_id == wallet.portfolio_id, Holding.stock_id == stock)
        .with_for_update()
    )
    if h is None:
        h = Holding(
            portfolio_id=wallet.portfolio_id,
            stock_id=stock,
            qty=0,
            reserved_qty=0,
            avg_cost=Decimal(0),
            realized_pnl=Decimal(0),
        )
        db.add(h)
        db.flush()
    return h


def average_cost(qty, cost, added, price):
    return ((qty * cost + added * price) / (qty + added)).quantize(
        Decimal(".00000001"), rounding=ROUND_HALF_EVEN
    )


def eligible(order, price):
    return order.order_type == "MARKET" or (
        price <= order.limit_price
        if order.side == "BUY"
        else price >= order.limit_price
    )


def settle(db, order, tick):
    if order.status != "PENDING":
        return
    w = wallet_for(db, order.user_id)
    h = holding_for(db, w, order.stock_id)
    amount = tick.price * order.qty
    if order.side == "BUY":
        w.cash_reserved -= order.reserved_cash
        w.cash_total -= amount
        h.avg_cost = average_cost(h.qty, h.avg_cost, order.qty, tick.price)
        h.qty += order.qty
    else:
        h.reserved_qty -= order.reserved_qty
        h.qty -= order.qty
        h.realized_pnl += order.qty * (tick.price - h.avg_cost)
        w.cash_total += amount
        if h.qty == 0:
            h.avg_cost = Decimal(0)
    order.reserved_cash = Decimal(0)
    order.reserved_qty = 0
    order.status = "FILLED"
    db.add(
        Trade(
            order_id=order.id,
            user_id=order.user_id,
            stock_id=order.stock_id,
            side=order.side,
            qty=order.qty,
            execution_price=tick.price,
        )
    )
    db.add(
        Ledger(
            wallet_id=w.id,
            order_id=order.id,
            amount_signed=-amount if order.side == "BUY" else amount,
            event_type=order.side,
        )
    )
    record(
        db,
        order.user_id,
        "ORDER_FILLED",
        "order",
        order.id,
        {"status": "PENDING"},
        {"status": "FILLED", "price": str(tick.price)},
    )
    notify(
        db,
        order.user_id,
        "Order filled",
        f"{order.side} {order.qty} shares at INR {tick.price}. Order #{order.id}.",
    )
    db.flush()


def process_pending(db, stock_id=None):
    if not market_open(db):
        return
    query = (
        select(Order)
        .where(Order.status == "PENDING")
        .order_by(Order.id)
        .with_for_update()
    )
    if stock_id is not None:
        query = query.where(Order.stock_id == stock_id)
    for o in db.scalars(query).all():
        s = db.get(Stock, o.stock_id)
        u = db.get(User, o.user_id)
        t = quote(db, o.stock_id)
        if s.active and u.active and usable(t) and eligible(o, t.price):
            settle(db, o, t)


def place(db, user, data):
    lock_market(db)
    existing = db.scalar(
        select(Order).where(
            Order.user_id == user.id, Order.idempotency_key == data.idempotency_key
        )
    )
    if existing:
        if (
            existing.stock_id,
            existing.side,
            existing.order_type,
            existing.qty,
            existing.limit_price,
        ) != (data.stock_id, data.side, data.type, data.quantity, data.limit_price):
            raise HTTPException(409, "Idempotency key already used for different order")
        return existing
    stock = db.get(Stock, data.stock_id)
    if not stock:
        raise HTTPException(404, "Instrument not found")
    o = Order(
        user_id=user.id,
        stock_id=stock.id,
        side=data.side,
        order_type=data.type,
        qty=data.quantity,
        limit_price=data.limit_price,
        idempotency_key=data.idempotency_key,
        reserved_cash=Decimal(0),
        reserved_qty=0,
        status="PENDING",
    )
    db.add(o)
    db.flush()
    w = wallet_for(db, user.id)
    h = holding_for(db, w, stock.id)
    t = quote(db, stock.id)
    reason = None
    if not stock.active:
        reason = "Instrument is disabled"
    elif data.quantity > settings.max_order_quantity:
        reason = f"Maximum order quantity is {settings.max_order_quantity}"
    elif not usable(t):
        reason = "Quote is missing or expired. Ask the market operator to publish a fresh quote."
    elif data.type == "MARKET" and not market_open(db):
        reason = "Market is closed. Use a limit order or wait for reopening."
    reserve = data.quantity * (
        data.limit_price if data.type == "LIMIT" else t.price if t else Decimal(0)
    )
    if not reason and data.side == "BUY" and reserve > w.cash_total - w.cash_reserved:
        reason = "Insufficient available virtual funds"
    if not reason and data.side == "SELL" and data.quantity > h.qty - h.reserved_qty:
        reason = "Insufficient unreserved shares"
    if reason:
        o.status = "REJECTED"
        o.rejection_reason = reason
        notify(db, user.id, "Order rejected", reason)
        record(db, user.id, "ORDER_REJECTED", "order", o.id, after={"reason": reason})
        return o
    if data.side == "BUY":
        w.cash_reserved += reserve
        o.reserved_cash = reserve
        if reserve > settings.initial_cash * Decimal(".5"):
            notify(
                db,
                user.id,
                "Concentration warning",
                "This order exceeds 50% of your initial virtual capital.",
            )
    else:
        h.reserved_qty += data.quantity
        o.reserved_qty = data.quantity
    record(
        db,
        user.id,
        "ORDER_RESERVED",
        "order",
        o.id,
        after={"cash": str(o.reserved_cash), "shares": o.reserved_qty},
    )
    db.flush()
    if market_open(db) and eligible(o, t.price):
        settle(db, o, t)
    return o


def cancel(db, user, ident):
    lock_market(db)
    o = db.scalar(
        select(Order)
        .where(Order.id == ident, Order.user_id == user.id)
        .with_for_update()
    )
    if not o:
        raise HTTPException(404, "Order not found")
    if o.status == "CANCELLED":
        return o
    if o.status != "PENDING":
        raise HTTPException(409, "Only pending orders can be cancelled")
    w = wallet_for(db, user.id)
    h = holding_for(db, w, o.stock_id)
    w.cash_reserved -= o.reserved_cash
    h.reserved_qty -= o.reserved_qty
    o.reserved_cash = Decimal(0)
    o.reserved_qty = 0
    o.status = "CANCELLED"
    record(
        db,
        user.id,
        "ORDER_CANCELLED",
        "order",
        o.id,
        {"status": "PENDING"},
        {"status": "CANCELLED"},
    )
    notify(db, user.id, "Order cancelled", f"Reservations released for order #{o.id}.")
    return o
