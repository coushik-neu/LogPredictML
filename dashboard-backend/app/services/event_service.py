import asyncio
from sqlalchemy import text
from app.database import SessionLocal
from app.websocket.events import (
    emit_model_update,
    emit_drift_update,
    emit_churn_update,
    emit_business_update
)


async def monitor_changes():

    while True:

        db = SessionLocal()

        # drift
        drift = db.execute(text("SELECT drift_detected, drift_score FROM drift_status LIMIT 1")).fetchone()

        await emit_drift_update({
            "drift_detected": drift[0],
            "drift_score": float(drift[1])
        })

        # churn distribution
        churn = db.execute(text("""
        SELECT COUNT(*) FILTER (WHERE churn_probability > 0.7),
               COUNT(*) FILTER (WHERE churn_probability BETWEEN 0.4 AND 0.7),
               COUNT(*) FILTER (WHERE churn_probability < 0.4)
        FROM customer_predictions
        """)).fetchone()

        await emit_churn_update({
            "high": churn[0],
            "medium": churn[1],
            "low": churn[2]
        })

        # model update
        model = db.execute(text("""
        SELECT model_version, f1_score FROM model_registry
        ORDER BY created_at DESC LIMIT 1
        """)).fetchone()

        await emit_model_update({
            "model_version": model[0],
            "f1": float(model[1])
        })

        # revenue update
        revenue = db.execute(text("SELECT SUM(sales) FROM sales_orders")).scalar()

        await emit_business_update({
            "total_revenue": float(revenue or 0)
        })

        db.close()

        await asyncio.sleep(5)