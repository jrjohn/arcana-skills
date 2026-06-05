# Node 04: test（測試自動化）

> **COR Node**: Containerized testing & quality gates

## Purpose

Configure containerized testing environment with unit, integration, and e2e tests. Set up SonarQube quality gates.

## Entry Conditions

- Node 03 (build) completed
- Docker images built successfully
- SonarQube running (from Node 01)

## Test Strategy by Language

| Language | Unit Test | Integration | E2E | Coverage Tool |
|----------|----------|-------------|-----|--------------|
| Java/Spring Boot | JUnit 5 | Testcontainers | REST Assured | JaCoCo |
| Python/Flask | pytest | pytest + docker | pytest | coverage.py |
| Node.js/Express | Jest | Jest + supertest | Cypress/Playwright | Jest --coverage |
| React | Jest + RTL | Cypress | Cypress | Jest --coverage |
| Angular | Karma/Jest | Cypress | Cypress | Istanbul |
| Swift/iOS | XCTest | XCTest | XCUITest | Xcode coverage |
| Android/Kotlin | JUnit | Espresso | Espresso | JaCoCo |

## SonarQube Quality Gate

### Default Quality Gate Rules

| Metric | Condition | Threshold |
|--------|-----------|-----------|
| Coverage | ≥ | 80% |
| Duplicated Lines | ≤ | 3% |
| Maintainability Rating | ≤ | A |
| Reliability Rating | ≤ | A |
| Security Rating | ≤ | A |
| Blocker Issues | = | 0 |
| Critical Issues | = | 0 |

## Actions

1. **Generate test configuration** per language
2. **Configure SonarQube project**
   - Create project in SonarQube
   - Configure quality gate
   - Set analysis properties (`sonar-project.properties`)
3. **Add test stage to Jenkinsfile** (if not present)
4. **Configure coverage reporting**
5. **Set up Trivy scanning** for Docker images

## Output

Create `{project-root}/.devops/test.json`:

```json
{
  "test_frameworks": {
    "unit": "jest",
    "integration": "supertest",
    "e2e": "cypress"
  },
  "sonarqube": {
    "project_key": "my-project",
    "quality_gate": "default",
    "url": "http://localhost:9000"
  },
  "coverage_threshold": 80,
  "configured_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/arcana-devops-skill/process/04-test/exit-validation.sh {project-root}`

### Success Criteria

- [ ] Test configuration files exist
- [ ] sonar-project.properties exists
- [ ] Coverage threshold configured (≥ 80%)
- [ ] test.json created

## Next Node

On success → `05-deploy`

## Error Handling

| Error | Action |
|-------|--------|
| SonarQube unreachable | Re-check Node 01 infra |
| Coverage below threshold | Warn user, suggest areas to improve |
| Test framework not found | Guide installation |
