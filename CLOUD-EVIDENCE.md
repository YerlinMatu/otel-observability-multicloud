# Evidencia de ejecución en GCP GKE

Ejecución verificada el **17 de agosto de 2026** en el proyecto académico `unisabana-kubernetes`, región `us-central1`, usando un clúster temporal GKE Autopilot llamado `otel-evidence`.

## Resultado

- Ocho pods en estado `Running`: `service-a`, `service-b`, dos réplicas de OTel Collector, Jaeger, Prometheus, Loki y Grafana.
- 70 solicitudes HTTP exitosas ejecutadas sobre `service-a -> service-b -> SQLite`.
- Jaeger recibió trazas distribuidas de 12 spans y dos servicios.
- La traza de evidencia `1cc2dbbec24fb00661a6f52e206bc38a` contiene HTTP entrante/saliente, `validate-order`, `calculate-price`, `CREATE`, `INSERT` y `SELECT`.
- Prometheus reportó `up` para `service-a`, `service-b` y ambas réplicas del Collector.
- Grafana mostró los seis paneles requeridos y disponibilidad del 100 %.
- Loki recibió logs JSON con `trace_id`, `span_id`, `service.name` y `deployment.environment=gcp-gke`.
- Cloud Logging recibió 40 eventos OTLP bajo `opentelemetry.io/collector-exported-log`, con enlaces nativos a Cloud Trace mediante `trace`.

## Capturas

- [Traza distribuida en Jaeger](report/evidence/gcp-gke-jaeger-trace.png)
- [Dashboard Grafana de seis paneles](report/evidence/gcp-gke-grafana-dashboard.png)
- [Logs en Grafana Explore con trace_id](report/evidence/gcp-gke-grafana-logs-trace-id.png)
- [Cloud Logging con correlación log-trace](report/evidence/gcp-cloud-logging-trace-correlation.png)

## Reproducibilidad

Las imágenes se publicaron temporalmente en Artifact Registry y el despliegue se realizó con el chart `infra/gcp`. El clúster y el repositorio de imágenes se eliminaron después de recolectar la evidencia para detener cargos. Los manifiestos versionados permiten repetir el procedimiento con otro proyecto, región y etiquetas de imagen.
