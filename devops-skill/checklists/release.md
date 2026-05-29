# Release Checklist

> Final verification before release

## Version Management

- [ ] Version number incremented (SemVer)
- [ ] Changelog updated
- [ ] Git tag created
- [ ] Release branch merged to main

## Quality Assurance

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] Performance tests pass (if applicable)
- [ ] SonarQube Quality Gate: PASSED
- [ ] Code coverage ≥ 80%
- [ ] No known critical bugs

## Security

- [ ] Trivy scan: PASSED
- [ ] Dependency audit: No critical vulnerabilities
- [ ] Secrets audit: No exposed secrets

## Mobile (if applicable)

### iOS

- [ ] Build number incremented
- [ ] Provisioning profiles valid
- [ ] App Store screenshots updated (if UI changes)
- [ ] App Store description updated
- [ ] TestFlight build verified by QA
- [ ] Privacy policy URL valid

### Android

- [ ] Version code incremented
- [ ] Signing key available
- [ ] Play Store listing updated (if needed)
- [ ] Internal testing verified
- [ ] Beta testing verified
- [ ] Content rating questionnaire updated (if needed)

## Compliance (IEC 62304, if applicable)

- [ ] SRS complete and reviewed
- [ ] SDD complete and reviewed
- [ ] STP complete and reviewed
- [ ] STC results collected
- [ ] RTM shows 100% traceability
- [ ] All compliance documents signed

## Deployment

- [ ] Pre-deploy checklist completed
- [ ] Deployment window confirmed
- [ ] Rollback plan ready
- [ ] Monitoring active
- [ ] On-call team notified

## Post-Release

- [ ] Deployment verified (health checks)
- [ ] Smoke tests pass
- [ ] Monitoring shows normal metrics
- [ ] Release notes published
- [ ] Stakeholders notified
