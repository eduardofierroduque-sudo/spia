# SPIA — Production Start Script (Linux/macOS)
# Usage: chmod +x start.sh && ./start.sh

set -e

echo "=== SPIA Production Deploy ==="

# Check for required env vars
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
  echo "ERROR: Set POSTGRES_USER and POSTGRES_PASSWORD environment variables"
  echo "  export POSTGRES_USER=spia_user"
  echo "  export POSTGRES_PASSWORD=your_secure_db_password"
  echo "  export SPIA_API_KEY=your_api_key"
  exit 1
fi

# Build frontend if needed
if [ ! -d "frontend/dist" ]; then
  echo "Building frontend..."
  cd frontend && npm install && npm run build && cd ..
fi

# Start services
echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=== SPIA is running ==="
echo "Frontend:  http://localhost"
echo "API Docs:  http://localhost:8000/docs (internal)"
echo ""
echo "License keys: python tools/generate_license.py pro"
echo "Default trial: SPIA-TRIAL-1XZxVL86m49H3lTiPmqSvbzH"
echo ""
echo "To stop: docker compose -f docker-compose.prod.yml down"
