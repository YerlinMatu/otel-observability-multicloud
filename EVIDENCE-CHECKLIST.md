# Lista de evidencias

1. [COMPLETADO LOCAL] Jaeger: traza completa `service-a -> service-b -> sqlite`, con 12 spans.
2. [COMPLETADO LOCAL] Grafana: dashboard con los 6 paneles cargados y tráfico activo.
3. [COMPLETADO LOCAL] Grafana Logs Drilldown: líneas JSON con `trace_id` y `span_id`.
4. [COMPLETADO LOCAL] Prometheus: cuatro targets en estado UP.
5. GKE: `kubectl get pods,svc -n observability` y logs del Collector.
6. ECS: servicios/tareas HEALTHY y grupo de CloudWatch Logs.
7. [COMPLETADO LOCAL] k6: baseline y OTel; `docker stats` para CPU y memoria.

Las capturas locales están en `report/evidence/`. Los puntos GKE/ECS continúan pendientes porque requieren cuentas cloud autorizadas.
