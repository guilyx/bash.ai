#!/bin/bash
# Setup script for Flourish

set -e

echo "🚀 Setting up Flourish..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12 or later."
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Found Python version: $PYTHON_VERSION"

# Check Python version (basic check)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    echo "❌ Error: Python 3.12 or later is required (you have $PYTHON_VERSION)"
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✓ Found uv"
fi

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    if [ -f env.example ]; then
        echo "📝 Creating .env file from env.example..."
        cp env.example .env
        echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"
    else
        echo "📝 Creating .env file..."
        cat > .env << EOF
GOOGLE_API_KEY=your-api-key-here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GEMINI_MODEL=gemini-2.0-flash
DEFAULT_BLACKLIST=rm,dd,format,mkfs,chmod 777
EOF
        echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"
    fi
else
    echo "✓ .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Install the package
echo "🔨 Installing Flourish..."
uv pip install -e .

if command -v flourish &> /dev/null; then
    echo "✅ Setup successful! Flourish is ready to use."
    echo ""
    echo "Next steps:"
    echo "1. Edit .env and add your API_KEY"
    echo "2. Try it out: flourish 'Hello, world!'"
    echo ""
    echo "To integrate with bash:"
    echo "  source scripts/bash_integration.sh"
    echo "  # or add to your ~/.bashrc or ~/.zshrc"
else
    echo "⚠️  flourish command not found in PATH"
    echo "   You can run it with: uv run flourish"
fi
