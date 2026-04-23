#!/bin/bash
# run_local.sh - Launches the FairLens platform in local demo mode

echo "🚀 Starting FairLens in Local Mode (No GCP required)..."

# Kill anything on 8080, 8000, or 5173 to prevent address in use errors
echo "🧹 Clearing ports (8080, 8000, 5173)..."
lsof -ti:8080,8000,5173 | xargs kill -9 2>/dev/null
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1

# Ensure database is seeded
echo "📦 Checking local database..."
python3 scripts/seed_local_db.py

# Start the FastAPI backend in the background
echo "⚡ Starting backend (FastAPI)..."
export LOCAL_MODE=true
export DEV_MODE=true
cd console/backend
uvicorn main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 2

# Start the Vite frontend
echo "🎨 Starting frontend (Vite)..."
cd console/frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ FairLens is running!"
echo "👉 Backend API: http://localhost:8080"
echo "👉 Frontend UI: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C to kill both background processes
trap "echo '\n🛑 Stopping FairLens...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

# Keep script running
wait
