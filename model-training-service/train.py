import pandas as pd
import psycopg2
import os
import joblib
import xgboost as xgb

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

# -------------------------------------
# 1. Connect to PostgreSQL (container-safe)
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

# -------------------------------------
# 2. Clean + Convert Date
# -------------------------------------

df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
df = df.dropna(subset=["order_date"])

# -------------------------------------
# 3. Create Customer-Level Dataset
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
# 4. Behavioural Feature Engineering
# -------------------------------------

# Recency
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

# Days between orders
customer_df["days_between_orders"] = (
    customer_df["customer_age_days"] / customer_df["total_orders"]
)

# Discount dependency
customer_df["discount_dependency"] = customer_df["avg_discount"] * customer_df["total_orders"]

# Profit ratio
customer_df["profit_ratio"] = customer_df["total_profit"] / customer_df["total_sales"]

# Behaviour consistency
customer_df["sales_per_order"] = customer_df["total_sales"] / customer_df["total_orders"]
customer_df["quantity_per_order"] = customer_df["total_quantity"] / customer_df["total_orders"]

# Recency ratio
customer_df["recency_ratio"] = customer_df["last_order_days"] / customer_df["customer_age_days"]

customer_df = customer_df.fillna(0)

print("Customer dataset shape:", customer_df.shape)

# -------------------------------------
# 5. Create churn label (robust version)
# -------------------------------------

# Dynamic threshold (based on data)
threshold = customer_df["last_order_days"].quantile(0.75)

print("Churn threshold:", threshold)

customer_df["churn"] = (customer_df["last_order_days"] > threshold).astype(int)

# Check distribution
print("\nChurn distribution:")
print(customer_df["churn"].value_counts())

# If still only one class, force fallback logic
if len(customer_df["churn"].unique()) < 2:
    print("\nFallback churn logic applied")

    customer_df["churn"] = (
        (customer_df["last_order_days"] > 10) &
        (customer_df["total_orders"] < customer_df["total_orders"].median())
    ).astype(int)

    print("\nNew churn distribution:")
    print(customer_df["churn"].value_counts())


# -------------------------------------
# 6. Features and Target
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

# Final safety check
if len(y.unique()) < 2:
    print("\nERROR: Still only one class present. Add more data.")
    exit()


# -------------------------------------
# 7. Train-test split (VERY IMPORTANT FIX)
# -------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y     # <-- this prevents the issue you are facing
)

print("\nTrain class distribution:")
print(y_train.value_counts())

print("\nTest class distribution:")
print(y_test.value_counts())



# -------------------------------------
# 8. Train XGBoost Model
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
# 9. Evaluation
# -------------------------------------

pred = model.predict(X_test)
prob = model.predict_proba(X_test)[:, 1]

print("F1 Score:", f1_score(y_test, pred))
print("ROC-AUC:", roc_auc_score(y_test, prob))

# -------------------------------------
# 10. Save Model
# -------------------------------------

os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/churn_model.pkl")

print("Model saved successfully!")