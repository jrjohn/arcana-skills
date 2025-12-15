#!/bin/bash
#
# Arcana Skills Uninstaller for Claude Code
#
# Usage:
#   ./uninstall.sh           # Interactive uninstall
#   ./uninstall.sh --all     # Uninstall all Arcana skills
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SKILLS_DIR="$HOME/.claude/skills"

# Skills managed by this installer
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
)

# Print banner
print_banner() {
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              Arcana Skills Uninstaller                       ║"
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

# Uninstall a single skill
uninstall_skill() {
    local skill_name=$1
    local target_path="$SKILLS_DIR/$skill_name"

    if [ ! -d "$target_path" ]; then
        warn "Skill not installed: $skill_name (skipping)"
        return 0
    fi

    info "Removing: $skill_name"
    rm -rf "$target_path"
    success "Removed: $skill_name"
}

# Uninstall all skills
uninstall_all_skills() {
    info "Uninstalling ${#SKILLS[@]} skills..."
    echo ""

    for skill in "${SKILLS[@]}"; do
        uninstall_skill "$skill"
    done
}

# Interactive skill selection for uninstall
select_skills_to_uninstall() {
    echo ""
    info "Installed Arcana skills:"
    echo ""

    local installed_skills=()
    local i=1

    for skill in "${SKILLS[@]}"; do
        if [ -d "$SKILLS_DIR/$skill" ]; then
            installed_skills+=("$skill")
            echo "  $i) $skill"
            ((i++))
        fi
    done

    if [ ${#installed_skills[@]} -eq 0 ]; then
        info "No Arcana skills are currently installed."
        exit 0
    fi

    echo ""
    echo "  a) Uninstall all skills"
    echo "  q) Quit"
    echo ""

    read -p "Enter skill numbers (comma-separated) or 'a' for all: " selection

    if [ "$selection" = "q" ]; then
        info "Uninstall cancelled"
        exit 0
    fi

    if [ "$selection" = "a" ]; then
        echo ""
        warn "This will remove ALL Arcana skills!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            uninstall_all_skills
        else
            info "Uninstall cancelled"
            exit 0
        fi
        return
    fi

    # Parse comma-separated selection
    IFS=',' read -ra SELECTED <<< "$selection"
    for idx in "${SELECTED[@]}"; do
        idx=$(echo "$idx" | tr -d ' ')
        if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le "${#installed_skills[@]}" ]; then
            uninstall_skill "${installed_skills[$((idx-1))]}"
        else
            warn "Invalid selection: $idx"
        fi
    done
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║              Uninstall Complete!                             ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Main
main() {
    print_banner

    # Parse arguments
    local uninstall_mode="interactive"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all|-a)
                uninstall_mode="all"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -a, --all     Uninstall all Arcana skills without prompting"
                echo "  -h, --help    Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Check if skills directory exists
    if [ ! -d "$SKILLS_DIR" ]; then
        info "Skills directory does not exist. Nothing to uninstall."
        exit 0
    fi

    # Uninstall skills
    if [ "$uninstall_mode" = "all" ]; then
        warn "This will remove ALL Arcana skills!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            uninstall_all_skills
        else
            info "Uninstall cancelled"
            exit 0
        fi
    else
        select_skills_to_uninstall
    fi

    print_completion
}

# Run main
main "$@"
