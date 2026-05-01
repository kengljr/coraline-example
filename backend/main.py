from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import csv
import io
import pika
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def publish_message(data):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('rabbitmq')  # docker service name
    )
    channel = connection.channel()

    channel.queue_declare(queue='user_queue', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key='user_queue',
        body=json.dumps(data),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )

    connection.close()

# 🔹 connect DB
def get_conn():
    return psycopg2.connect(
        host="postgres_db",          # docker service name
        database="app_database",
        user="postgres",
        password="postgres",
        port=5432
    )

# 🔹 GET users (ดึงจาก DB จริง)
@app.get("/users")
def get_users():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, full_name, email FROM user_information ORDER BY id DESC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {"id": r[0], "full_name": r[1], "email": r[2]}
        for r in rows
    ]


# 🔹 upload CSV แล้ว insert
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")

    csv_reader = csv.DictReader(io.StringIO(text))

    count = 0
    for row in csv_reader:
        publish_message(row)
        count += 1

    return {
        "message": "Upload queued",
        "total": count
    }