from sqlalchemy import text


def get_churn_distribution(db):

    q = """
    SELECT
        CASE
            WHEN churn_probability > 0.7 THEN 'high'
            WHEN churn_probability > 0.4 THEN 'medium'
            ELSE 'low'
        END as risk_level,
        COUNT(*)
    FROM customer_predictions
    GROUP BY risk_level
    """

    rows = db.execute(text(q)).fetchall()

    data = {"high": 0, "medium": 0, "low": 0}

    for r in rows:
        data[r[0]] = r[1]

    return data


def get_high_risk_customers(db):

    q = """
    SELECT
        p.customer_id,
        p.churn_probability,
        f.total_orders,
        f.avg_order_value,
        f.last_order_days,
        f.total_sales
    FROM customer_predictions p
    JOIN customer_features f ON p.customer_id = f.customer_id
    ORDER BY p.churn_probability DESC
    LIMIT 10
    """

    rows = db.execute(text(q)).fetchall()

    return [
        {
            "customer_id": r[0],
            "churn_probability": float(r[1]),
            "total_orders": r[2],
            "avg_order_value": float(r[3]),
            "last_order_days": r[4],
            "total_sales": float(r[5])
        }
        for r in rows
    ]