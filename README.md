# Arcana Skills for Claude Code

Enterprise-grade development skills collection for Claude Code CLI.

## Quick Installation

### Option 1: One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash
```

### Option 2: Clone and Install

```bash
git clone https://github.com/jrjohn/arcana-skills.git
cd arcana-skills
./install.sh
```

### Installation Options

```bash
# Interactive installation (select skills to install)
./install.sh

# Install all skills
./install.sh --all
```

## Included Skills

### Development Framework Skills

| Skill | Description |
|-------|-------------|
| `ios-developer-skill` | iOS development guide based on Arcana iOS enterprise architecture (Clean Architecture, MVVM, SwiftUI) |
| `android-developer-skill` | Android development guide based on Arcana Android enterprise architecture (Jetpack Compose, Hilt DI) |
| `react-developer-skill` | React development guide based on Arcana React enterprise architecture (React 19, Offline-First) |
| `angular-developer-skill` | Angular development guide based on Arcana Angular enterprise architecture (Angular Signals) |
| `nodejs-developer-skill` | Node.js/Express development guide (gRPC-first, Prisma ORM) |
| `python-developer-skill` | Python/Flask development guide (gRPC-first, Clean Architecture) |
| `springboot-developer-skill` | Spring Boot development guide (Dual-protocol, OSGi Plugin System) |
| `windows-developer-skill` | Windows desktop development guide (WinUI 3, CRDT-based offline sync) |

### Domain-Specific Skills

| Skill | Description |
|-------|-------------|
| `medical-software-requirements-skill` | Medical device software requirements gathering and documentation (IEC 62304 compliant) |

## Uninstallation

```bash
# Interactive uninstall
./uninstall.sh

# Uninstall all
./uninstall.sh --all
```

## Manual Installation

If you only want to install a specific skill, you can manually copy it:

```bash
# Copy a single skill to Claude Code skills directory
cp -r ios-developer-skill ~/.claude/skills/
```

## Directory Structure

```
arcana-skills/
├── install.sh                          # Installation script
├── uninstall.sh                        # Uninstallation script
├── README.md                           # This file
├── ios-developer-skill/                # iOS Development Skill
│   ├── SKILL.md                        # Skill definition (required)
│   ├── README.md                       # Documentation
│   ├── reference.md                    # API reference
│   ├── examples.md                     # Examples
│   ├── patterns.md                     # Design patterns
│   ├── patterns/                       # Pattern details
│   ├── checklists/                     # Checklists
│   └── verification/                   # Verification commands
├── android-developer-skill/
├── angular-developer-skill/
├── react-developer-skill/
├── nodejs-developer-skill/
├── python-developer-skill/
├── springboot-developer-skill/
├── windows-developer-skill/
└── medical-software-requirements-skill/
```

## System Requirements

- macOS / Linux / Windows (WSL)
- Git
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+ (required for some skills)

## Verify Installation

After installation, start Claude Code and ask:

```
What Skills are available?
```

Or use a specific skill:

```
Use ios-developer-skill to help me create a new iOS project
```

## Update Skills

```bash
cd arcana-skills
git pull
./install.sh --all
```

## License

MIT License

## Contributing

Pull requests and issues are welcome!
