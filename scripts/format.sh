#!/bin/bash

# Auto-format script for the RAG chatbot project
# Runs formatters to automatically fix code style issues

set -e  # Exit on error

echo "🎨 Auto-formatting code..."
echo "=========================="

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")/.."

# Run Black formatter
echo -e "\n${YELLOW}📝 Formatting Python code with Black...${NC}"
uv run black backend/
echo -e "${GREEN}✅ Black formatting complete${NC}"

# Run Ruff with auto-fix
echo -e "\n${YELLOW}🔧 Auto-fixing linting issues with Ruff...${NC}"
uv run ruff check --fix backend/ || true
echo -e "${GREEN}✅ Ruff auto-fix complete${NC}"

# Sort imports with Ruff
echo -e "\n${YELLOW}📦 Sorting imports...${NC}"
uv run ruff check --select I --fix backend/
echo -e "${GREEN}✅ Import sorting complete${NC}"

echo -e "\n${GREEN}✨ Code formatting complete!${NC}"
echo -e "Run ${YELLOW}./scripts/quality.sh${NC} to verify all checks pass."