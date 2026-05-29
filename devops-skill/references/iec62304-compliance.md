# IEC 62304 Compliance Automation

> DevOps Skill Reference

## Overview

IEC 62304 is the standard for medical device software lifecycle processes. This skill automates compliance artifact collection from CI/CD pipelines.

## Required Documents

| Document | Code | Source |
|----------|------|--------|
| Software Requirements Specification | SRS | `app-requirements-skill` |
| Software Design Description | SDD | `app-requirements-skill` |
| Software Test Plan | STP | CI/CD test configuration |
| Software Test Cases | STC | Automated test results |
| Software Verification & Validation | SVV | Test + quality reports |
| Requirements Traceability Matrix | RTM | Cross-reference all docs |

## CI/CD Artifact Mapping

| CI/CD Artifact | IEC 62304 Document | Evidence Type |
|---------------|---------------------|---------------|
| Unit test results (JUnit XML) | STC | Test execution evidence |
| Integration test results | STC | Test execution evidence |
| Code coverage report (JaCoCo/Jest) | STP | Coverage metrics |
| SonarQube analysis report | SDD | Code quality evidence |
| Trivy scan report | SVV | Security assessment |
| Build log | SVV | Build verification |
| Deployment log | SVV | Deployment verification |
| Monitoring data | SVV | Operational verification |

## Automation Pipeline

```
Code Commit
  ↓
Build + Test → Collect test results → Generate STC evidence
  ↓
SonarQube → Collect quality report → Update SDD quality section
  ↓
Trivy Scan → Collect scan report → Update SVV security section
  ↓
Deploy → Collect deploy log → Update SVV deployment section
  ↓
Generate RTM → Cross-reference all artifacts
  ↓
Compliance Report → Aggregate all evidence
```

## Integration with app-requirements-skill

After CI/CD artifacts are collected:
1. Feed results back to `app-requirements-skill`
2. Auto-update SRS/SDD with CI/CD references
3. Generate updated RTM with full traceability
4. Produce compliance report package

## Quality Gate for Compliance

Before release approval, verify:
- [ ] All STC test cases executed and passed
- [ ] Coverage meets threshold (≥ 80%)
- [ ] No CRITICAL/HIGH security vulnerabilities
- [ ] All SRS requirements traced to STC
- [ ] RTM shows 100% traceability
- [ ] All documents generated and signed

## Software Safety Classification

| Class | Risk | Testing Required |
|-------|------|-----------------|
| A | No injury possible | Basic testing |
| B | Non-serious injury | Moderate testing |
| C | Death or serious injury | Rigorous testing |
