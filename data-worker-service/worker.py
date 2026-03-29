import pika
import json
import time
import os
from sqlalchemy import create_engine, text

# ==========================================================
# ENV VARIABLES (safe defaults so container never crashes)
# ==========================================================

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")

POSTGRES_USER = os.getenv("DB_USER")
POSTGRES_PASSWORD = os.getenv("DB_PASSWORD")
POSTGRES_DB = os.getenv("DB_NAME")
POSTGRES_HOST = os.getenv("DB_HOST")
POSTGRES_PORT = os.getenv("DB_PORT")


DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# ==========================================================
# CONNECT TO POSTGRES (retry until DB is ready)
# ==========================================================

def connect_db():
    while True:
        try:
            print("Connecting to PostgreSQL...")
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Connected to PostgreSQL!")
            return engine
        except Exception as e:
            print(f"PostgreSQL not ready: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

engine = connect_db()

# ==========================================================
# CONNECT TO RABBITMQ (retry until ready)
# ==========================================================

def connect_rabbitmq():
    while True:
        try:
            print("Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            print("Connected to RabbitMQ!")
            return connection
        except Exception as e:
            print(f"RabbitMQ not ready: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

connection = connect_rabbitmq()
channel = connection.channel()

channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

print("Worker is ready. Waiting for messages...")

# ==========================================================
# INSERT FUNCTION
# ==========================================================

def insert_into_db(data):
    try:
        query = text("""
            INSERT INTO sales_orders (
                order_id, order_date, date_key,
                contact_name, country, city, region, subregion,
                customer, customer_id, industry, segment,
                product, license,
                sales, quantity, discount, profit
            )
            VALUES (
                :order_id, :order_date, :date_key,
                :contact_name, :country, :city, :region, :subregion,
                :customer, :customer_id, :industry, :segment,
                :product, :license,
                :sales, :quantity, :discount, :profit
            )
        """)

        with engine.begin() as conn:
            conn.execute(query, data)

        print(f"Inserted into DB: {data['order_id']}")

    except Exception as e:
        print(f"DB insert failed: {e}")

# ==========================================================
# MESSAGE CONSUMER
# ==========================================================

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)

        print(f"Received message: {data['order_id']}")

        insert_into_db(data)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error processing message: {e}")

# process 1 message at a time (safe for heavy load)
channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)

channel.start_consuming()