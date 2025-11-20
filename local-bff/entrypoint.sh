#!/bin/bash
set -e

echo "=========================================="
echo "Starting backend entrypoint script"
echo "=========================================="

echo ""
echo "Step 1: Running database migrations..."
echo "------------------------------------------"

# Run Alembic migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations applied successfully"
else
    echo "✗ Migration failed! Exiting..."
    exit 1
fi

echo ""
echo "Step 2: Starting FastAPI server..."
echo "------------------------------------------"

# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
