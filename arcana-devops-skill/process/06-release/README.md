# Node 06: release（自動送審 & 合規）

> **COR Node**: Automated release submission & compliance

## Purpose

Configure automated release pipelines including App Store/Play Store submission via Fastlane, IEC 62304 compliance documentation, and quality report integration.

## Entry Conditions

- Node 05 (deploy) completed
- Build artifacts available
- Version number defined

## Mobile Submission Flow

### iOS (App Store)

```
Build → Archive → Sign → Upload TestFlight → Submit Review
```

| Step | Tool | Config |
|------|------|--------|
| Build | Xcode/xcodebuild | scheme, configuration |
| Archive | Fastlane (gym) | export method |
| Sign | Fastlane (match) | provisioning profiles |
| Upload | Fastlane (pilot) | TestFlight |
| Submit | Fastlane (deliver) | App Store Connect |

### Android (Play Store)

```
Build → Sign → Upload → Promote Track
```

| Step | Tool | Config |
|------|------|--------|
| Build | Gradle | assembleRelease/bundleRelease |
| Sign | Gradle signing config | keystore |
| Upload | Fastlane (supply) | Google Play Console |
| Promote | Fastlane (supply) | internal → alpha → beta → production |

## IEC 62304 Compliance

Integrates with `app-requirements-skill` to auto-generate:
- **SRS** — Software Requirements Specification
- **SDD** — Software Design Description
- **STP** — Software Test Plan
- **STC** — Software Test Cases
- **RTM** — Requirements Traceability Matrix

### Compliance Artifacts from CI/CD

| Artifact | Source | IEC 62304 Document |
|----------|--------|---------------------|
| Test results | Jenkins test stage | STP/STC evidence |
| Code coverage | JaCoCo/Jest/coverage.py | STP metrics |
| SonarQube report | SonarQube analysis | SDD code quality |
| Trivy scan | Docker image scan | Security assessment |
| Build log | Jenkins build output | Build verification |

## HarmonyOS Submission Flow (AppGallery)

```
Build HAP → Sign → Upload AppGallery → Submit Review
```

| Step | Tool | Config |
|------|------|--------|
| Build | hvigorw | `assembleHap --mode module` |
| Sign | hap-sign | signing key + profile |
| Upload | AppGallery Connect API | client_id + client_secret |
| Promote | AppGallery Connect API | internal → beta → production |

See: `templates/mobile/Fastfile.harmonyos`, `templates/jenkins/Jenkinsfile.harmonyos`

## Windows/.NET Release Flow

### API (.NET)

Standard Docker-based release (same as other server apps):
```
Build → Test → Docker → Push → Deploy
```

### Desktop (WinUI 3 / MSIX)

```
Build → Test → MSIX Package → Sign → Distribute
```

| Distribution | Method |
|-------------|--------|
| Microsoft Store | Upload MSIX to Partner Center |
| Enterprise | Sideload via SCCM / Intune |
| Direct | Host MSIX on internal server |

See: `templates/jenkins/Jenkinsfile.dotnet`

## Embedded Firmware Release Flow

```
Build → Test → Static Analysis → Sign → Archive → OTA/Flash
```

| Step | Tool |
|------|------|
| Build | Docker build env (ESP-IDF / ARM GCC) |
| Test | Unity framework / CTest / QEMU |
| Static Analysis | cppcheck + clang-tidy |
| Sign | espsecure.py (ESP32) / OpenSSL (STM32) |
| Archive | Jenkins artifact storage |
| Deploy | OTA server / USB flash / JTAG |

**Key differences from server releases:**
- No Docker registry push
- Firmware signing is critical for security
- OTA requires device fleet management
- Rollback = previous firmware version stored on device

See: `references/embedded-patterns.md`, `templates/jenkins/Jenkinsfile.embedded`

---

## Quality Gate Integration

Before release approval:
- [ ] SonarQube Quality Gate: PASSED
- [ ] Trivy Scan: No CRITICAL/HIGH vulnerabilities
- [ ] Test Coverage: ≥ 80%
- [ ] All automated tests: PASSED
- [ ] IEC 62304 documents: Generated and complete

## Actions

1. **Generate Fastlane configuration** (if mobile project)
   - `Fastfile` for iOS and/or Android
   - `Appfile` with app metadata
   - `.env.default` for Fastlane environment

2. **Configure version management**
   - Semantic versioning scheme
   - Auto-increment build numbers

3. **Set up IEC 62304 document generation**
   - Configure CI/CD artifact collection
   - Link with `app-requirements-skill`

4. **Generate release scripts**
   - Version bump script
   - Release notes generator
   - Compliance report aggregator

## Output

Create `{project-root}/.devops/release.json`:

```json
{
  "mobile": {
    "ios": { "fastfile": "fastlane/Fastfile", "bundle_id": "" },
    "android": { "fastfile": "fastlane/Fastfile", "package": "" }
  },
  "versioning": "semver",
  "compliance": {
    "iec62304": true,
    "documents": ["SRS", "SDD", "STP", "STC", "RTM"]
  },
  "quality_gates": {
    "sonarqube": true,
    "trivy": true,
    "coverage_min": 80
  },
  "configured_at": "2026-02-11T10:00:00Z"
}
```

## Exit Validation

Run: `bash ~/.claude/skills/arcana-devops-skill/process/06-release/exit-validation.sh {project-root}`

### Success Criteria

- [ ] Fastlane config exists (if mobile project)
- [ ] Version management configured
- [ ] release.json created
- [ ] Quality gate criteria defined

## Next Node

On success → `07-monitor`

## Error Handling

| Error | Action |
|-------|--------|
| Fastlane not installed | Guide: `gem install fastlane` or `brew install fastlane` |
| Code signing issues | Guide match setup or manual provisioning |
| Missing app credentials | Guide API key setup for stores |
