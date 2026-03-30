from sqlalchemy import text


def get_model_health(db):

    q = """
    SELECT model_version, f1_score, roc_auc, rows_used, customers_used, created_at
    FROM model_registry
    ORDER BY created_at DESC
    LIMIT 1
    """

    row = db.execute(text(q)).fetchone()

    if not row:
        return {"status": "no model"}

    return {
        "model_version": row[0],
        "f1_score": float(row[1]),
        "roc_auc": float(row[2]),
        "rows_used": row[3],
        "customers_used": row[4],
        "trained_at": str(row[5])
    }


def get_performance_trend(db):

    q = """
    SELECT model_version, f1_score, roc_auc, created_at
    FROM model_registry
    ORDER BY created_at
    """

    rows = db.execute(text(q)).fetchall()

    return [
        {
            "model_version": r[0],
            "f1_score": float(r[1]),
            "roc_auc": float(r[2]),
            "date": str(r[3])
        }
        for r in rows
    ]