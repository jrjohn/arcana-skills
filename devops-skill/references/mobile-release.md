# Mobile Release Patterns

> DevOps Skill Reference

## iOS Release Flow

```
Build → Archive → Sign → TestFlight → App Store Review → Release
```

### Fastlane Lanes

| Lane | Purpose | Trigger |
|------|---------|---------|
| `test` | Run XCTest suite | Every PR |
| `build` | Build + Archive | Merge to develop |
| `beta` | Upload to TestFlight | Merge to release/* |
| `release` | Submit to App Store | Tag v*.*.* |

### Code Signing

| Method | Use Case |
|--------|----------|
| `match` | Team code signing via Git repo |
| Manual | Individual provisioning profiles |

### Certificates

| Type | Purpose |
|------|---------|
| Development | Debug builds |
| Ad Hoc | Internal testing |
| App Store | App Store distribution |

## Android Release Flow

```
Build → Sign → Upload → Internal → Alpha → Beta → Production
```

### Fastlane Lanes

| Lane | Purpose | Trigger |
|------|---------|---------|
| `test` | Run JUnit + Espresso | Every PR |
| `build` | Build AAB/APK | Merge to develop |
| `internal` | Upload to internal track | Merge to release/* |
| `beta` | Promote to beta | Manual approval |
| `release` | Promote to production | Manual approval |

### Play Store Tracks

| Track | Audience | Auto-Review |
|-------|----------|-------------|
| Internal | Team only (100 max) | No |
| Alpha | Selected testers | No |
| Beta | Open beta testers | No |
| Production | All users | Yes |

### Staged Rollout (Android)

```
Production: 10% → 25% → 50% → 100%
```

## Version Management

### iOS
- **Version** (CFBundleShortVersionString): `1.2.3` — User-facing
- **Build** (CFBundleVersion): `42` — Auto-incremented

### Android
- **versionName**: `1.2.3` — User-facing
- **versionCode**: `42` — Auto-incremented integer

## Prerequisites

| Tool | Installation |
|------|-------------|
| Fastlane | `gem install fastlane` or `brew install fastlane` |
| Xcode CLI | `xcode-select --install` |
| CocoaPods | `gem install cocoapods` |
| Android SDK | Android Studio or `sdkmanager` |

## Common Issues

| Issue | Solution |
|-------|----------|
| Code signing failure | Re-run `fastlane match` |
| Build number conflict | Increment build number |
| Missing provisioning profile | Check Apple Developer portal |
| Play Store upload rejected | Check version code is higher |
| Screenshot size mismatch | Use `fastlane snapshot` |
