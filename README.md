# Arcana Skills for Claude Code

Enterprise-grade development skills collection for Claude Code CLI.

## Quick Installation

### macOS / Linux

#### Option 1: One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash
```

> **Note**: Pipe mode automatically installs all skills and auto-configures settings.

#### Option 2: Clone and Install

```bash
git clone https://github.com/jrjohn/arcana-skills.git
cd arcana-skills
./install.sh
```

#### Installation Options

```bash
# Interactive installation (select skills to install)
./install.sh

# Install all skills
./install.sh --all
```

### Windows

#### Option 1: PowerShell One-Line Install (Recommended)

```powershell
iwr -useb https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.ps1 | iex
```

#### Option 2: Clone and Install

```powershell
git clone https://github.com/jrjohn/arcana-skills.git
cd arcana-skills
.\install.ps1
```

#### Installation Options

```powershell
.\install.ps1           # Interactive installation
.\install.ps1 -All      # Install all skills
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

### Design Skills

| Skill | Description |
|-------|-------------|
| `app-uiux-designer.skill` | Enterprise-grade UI/UX design expert (SRS/SDD → Batch UI Generation, Visual Style Extraction, Motion Design, Dark Mode, i18n Localization, Design Review) |

### Requirements & Documentation Skills

| Skill | Description |
|-------|-------------|
| `app-requirements-skill` | IEC 62304 compliant software requirements gathering and documentation (SRS/SDD/SWD/STP/STC/SVV/RTM with 100% traceability) |

### Utility Skills

| Skill | Description |
|-------|-------------|
| `doc-indexer-skill` | Document indexing and full-text search tool (Apache Tika + Lucene, PDF/Word/Excel/OCR support, Chinese tokenization) |

## Uninstallation

### macOS / Linux

```bash
# Interactive uninstall
./uninstall.sh

# Uninstall all
./uninstall.sh --all
```

### Windows

```powershell
# Manual uninstall - remove skills directory
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills"
```

## Manual Installation

If you only want to install a specific skill, you can manually copy it:

### macOS / Linux

```bash
# Copy a single skill to Claude Code skills directory
cp -r ios-developer-skill ~/.claude/skills/
```

### Windows

```powershell
# Copy a single skill to Claude Code skills directory
Copy-Item -Recurse ios-developer-skill "$env:USERPROFILE\.claude\skills\"
```

## Directory Structure

```
arcana-skills/
├── install.sh                          # Installation script (macOS/Linux)
├── install.ps1                         # Installation script (Windows PowerShell)
├── uninstall.sh                        # Uninstallation script
├── README.md                           # This file
├── config/                             # Auto-configuration templates
│   ├── settings.template.json          # Claude Code settings (macOS/Linux)
│   ├── settings.template.windows.json  # Claude Code settings (Windows)
│   ├── CLAUDE.template.md              # CLAUDE.md template
│   ├── statusline-command.sh           # Status line script (macOS/Linux)
│   ├── statusline-command.ps1          # Status line script (Windows)
│   └── hooks/                          # Hook scripts
│       ├── validate-ui-flow.sh         # (macOS/Linux)
│       └── validate-ui-flow.ps1        # (Windows)
├── ios-developer-skill/
├── android-developer-skill/
├── angular-developer-skill/
├── react-developer-skill/
├── nodejs-developer-skill/
├── python-developer-skill/
├── springboot-developer-skill/
├── windows-developer-skill/
├── app-requirements-skill/
├── app-uiux-designer.skill/
└── doc-indexer-skill/
```

## System Requirements

- **macOS / Linux**: Bash, Git, curl, rsync
- **Windows**: PowerShell 5.1+ or PowerShell Core, Git
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+ (required for some skills)
- Java 17+ (required for doc-indexer-skill)
- jq (optional, for settings auto-configuration on macOS/Linux)

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

> **Note:** The installer automatically removes old skill versions before reinstalling, ensuring a clean update.

### macOS / Linux

#### Option 1: One-Line Update (Recommended)

If you used the one-line install method, simply run the same command again to update:

```bash
curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash
```

#### Option 2: Update from Cloned Repository

If you cloned the repository:

```bash
cd arcana-skills
git pull
./install.sh --all
```

### Windows

#### Option 1: One-Line Update (Recommended)

```powershell
iwr -useb https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.ps1 | iex
```

#### Option 2: Update from Cloned Repository

**PowerShell:**
```powershell
cd arcana-skills
git pull
.\install.ps1 -All
```

**Command Prompt (cmd.exe):**
```cmd
cd arcana-skills
git pull
install.bat -All
```

## License

MIT License

## Contributing

Pull requests and issues are welcome!
