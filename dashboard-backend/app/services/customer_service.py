from sqlalchemy import text

def get_customer_orders(db, customer_id: int, limit: int = 50):

    rows = db.execute(text("""
        SELECT
            order_id,
            order_date,
            product,
            sales,
            quantity,
            profit,
            discount,
            industry,
            segment
        FROM sales_orders
        WHERE customer_id = :customer_id
        ORDER BY order_date DESC
        LIMIT :limit
    """), {
        "customer_id": customer_id,
        "limit": limit
    }).fetchall()

    return [dict(r._mapping) for r in rows]

def get_high_risk_customers(db, type: str = "active", page: int = 1, page_size: int = 20):

    offset = (page - 1) * page_size

    # -----------------------------
    # FILTER + ORDER LOGIC
    # -----------------------------
    if type == "high_risk":
        where_clause = "cp.churn_probability > 0.7"
        order_clause = "cp.churn_probability DESC"
    else:  # ✅ ACTIVE (low churn + high orders)
        where_clause = "cp.churn_probability < 0.4"
        order_clause = "cf.total_orders DESC"

    # -----------------------------
    # MAIN QUERY (FIXED)
    # -----------------------------
    rows = db.execute(text(f"""
        SELECT
            cp.customer_id,
            cp.churn_probability,

            cf.total_orders,
            cf.total_sales,
            cf.avg_order_value,
            cf.last_order_days,

            MAX(so.contact_name) AS contact_name,
            MAX(so.customer) AS customer,
            MAX(so.industry) AS industry,
            MAX(so.segment) AS segment

        FROM customer_predictions cp

        JOIN customer_features cf
            ON cp.customer_id = cf.customer_id

        LEFT JOIN sales_orders so
            ON so.customer_id = cp.customer_id

        WHERE {where_clause}

        GROUP BY
            cp.customer_id,
            cp.churn_probability,
            cf.total_orders,
            cf.total_sales,
            cf.avg_order_value,
            cf.last_order_days

        ORDER BY {order_clause}

        LIMIT :limit OFFSET :offset
    """), {
        "limit": page_size,
        "offset": offset
    }).fetchall()

    # -----------------------------
    # TOTAL COUNT (MATCHES FILTER)
    # -----------------------------
    total = db.execute(text(f"""
        SELECT COUNT(*)
        FROM customer_predictions cp
        WHERE {where_clause}
    """)).scalar()

    return {
        "data": [dict(r._mapping) for r in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": offset + page_size < total
    }




def get_customer_summary(db, customer_id: int):

    row = db.execute(text("""
        SELECT *
        FROM customer_features
        WHERE customer_id = :customer_id
    """), {"customer_id": customer_id}).fetchone()

    if not row:
        return None

    return dict(row._mapping)


def get_customer_revenue_trend(db, customer_id: int):

    rows = db.execute(text("""
        SELECT order_date, SUM(sales) as revenue
        FROM sales_orders
        WHERE customer_id = :customer_id
        GROUP BY order_date
        ORDER BY order_date
    """), {"customer_id": customer_id}).fetchall()

    return [
        {"date": str(r[0]), "revenue": float(r[1])}
        for r in rows
    ]