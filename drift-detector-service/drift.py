import pandas as pd
import numpy as np
import time
import os
from sqlalchemy import create_engine, text

# -------------------------------------
# ADD THIS BLOCK (safe DB startup)
# -------------------------------------

print("Starting drift detector service...")

time.sleep(10)   # wait for postgres container to be ready

# -------------------------------------
# DB connection
# -------------------------------------

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DATA_DRIFT_THRESHOLD = os.getenv("DATA_DRIFT_THRESHOLD")

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("Drift detector started... Connected to DB")

# -------------------------------------
# Continuous monitoring
# -------------------------------------

while True:
    try:

        print("\nChecking drift...")

        # -------------------------------------
        # OLD data (first 5000 rows)
        # -------------------------------------

        old_data = pd.read_sql("""
            SELECT sales, quantity, discount, profit
            FROM sales_orders
            ORDER BY row_id ASC
            LIMIT 5000
        """, engine)

        # -------------------------------------
        # NEW data (latest 5000 rows)
        # -------------------------------------

        new_data = pd.read_sql("""
            SELECT sales, quantity, discount, profit
            FROM sales_orders
            ORDER BY row_id DESC
            LIMIT 5000
        """, engine)

        # -------------------------------------
        # Compute drift score
        # -------------------------------------

        old_mean = old_data.mean()
        new_mean = new_data.mean()

        drift_score = np.abs(old_mean - new_mean).mean()

        print("Drift score:", drift_score)

        # -------------------------------------
        # Decide drift
        # -------------------------------------

        if drift_score > DATA_DRIFT_THRESHOLD:
            drift_flag = True
            print("Drift detected!")
        else:
            drift_flag = False
            print("No drift detected")

        # -------------------------------------
        # FIXED SQLALCHEMY 2.0 UPDATE (added on top of your logic)
        # -------------------------------------

        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE drift_status
                SET drift_detected = :flag,
                    drift_score = :score,
                    last_checked = NOW()
                WHERE id = 1
            """), {
                "flag": drift_flag,
                "score": float(drift_score)
            })

        print("Drift status updated in database")

        # -------------------------------------
        # Wait before next check
        # -------------------------------------

        print("Sleeping 5 minutes...\n")
        time.sleep(300)

    except Exception as e:
        print("Error in drift detector:", e)
        print("Retrying in 60 seconds...\n")
        time.sleep(60)