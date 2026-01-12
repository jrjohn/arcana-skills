#!/bin/bash
#
# Arcana Skills Installer for Claude Code
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash
#
# Or clone and run locally:
#   git clone https://github.com/jrjohn/arcana-skills.git
#   cd arcana-skills
#   ./install.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/jrjohn/arcana-skills.git"
SKILLS_DIR="$HOME/.claude/skills"
TEMP_DIR=$(mktemp -d)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Skills to install
SKILLS=(
    "ios-developer-skill"
    "android-developer-skill"
    "react-developer-skill"
    "angular-developer-skill"
    "nodejs-developer-skill"
    "python-developer-skill"
    "springboot-developer-skill"
    "windows-developer-skill"
    "app-requirements-skill"
    "app-uiux-designer.skill"
)

# Config paths
CLAUDE_DIR="$HOME/.claude"
USER_SETTINGS="$CLAUDE_DIR/settings.json"
USER_CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
HOOKS_DIR="$CLAUDE_DIR/hooks"

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              Arcana Skills Installer                         ║"
    echo "║              for Claude Code                                 ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print message with color
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Install Node.js
install_nodejs() {
    info "Installing Node.js..."
    case "$(uname -s)" in
        Darwin*)
            if command -v brew &> /dev/null; then
                info "Using Homebrew to install Node.js..."
                brew install node
            else
                error "Homebrew not found. Please install Node.js manually."
                info "Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                info "Or download Node.js from: https://nodejs.org/"
                exit 1
            fi
            ;;
        Linux*)
            if command -v apt-get &> /dev/null; then
                info "Using apt to install Node.js..."
                curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                sudo apt-get install -y nodejs
            elif command -v yum &> /dev/null; then
                info "Using yum to install Node.js..."
                curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
                sudo yum install -y nodejs
            elif command -v pacman &> /dev/null; then
                info "Using pacman to install Node.js..."
                sudo pacman -S nodejs npm
            else
                error "Package manager not found. Please install Node.js manually."
                info "Install from: https://nodejs.org/"
                exit 1
            fi
            ;;
        *)
            error "Unsupported OS. Please install Node.js manually."
            info "Install from: https://nodejs.org/"
            exit 1
            ;;
    esac

    # Verify installation
    if command -v node &> /dev/null; then
        success "Node.js installed successfully: $(node --version)"
    else
        error "Node.js installation failed."
        exit 1
    fi
}

# Install Claude Code CLI
install_claude_cli() {
    info "Installing Claude Code CLI..."
    npm install -g @anthropic-ai/claude-code

    # Verify installation
    if command -v claude &> /dev/null; then
        success "Claude Code CLI installed successfully"
    else
        error "Claude Code CLI installation failed."
        info "Try running: sudo npm install -g @anthropic-ai/claude-code"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    # Check if git is installed
    if ! command -v git &> /dev/null; then
        error "git is not installed. Please install git first."
        exit 1
    fi

    # Check if rsync is installed (required for copying skills)
    if ! command -v rsync &> /dev/null; then
        error "rsync is not installed. Please install rsync first."
        case "$(uname -s)" in
            Linux*)
                info "Install via: sudo apt install rsync (Debian/Ubuntu)"
                info "         or: sudo yum install rsync (RHEL/CentOS)"
                ;;
            Darwin*)
                info "Install via: brew install rsync"
                ;;
        esac
        exit 1
    fi

    # Check if Node.js is installed (required)
    if ! command -v node &> /dev/null; then
        warn "Node.js is not installed."
        if [ -t 0 ]; then
            read -p "  Install Node.js automatically? (Y/n) " -n 1 -r
            echo
        else
            info "  Auto-installing Node.js (pipe mode)..."
            REPLY="y"
        fi
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            install_nodejs
        else
            error "Node.js is required. Please install it manually."
            info "Install from: https://nodejs.org/"
            exit 1
        fi
    fi

    # Check if Claude Code is installed (required)
    if ! command -v claude &> /dev/null; then
        warn "Claude Code CLI not found."
        if [ -t 0 ]; then
            read -p "  Install Claude Code CLI automatically? (Y/n) " -n 1 -r
            echo
        else
            info "  Auto-installing Claude Code CLI (pipe mode)..."
            REPLY="y"
        fi
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            install_claude_cli
        else
            error "Claude Code CLI is required. Please install it manually."
            info "Install: npm install -g @anthropic-ai/claude-code"
            exit 1
        fi
    fi

    success "Prerequisites check passed"
}

# Check and install jq if needed (for JSON merging)
ensure_jq() {
    if command -v jq &> /dev/null; then
        return 0
    fi

    warn "jq is not installed (needed for settings merge)."
    if [ -t 0 ]; then
        read -p "  Install jq automatically? (Y/n) " -n 1 -r
        echo
    else
        info "  Auto-installing jq (pipe mode)..."
        REPLY="y"
    fi

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        warn "Skipping settings.json merge (jq not available)"
        return 1
    fi

    info "Installing jq..."
    case "$(uname -s)" in
        Darwin*)
            if command -v brew &> /dev/null; then
                brew install jq
            else
                error "Homebrew not found. Please install jq manually: brew install jq"
                return 1
            fi
            ;;
        Linux*)
            if command -v apt-get &> /dev/null; then
                sudo apt-get install -y jq
            elif command -v yum &> /dev/null; then
                sudo yum install -y jq
            elif command -v pacman &> /dev/null; then
                sudo pacman -S jq
            else
                error "Package manager not found. Please install jq manually."
                return 1
            fi
            ;;
        *)
            error "Unsupported OS. Please install jq manually."
            return 1
            ;;
    esac

    if command -v jq &> /dev/null; then
        success "jq installed successfully"
        return 0
    else
        error "jq installation failed"
        return 1
    fi
}

# Generate skill permissions JSON array from SKILLS array
generate_skill_permissions() {
    local permissions=""
    for skill in "${SKILLS[@]}"; do
        if [ -n "$permissions" ]; then
            permissions="$permissions,"
        fi
        permissions="$permissions\"Skill($skill)\""
    done
    echo "[$permissions]"
}

# Merge settings.json
merge_settings() {
    local template_settings="$SCRIPT_DIR/config/settings.template.json"

    if [ ! -f "$template_settings" ]; then
        warn "settings.template.json not found, skipping settings merge"
        return 0
    fi

    # Ensure jq is available
    if ! ensure_jq; then
        return 0
    fi

    info "Merging settings.json..."

    # Generate dynamic skill permissions from SKILLS array
    local skill_perms
    skill_perms=$(generate_skill_permissions)

    # Create enriched template with dynamic skill permissions
    local enriched_template
    enriched_template=$(jq --argjson skills "$skill_perms" '
        .permissions.allow = (.permissions.allow + $skills | unique)
    ' "$template_settings")

    # Create user settings if not exists
    if [ ! -f "$USER_SETTINGS" ]; then
        info "  Creating new settings.json"
        echo "$enriched_template" > "$USER_SETTINGS"
        success "Settings configured"
        return 0
    fi

    # Backup existing settings
    cp "$USER_SETTINGS" "$USER_SETTINGS.backup"
    info "  Backed up existing settings to settings.json.backup"

    # Deep merge using jq (preserves user's existing settings while adding new ones)
    echo "$enriched_template" | jq -s '
        def deep_merge(a; b):
            a as $a | b as $b |
            if ($a | type) == "object" and ($b | type) == "object" then
                ($a | keys) + ($b | keys) | unique |
                map({(.): deep_merge($a[.]; $b[.])}) | add
            elif $b == null then $a
            else $b
            end;
        deep_merge(.[0]; .[1])
    ' "$USER_SETTINGS.backup" - > "$USER_SETTINGS.tmp"

    if [ -s "$USER_SETTINGS.tmp" ]; then
        mv "$USER_SETTINGS.tmp" "$USER_SETTINGS"
        success "Settings merged successfully"
    else
        error "Settings merge failed, restoring backup"
        mv "$USER_SETTINGS.backup" "$USER_SETTINGS"
        rm -f "$USER_SETTINGS.tmp"
    fi
}

# Merge CLAUDE.md
merge_claude_md() {
    local template_claude_md="$SCRIPT_DIR/config/CLAUDE.template.md"
    local marker="# Arcana Skills Configuration"

    if [ ! -f "$template_claude_md" ]; then
        warn "CLAUDE.template.md not found, skipping CLAUDE.md merge"
        return 0
    fi

    info "Configuring CLAUDE.md..."

    # Create user CLAUDE.md if not exists
    if [ ! -f "$USER_CLAUDE_MD" ]; then
        info "  Creating new CLAUDE.md"
        cp "$template_claude_md" "$USER_CLAUDE_MD"
        success "CLAUDE.md configured"
        return 0
    fi

    # Check if already contains our config
    if grep -q "$marker" "$USER_CLAUDE_MD" 2>/dev/null; then
        info "  CLAUDE.md already contains Arcana Skills config"

        # In pipe mode, auto-update; otherwise ask
        if [ -t 0 ]; then
            read -p "  Update existing Arcana Skills config? (y/N) " -n 1 -r
            echo
        else
            info "  Auto-updating config (pipe mode)..."
            REPLY="y"
        fi
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "  Keeping existing config"
            return 0
        fi

        # Remove old config and add new
        info "  Updating Arcana Skills config..."
        sed -i.backup "/$marker/,/# End Arcana Skills/d" "$USER_CLAUDE_MD"
    fi

    # Append template to user's CLAUDE.md
    echo "" >> "$USER_CLAUDE_MD"
    cat "$template_claude_md" >> "$USER_CLAUDE_MD"
    success "CLAUDE.md updated"
}

# Install hooks
install_hooks() {
    local hooks_source="$SCRIPT_DIR/config/hooks"

    if [ ! -d "$hooks_source" ]; then
        return 0
    fi

    info "Installing hooks..."
    mkdir -p "$HOOKS_DIR"

    # Copy all hook scripts
    for hook_file in "$hooks_source"/*.sh; do
        if [ -f "$hook_file" ]; then
            local filename=$(basename "$hook_file")
            cp "$hook_file" "$HOOKS_DIR/$filename"
            chmod +x "$HOOKS_DIR/$filename"
            info "  Installed hook: $filename"
        fi
    done

    # Also install statusline command if exists
    if [ -f "$SCRIPT_DIR/config/statusline-command.sh" ]; then
        cp "$SCRIPT_DIR/config/statusline-command.sh" "$CLAUDE_DIR/statusline-command.sh"
        chmod +x "$CLAUDE_DIR/statusline-command.sh"
        info "  Installed statusline command"
    fi

    success "Hooks installed"
}

# Create skills directory if not exists
ensure_skills_dir() {
    if [ ! -d "$SKILLS_DIR" ]; then
        info "Creating skills directory: $SKILLS_DIR"
        mkdir -p "$SKILLS_DIR"
    fi
}

# Detect if running from cloned repo or via curl
detect_source() {
    if [ -f "$SCRIPT_DIR/ios-developer-skill/SKILL.md" ]; then
        echo "local"
    else
        echo "remote"
    fi
}

# Clone repository
clone_repo() {
    info "Cloning repository from $REPO_URL..."
    git clone --depth 1 "$REPO_URL" "$TEMP_DIR/arcana-skills"
    SCRIPT_DIR="$TEMP_DIR/arcana-skills"
}

# Install a single skill
install_skill() {
    local skill_name=$1
    local source_path="$SCRIPT_DIR/$skill_name"
    local target_path="$SKILLS_DIR/$skill_name"

    if [ ! -d "$source_path" ]; then
        warn "Skill not found: $skill_name (skipping)"
        return 0
    fi

    # Auto-remove old skill if exists (for clean reinstall)
    if [ -d "$target_path" ]; then
        info "Removing old version: $skill_name"
        rm -rf "$target_path"
    fi

    # Copy skill (excluding node_modules, .git, etc.)
    info "Installing: $skill_name"
    mkdir -p "$target_path"

    rsync -av --exclude='node_modules' \
              --exclude='.git' \
              --exclude='.DS_Store' \
              --exclude='*.log' \
              "$source_path/" "$target_path/"

    # Install npm dependencies if package.json exists
    if [ -f "$target_path/package.json" ]; then
        info "  Installing npm dependencies for $skill_name..."
        (cd "$target_path" && npm install --silent)
    fi

    success "Installed: $skill_name"
}

# Install all skills
install_all_skills() {
    info "Installing ${#SKILLS[@]} skills..."
    echo ""

    for skill in "${SKILLS[@]}"; do
        install_skill "$skill"
    done
}

# Interactive skill selection
select_skills() {
    echo ""
    info "Available skills:"
    echo ""

    local i=1
    for skill in "${SKILLS[@]}"; do
        echo "  $i) $skill"
        ((i++))
    done

    echo ""
    echo "  a) Install all skills"
    echo "  q) Quit"
    echo ""

    read -p "Enter skill numbers (comma-separated) or 'a' for all: " selection

    if [ "$selection" = "q" ]; then
        info "Installation cancelled"
        exit 0
    fi

    if [ "$selection" = "a" ]; then
        install_all_skills
        return
    fi

    # Parse comma-separated selection
    IFS=',' read -ra SELECTED <<< "$selection"
    for idx in "${SELECTED[@]}"; do
        idx=$(echo "$idx" | tr -d ' ')
        if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le "${#SKILLS[@]}" ]; then
            install_skill "${SKILLS[$((idx-1))]}"
        else
            warn "Invalid selection: $idx"
        fi
    done
}

# Cleanup
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║              Installation Complete!                          ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    info "Skills installed to: $SKILLS_DIR"
    echo ""
    info "To verify installation, run Claude Code and ask:"
    echo "  'What Skills are available?'"
    echo ""
}

# Main
main() {
    print_banner

    # Parse arguments
    local install_mode="interactive"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all|-a)
                install_mode="all"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -a, --all     Install all skills without prompting"
                echo "  -h, --help    Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Auto-detect pipe mode (curl | bash) - stdin is not a terminal
    if [ "$install_mode" = "interactive" ] && [ ! -t 0 ]; then
        info "Detected pipe mode (curl | bash), installing all skills..."
        install_mode="all"
    fi

    check_prerequisites
    ensure_skills_dir

    # Detect source and clone if needed
    local source=$(detect_source)
    if [ "$source" = "remote" ]; then
        clone_repo
    fi

    # Install skills
    if [ "$install_mode" = "all" ]; then
        install_all_skills
    else
        select_skills
    fi

    # Configure settings and hooks
    echo ""
    info "Configuring Claude Code settings..."
    merge_settings
    merge_claude_md
    install_hooks

    cleanup
    print_completion
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main
main "$@"
