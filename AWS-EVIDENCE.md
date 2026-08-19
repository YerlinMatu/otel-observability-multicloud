# Evidencia de ejecución en AWS ECS Fargate

Ejecución verificada el **17-18 de agosto de 2026** en la cuenta AWS `255191476203`, región `us-east-1` (N. Virginia), usando un clúster ECS Fargate temporal llamado `otel-lab`.

## Resultado

- Una tarea Fargate con 3 contenedores (`service-a`, `service-b`, `otel-collector` con la imagen de AWS Distro for OpenTelemetry) corriendo en estado `RUNNING` bajo el servicio ECS `otel-lab`, en subred pública con IP pública propia.
- 10 solicitudes HTTP exitosas ejecutadas sobre `service-a -> service-b -> SQLite` (`GET /orders/{order_id}`).
- AWS X-Ray recibió trazas distribuidas completas. Traza de referencia: `trace_id` OTel `e47a885c3d7cfecfe34b8d3e85632cd9`, equivalente en formato X-Ray `1-e47a885c-3d7cfecfe34b8d3e85632cd9`. El waterfall muestra `service-a` -> `validate-order` -> llamada HTTP a `service-b` -> `calculate-price` -> spans SQL `CREATE`/`INSERT`/`SELECT`, con el mapa de servicio correspondiente.
- CloudWatch Logs (log group `/otel/microservices`) recibió logs JSON estructurados de `service-a` y `service-b` con el mismo `trace_id`, `span_id`, `service.name` y `deployment.environment=aws-ecs`, confirmando la correlación log-traza.
- CloudWatch Metrics (namespace `ObservabilityLab`) recibió métricas reales: `business.orders`, `business.order.duration`, `http.server.duration`, `http.server.active_requests`, `http.client.duration`, `http.server.response.size`, con dimensiones `service.name`, `deployment.environment=aws-ecs` y `cloud.provider=aws`.

## Capturas

- [X-Ray: waterfall de la traza distribuida](report/evidence/aws-ecs-xray-trace-waterfall.png)
- [X-Ray: mapa de servicio](report/evidence/aws-ecs-xray-trace-map.png)
- [CloudWatch Logs: service-a con trace_id](report/evidence/aws-ecs-cloudwatch-logs-trace-id-a.png)
- [CloudWatch Logs: service-b con trace_id (mismo trace que X-Ray)](report/evidence/aws-ecs-cloudwatch-logs-trace-id-b.png)
- [CloudWatch Logs: stream completo de service-a](report/evidence/aws-ecs-cloudwatch-logs-service-a.png)
- [CloudWatch Metrics: business.order.duration](report/evidence/aws-ecs-cloudwatch-metrics-business-order-duration.png)

## Decisiones de diseño específicas de AWS

- **Métricas vía CloudWatch EMF, no Prometheus/Grafana adicional**: el exporter `awsemf` del Collector (`otel/collector-aws.yaml`) convierte las métricas OTLP en Embedded Metric Format y las publica directamente como métricas nativas de CloudWatch (namespace `ObservabilityLab`). Se prefirió sobre desplegar un Prometheus+Grafana adicional en ECS por ser más simple, más barato y más idiomático en Fargate.
- **Subredes públicas sin NAT Gateway**: las tareas usan `assign_public_ip=true` en lugar de una VPC privada con NAT Gateway, para evitar el costo (~USD 32/mes + tráfico) y la complejidad de red en un laboratorio académico temporal. El tráfico de entrada se restringe al puerto 8080 del security group.
- **Imagen compartida, comando por contenedor**: `services/Dockerfile` no define `CMD` (igual que en `docker-compose.yml`); el `command` de cada contenedor en el task definition de Terraform decide si corre `service_a:app` o `service_b:app`, permitiendo publicar una sola imagen a los dos repositorios ECR.

## Fallas reales encontradas y corregidas durante el despliegue

Documentar estas dos fallas es en sí mismo parte de la evidencia de un despliegue real (no simulado):

### 1. Crashloop por puerto de métricas duplicado

**Síntoma**: el servicio ECS reemplazaba tareas repetidamente (3 tareas distintas en ~2 minutos, eventos `"started 1 tasks"` seguidos). `aws ecs describe-tasks` sobre las tareas detenidas mostró `service-b` (ocasionalmente `service-a`) saliendo con `exitCode: 1`.

**Causa raíz**: `network_mode = "awsvpc"` hace que los 3 contenedores de una tarea Fargate compartan una única interfaz de red (equivalente a un Pod de Kubernetes), a diferencia de `docker-compose`, donde cada servicio tiene su propia red aislada. `telemetry.py` abre un servidor de métricas Prometheus en el puerto `METRICS_PORT` (default `9464`); como `service-a` y `service-b` no tenían el mismo puerto diferenciado en el task definition original, ambos intentaban abrir `9464` en la misma IP compartida y el segundo en arrancar fallaba con "Address already in use".

**Fix**: se agregó `METRICS_PORT=9465` explícito a `service-b` en `infra/aws/main.tf` (igual patrón que ya usaba `docker-compose.yml`).

### 2. Namespace de CloudWatch Metrics vacío

**Síntoma**: tras el primer despliegue exitoso (sin crashloop) y tráfico real generado, `aws cloudwatch list-metrics --namespace ObservabilityLab` devolvía una lista vacía.

**Causa raíz**: `telemetry.py` solo configuraba un `PrometheusMetricReader` (modelo *pull*): funciona en local/GCP porque Prometheus scrapea `/metrics` directamente en cada servicio, sin pasar por el Collector. Pero el pipeline de métricas del Collector en AWS (`awsemf` -> CloudWatch) solo recibe datos si algo se los empuja por OTLP, y CloudWatch no hace scraping — nada llegaba nunca al Collector.

**Fix**: se agregó un segundo `MetricReader` (`PeriodicExportingMetricReader` + `OTLPMetricExporter`, push cada 15s) en `services/telemetry.py`, sin remover el `PrometheusMetricReader` existente, para no afectar la evidencia ya capturada en local/GCP.

## Reproducibilidad

Las imágenes se publicaron temporalmente en dos repositorios ECR (`otel-lab/service-a`, `otel-lab/service-b`) y el despliegue se realizó con `infra/aws/main.tf` vía `terraform apply`. El clúster, el servicio, el task definition, el security group y el rol IAM se destruyeron (`terraform destroy`) inmediatamente después de recolectar la evidencia para detener cargos. Los manifiestos versionados permiten repetir el procedimiento con otra cuenta, región y tags de imagen; ver la sección "AWS ECS Fargate" del reporte técnico y el README para el procedimiento paso a paso.
