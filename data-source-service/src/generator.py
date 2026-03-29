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
# Main generator logic (SMART VERSION)
# -------------------------------------

def generate_new_sale(df):

    today = datetime.now()

    # Decide customer type
    r = random.random()

    # 60% new customers
    if r < 0.60:
        base = generate_new_customer(df)

    # 25% normal customers
    elif r < 0.85:
        base = generate_existing_customer_order(df)

    # 15% loyal customers (repeat customers more frequently)
    else:
        base = generate_existing_customer_order(df)

    # Pick random row for product behaviour
    product_row = df.sample(1).iloc[0]

    new_row = {
        "order_id": generate_order_id(),
        "order_date": today.strftime("%Y-%m-%d"),

        "contact_name": base["contact_name"],
        "country": base["country"],
        "city": base["city"],
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

def _run_generator(df, insert_sale):
    global generator_running

    while generator_running:
        new_row = generate_new_sale(df)

        insert_sale(new_row)

        print("Inserted new generated sale:", new_row["customer_id"])


# -------------------------------------
# Start / Stop functions
# -------------------------------------

def start_generator(df, insert_sale):
    global generator_running

    if not generator_running:
        generator_running = True
        Thread(target=_run_generator, args=(df, insert_sale)).start()


def stop_generator():
    global generator_running
    generator_running = False