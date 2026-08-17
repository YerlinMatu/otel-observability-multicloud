#!/usr/bin/env bash
set -euo pipefail
mkdir -p benchmark/results
run_case() {
  local name="$1" disabled="$2"
  OTEL_SDK_DISABLED="$disabled" docker compose up --build -d service-a service-b
  sleep 8
  docker run --rm -e BASE_URL=http://host.docker.internal:8080 \
    -e DURATION=60s -e VUS=20 \
    -v "$PWD/benchmark/load.js:/scripts/load.js:ro" \
    -v "$PWD/benchmark/results:/results" \
    grafana/k6:0.56.0 run --summary-export "/results/${name}.json" /scripts/load.js \
    > "benchmark/results/${name}-k6.txt" 2>&1 &
  local k6_pid=$!
  : > "benchmark/results/${name}-resources.csv"
  while kill -0 "$k6_pid" 2>/dev/null; do
    docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}}' \
      otel-observability-lab-service-a-1 otel-observability-lab-service-b-1 \
      >> "benchmark/results/${name}-resources.csv"
    sleep 2
  done
  wait "$k6_pid"
  tail -30 "benchmark/results/${name}-k6.txt"
}
run_case baseline true
run_case otel false
echo "Resultados en benchmark/results. Repita tres veces y reporte medianas."
