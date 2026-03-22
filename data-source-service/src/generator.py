import random
import time
from datetime import datetime
from threading import Thread

generator_running = False  

def generate_order_id():
    year = datetime.now().year
    random_num = random.randint(100000, 999999)
    return f"EMEA-{year}-{random_num}"


def generate_new_sale(df):

    row = df.sample(1).iloc[0]

    today = datetime.now()

    new_row = {
        "order_id": generate_order_id(),
        "order_date": today.strftime("%Y-%m-%d"),
        "contact_name": row["Contact Name"],
        "country": row["Country"],
        "city": row["City"],
        "customer": row["Customer"],
        "customer_id": row["Customer ID"],
        "industry": row["Industry"],
        "segment": row["Segment"],
        "product": row["Product"],
        "license": row["License"],
        "sales": round(row["Sales"] + random.uniform(-20, 20), 2),
        "quantity": max(1, int(row["Quantity"] + random.randint(-1, 1))),
        "discount": round(max(0, row["Discount"] + random.uniform(-0.05, 0.05)), 2),
        "profit": round(row["Profit"] + random.uniform(-10, 10), 2)
    }

    return new_row


# ------------------------------
# generator loop
# ------------------------------

def _run_generator(df, insert_sale):
    global generator_running

    while generator_running:
        new_row = generate_new_sale(df)

        insert_sale(new_row)

        print("Inserted new generated sale")

        time.sleep(5)


def start_generator(df, insert_sale):
    global generator_running

    if not generator_running:
        generator_running = True
        Thread(target=_run_generator, args=(df, insert_sale)).start()


def stop_generator():
    global generator_running
    generator_running = False