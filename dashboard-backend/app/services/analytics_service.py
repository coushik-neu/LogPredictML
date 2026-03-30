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

def get_model_performance_trend(db):

    rows = db.execute(text("""
        SELECT
            created_at AS date,
            f1_score,
            roc_auc
        FROM model_registry
        ORDER BY created_at ASC
    """)).fetchall()

    return [dict(r._mapping) for r in rows]


# ----------------------------------------
# CURRENT MODEL (PRODUCTION)
# ----------------------------------------
def get_current_model(db):

    row = db.execute(text("""
        SELECT
            model_version,
            f1_score,
            roc_auc,
            rows_used,
            customers_used,
            created_at
        FROM model_registry
        WHERE is_production = TRUE
        ORDER BY created_at DESC
        LIMIT 1
    """)).fetchone()

    if not row:
        return {
            "model_version": "N/A",
            "f1_score": 0,
            "roc_auc": 0
        }

    return dict(row._mapping)


# ----------------------------------------
# ALL MODELS (PAGINATED)
# ----------------------------------------
def get_all_models(db, page=1, page_size=10):

    offset = (page - 1) * page_size

    rows = db.execute(text("""
        SELECT
            model_id,
            model_version,
            f1_score,
            roc_auc,
            rows_used,
            customers_used,
            is_production,
            created_at
        FROM model_registry
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """), {
        "limit": page_size,
        "offset": offset
    }).fetchall()

    total = db.execute(text("""
        SELECT COUNT(*) FROM model_registry
    """)).scalar()

    return {
        "data": [dict(r._mapping) for r in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": offset + page_size < total
    }
