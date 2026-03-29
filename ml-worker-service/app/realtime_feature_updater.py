import time
import pandas as pd
from db import get_connection
from load_model import load_model
import os, time

print("Starting realtime ML worker...")


print("Waiting for initial dataset...")

while not os.path.exists("/ready/data_loaded.flag"):
    print("Waiting for data-init to finish...")
    time.sleep(2)

print("Initial data found. Starting generator...")

# ---------------------------------------
# Load model only once
# ---------------------------------------
model = load_model()

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()

while True:

    try:
        # ---------------------------------------
        # 1. Get last processed row
        # ---------------------------------------

        cursor.execute("SELECT last_processed_row FROM model_checkpoint WHERE id = 1")
        last_row = cursor.fetchone()[0]

        # ---------------------------------------
        # 2. Fetch only new rows
        # ---------------------------------------

        cursor.execute("""
            SELECT row_id, customer_id, sales, quantity, discount, profit
            FROM sales_orders
            WHERE row_id > %s
            ORDER BY row_id ASC
        """, (last_row,))

        new_rows = cursor.fetchall()

        if not new_rows:
            print("No new data...")
            time.sleep(1)
            continue

        print(f"Processing {len(new_rows)} new rows...")

        # ---------------------------------------
        # 3. Process each new row
        # ---------------------------------------

        for row in new_rows:

            row_id, customer_id, sales, quantity, discount, profit = row

            # ---------------------------------------
            # 3A. Insert/Update FULL feature row
            # ---------------------------------------

            avg_order_value = sales
            profit_per_order = profit
            orders_per_month = 1
            customer_age_days = 1
            days_between_orders = 0
            discount_dependency = discount
            profit_ratio = profit / sales if sales != 0 else 0
            sales_per_order = sales
            quantity_per_order = quantity
            recency_ratio = 0
            last_order_days = 0

            cursor.execute("""
                INSERT INTO customer_features (
                    customer_id,
                    total_sales,
                    total_quantity,
                    total_profit,
                    avg_discount,
                    total_orders,
                    avg_order_value,
                    profit_per_order,
                    orders_per_month,
                    customer_age_days,
                    days_between_orders,
                    discount_dependency,
                    profit_ratio,
                    sales_per_order,
                    quantity_per_order,
                    recency_ratio,
                    last_order_days
                )
                VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                ON CONFLICT (customer_id)
                DO UPDATE SET
                    total_orders = customer_features.total_orders + 1,
                    total_sales = customer_features.total_sales + EXCLUDED.total_sales,
                    total_quantity = customer_features.total_quantity + EXCLUDED.total_quantity,
                    total_profit = customer_features.total_profit + EXCLUDED.total_profit,
                    avg_discount = (customer_features.avg_discount + EXCLUDED.avg_discount) / 2,
                    avg_order_value = (customer_features.total_sales + EXCLUDED.total_sales) /
                                      (customer_features.total_orders + 1),
                    profit_per_order = (customer_features.total_profit + EXCLUDED.total_profit) /
                                       (customer_features.total_orders + 1),
                    profit_ratio = (customer_features.total_profit + EXCLUDED.total_profit) /
                                   (customer_features.total_sales + EXCLUDED.total_sales),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                customer_id,
                sales,
                quantity,
                profit,
                discount,
                avg_order_value,
                profit_per_order,
                orders_per_month,
                customer_age_days,
                days_between_orders,
                discount_dependency,
                profit_ratio,
                sales_per_order,
                quantity_per_order,
                recency_ratio,
                last_order_days
            ))

            # ---------------------------------------
            # 3B. Fetch full feature row for prediction
            # ---------------------------------------

            cursor.execute("""
                SELECT
                    total_sales,
                    total_quantity,
                    total_profit,
                    avg_discount,
                    total_orders,
                    avg_order_value,
                    profit_per_order,
                    orders_per_month,
                    customer_age_days,
                    days_between_orders,
                    discount_dependency,
                    profit_ratio,
                    sales_per_order,
                    quantity_per_order,
                    recency_ratio
                FROM customer_features
                WHERE customer_id = %s
            """, (customer_id,))

            features = cursor.fetchone()

            if features is None:
                continue

            # ---------------------------------------
            # 3C. Convert to DataFrame (exact same order as training)
            # ---------------------------------------

            X = pd.DataFrame([features], columns=[
                "total_sales",
                "total_quantity",
                "total_profit",
                "avg_discount",
                "total_orders",
                "avg_order_value",
                "profit_per_order",
                "orders_per_month",
                "customer_age_days",
                "days_between_orders",
                "discount_dependency",
                "profit_ratio",
                "sales_per_order",
                "quantity_per_order",
                "recency_ratio"
            ])

            # ---------------------------------------
            # 3D. Predict churn
            # ---------------------------------------

            prob = model.predict_proba(X)[0][1]
            pred = int(prob > 0.5)

            # ---------------------------------------
            # 3E. Save prediction
            # ---------------------------------------

            cursor.execute("""
                INSERT INTO customer_predictions (
                    customer_id,
                    churn_probability,
                    churn_prediction,
                    model_version
                )
                VALUES (%s, %s, %s, 'v1.0')

                ON CONFLICT (customer_id)
                DO UPDATE SET
                    churn_probability = EXCLUDED.churn_probability,
                    churn_prediction = EXCLUDED.churn_prediction,
                    last_updated = CURRENT_TIMESTAMP
            """, (customer_id, float(prob), pred))

            last_row = row_id

        # ---------------------------------------
        # 4. Update checkpoint
        # ---------------------------------------

        cursor.execute("""
            UPDATE model_checkpoint
            SET last_processed_row = %s
            WHERE id = 1
        """, (last_row,))

        print("Checkpoint updated:", last_row)

        time.sleep(1)

    except Exception as e:
        print("Worker error:", e)
        time.sleep(3)