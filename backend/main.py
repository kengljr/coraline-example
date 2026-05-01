from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import csv
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    conn = get_conn()
    cur = conn.cursor()

    for row in csv_reader:
        cur.execute(
            """
            INSERT INTO user_information (full_name, email, phone, city, country)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING;
            """,
            (
                row.get("full_name"),
                row.get("email"),
                row.get("phone"),
                row.get("city"),
                row.get("country"),
            )
        )

    conn.commit()

    # 🔥 return data หลัง insert
    cur.execute("SELECT id, full_name, email FROM user_information ORDER BY id DESC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "message": "Upload success",
        "data": [
            {"id": r[0], "full_name": r[1], "email": r[2]}
            for r in rows
        ]
    }