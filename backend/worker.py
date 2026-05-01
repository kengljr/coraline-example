import pika
import json
import psycopg2

def get_conn():
    return psycopg2.connect(
        host="postgres_db",
        database="app_database",
        user="postgres",
        password="postgres",
        port=5432
    )

def callback(ch, method, properties, body):
    data = json.loads(body)

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO user_information (full_name, email, phone, city, country)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING;
            """,
            (
                data.get("full_name"),
                data.get("email"),
                data.get("phone"),
                data.get("city"),
                data.get("country"),
            )
        )
        conn.commit()
        print("Inserted:", data.get("email"))

    except Exception as e:
        print("Error:", e)

    finally:
        cur.close()
        conn.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)


connection = pika.BlockingConnection(
    pika.ConnectionParameters('rabbitmq')
)
channel = connection.channel()

channel.queue_declare(queue='user_queue', durable=True)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='user_queue', on_message_callback=callback)

print("Worker started...")
channel.start_consuming()