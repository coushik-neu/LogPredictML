import time
import pandas as pd
from db import get_connection
from model_loader import load_model

print("Starting realtime ML worker...")

# Load model only once
model = load_model()

conn = get_connection()
conn.autocommit = True
cursor = conn.cursor()


while True:

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
    # 3. Process each row
    # ---------------------------------------

    for row in new_rows:

        row_id, customer_id, sales, quantity, discount, profit = row

        # ---------------------------------------
        # Update feature table
        # ---------------------------------------

        cursor.execute("""
            INSERT INTO customer_features (
                customer_id,
                total_orders,
                total_sales,
                avg_order_value,
                last_order_days,
                total_profit,
                discount_usage_rate
            )
            VALUES (%s, 1, %s, %s, 0, %s, %s)

            ON CONFLICT (customer_id)
            DO UPDATE SET
                total_orders = customer_features.total_orders + 1,
                total_sales = customer_features.total_sales + EXCLUDED.total_sales,
                total_profit = customer_features.total_profit + EXCLUDED.total_profit,
                avg_order_value = (customer_features.total_sales + EXCLUDED.total_sales) /
                                  (customer_features.total_orders + 1),
                discount_usage_rate = (
                    customer_features.discount_usage_rate + EXCLUDED.discount_usage_rate
                ) / 2,
                updated_at = CURRENT_TIMESTAMP
        """, (customer_id, sales, sales, profit, discount))

        # ---------------------------------------
        # Fetch updated features
        # ---------------------------------------

        cursor.execute("""
            SELECT total_sales, total_orders, avg_order_value,
                   total_profit, discount_usage_rate, last_order_days
            FROM customer_features
            WHERE customer_id = %s
        """, (customer_id,))

        features = cursor.fetchone()

        if features is None:
            continue

        # ---------------------------------------
        # Convert to DataFrame
        # ---------------------------------------

        X = pd.DataFrame([features], columns=[
            "total_sales",
            "total_orders",
            "avg_order_value",
            "total_profit",
            "discount_usage_rate",
            "last_order_days"
        ])

        # ---------------------------------------
        # Predict churn
        # ---------------------------------------

        prob = model.predict_proba(X)[0][1]
        pred = int(prob > 0.5)

        # ---------------------------------------
        # Save prediction
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