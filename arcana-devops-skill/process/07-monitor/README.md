# Node 07: monitor（監控與可觀測性）

> **COR Node**: Monitoring & observability setup

## Purpose

Set up monitoring and alerting infrastructure with Prometheus, Grafana, and AlertManager. Configure health check endpoints and dashboards.

## Entry Conditions

- Node 06 (release) completed
- Deployed services available
- Infrastructure running

## Monitoring Stack

| Component | Image | Port | Purpose |
|-----------|-------|------|---------|
| Prometheus | prom/prometheus | 9090 | Metrics collection & alerting rules |
| Grafana | grafana/grafana | 3000 | Dashboard visualization |
| AlertManager | prom/alertmanager | 9093 | Alert routing & notification |
| Node Exporter | prom/node-exporter | 9100 | Host metrics (optional) |
| cAdvisor | gcr.io/cadvisor/cadvisor | 8082 | Container metrics (optional) |

## Metrics by Language

| Language | Metrics Library | Endpoint |
|----------|----------------|----------|
| Java/Spring Boot | Micrometer + Actuator | `/actuator/prometheus` |
| Python/Flask | prometheus_flask_instrumentator | `/metrics` |
| Node.js/Express | prom-client | `/metrics` |
| React/Angular | (Frontend) | RUM via Grafana Faro |

## Alert Rules

### Critical Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| ServiceDown | up == 0 for 1m | critical |
| HighCPU | CPU > 90% for 5m | critical |
| HighMemory | Memory > 90% for 5m | critical |
| DiskFull | Disk > 90% | critical |

### Warning Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighLatency | p99 > 1s for 5m | warning |
| HighErrorRate | 5xx > 5% for 5m | warning |
| PodRestart | restart count > 3 in 10m | warning |

## Actions

1. **Generate Prometheus config** — `prometheus.yml`
2. **Generate AlertManager config** — `alertmanager.yml`
3. **Generate Grafana dashboards** — `grafana-dashboard.json`
4. **Add monitoring to Docker Compose**
5. **Configure service metrics endpoints**
6. **Set up alert notification channels** (Slack, Email, etc.)

## Output

Create `{project-root}/.devops/monitor.json`:

```json
{
  "prometheus": { "url": "http://localhost:9090", "config": "prometheus.yml" },
  "grafana": { "url": "http://localhost:3000", "dashboard": "grafana-dashboard.json" },
  "alertmanager": { "url": "http://localhost:9093", "config": "alertmanager.yml" },
  "metrics_endpoints": {
    "api": "/actuator/prometheus"
  },
  "configured_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/arcana-devops-skill/process/07-monitor/exit-validation.sh {project-root}`

### Success Criteria

- [ ] prometheus.yml exists and is valid
- [ ] grafana-dashboard.json exists
- [ ] alertmanager.yml exists
- [ ] monitor.json created
- [ ] Prometheus can scrape configured targets (if running)

## Next Node

On success → `08-verify`

## Error Handling

| Error | Action |
|-------|--------|
| Prometheus config invalid | Validate with promtool |
| Grafana not starting | Check port 3000, review logs |
| No metrics endpoint | Generate metrics middleware for service |
