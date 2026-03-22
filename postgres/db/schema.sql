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