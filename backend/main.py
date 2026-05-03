from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (    # ← เพิ่มทุกตัวที่ใช้
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)
from fastapi.responses import Response
import psycopg2
import csv
import io
import pika
import json
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Prometheus Metrics ───────────────────────────────────────────
UPLOAD_COUNTER = Counter(
    "upload_requests_total",
    "Total number of upload requests",
    ["status"]
)

UPLOAD_ROWS_COUNTER = Counter(
    "upload_rows_total",
    "Total number of CSV rows queued"
)

UPLOAD_DURATION = Histogram(
    "upload_duration_seconds",
    "Time spent processing upload",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

UPLOAD_FILE_SIZE = Histogram(
    "upload_file_size_bytes",
    "Size of uploaded CSV files in bytes",
    buckets=[1024, 10240, 102400, 1048576, 10485760]  # 1KB to 10MB
)
# ─────────────────────────────────────────────────────────────────

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
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
    start_time = time.time()
    try:
        content = await file.read()
        
        # Track file size
        UPLOAD_FILE_SIZE.observe(len(content))
        
        text = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(text))
        
        count = 0
        for row in csv_reader:
            publish_message(row)
            count += 1

        # Track success metrics
        UPLOAD_COUNTER.labels(status="success").inc()
        UPLOAD_ROWS_COUNTER.inc(count)

        return {"message": "Upload queued", "total": count}

    except Exception as e:
        # Track failed metrics
        UPLOAD_COUNTER.labels(status="failed").inc()
        raise e

    finally:
        # Always record duration
        UPLOAD_DURATION.observe(time.time() - start_time)