-- A miniature OLTP: customers + orders + line_items.
-- Realistic shape: surrogate ids, updated_at maintained by trigger.

CREATE TABLE customers (
    id          BIGSERIAL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    full_name   TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id           BIGSERIAL PRIMARY KEY,
    customer_id  BIGINT NOT NULL REFERENCES customers(id),
    status       TEXT NOT NULL CHECK (status IN ('pending','paid','shipped','cancelled')),
    total_cents  INTEGER NOT NULL,
    currency     TEXT NOT NULL DEFAULT 'USD',
    placed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE line_items (
    id          BIGSERIAL PRIMARY KEY,
    order_id    BIGINT NOT NULL REFERENCES orders(id),
    sku         TEXT NOT NULL,
    qty         INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- updated_at trigger (the cursor-field exercises depend on this)
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER customers_touch BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER orders_touch BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER line_items_touch BEFORE UPDATE ON line_items
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
