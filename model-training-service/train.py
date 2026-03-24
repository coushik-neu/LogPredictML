import pandas as pd
import psycopg2
import os
import joblib
import xgboost as xgb
import time

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

print("ML Training Service Started...")

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

        if rows_since_last_training < 5000:
            print("Not enough new data. Waiting 60 seconds...")
            time.sleep(60)
            continue

        print("\nRetraining model...")

        # -------------------------------------
        # 3. Load data
        # -------------------------------------

        query = "SELECT * FROM sales_orders;"
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
        # 6. Behavioural Feature Engineering
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

        threshold = customer_df["last_order_days"].quantile(0.75)
        print("Churn threshold:", threshold)

        customer_df["churn"] = (customer_df["last_order_days"] > threshold).astype(int)

        print("\nChurn distribution:")
        print(customer_df["churn"].value_counts())

        # Fallback if only one class
        if len(customer_df["churn"].unique()) < 2:
            print("\nFallback churn logic applied")

            customer_df["churn"] = (
                (customer_df["last_order_days"] > 10) &
                (customer_df["total_orders"] < customer_df["total_orders"].median())
            ).astype(int)

            print("\nNew churn distribution:")
            print(customer_df["churn"].value_counts())

        # -------------------------------------
        # 8. Features and Target
        # -------------------------------------

        X = customer_df[
            [
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
        ]

        y = customer_df["churn"]

        if len(y.unique()) < 2:
            print("\nERROR: Only one class present. Waiting for more data.")
            time.sleep(60)
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

        print("\nTrain class distribution:")
        print(y_train.value_counts())

        print("\nTest class distribution:")
        print(y_test.value_counts())

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

        # -------------------------------------
        # 12. Save Model to shared Docker volume
        # -------------------------------------

        MODEL_PATH = "/models/churn_model.pkl"

        joblib.dump(model, MODEL_PATH)

        print("\nModel saved to shared volume:", MODEL_PATH)

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

        # -------------------------------------
        # 14. Wait before next cycle
        # -------------------------------------

        print("\nWaiting 60 seconds before next check...\n")
        time.sleep(60)

    except Exception as e:
        print("\nERROR in training service:", e)
        print("Retrying in 60 seconds...\n")
        time.sleep(60)