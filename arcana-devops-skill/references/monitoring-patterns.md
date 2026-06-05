# Monitoring & Observability Patterns

> DevOps Skill Reference

## Three Pillars of Observability

| Pillar | Tool | Purpose |
|--------|------|---------|
| Metrics | Prometheus + Grafana | Quantitative measurements over time |
| Logs | ELK Stack / Loki | Discrete event records |
| Traces | Jaeger / OpenTelemetry | Request flow across services |

## Prometheus Metrics Types

| Type | Use Case | Example |
|------|----------|---------|
| Counter | Monotonically increasing values | `http_requests_total` |
| Gauge | Values that go up and down | `active_connections` |
| Histogram | Distribution of values | `request_duration_seconds` |
| Summary | Pre-calculated quantiles | `request_duration_quantile` |

## Key Metrics (RED Method)

| Metric | Description | PromQL Example |
|--------|-------------|----------------|
| **R**ate | Request throughput | `rate(http_requests_total[5m])` |
| **E**rrors | Error percentage | `rate(http_errors_total[5m]) / rate(http_requests_total[5m])` |
| **D**uration | Response latency | `histogram_quantile(0.99, rate(http_duration_bucket[5m]))` |

## Key Metrics (USE Method for Infrastructure)

| Metric | Description |
|--------|-------------|
| **U**tilization | % of resource capacity used |
| **S**aturation | Queue depth / backlog |
| **E**rrors | Error count |

## Alert Rules Best Practices

### Alert Severity

| Severity | Action | Response Time |
|----------|--------|---------------|
| Critical | Page on-call, immediate action | < 5 min |
| Warning | Investigate during business hours | < 4 hours |
| Info | Review at next opportunity | Next business day |

### Alert Rules Examples

```yaml
groups:
  - name: app
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
```

## Grafana Dashboard Guidelines

### Recommended Panels

| Panel | Type | Purpose |
|-------|------|---------|
| Request Rate | Time series | Traffic overview |
| Error Rate | Stat / Gauge | Quick error visibility |
| Response Time | Time series | Latency distribution (p50/p95/p99) |
| CPU Usage | Gauge | Resource utilization |
| Memory Usage | Gauge | Resource utilization |
| Uptime | Stat | Service availability |

## Metrics by Framework

| Framework | Library | Endpoint |
|-----------|---------|----------|
| Spring Boot | Micrometer | `/actuator/prometheus` |
| Flask | prometheus_flask_instrumentator | `/metrics` |
| Express | prom-client | `/metrics` |
| React/Angular | Grafana Faro (RUM) | Browser SDK |

### Custom Application Metrics Examples

**Spring Boot (Micrometer):**
```java
@Component
public class OrderMetrics {
    private final Counter ordersTotal;
    private final Timer orderProcessingTime;

    public OrderMetrics(MeterRegistry registry) {
        this.ordersTotal = Counter.builder("orders_total")
            .description("Total orders processed")
            .tag("status", "completed")
            .register(registry);
        this.orderProcessingTime = Timer.builder("order_processing_seconds")
            .description("Order processing duration")
            .register(registry);
    }
}
```

**Flask (prometheus_flask_instrumentator):**
```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('app_request_duration_seconds', 'Request latency', ['endpoint'])

@app.after_request
def track_metrics(response):
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response
```

**Express (prom-client):**
```javascript
const client = require('prom-client');

const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5]
});

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();
  res.on('finish', () => end({ method: req.method, route: req.route?.path || req.path, status: res.statusCode }));
  next();
});
```

---

## Log Aggregation

### Architecture Options

| Stack | Components | Best For |
|-------|-----------|----------|
| **ELK** | Elasticsearch + Logstash + Kibana | Full-text search, complex queries |
| **EFK** | Elasticsearch + Fluentd + Kibana | K8s native (Fluentd DaemonSet) |
| **PLG** | Promtail + Loki + Grafana | Lightweight, label-based, pairs with Prometheus |

### Loki + Promtail (Recommended for Docker Compose)

```yaml
# docker-compose.monitoring.yml (add to infra)
services:
  loki:
    image: grafana/loki:3.0.0
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:3.0.0
    volumes:
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
```

### Structured Logging Format

All services should output JSON logs for machine parsing:

```json
{
  "timestamp": "2026-02-11T10:30:00.000Z",
  "level": "ERROR",
  "service": "api",
  "trace_id": "abc123",
  "message": "Database connection failed",
  "error": "ECONNREFUSED",
  "duration_ms": 5023
}
```

| Framework | Library |
|-----------|---------|
| Spring Boot | `logback-encoder` (net.logstash.logback) |
| Flask | `python-json-logger` |
| Express | `pino` or `winston` with JSON transport |

---

## Alerting Best Practices

### When to Page vs. Ticket

| Condition | Action | Channel |
|-----------|--------|---------|
| Service down (up == 0) | **Page** on-call | PagerDuty / OpsGenie |
| Error rate > 5% for 5 min | **Page** on-call | PagerDuty / OpsGenie |
| Error rate > 1% for 15 min | **Ticket** | Jira / GitHub Issue |
| Disk usage > 90% | **Page** on-call | PagerDuty / OpsGenie |
| Disk usage > 70% | **Ticket** | Jira / GitHub Issue |
| Response time p99 > 2s for 10 min | **Ticket** | Jira / GitHub Issue |
| Certificate expiry < 7 days | **Ticket** | Slack + Email |
| Certificate expiry < 1 day | **Page** on-call | PagerDuty / OpsGenie |

### Alert Fatigue Prevention

| Practice | Description |
|----------|-------------|
| Use `for` duration | Avoid alerting on transient spikes (e.g. `for: 5m`) |
| Group related alerts | AlertManager `group_by` to batch notifications |
| Route by severity | Critical → Page, Warning → Slack, Info → Dashboard only |
| Review alerts monthly | Remove alerts that never fire or always fire |
| Runbook links | Every alert annotation should include a runbook URL |

### AlertManager Routing Example

```yaml
route:
  receiver: 'slack-default'
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      repeat_interval: 15m
    - match:
        severity: warning
      receiver: 'slack-warnings'
```

---

## Alert on the Damaging Event, Not the Post-Remediation State (TESTED)

Anti-pattern from a real incident (2026-06-04): a disk watchdog pruned at ≥88%
and alerted only if usage was **still ≥95% after the prune**. During a build
storm the disk spiked to 100% three times in 45 minutes — corrupting docker's
network state — yet every prune pulled it back to ~90%, so **zero alerts were
sent** while the damage happened.

Rule: the alert condition must test the **pre-remediation spike** (the event
that causes damage), not the post-remediation residue (what's left after
self-healing). Self-heal and alert are separate concerns:

```bash
UP=$(used_pct)                       # measure BEFORE remediation
[ "$UP" -ge 95 ] && add_alert "..."  # the spike itself is the incident
[ "$UP" -ge 88 ] && remediate        # then self-heal
# (post-remediation check is a SECOND alert: "self-heal is losing")
```

Dedup tip: keep dynamic numbers out of the alert text so the dedup hash stays
stable (otherwise each tick's different % defeats max-1-per-N-hours dedup).

## Disk-Pressure Defense in Depth (CI build host, TESTED)

Per-build cleanup inside pipelines races concurrent builds (a prune can delete
another build's image between tag and use). Move cleanup out of the build path
into independent layers:

| layer | cadence | scope |
|---|---|---|
| age-based image GC | */20 min | `*:build-N` tags older than 6h (age, not keep-N — multibranch shares one tag space, keep-N kills in-progress PR builds) |
| global cleanup | nightly off-peak | registry tag+blob GC, `image prune -a --filter until=6h`, builder/volume prune |
| watchdog | */15 min | self-heal prune at ≥88%, alert at ≥95% pre-prune |

Run the watchdog from a **different disk** than the one it watches, so it still
works at 100%. GC buys time, not capacity — recurring ≥95% peaks mean the
volume must grow. At 100%, docker can corrupt live container network state
(observed: a container lost its embedded-DNS endpoint and stayed broken until
restarted — survivors of the full disk are not necessarily healthy).

---

## Dashboard as Code

### Managing Grafana Dashboards in Git

| Approach | Tool | Complexity |
|----------|------|------------|
| JSON export/import | Grafana UI + Git | Low |
| Provisioning | Grafana provisioning API | Medium |
| Grafonnet | Jsonnet library | High (programmable) |

### Grafana Provisioning (Recommended)

```yaml
# grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

Mount dashboard JSON files into `/var/lib/grafana/dashboards/`:

```yaml
# docker-compose.infra.yml (grafana service)
volumes:
  - ./grafana/provisioning:/etc/grafana/provisioning
  - ./grafana/dashboards:/var/lib/grafana/dashboards
```

Workflow:
1. Edit dashboard in Grafana UI
2. Export JSON via dashboard settings → JSON Model
3. Save to `grafana/dashboards/{service}.json` in Git
4. Grafana auto-reloads on file change (30s interval)

See: `templates/monitoring/grafana-dashboard.json` for template
