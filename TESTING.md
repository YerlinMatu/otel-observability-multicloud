# Validación realizada

Fecha: 2026-08-17. Entorno: macOS arm64, Python 3.13 y OpenTelemetry Collector Contrib 0.132.0.

## Prueba funcional local sin Docker

Se iniciaron ambos servicios con las dependencias declaradas y un receptor OTLP gRPC de prueba. La solicitud `GET /orders/e2e-final` devolvió HTTP 200 y produjo:

- Un único `trace_id` de negocio propagado entre `service-a` y `service-b`.
- 12 spans dentro de esa traza.
- Spans custom `validate-order` y `calculate-price`.
- Spans HTTP de servidor y cliente.
- Spans SQLite `CREATE`, `INSERT` y `SELECT`.
- Cuatro logs OTLP correlacionados; ambos servicios presentes.
- Métricas `business_orders_total` y `http_server_duration_milliseconds` en los endpoints Prometheus.

La prueba detectó y permitió corregir el uso de `connection.execute`, que el instrumentador SQLite no interceptaba en el runtime probado.

## Validaciones de configuración

- Las configuraciones local, GCP, AWS y la incluida en Helm pasan `otelcol-contrib validate` 0.132.0.
- El chart GKE pasa `helm lint` y `helm template` con Helm 3.18.6.
- Terraform AWS pasa `terraform init -backend=false` y `terraform validate` con Terraform 1.13.3 y AWS provider 5.100.0.
- Las variantes `OTEL_SDK_DISABLED=true/false` aparecen en ambos contenedores al renderizar Compose.
- El JSON del dashboard es válido y su regex extrae un `trace_id` de una línea real de log.

## Limitaciones

El stack Docker completo fue ejecutado y verificado: siete contenedores activos, cuatro targets Prometheus UP, trazas Jaeger de 12 spans, logs Loki correlacionados y dashboard Grafana de seis paneles. El benchmark de 60 segundos por condición obtuvo p99 545.23 ms sin OTel y 559.52 ms con OTel. No se desplegó en GCP/AWS porque requiere credenciales autorizadas y puede generar costos; la IaC sí fue validada.
