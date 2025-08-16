#!/bin/bash

# Development helper script
# Provides shortcuts for common development tasks

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")/.."

# Function to display help
show_help() {
    echo -e "${CYAN}RAG Chatbot Development Helper${NC}"
    echo -e "==============================="
    echo -e ""
    echo -e "${YELLOW}Usage:${NC} ./scripts/dev.sh [command]"
    echo -e ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}format${NC}    - Auto-format code with Black and Ruff"
    echo -e "  ${GREEN}check${NC}     - Run all quality checks (formatting, linting, types, tests)"
    echo -e "  ${GREEN}lint${NC}      - Run Ruff linter only"
    echo -e "  ${GREEN}types${NC}     - Run MyPy type checker only"
    echo -e "  ${GREEN}test${NC}      - Run pytest tests only"
    echo -e "  ${GREEN}server${NC}    - Start the development server"
    echo -e "  ${GREEN}clean${NC}     - Clean cache and temporary files"
    echo -e "  ${GREEN}help${NC}      - Show this help message"
    echo -e ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ./scripts/dev.sh format   # Format all code"
    echo -e "  ./scripts/dev.sh check    # Run all checks before commit"
    echo -e "  ./scripts/dev.sh server   # Start development server"
}

# Parse command
case "$1" in
    format)
        echo -e "${CYAN}Running code formatter...${NC}"
        ./scripts/format.sh
        ;;
    check)
        echo -e "${CYAN}Running quality checks...${NC}"
        ./scripts/quality.sh
        ;;
    lint)
        echo -e "${CYAN}Running linter...${NC}"
        uv run ruff check backend/
        ;;
    types)
        echo -e "${CYAN}Running type checker...${NC}"
        uv run mypy backend/ --ignore-missing-imports
        ;;
    test)
        echo -e "${CYAN}Running tests...${NC}"
        uv run pytest backend/tests/ -v
        ;;
    server)
        echo -e "${CYAN}Starting development server...${NC}"
        cd backend && uv run uvicorn app:app --reload --port 8000
        ;;
    clean)
        echo -e "${CYAN}Cleaning cache files...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}✅ Cache cleaned${NC}"
        ;;
    help|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac