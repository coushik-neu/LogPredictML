CREATE TABLE sales_orders (

    row_id SERIAL PRIMARY KEY,

    order_id TEXT,
    order_date DATE,
    date_key INT,

    contact_name TEXT,
    country TEXT,
    city TEXT,
    region TEXT,
    subregion TEXT,

    customer TEXT,
    customer_id INT,

    industry TEXT,
    segment TEXT,

    product TEXT,
    license TEXT,

    sales FLOAT,
    quantity INT,
    discount FLOAT,
    profit FLOAT
);

CREATE INDEX idx_customer_id 
ON sales_orders(customer_id);

CREATE INDEX idx_order_date 
ON sales_orders(order_date);

CREATE INDEX idx_customer_date 
ON sales_orders(customer_id, order_date DESC);

CREATE INDEX idx_industry 
ON sales_orders(industry);

CREATE INDEX idx_product 
ON sales_orders(product);

CREATE TABLE IF NOT EXISTS customer_features (
    customer_id INT PRIMARY KEY,

    total_sales FLOAT,
    total_quantity INT,
    total_profit FLOAT,
    avg_discount FLOAT,
    total_orders INT,

    avg_order_value FLOAT,
    profit_per_order FLOAT,
    orders_per_month FLOAT,
    customer_age_days INT,
    days_between_orders FLOAT,
    discount_dependency FLOAT,
    profit_ratio FLOAT,
    sales_per_order FLOAT,
    quantity_per_order FLOAT,
    recency_ratio FLOAT,

    last_order_days INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_predictions (
    customer_id        INT PRIMARY KEY,

    churn_probability  NUMERIC(5,4),
    churn_prediction   INT,
    model_version      VARCHAR(20),

    last_updated       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customer_features_customer
ON customer_features(customer_id);

CREATE INDEX IF NOT EXISTS idx_customer_predictions_customer
ON customer_predictions(customer_id);

CREATE TABLE IF NOT EXISTS model_checkpoint (
    id INT PRIMARY KEY,
    last_processed_row INT,
    last_trained_row INT
);

INSERT INTO model_checkpoint (id, last_processed_row, last_trained_row)
VALUES (1, 0, 0)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS model_registry (

    model_id SERIAL PRIMARY KEY,

    model_version      VARCHAR(50),
    model_path         TEXT,

    f1_score           FLOAT,
    roc_auc            FLOAT,

    rows_used          INT,
    customers_used     INT,

    is_production      BOOLEAN DEFAULT FALSE,

    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drift_status (
    id INT PRIMARY KEY,
    drift_detected BOOLEAN,
    drift_score FLOAT,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO drift_status (id, drift_detected, drift_score)
VALUES (1, FALSE, 0)
ON CONFLICT (id) DO NOTHING;

