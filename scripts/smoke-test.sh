#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 1 20); do curl -fsS "http://localhost:8080/orders/demo-$i" >/dev/null; done
curl -fsS http://localhost:8080/healthz
curl -fsS http://localhost:8081/healthz
echo " Demo OK. Abra Jaeger y Grafana."

