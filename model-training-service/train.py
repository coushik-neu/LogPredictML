import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import joblib
import os

# -------------------------------------
# 1. Connect to Postgres (container-safe)
# -------------------------------------

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

query = "SELECT * FROM sales_orders;"
df = pd.read_sql(query, conn)

print("Data Loaded:", df.shape)
print(df.head())
# -------------------------------------
# 2. Convert date column
# -------------------------------------

df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
df = df.dropna(subset=["order_date"])

# -------------------------------------
# 3. Create customer-level dataset (RFM-style features)
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
# 4. Create behavioural features
# -------------------------------------

# Recency (used only to create target)
customer_df["last_order_days"] = (today - customer_df["last_order_date"]).dt.days

# Customer lifetime
customer_df["customer_age_days"] = (
    customer_df["last_order_date"] - customer_df["first_order_date"]
).dt.days + 1

# Avg order value
customer_df["avg_order_value"] = customer_df["total_sales"] / customer_df["total_orders"]

# Profit per order
customer_df["profit_per_order"] = customer_df["total_profit"] / customer_df["total_orders"]

# Orders per month (activity level)
customer_df["orders_per_month"] = customer_df["total_orders"] / (customer_df["customer_age_days"] / 30)

print(customer_df.head())

# -------------------------------------
# 5. Create churn column
# -------------------------------------

customer_df["churn"] = customer_df["last_order_days"].apply(
    lambda x: 1 if x > 30 else 0
)

# -------------------------------------
# 6. Features and target (IMPORTANT: no leakage)
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
        "customer_age_days"
    ]
]

y = customer_df["churn"]

# -------------------------------------
# 6. Train-test split
# -------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------------------
# 7. Baseline model
# -------------------------------------

baseline = LogisticRegression()
baseline.fit(X_train, y_train)

pred = baseline.predict(X_test)

print("Baseline F1:", f1_score(y_test, pred))
print("Baseline ROC-AUC:", roc_auc_score(y_test, pred))

# -------------------------------------
# 8. XGBoost (main model)
# -------------------------------------

model = xgb.XGBClassifier()
model.fit(X_train, y_train)

pred = model.predict(X_test)

print("XGBoost F1:", f1_score(y_test, pred))
print("XGBoost ROC-AUC:", roc_auc_score(y_test, pred))

# -------------------------------------
# 9. Save model
# -------------------------------------

joblib.dump(model, "/models/churn_model.pkl")

print("Model Saved Successfully!")