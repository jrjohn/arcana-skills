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
    "medical-software-requirements-skill"
    "app-uiux-designer.skill"
)

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
        read -p "  Install Node.js automatically? (Y/n) " -n 1 -r
        echo
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
        read -p "  Install Claude Code CLI automatically? (Y/n) " -n 1 -r
        echo
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

    cleanup
    print_completion
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main
main "$@"
