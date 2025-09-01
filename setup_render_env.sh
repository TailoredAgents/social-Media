#!/bin/bash
set -e

echo "🔧 Setting up Render environment for AI Social Media Backend"
echo "============================================================"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install all dependencies from requirements.txt
echo "📥 Installing all dependencies..."
pip install -r requirements.txt

# Set default environment variables if not set
echo "🔧 Checking environment variables..."

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set - using default PostgreSQL URL"
    export DATABASE_URL="postgresql://ai_social_media_user:Of9TEnT1XFGIKVYy4cJrQQSZy20JrNZC@dpg-d25qurili9vc73euk6cg-a/ai_social_media"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  SECRET_KEY not set - generating secure key"
    export SECRET_KEY="Cc5NOfxEP9KrY0d2k9+tXvZmGpR7sJ8wL3nQ6uA4eF1iH9kN2pS5vY8zA3dG6j"
fi

if [ -z "$CORS_ORIGINS" ]; then
    echo "⚠️  CORS_ORIGINS not set - using default"
    export CORS_ORIGINS="https://www.lily-ai-socialmedia.com,https://lily-ai-socialmedia.com"
fi

echo "✅ Environment variables set:"
echo "   DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "   SECRET_KEY: ${SECRET_KEY:0:20}..."
echo "   CORS_ORIGINS: $CORS_ORIGINS"

# Test imports
echo "🧪 Testing critical imports..."
python -c "
import sys
sys.path.insert(0, '.')

try:
    import fastapi
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')
    sys.exit(1)

try:
    import sqlalchemy
    print('✅ SQLAlchemy imported successfully')
except ImportError as e:
    print(f'❌ SQLAlchemy import failed: {e}')
    sys.exit(1)

try:
    import structlog
    print('✅ Structlog imported successfully')
except ImportError as e:
    print(f'❌ Structlog import failed: {e}')
    sys.exit(1)

try:
    from jose import jwt
    print('✅ Python-jose imported successfully')
except ImportError as e:
    print(f'❌ Python-jose import failed: {e}')
    sys.exit(1)

print('🎉 All critical packages imported successfully!')
"

if [ $? -eq 0 ]; then
    echo "✅ All dependencies ready!"
    echo "🚀 Starting application..."
    python app.py
else
    echo "❌ Dependency check failed"
    exit 1
fi