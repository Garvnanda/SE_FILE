"""Frozen initial PostgreSQL schema. Do not edit after applying."""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "\nCREATE TABLE stocks (\n\tid SERIAL NOT NULL, \n\tsymbol VARCHAR(16) NOT NULL, \n\tname VARCHAR(100) NOT NULL, \n\tsector VARCHAR(100) NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (symbol)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE users (\n\tid SERIAL NOT NULL, \n\temail VARCHAR(254) NOT NULL, \n\tpassword_hash VARCHAR NOT NULL, \n\trole VARCHAR(24) NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (role IN ('TRADER','ADMIN','MARKET_OPERATOR')), \n\tUNIQUE (email)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE audit_logs (\n\tid SERIAL NOT NULL, \n\tactor_id INTEGER, \n\taction VARCHAR NOT NULL, \n\tentity_type VARCHAR NOT NULL, \n\tentity_id INTEGER, \n\tbefore_json JSON NOT NULL, \n\tafter_json JSON NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(actor_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE auth_sessions (\n\ttoken_hash VARCHAR(64) NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tcsrf VARCHAR NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (token_hash), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE market_sessions (\n\tid SERIAL NOT NULL, \n\tis_open BOOLEAN NOT NULL, \n\tupdated_by INTEGER, \n\teffective_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(updated_by) REFERENCES users (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE notifications (\n\tid SERIAL NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\ttitle VARCHAR NOT NULL, \n\tbody VARCHAR NOT NULL, \n\tread_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE orders (\n\tid SERIAL NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tstock_id INTEGER NOT NULL, \n\tside VARCHAR NOT NULL, \n\torder_type VARCHAR NOT NULL, \n\tqty INTEGER NOT NULL, \n\tlimit_price NUMERIC(18, 4), \n\tstatus VARCHAR NOT NULL, \n\treserved_cash NUMERIC(24, 4) NOT NULL, \n\treserved_qty INTEGER NOT NULL, \n\tidempotency_key VARCHAR NOT NULL, \n\trejection_reason VARCHAR, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (user_id, idempotency_key), \n\tCHECK (qty > 0), \n\tCHECK (status IN ('PENDING','FILLED','CANCELLED','REJECTED')), \n\tCHECK (side IN ('BUY','SELL')), \n\tCHECK (order_type IN ('MARKET','LIMIT')), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(stock_id) REFERENCES stocks (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_orders_user_id ON orders (user_id)")
    op.execute("CREATE INDEX ix_orders_status ON orders (status)")
    op.execute(
        "\nCREATE TABLE portfolios (\n\tid SERIAL NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (user_id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE price_ticks (\n\tid SERIAL NOT NULL, \n\tstock_id INTEGER NOT NULL, \n\tprice NUMERIC(18, 4) NOT NULL, \n\tsource VARCHAR NOT NULL, \n\trecorded_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tevent_key VARCHAR, \n\tPRIMARY KEY (id), \n\tCHECK (price > 0), \n\tFOREIGN KEY(stock_id) REFERENCES stocks (id), \n\tUNIQUE (event_key)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_price_ticks_stock_id ON price_ticks (stock_id)")
    op.execute(
        "\nCREATE TABLE watchlists (\n\tid SERIAL NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tname VARCHAR(80) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE holdings (\n\tid SERIAL NOT NULL, \n\tportfolio_id INTEGER NOT NULL, \n\tstock_id INTEGER NOT NULL, \n\tqty INTEGER NOT NULL, \n\treserved_qty INTEGER NOT NULL, \n\tavg_cost NUMERIC(24, 8) NOT NULL, \n\trealized_pnl NUMERIC(24, 8) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (portfolio_id, stock_id), \n\tCHECK (qty >= reserved_qty AND reserved_qty >= 0), \n\tFOREIGN KEY(portfolio_id) REFERENCES portfolios (id), \n\tFOREIGN KEY(stock_id) REFERENCES stocks (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE trades (\n\tid SERIAL NOT NULL, \n\torder_id INTEGER NOT NULL, \n\tuser_id INTEGER NOT NULL, \n\tstock_id INTEGER NOT NULL, \n\tside VARCHAR NOT NULL, \n\tqty INTEGER NOT NULL, \n\texecution_price NUMERIC(18, 4) NOT NULL, \n\texecuted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (order_id), \n\tFOREIGN KEY(order_id) REFERENCES orders (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(stock_id) REFERENCES stocks (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE wallets (\n\tid SERIAL NOT NULL, \n\tportfolio_id INTEGER NOT NULL, \n\tcash_total NUMERIC(24, 4) NOT NULL, \n\tcash_reserved NUMERIC(24, 4) NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (cash_total >= cash_reserved AND cash_reserved >= 0), \n\tUNIQUE (portfolio_id), \n\tFOREIGN KEY(portfolio_id) REFERENCES portfolios (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE watchlist_items (\n\tid SERIAL NOT NULL, \n\twatchlist_id INTEGER NOT NULL, \n\tstock_id INTEGER NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (watchlist_id, stock_id), \n\tFOREIGN KEY(watchlist_id) REFERENCES watchlists (id), \n\tFOREIGN KEY(stock_id) REFERENCES stocks (id)\n)\n\n"
    )
    op.execute(
        "\nCREATE TABLE wallet_ledger (\n\tid SERIAL NOT NULL, \n\twallet_id INTEGER NOT NULL, \n\torder_id INTEGER, \n\tamount_signed NUMERIC(24, 4) NOT NULL, \n\tevent_type VARCHAR NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(wallet_id) REFERENCES wallets (id), \n\tFOREIGN KEY(order_id) REFERENCES orders (id)\n)\n\n"
    )


def downgrade():
    op.drop_table("wallet_ledger")
    op.drop_table("watchlist_items")
    op.drop_table("wallets")
    op.drop_table("trades")
    op.drop_table("holdings")
    op.drop_table("watchlists")
    op.drop_table("price_ticks")
    op.drop_table("portfolios")
    op.drop_table("orders")
    op.drop_table("notifications")
    op.drop_table("market_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("stocks")
