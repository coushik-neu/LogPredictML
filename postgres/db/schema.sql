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
    customer_id        INT PRIMARY KEY,

    total_orders       INT,
    total_sales        NUMERIC(12,2),
    avg_order_value    NUMERIC(12,2),
    last_order_days    INT,
    total_profit       NUMERIC(12,2),
    discount_usage_rate NUMERIC(5,4),

    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
