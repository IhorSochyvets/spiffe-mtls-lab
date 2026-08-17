import os

import psycopg
from fastapi import FastAPI


app = FastAPI(
    title="SPIFFE mTLS Lab Backend",
    version="1.0.0",
)


DB_HOST = os.getenv("DB_HOST", "database")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lab")
DB_USER = os.getenv("DB_USER", "lab")
DB_PASSWORD = os.getenv("DB_PASSWORD", "lab")


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


@app.get("/")
def root():

    return {
        "service": "backend",
        "status": "ok",
        "lab": "Lab 1",
        "transport": "HTTP",
        "mtls": False,
        "spiffe": False,
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/messages")
def get_messages():

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    message
                FROM messages
                ORDER BY id
                """
            )

            rows = cursor.fetchall()

    return {
        "database": DB_HOST,
        "tls": False,
        "messages": [
            {
                "id": row[0],
                "message": row[1],
            }
            for row in rows
        ],
    }