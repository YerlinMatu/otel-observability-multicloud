import logging
import os
import time

import httpx
from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from telemetry import configure_telemetry

app = FastAPI(title="service-a")
configure_telemetry(app)
HTTPXClientInstrumentor().instrument()
tracer = trace.get_tracer("service-a.business")
meter = metrics.get_meter("orders")
orders = meter.create_counter("business.orders", description="Orders requested")
duration = meter.create_histogram("business.order.duration", unit="s")
log = logging.getLogger("service-a")


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/orders/{order_id}")
async def order(order_id: str):
    started = time.perf_counter()
    orders.add(1, {"operation": "get_order"})
    with tracer.start_as_current_span("validate-order") as span:
        span.set_attribute("app.order_id", order_id)
        if not order_id.strip():
            raise HTTPException(400, "order_id required")
        log.info("order validated: %s", order_id)
    url = f"{os.getenv('SERVICE_B_URL', 'http://localhost:8081')}/price/{order_id}"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        log.exception("service-b request failed")
        raise HTTPException(502, "pricing unavailable") from exc
    duration.record(time.perf_counter() - started, {"status": "ok"})
    log.info("order completed: %s", order_id)
    return {"order_id": order_id, **response.json()}

