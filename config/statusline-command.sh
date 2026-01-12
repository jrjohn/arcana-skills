#!/bin/bash
#
# Claude Code Status Line Command
# Shows project context and git status
#

# Get current directory name
PROJECT_NAME=$(basename "$(pwd)")

# Get git branch if in a git repo
GIT_BRANCH=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_BRANCH=$(git branch --show-current 2>/dev/null)
    if [ -n "$GIT_BRANCH" ]; then
        GIT_BRANCH=" [$GIT_BRANCH]"
    fi
fi

# Get number of modified files
MODIFIED_COUNT=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    if [ "$COUNT" -gt 0 ]; then
        MODIFIED_COUNT=" (+$COUNT)"
    fi
fi

# Output status line
echo "${PROJECT_NAME}${GIT_BRANCH}${MODIFIED_COUNT}"
