# Lista de evidencias

1. [COMPLETADO LOCAL] Jaeger: traza completa `service-a -> service-b -> sqlite`, con 12 spans.
2. [COMPLETADO LOCAL] Grafana: dashboard con los 6 paneles cargados y tráfico activo.
3. [COMPLETADO LOCAL] Grafana Logs Drilldown: líneas JSON con `trace_id` y `span_id`.
4. [COMPLETADO LOCAL] Prometheus: cuatro targets en estado UP.
5. [COMPLETADO GCP] GKE: 8 pods Running, Jaeger, Grafana (6 paneles) y Cloud Logging con evidencia real. Ver `CLOUD-EVIDENCE.md`.
6. [COMPLETADO AWS] ECS Fargate: tarea RUNNING, X-Ray con traza distribuida completa, CloudWatch Logs con `trace_id` y CloudWatch Metrics (namespace `ObservabilityLab`) con datos reales. Ver `AWS-EVIDENCE.md`.
7. [COMPLETADO LOCAL] k6: baseline y OTel; `docker stats` para CPU y memoria.

Las capturas están en `report/evidence/` (prefijo `gcp-` para GCP GKE, `aws-ecs-` para AWS ECS Fargate, sin prefijo para el stack local). Los tres entornos (local, GCP GKE, AWS ECS Fargate) fueron ejecutados realmente; los clústeres y servicios cloud se destruyeron después de capturar evidencia para no generar costos.
