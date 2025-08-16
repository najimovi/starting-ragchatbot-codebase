#!/bin/bash

# Quality checks script for the RAG chatbot project
# Run all code quality tools in sequence

set -e  # Exit on error

echo "🔍 Running code quality checks..."
echo "================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")/.."

# Run Black formatter check
echo -e "\n${YELLOW}📝 Checking code formatting with Black...${NC}"
if uv run black --check backend/; then
    echo -e "${GREEN}✅ Black: Code is properly formatted${NC}"
else
    echo -e "${RED}❌ Black: Code needs formatting. Run 'uv run black backend/' to fix.${NC}"
    exit 1
fi

# Run Ruff linter
echo -e "\n${YELLOW}🔧 Running Ruff linter...${NC}"
if uv run ruff check backend/; then
    echo -e "${GREEN}✅ Ruff: No linting issues found${NC}"
else
    echo -e "${RED}❌ Ruff: Linting issues found${NC}"
    exit 1
fi

# Run MyPy type checker
echo -e "\n${YELLOW}🔎 Running MyPy type checker...${NC}"
if uv run mypy backend/ --ignore-missing-imports; then
    echo -e "${GREEN}✅ MyPy: Type checking passed${NC}"
else
    echo -e "${YELLOW}⚠️  MyPy: Type checking issues found (non-blocking)${NC}"
fi

# Run tests if they exist
echo -e "\n${YELLOW}🧪 Running tests...${NC}"
if uv run pytest backend/tests/ -v; then
    echo -e "${GREEN}✅ Tests: All tests passed${NC}"
else
    echo -e "${RED}❌ Tests: Some tests failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}✨ All quality checks passed!${NC}"