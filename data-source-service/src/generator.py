import random
import time
from datetime import datetime, timedelta
from threading import Thread

generator_running = False

# -------------------------------------
# Order ID generator
# -------------------------------------

def generate_order_id():
    year = datetime.now().year
    random_num = random.randint(100000, 999999)
    return f"EMEA-{year}-{random_num}"


# -------------------------------------
# Generate NEW customer
# -------------------------------------

def generate_new_customer(df):
    row = df.sample(1).iloc[0]

    new_customer_id = random.randint(2000, 9000)

    return {
        "contact_name": row["Contact Name"],
        "country": row["Country"],
        "city": row["City"],
        "customer": row["Customer"],
        "customer_id": new_customer_id,
        "industry": row["Industry"],
        "segment": row["Segment"],
    }


# -------------------------------------
# Generate order for EXISTING customer
# -------------------------------------

def generate_existing_customer_order(df):
    row = df.sample(1).iloc[0]

    return {
        "contact_name": row["Contact Name"],
        "country": row["Country"],
        "city": row["City"],
        "customer": row["Customer"],
        "customer_id": row["Customer ID"],
        "industry": row["Industry"],
        "segment": row["Segment"],
    }

# -------------------------------------
# Region mapping (based on country)
# -------------------------------------

def get_region(country):
    europe = ["Germany", "France", "UK", "Italy", "Spain", "Netherlands", "Switzerland"]
    apac = ["India", "Japan", "China", "Singapore", "Australia"]
    america = ["USA", "Canada", "Brazil", "Mexico"]

    if country in europe:
        return "EMEA", "Europe"

    elif country in apac:
        return "APAC", "Asia Pacific"

    elif country in america:
        return "AMER", "North America"

    return "OTHER", "Unknown"

# -------------------------------------
# Main generator logic (SMART VERSION)
# -------------------------------------
def generate_new_sale(df):

    today = datetime.now()

    # -------------------------------------
    # Decide customer behaviour type
    # -------------------------------------

    r = random.random()

    # 50% new customers
    if r < 0.50:
        base = generate_new_customer(df)

        # new customers usually order recently
        order_date = today - timedelta(days=random.randint(0, 5))

    # 25% normal customers
    elif r < 0.75:
        base = generate_existing_customer_order(df)

        # normal customers order within last 15 days
        order_date = today - timedelta(days=random.randint(0, 15))

    # 15% loyal customers (very active)
    elif r < 0.90:
        base = generate_existing_customer_order(df)

        # loyal customers may even have future orders scheduled
        order_date = today + timedelta(days=random.randint(1, 7))

    # 10% risky customers (simulate churn behaviour)
    else:
        base = generate_existing_customer_order(df)

        # risky customers ordered long ago
        order_date = today - timedelta(days=random.randint(20, 60))

    # -------------------------------------
    # Product behaviour
    # -------------------------------------

    product_row = df.sample(1).iloc[0]

    region, subregion = get_region(base["country"])

    # order_date can already be past OR future from your logic
    order_date_str = order_date.strftime("%Y-%m-%d")

    # date_key must always match the same date (even if future)
    date_key = int(order_date.strftime("%Y%m%d"))

    new_row = {
        "order_id": generate_order_id(),
        "order_date": order_date_str,
        "date_key": date_key,

        "contact_name": base["contact_name"],
        "country": base["country"],
        "city": base["city"],
        "region": region,
        "subregion": subregion,

        "customer": base["customer"],
        "customer_id": base["customer_id"],
        "industry": base["industry"],
        "segment": base["segment"],

        "product": product_row["Product"],
        "license": product_row["License"],

        "sales": round(product_row["Sales"] + random.uniform(-30, 30), 2),
        "quantity": max(1, int(product_row["Quantity"] + random.randint(-1, 2))),
        "discount": round(max(0, product_row["Discount"] + random.uniform(-0.1, 0.1)), 2),
        "profit": round(product_row["Profit"] + random.uniform(-20, 20), 2),
    }
        
    return new_row


# -------------------------------------
# Generator loop
# -------------------------------------

def _run_generator(df, publish_sale):
    global generator_running

    while generator_running:
        new_row = generate_new_sale(df)

        publish_sale(new_row)

        print("Inserted new generated sale:", new_row["customer_id"])

        time.sleep(1)


# -------------------------------------
# Start / Stop functions
# -------------------------------------

def start_generator(df, publish_sale):
    global generator_running

    if not generator_running:
        generator_running = True
        Thread(target=_run_generator, args=(df, publish_sale)).start()


def stop_generator():
    global generator_running
    generator_running = False