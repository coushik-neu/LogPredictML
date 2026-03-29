import pandas as pd
import psycopg2
import os
import time, sys

# -----------------------------------
# Connect to Postgres
# -----------------------------------
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

while True:
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=5432
        )
        print("Connected to PostgreSQL!")
        break
    except Exception as e:
        print("PostgreSQL not ready, retrying in 3 seconds...")
        time.sleep(3)

cur = conn.cursor()

# -----------------------------------
# Check if data already exists
# -----------------------------------

cur.execute("SELECT COUNT(*) FROM sales_orders;")
count = cur.fetchone()[0]

if count > 0:
    print("Data already exists. Skipping insert.")
    cur.close()
    conn.close()
    exit()

print("Table empty. Loading CSV...")

# -----------------------------------
# Load CSV
# -----------------------------------

df = pd.read_csv("sales_data.csv")

df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

df = df.dropna()
df = df.drop_duplicates()

print(f"Inserting {len(df)} rows...")

# -----------------------------------
# Insert into DB
# -----------------------------------

insert_query = """
INSERT INTO sales_orders (
    order_id,
    order_date,
    date_key,
    contact_name,
    country,
    city,
    region,
    subregion,
    customer,
    customer_id,
    industry,
    segment,
    product,
    license,
    sales,
    quantity,
    discount,
    profit
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df.iterrows():
    cur.execute(insert_query, (
        row["Order ID"],
        row["Order Date"],
        row["Date Key"],
        row["Contact Name"],
        row["Country"],
        row["City"],
        row["Region"],
        row["Subregion"],
        row["Customer"],
        row["Customer ID"],
        row["Industry"],
        row["Segment"],
        row["Product"],
        row["License"],
        row["Sales"],
        row["Quantity"],
        row["Discount"],
        row["Profit"]
    ))

conn.commit()

print("Data inserted successfully!")

os.makedirs("/ready", exist_ok=True)
with open("/ready/data_loaded.flag", "w") as f:
    f.write("done")

print("Data ready flag created.")

cur.close()
conn.close()


sys.exit(0)