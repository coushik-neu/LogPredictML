from sqlalchemy import text


def get_total_revenue(db):

    q = "SELECT SUM(sales) FROM sales_orders"
    val = db.execute(text(q)).scalar()

    return {"total_revenue": float(val or 0)}


def get_orders_today(db):

    q = "SELECT COUNT(*) FROM sales_orders WHERE order_date = CURRENT_DATE"
    return {"orders_today": db.execute(text(q)).scalar()}


def get_top_industries(db):

    q = """
    SELECT industry, SUM(sales) as revenue
    FROM sales_orders
    GROUP BY industry
    ORDER BY revenue DESC
    LIMIT 5
    """

    rows = db.execute(text(q)).fetchall()

    return [{"industry": r[0], "revenue": float(r[1])} for r in rows]


def get_top_products(db):

    q = """
    SELECT product, SUM(sales)
    FROM sales_orders
    GROUP BY product
    ORDER BY SUM(sales) DESC
    LIMIT 5
    """

    rows = db.execute(text(q)).fetchall()

    return [{"product": r[0], "sales": float(r[1])} for r in rows]


def get_revenue_trend(db):

    q = """
    SELECT order_date, SUM(sales)
    FROM sales_orders
    GROUP BY order_date
    ORDER BY order_date
    """

    rows = db.execute(text(q)).fetchall()

    return [{"date": str(r[0]), "sales": float(r[1])} for r in rows]