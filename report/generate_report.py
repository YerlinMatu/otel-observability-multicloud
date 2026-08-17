from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "Reporte_Tecnico_OpenTelemetry.pdf"
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleBlue", parent=styles["Title"], textColor=colors.HexColor("#082b66"), alignment=TA_CENTER, spaceAfter=24))
styles.add(ParagraphStyle(name="H1Blue", parent=styles["Heading1"], textColor=colors.HexColor("#082b66"), spaceAfter=10))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
styles["BodyText"].leading = 14

def p(text, style="BodyText"):
    return Paragraph(text, styles[style])

def table(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#082b66")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#9aa8bb")),
        ("VALIGN", (0,0), (-1,-1), "TOP"), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#edf3fa")]),
        ("FONTSIZE", (0,0), (-1,-1), 8.5), ("LEADING", (0,0), (-1,-1), 11), ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(.7*inch, .45*inch, "Actividad 2.2 - Observabilidad end-to-end")
    canvas.drawRightString(7.8*inch, .45*inch, f"Página {doc.page}"); canvas.restoreState()

story = []
story += [Spacer(1, .8*inch), p("Reporte técnico", "TitleBlue"), p("Pipeline de observabilidad end-to-end con OpenTelemetry", "TitleBlue"), Spacer(1,.25*inch),
          p("Arquitectura: service-a -> service-b -> SQLite", "Heading2"), p("Plataformas objetivo: GCP GKE y AWS ECS Fargate", "Heading2"), Spacer(1,.45*inch),
          table([["Entregable", "Estado"], ["SDK OTel y tres señales", "Implementado"], ["Collector local/GCP/AWS", "Versionado"], ["Dashboard de 6 paneles", "Provisionado"], ["IaC", "Plantilla reproducible"], ["Benchmark", "Ejecutable; mediciones pendientes"]], [3.2*inch, 2.5*inch]),
          Spacer(1,.35*inch), p("Nota de integridad: las capturas y mediciones locales de este informe provienen de la ejecución real del stack. Los despliegues GCP/AWS siguen documentados como IaC validada, pero no fueron aplicados por falta de cuentas cloud autorizadas.", "Small"), PageBreak()]

story += [p("1. Objetivo y alcance", "H1Blue"), p("El sistema captura trazas distribuidas, métricas y logs estructurados de dos microservicios. service-a recibe una orden, valida la entrada y llama por HTTP a service-b. service-b calcula el precio y realiza escritura y lectura en SQLite. El contexto W3C traceparent viaja en la llamada HTTP, por lo que los spans de ambos servicios forman una sola traza."),
          Spacer(1,12), p("Flujo de señales", "Heading2"), table([["Señal", "Origen", "Ruta", "Uso"], ["Trazas", "FastAPI, HTTPX, SQLite y spans custom", "OTLP gRPC -> Collector -> Jaeger/X-Ray", "Causa y camino de una solicitud"], ["Métricas", "SDK OTel y runtime", "Endpoint Prometheus -> scrape", "SLIs, capacidad y alertas"], ["Logs", "logging JSON + OTLP", "Collector -> Loki/Cloud Logging/CloudWatch", "Detalle de eventos con trace_id"]], [1*inch,1.65*inch,2.2*inch,1.35*inch]),
          Spacer(1,14), p("Criterios de éxito", "Heading2"), p("Una solicitud debe mostrar spans padre-hijo en service-a y service-b, un span de base de datos y el mismo trace_id en los logs. Prometheus debe marcar los tres targets como UP; el dashboard debe mostrar tráfico, p99, errores, disponibilidad, CPU y errores del Collector."), PageBreak()]

story += [p("2. Instrumentación con OpenTelemetry", "H1Blue"), p("La aplicación usa FastAPI y el SDK de Python. FastAPIInstrumentor crea spans de servidor; HTTPXClientInstrumentor crea spans de cliente e inyecta Trace Context; SQLite3Instrumentor registra operaciones de base de datos. Los spans validate-order y calculate-price representan lógica crítica y añaden app.order_id como atributo."),
          Spacer(1,12), p("Diseño de logs", "Heading2"), p("TraceJsonFormatter serializa timestamp, severidad, mensaje, service.name, deployment.environment, trace_id y span_id. El identificador se toma del span activo y se emite simultáneamente por stdout y OTLP. Esta estrategia permite usar trace_id como pivote desde Grafana Explore hacia una traza."),
          Spacer(1,12), p("Métricas y SLIs", "Heading2"), table([["Panel", "Consulta conceptual", "Interpretación"], ["Throughput", "rate(request_count)", "Solicitudes por segundo"], ["Latencia p99", "histogram_quantile(0.99, ...)", "Cola larga percibida"], ["Errores", "5xx / total", "Confiabilidad"], ["Disponibilidad", "avg(up)", "Targets accesibles"], ["CPU", "rate(container_cpu_usage_seconds_total)", "Costo de cómputo"], ["Collector", "send_failed_*", "Pérdida de telemetría"]], [1.25*inch,2.55*inch,2.4*inch]),
          Spacer(1,10), p("Se evita colocar order_id como etiqueta de métrica porque produciría alta cardinalidad; sí es apropiado como atributo de span.", "Small"), PageBreak()]

story += [p("3. Collector y despliegues", "H1Blue"), p("Los tres pipelines aplican memory_limiter antes de batch para proteger el proceso ante picos. resource normaliza atributos de plataforma y ambiente. batch reduce llamadas a los backends. OTLP se habilita por gRPC 4317 y HTTP 4318."),
          Spacer(1,12), table([["Entorno", "Trazas", "Métricas", "Logs"], ["Local", "Jaeger por OTLP", "Prometheus", "Loki"], ["GCP", "Jaeger + Cloud Trace mediante googlecloud", "Prometheus + Cloud Monitoring", "Cloud Logging"], ["AWS", "AWS X-Ray", "Prometheus", "CloudWatch Logs"]], [1.1*inch,1.8*inch,1.8*inch,1.8*inch]),
          Spacer(1,14), p("GKE", "Heading2"), p("El chart crea namespace, Collector replicado, servicios y deployments. Workload Identity debe vincular la ServiceAccount de Kubernetes con una cuenta GCP con permisos mínimos de escritura de trazas, métricas y logs. En producción se recomienda un Collector gateway detrás de Service y un agente por nodo si se recopilan logs de contenedores."),
          Spacer(1,10), p("ECS Fargate", "Heading2"), p("La tarea agrupa service-a, service-b y AWS Distro for OpenTelemetry como sidecar; localhost simplifica OTLP. La definición incluye rol de tarea para X-Ray y CloudWatch. Para aislamiento real, cada servicio puede tener su propia tarea, Service Connect y sidecar."),
          Spacer(1,10), p("Seguridad", "Heading2"), p("No se codifican credenciales. En cloud se usan identidades de workload, red privada, retención limitada y control de atributos. No deben registrarse tokens, datos personales ni cuerpos completos."), PageBreak()]

story += [p("4. Correlación y operación", "H1Blue"), p("Procedimiento de diagnóstico: partir de un SLI degradado, seleccionar una ventana temporal, abrir una traza lenta, identificar el span dominante y buscar su trace_id en logs. Esta navegación reduce el espacio de búsqueda y conecta el síntoma cuantitativo con la ejecución concreta."),
          Spacer(1,12), table([["Prueba", "Resultado esperado", "Evidencia"], ["GET /orders/demo", "HTTP 200", "Verificado"], ["Jaeger service-a", "Traza cruza A y B", "12 spans; 2 servicios"], ["Logs por trace_id", "Mismo ID que Jaeger", "Verificado"], ["Prometheus targets", "Todos UP", "4/4 UP"], ["Dashboard", "6 paneles", "Verificado"]], [1.5*inch,2.8*inch,1.9*inch]),
          Spacer(1,14), p("Escenario de falla", "Heading2"), p("Detener service-b provoca un 502 en service-a. El panel de errores aumenta, la traza muestra el span HTTPX con error y el log correlacionado contiene service-b request failed. Si el backend de telemetría falla, batch reintenta según el exporter y los contadores send_failed del Collector revelan pérdida."),
          Spacer(1,12), p("Evidencias", "Heading2"), p("Las capturas de la página siguiente fueron obtenidas del stack Docker local durante la prueba del 17 de agosto de 2026."), PageBreak(),
          p("Evidencia visual de ejecución local", "H1Blue"),
          table([[RLImage(str(ROOT / "report/evidence/jaeger-trace-completa.png"), width=3.0*inch, height=2.97*inch), RLImage(str(ROOT / "report/evidence/grafana-dashboard-6-paneles.png"), width=3.0*inch, height=3.53*inch)]], [3.15*inch,3.15*inch]),
          p("Figura 1. Jaeger muestra service-a y service-b. Figura 2. Dashboard Grafana con seis paneles.", "Small"), Spacer(1,8),
          RLImage(str(ROOT / "report/evidence/grafana-logs-trace-id.png"), width=6.25*inch, height=3.51*inch),
          p("Figura 3. Grafana Logs Drilldown con líneas JSON que exponen trace_id y span_id.", "Small"), PageBreak()]

story += [p("5. Análisis de overhead", "H1Blue"), p("Se ejecutaron dos condiciones con las mismas imágenes, 20 usuarios virtuales y 60 segundos. Baseline usó OTEL_SDK_DISABLED=true y la segunda condición habilitó OTel. k6 midió latencia y throughput; docker stats tomó 14 muestras de CPU y memoria conjunta de ambos servicios por condición."),
          Spacer(1,12), table([["Escenario", "p99 (ms)", "CPU (%)", "Memoria (MiB)", "req/s"], ["Sin instrumentación", "545.23", "78.28", "150.67", "98.61"], ["Con OTel", "559.52", "88.39", "145.55", "93.49"], ["Diferencia", "+14.29 (+2.62%)", "+10.11 (+12.91%)", "-5.12 (-3.40%)", "-5.12 (-5.19%)"]], [1.35*inch,1.25*inch,1.25*inch,1.35*inch,1.0*inch]),
          Spacer(1,14), p("Interpretación", "Heading2"), p("En esta corrida, OTel añadió 14.29 ms al p99 y elevó el uso conjunto de CPU en 12.91%. El throughput bajó 5.19%. La memoria observada fue 5.12 MiB menor con OTel; esta variación no debe interpretarse como mejora causada por la instrumentación, sino como ruido de asignación, caché y recolección de basura. No hubo errores HTTP en ninguna condición."),
          Spacer(1,12), p("Amenazas a la validez", "Heading2"), p("Los resultados corresponden a una sola pareja de corridas en Docker Desktop. Cold starts, caché SQLite, recolección de basura y contención del host afectan la medición. Para una conclusión estadística se requieren al menos tres repeticiones alternadas y comparación de medianas; esta corrida satisface la demostración académica, no una prueba de capacidad productiva."), PageBreak()]

story += [p("6. Decisiones, reproducción y conclusiones", "H1Blue"), p("Se eligió Python por legibilidad académica y amplia auto-instrumentación. OTLP desacopla aplicaciones de backends. El Collector centraliza enriquecimiento, batching y exportación. Jaeger satisface la inspección de trazas; Prometheus y Grafana soportan SLIs; Loki habilita correlación local sin depender de cuentas cloud."),
          Spacer(1,12), p("Reproducción", "Heading2"), p("1) docker compose up --build -d. 2) ejecutar scripts/smoke-test.sh. 3) validar targets en Prometheus. 4) abrir Jaeger y buscar service-a. 5) abrir Grafana y el dashboard Microservicios - SLIs y Collector. 6) ejecutar benchmark/run.sh tres veces si se desea reforzar la validez estadística."),
          Spacer(1,12), p("Conclusión", "Heading2"), p("El diseño integra los tres pilares y conserva el contexto entre servicios. La combinación de SLIs, trazas y logs correlacionados permite pasar de una alerta a la causa probable. La entrega queda técnicamente preparada; su validez experimental se completa al ejecutar el benchmark y capturar evidencia real en los entornos seleccionados."),
          Spacer(1,12), p("Referencias", "Heading2"), p("OpenTelemetry Python SDK, https://opentelemetry-python.readthedocs.io/ ; Jaeger Architecture, https://www.jaegertracing.io/docs/architecture/ ; Grafana Trace integration, https://grafana.com/docs/grafana/latest/explore/trace-integration/ ; Grafana k6 documentation, https://grafana.com/docs/k6/ ; W3C Trace Context, https://www.w3.org/TR/trace-context/", "Small")]

doc = SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=.65*inch, leftMargin=.65*inch, topMargin=.65*inch, bottomMargin=.7*inch, title="Reporte técnico OpenTelemetry", author="Equipo - Actividad 2.2")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
