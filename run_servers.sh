#!/bin/bash

# Kill any existing processes on ports 3000 and 8000
echo "Stopping existing servers..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Activate Virtual Environment
source ./venv/bin/activate

# Start Backend in background
echo "Starting Backend (FastAPI) on port 8000..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend in background
echo "Starting Frontend (SimpleHTTP) on port 3000..."
python -m http.server 3000 --directory frontend &
FRONTEND_PID=$!

echo "Servers are running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Access the app at http://localhost:3000"

# Wait for process to exit
wait
