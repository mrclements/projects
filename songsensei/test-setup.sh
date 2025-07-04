#!/bin/bash

echo "🎵 SongSensei MVP - Testing Setup"
echo "================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check if required files exist
REQUIRED_FILES=(
    "docker-compose.yml"
    "Makefile"
    "README.md"
    "api/package.json"
    "api/Dockerfile"
    "web/package.json"
    "web/Dockerfile"
    "analysis/requirements.txt"
    "analysis/Dockerfile"
    "analysis/main.py"
)

echo "🔍 Checking required files..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

echo ""
echo "🚀 Ready to build and run SongSensei MVP!"
echo ""
echo "Next steps:"
echo "1. Run: make build"
echo "2. Run: make up"
echo "3. Open: http://localhost:3000"
echo ""
echo "Services will be available at:"
echo "- Web UI: http://localhost:3000"
echo "- API: http://localhost:4000"
echo "- Analysis Service: http://localhost:5000"
