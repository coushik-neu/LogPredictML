import json
import pika
import os
import time

# ----------------------------------------
# Environment variables (safe defaults)
# ----------------------------------------

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "sales_queue")

# ----------------------------------------
# Connect to RabbitMQ with retry
# ----------------------------------------

def connect_to_rabbitmq():
    while True:
        try:
            print("Connecting to RabbitMQ...")

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )

            print("Connected to RabbitMQ successfully!")
            return connection

        except Exception as e:
            print(f"Connection failed: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)


# ----------------------------------------
# Create connection + channel
# ----------------------------------------

connection = connect_to_rabbitmq()
channel = connection.channel()

# Make queue durable so messages survive container restarts
channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)


# ----------------------------------------
# Publish function
# ----------------------------------------
def publish_sale(data: dict):
    try:
        # Convert numpy values to normal Python types
        clean_data = {}

        for key, value in data.items():
            if hasattr(value, "item"):   # numpy.int64 / numpy.float64
                clean_data[key] = value.item()
            else:
                clean_data[key] = value

        message = json.dumps(clean_data)

        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2
            ),
        )


    except Exception as e:
        print(f"Failed to publish message: {e}")

