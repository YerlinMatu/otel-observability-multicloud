import logging
import os
import sqlite3

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

from telemetry import configure_telemetry

app = FastAPI(title="service-b")
configure_telemetry(app)
tracer = trace.get_tracer("service-b.business")
log = logging.getLogger("service-b")


def connection():
    db = sqlite3.connect(os.getenv("DB_PATH", "/tmp/orders.db"))
    # Explicitly wrap each connection. This keeps DB auto-spans reliable on
    # Python runtimes where monkey-patching sqlite3.connect is ineffective.
    db = SQLite3Instrumentor().instrument_connection(db)
    db.cursor().execute("CREATE TABLE IF NOT EXISTS prices (order_id TEXT PRIMARY KEY, amount REAL)")
    return db


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/price/{order_id}")
def price(order_id: str):
    with tracer.start_as_current_span("calculate-price") as span:
        span.set_attribute("app.order_id", order_id)
        amount = round(10 + (sum(map(ord, order_id)) % 900) / 10, 2)
        with connection() as db:
            cursor = db.cursor()
            cursor.execute("INSERT OR REPLACE INTO prices VALUES (?, ?)", (order_id, amount))
            cursor.execute("SELECT amount FROM prices WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
        log.info("price calculated: %s", order_id)
        return {"amount": row[0], "currency": "USD"}
