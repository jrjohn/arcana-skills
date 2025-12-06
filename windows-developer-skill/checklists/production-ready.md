# Production Readiness Checklist

## Pre-Release Checklist

### 🔴 CRITICAL (Must Pass)
- [ ] **Build succeeds** - `dotnet build -c Release`
- [ ] **All tests pass** - `dotnet test`
- [ ] **No empty handlers** - `grep "Click=\"\"" *.xaml`
- [ ] **Navigation complete** - All NavGraph methods implemented
- [ ] **No placeholder code** - `grep "NotImplementedException" src/`
- [ ] **No hardcoded secrets** - Check for API keys in code

### 🟡 IMPORTANT (Should Pass)
- [ ] **Loading states** - All data views show progress
- [ ] **Error states** - All views handle errors
- [ ] **Empty states** - All lists handle empty data
- [ ] **Offline support** - CRDT sync configured
- [ ] **Input validation** - All forms validate

### 🟢 RECOMMENDED (Nice to Have)
- [ ] **Animations** - Smooth transitions
- [ ] **Dark mode** - Theme support
- [ ] **Accessibility** - Screen reader support
- [ ] **Telemetry** - Analytics configured

## Test Coverage Targets

| Layer | Target |
|-------|--------|
| ViewModel | 90%+ |
| Service | 85%+ |
| Repository | 80%+ |

## Release Commands

```bash
# Build Release
dotnet publish -c Release

# Create MSIX
dotnet publish -c Release -p:GenerateAppxPackageOnBuild=true

# Code signing
signtool sign /f cert.pfx /p password /t timestamp app.msix
```
