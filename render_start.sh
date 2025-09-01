#!/bin/bash
set -e

echo "🚀 Starting Render deployment..."
echo "📦 Installing critical dependencies..."

# Run the dependency installer
python install_deps.py

if [ $? -ne 0 ]; then
    echo "❌ Dependency installation failed, trying pip install -r requirements.txt"
    pip install --force-reinstall --no-cache-dir -r requirements.txt
fi

echo "✅ Dependencies installed"

echo "🔄 Running database migrations..."
python run_migrations.py

if [ $? -ne 0 ]; then
    echo "❌ Database migrations failed, but continuing..."
fi

echo "✅ Starting application..."

# Start the application
exec python app.py