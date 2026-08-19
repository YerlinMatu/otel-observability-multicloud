# Laboratorio de observabilidad end-to-end con OpenTelemetry

Proyecto académico reproducible con dos microservicios Python (`service-a -> service-b -> SQLite`), métricas Prometheus, logs JSON correlacionados y trazas OTLP. Incluye demo local, configuraciones de Collector para GCP/AWS, IaC de referencia, dashboard Grafana y benchmark k6.

## Inicio rápido (demo evaluable)

Requisitos: Docker con Compose y 4 GB de RAM disponibles.

```bash
docker compose up --build -d
./scripts/smoke-test.sh
```

Interfaces:

| Recurso | URL |
|---|---|
| Aplicación | http://localhost:8080/orders/demo |
| Jaeger | http://localhost:16686 |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |
| Métricas A/B | http://localhost:9464/metrics / http://localhost:9465/metrics |

En Jaeger, seleccione `service-a` y abra una traza: debe contener el span HTTP entrante, `validate-order`, la llamada a `service-b`, `calculate-price` y el acceso SQLite. En Grafana use **Explore > Loki** y filtre `{service_name="service-a"} | json`; el campo `trace_id` permite saltar a Tempo/Jaeger según el datasource configurado.

## Estructura

- `services/`: instrumentación OTel automática (FastAPI, HTTPX, SQLite) y spans custom.
- `otel/`: Collector local, GCP y AWS.
- `observability/`: Prometheus, Loki y dashboard Grafana de seis paneles.
- `infra/gcp/`: Helm/Kubernetes para GKE.
- `infra/aws/`: Terraform para ECS Fargate (plantilla parametrizada).
- `benchmark/`: k6 y captura de CPU/memoria.
- `report/`: reporte técnico final, fuente del informe y evidencias visuales.

## Reporte técnico

El entregable académico final, con evidencia real de ejecución en Docker local, GCP GKE y AWS ECS Fargate, está disponible en:

- [`report/Reporte_Tecnico_OpenTelemetry_Actividad-2.2.pdf`](report/Reporte_Tecnico_OpenTelemetry_Actividad-2.2.pdf)
- [`report/Reporte_Tecnico_OpenTelemetry_Actividad-2.2.docx`](report/Reporte_Tecnico_OpenTelemetry_Actividad-2.2.docx)

## Tres señales y correlación

- **Trazas:** W3C Trace Context se propaga automáticamente por HTTP; OTLP llega al Collector.
- **Métricas:** cada servicio expone `/metrics` (Prometheus scrapea directo en local/GCP) y además empuja por OTLP al Collector cada 15s (necesario en AWS, donde CloudWatch EMF recibe lo que el Collector reenvía).
- **Logs:** JSON a stdout y OTLP; cada registro incluye `trace_id`, `span_id`, `service.name` y `deployment.environment`.

## Benchmark

```bash
./benchmark/run.sh
```

Ejecuta dos variantes con la misma imagen: `OTEL_SDK_DISABLED=true` y `false`. Los archivos salen en `benchmark/results/`. La corrida incluida (20 VUs, 60 s) midió p99 de 545.23 ms sin OTel y 559.52 ms con OTel (+2.62%), CPU conjunta +12.91% y 0% de errores. Repita al menos tres veces si necesita mayor validez estadística.

## Despliegue cloud

Las carpetas `infra/gcp` e `infra/aws` son reproducibles y ambas fueron desplegadas realmente en clústeres/servicios temporales (ver evidencia abajo). Requieren completar proyecto/región, red, repositorio de imágenes, credenciales e IAM antes de aplicar. Revise con `terraform validate`/`helm lint` antes de aplicar, y destruya los recursos (`terraform destroy`) apenas termine de capturar evidencia para no generar costos.

## Evidencias para entregar

Consulte [EVIDENCE-CHECKLIST.md](EVIDENCE-CHECKLIST.md). El repositorio incluye capturas reales del stack local, de una ejecución temporal en GCP GKE y de una ejecución temporal en AWS ECS Fargate dentro de `report/evidence/`.

La ejecución real en GCP GKE, sus verificaciones y capturas están documentadas en [CLOUD-EVIDENCE.md](CLOUD-EVIDENCE.md). La ejecución real en AWS ECS Fargate, incluyendo dos fallas encontradas y corregidas durante el despliegue, está documentada en [AWS-EVIDENCE.md](AWS-EVIDENCE.md).
