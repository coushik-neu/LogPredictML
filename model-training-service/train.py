import pandas as pd
import psycopg2
import os
import joblib
import xgboost as xgb
import time
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, roc_auc_score

import os, time


mlflow.set_tracking_uri("http://mlflow:5000")
mlflow.set_experiment("customer_churn_training")


print("Waiting for initial dataset...")

while not os.path.exists("/ready/data_loaded.flag"):
    print("Waiting for data-init to finish...")
    time.sleep(2)

print("Initial data found. Starting generator...")

print("ML Training Service Started...")

MODEL_PATH = "/models/churn_model.pkl"

FEATURE_COLUMNS = [
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
]

while True:
    try:
        print("\nChecking if retraining is needed...")

        # -------------------------------------
        # 1. Connect to PostgreSQL
        # -------------------------------------

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        cursor = conn.cursor()

        # -------------------------------------
        # 2. Check retraining trigger
        # -------------------------------------

        cursor.execute("""
            SELECT last_processed_row, last_trained_row
            FROM model_checkpoint
            WHERE id = 1
        """)

        last_processed_row, last_trained_row = cursor.fetchone()

        rows_since_last_training = last_processed_row - last_trained_row

        print("Rows since last training:", rows_since_last_training)

        model_exists = os.path.exists(MODEL_PATH)

        cursor.execute("SELECT drift_detected FROM drift_status WHERE id = 1")
        drift_flag = cursor.fetchone()[0]
        
        if model_exists and not drift_flag and rows_since_last_training < 2000:
            print("No drift and not enough new rows. Waiting...")
            time.sleep(60)
            continue

        print("\nRetraining model...")

        with mlflow.start_run():

            # -------------------------------------
            # 3. Load data
            # -------------------------------------

            query = "SELECT * FROM sales_orders ORDER BY row_id DESC LIMIT 50000"
            df = pd.read_sql(query, conn)

            print("Data Loaded:", df.shape)

            # -------------------------------------
            # 4. Clean + Convert Date
            # -------------------------------------

            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
            df = df.dropna(subset=["order_date"])

            # -------------------------------------
            # 5. Create Customer-Level Dataset
            # -------------------------------------

            today = df["order_date"].max()

            customer_df = df.groupby("customer_id").agg(
                last_order_date=("order_date", "max"),
                first_order_date=("order_date", "min"),
                total_sales=("sales", "sum"),
                total_quantity=("quantity", "sum"),
                total_profit=("profit", "sum"),
                avg_discount=("discount", "mean"),
                total_orders=("order_id", "count")
            ).reset_index()

            # -------------------------------------
            # 6. Feature Engineering (same as worker)
            # -------------------------------------

            customer_df["last_order_days"] = (today - customer_df["last_order_date"]).dt.days
            customer_df["customer_age_days"] = (
                customer_df["last_order_date"] - customer_df["first_order_date"]
            ).dt.days + 1

            customer_df["avg_order_value"] = customer_df["total_sales"] / customer_df["total_orders"]
            customer_df["profit_per_order"] = customer_df["total_profit"] / customer_df["total_orders"]
            customer_df["orders_per_month"] = customer_df["total_orders"] / (customer_df["customer_age_days"] / 30)
            customer_df["days_between_orders"] = customer_df["customer_age_days"] / customer_df["total_orders"]
            customer_df["discount_dependency"] = customer_df["avg_discount"] * customer_df["total_orders"]
            customer_df["profit_ratio"] = customer_df["total_profit"] / customer_df["total_sales"]
            customer_df["sales_per_order"] = customer_df["total_sales"] / customer_df["total_orders"]
            customer_df["quantity_per_order"] = customer_df["total_quantity"] / customer_df["total_orders"]
            customer_df["recency_ratio"] = customer_df["last_order_days"] / customer_df["customer_age_days"]

            customer_df = customer_df.fillna(0)

            print("Customer dataset shape:", customer_df.shape)

            # -------------------------------------
            # 7. Create churn label
            # -------------------------------------

            customer_df["churn_score"] = 0

            customer_df.loc[customer_df["last_order_days"] > 7, "churn_score"] += 1
            customer_df.loc[customer_df["total_orders"] <= 2, "churn_score"] += 1
            customer_df.loc[customer_df["orders_per_month"] < 1, "churn_score"] += 1
            customer_df.loc[customer_df["avg_discount"] > 0.3, "churn_score"] += 1
            customer_df.loc[customer_df["total_sales"] < customer_df["total_sales"].median(), "churn_score"] += 1

            customer_df["churn"] = (customer_df["churn_score"] >= 2).astype(int)

            # -------------------------------------
            # 8. Features and Target
            # -------------------------------------

            X = customer_df[FEATURE_COLUMNS]
            y = customer_df["churn"]

            print("\nNumber of features used:", X.shape[1])
            print("Feature names:", list(X.columns))

            if len(y.unique()) < 2:
                print("Only one class found. Waiting for more data...")
                time.sleep(60)
                mlflow.end_run()
                continue

            # -------------------------------------
            # 9. Train-test split
            # -------------------------------------

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.2,
                random_state=42,
                stratify=y
            )

            # -------------------------------------
            # 10. Train XGBoost Model
            # -------------------------------------

            model = xgb.XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )

            model.fit(X_train, y_train)

            # -------------------------------------
            # 11. Evaluation
            # -------------------------------------

            pred = model.predict(X_test)
            prob = model.predict_proba(X_test)[:, 1]

            print("\nF1 Score:", f1_score(y_test, pred))
            print("ROC-AUC:", roc_auc_score(y_test, prob))

            mlflow.log_metric("f1_score", f1_score(y_test, pred))
            mlflow.log_metric("roc_auc", roc_auc_score(y_test, prob))
            mlflow.log_metric("rows_used", len(df))
            mlflow.log_metric("customers", len(customer_df))

            # -------------------------------------
            # 12. Save model + feature list
            # -------------------------------------

                    
            # -------------------------------------
    # 12. Save model + version + auto promotion
    # -------------------------------------

            model_package = {
                "model": model,
                "features": FEATURE_COLUMNS
            }

            # Create model version
            timestamp = int(time.time())
            model_version = f"churn_model_{timestamp}"
            model_path = f"/models/{model_version}.pkl"

            # Always save versioned model
            joblib.dump(model_package, model_path)

            print("\nVersioned model saved:", model_path)

            # -------------------------------------
            # 13. Check if this is the best model
            # -------------------------------------

            new_f1 = f1_score(y_test, pred)
            new_auc = roc_auc_score(y_test, prob)

            cursor.execute("""
                SELECT f1_score FROM model_registry
                WHERE is_production = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

            best_f1 = row[0] if row else 0

            print("Best production F1:", best_f1)
            print("New model F1:", new_f1)

            # -------------------------------------
            # 14. Promote model only if better
            # -------------------------------------

            is_production = False

            if new_f1 > best_f1:
                print("Better model found. Promoting to production...")

                # overwrite production model used by ml-worker
                joblib.dump(model_package, MODEL_PATH)

                is_production = True

                # mark old production models as false
                cursor.execute("""
                    UPDATE model_registry
                    SET is_production = FALSE
                    WHERE is_production = TRUE
                """)

            else:
                print("New model is worse. Keeping current production model.")

            # -------------------------------------
            # 15. Save model metadata in DB
            # -------------------------------------

            cursor.execute("""
                INSERT INTO model_registry (
                    model_version,
                    model_path,
                    f1_score,
                    roc_auc,
                    rows_used,
                    customers_used,
                    is_production
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                model_version,
                model_path,
                new_f1,
                new_auc,
                len(df),
                len(customer_df),
                is_production
            ))

            conn.commit()

            print("Model metadata stored in DB.")

            # -------------------------------------
            # 13. Update checkpoint
            # -------------------------------------

            cursor.execute("""
                UPDATE model_checkpoint
                SET last_trained_row = %s
                WHERE id = 1
            """, (last_processed_row,))

            conn.commit()

            print("Training checkpoint updated successfully!")

            print("\nWaiting 60 seconds before next check...\n")
            time.sleep(60)

    except Exception as e:
        print("\nERROR in training service:", e)
        print("Retrying in 60 seconds...\n")
        time.sleep(60)