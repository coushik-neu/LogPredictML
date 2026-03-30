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

    last_drift_score = None
    last_model_version = None
    last_revenue = None
    last_churn_snapshot = None

    while True:

        db = SessionLocal()

        # -------------------------------------
        # 1. DRIFT UPDATE
        # -------------------------------------
        drift = db.execute(text("""
            SELECT drift_detected, drift_score
            FROM drift_status
            LIMIT 1
        """)).fetchone()

        if drift:
            drift_data = (drift[0], float(drift[1]))

            if drift_data != last_drift_score:
                last_drift_score = drift_data

                await emit_drift_update({
                    "drift_detected": drift[0],
                    "drift_score": float(drift[1])
                })


        # -------------------------------------
        # 2. CHURN DISTRIBUTION UPDATE
        # -------------------------------------
        churn = db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE churn_probability > 0.7),
            COUNT(*) FILTER (WHERE churn_probability BETWEEN 0.4 AND 0.7),
            COUNT(*) FILTER (WHERE churn_probability < 0.4)
        FROM customer_predictions
        """)).fetchone()

        if churn:
            churn_data = (churn[0], churn[1], churn[2])

            if churn_data != last_churn_snapshot:
                last_churn_snapshot = churn_data

                await emit_churn_update({
                    "high": churn[0],
                    "medium": churn[1],
                    "low": churn[2]
                })


        # -------------------------------------
        # 3. MODEL UPDATE
        # -------------------------------------
        model = db.execute(text("""
        SELECT model_version, f1_score
        FROM model_registry
        ORDER BY created_at DESC
        LIMIT 1
        """)).fetchone()

        if model:
            model_data = model[0]

            if model_data != last_model_version:
                last_model_version = model_data

                await emit_model_update({
                    "model_version": model[0],
                    "f1": float(model[1])
                })


        # -------------------------------------
        # 4. BUSINESS METRICS UPDATE
        # -------------------------------------
        revenue = db.execute(text("SELECT SUM(sales) FROM sales_orders")).scalar()
        revenue = float(revenue or 0)

        if revenue != last_revenue:
            last_revenue = revenue

            await emit_business_update({
                "total_revenue": revenue
            })

        db.close()

        await asyncio.sleep(3)