#!/bin/bash

# VoxTrace Startup Script

echo "🎙️  Starting VoxTrace..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if PostgreSQL is running
echo "Checking PostgreSQL..."
if ! docker ps | grep -q postgres; then
    echo "Starting PostgreSQL with Docker Compose..."
    docker-compose up -d
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Create audio storage directory
mkdir -p audio_storage

echo ""
echo "✅ VoxTrace is ready!"
echo ""
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start the application
python main.py
