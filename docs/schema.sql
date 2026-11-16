
CREATE TABLE stocks (
	id SERIAL NOT NULL, 
	symbol VARCHAR(16) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	sector VARCHAR(100) NOT NULL, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (symbol)
)

;

CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	role VARCHAR(24) NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('TRADER','ADMIN','MARKET_OPERATOR')), 
	UNIQUE (email)
)

;

CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	actor_id INTEGER, 
	action VARCHAR NOT NULL, 
	entity_type VARCHAR NOT NULL, 
	entity_id INTEGER, 
	before_json JSON NOT NULL, 
	after_json JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
)

;

CREATE TABLE auth_sessions (
	token_hash VARCHAR(64) NOT NULL, 
	user_id INTEGER NOT NULL, 
	csrf VARCHAR NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (token_hash), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE market_sessions (
	id SERIAL NOT NULL, 
	is_open BOOLEAN NOT NULL, 
	updated_by INTEGER, 
	effective_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
)

;

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	title VARCHAR NOT NULL, 
	body VARCHAR NOT NULL, 
	read_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE orders (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	stock_id INTEGER NOT NULL, 
	side VARCHAR NOT NULL, 
	order_type VARCHAR NOT NULL, 
	qty INTEGER NOT NULL, 
	limit_price NUMERIC(18, 4), 
	status VARCHAR NOT NULL, 
	reserved_cash NUMERIC(24, 4) NOT NULL, 
	reserved_qty INTEGER NOT NULL, 
	idempotency_key VARCHAR NOT NULL, 
	rejection_reason VARCHAR, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, idempotency_key), 
	CHECK (qty > 0), 
	CHECK (status IN ('PENDING','FILLED','CANCELLED','REJECTED')), 
	CHECK (side IN ('BUY','SELL')), 
	CHECK (order_type IN ('MARKET','LIMIT')), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(stock_id) REFERENCES stocks (id)
)

;
CREATE INDEX ix_orders_status ON orders (status);
CREATE INDEX ix_orders_user_id ON orders (user_id);

CREATE TABLE portfolios (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE price_ticks (
	id SERIAL NOT NULL, 
	stock_id INTEGER NOT NULL, 
	price NUMERIC(18, 4) NOT NULL, 
	source VARCHAR NOT NULL, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	event_key VARCHAR, 
	PRIMARY KEY (id), 
	CHECK (price > 0), 
	FOREIGN KEY(stock_id) REFERENCES stocks (id), 
	UNIQUE (event_key)
)

;
CREATE INDEX ix_price_ticks_stock_id ON price_ticks (stock_id);

CREATE TABLE watchlists (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE holdings (
	id SERIAL NOT NULL, 
	portfolio_id INTEGER NOT NULL, 
	stock_id INTEGER NOT NULL, 
	qty INTEGER NOT NULL, 
	reserved_qty INTEGER NOT NULL, 
	avg_cost NUMERIC(24, 8) NOT NULL, 
	realized_pnl NUMERIC(24, 8) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (portfolio_id, stock_id), 
	CHECK (qty >= reserved_qty AND reserved_qty >= 0), 
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id), 
	FOREIGN KEY(stock_id) REFERENCES stocks (id)
)

;

CREATE TABLE trades (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	stock_id INTEGER NOT NULL, 
	side VARCHAR NOT NULL, 
	qty INTEGER NOT NULL, 
	execution_price NUMERIC(18, 4) NOT NULL, 
	executed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(stock_id) REFERENCES stocks (id)
)

;

CREATE TABLE wallets (
	id SERIAL NOT NULL, 
	portfolio_id INTEGER NOT NULL, 
	cash_total NUMERIC(24, 4) NOT NULL, 
	cash_reserved NUMERIC(24, 4) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (cash_total >= cash_reserved AND cash_reserved >= 0), 
	UNIQUE (portfolio_id), 
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id)
)

;

CREATE TABLE watchlist_items (
	id SERIAL NOT NULL, 
	watchlist_id INTEGER NOT NULL, 
	stock_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (watchlist_id, stock_id), 
	FOREIGN KEY(watchlist_id) REFERENCES watchlists (id), 
	FOREIGN KEY(stock_id) REFERENCES stocks (id)
)

;

CREATE TABLE wallet_ledger (
	id SERIAL NOT NULL, 
	wallet_id INTEGER NOT NULL, 
	order_id INTEGER, 
	amount_signed NUMERIC(24, 4) NOT NULL, 
	event_type VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(wallet_id) REFERENCES wallets (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
)

;