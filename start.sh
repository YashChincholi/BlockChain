#!/bin/bash

# Start script for Production-Ready Blockchain Application

echo "========================================="
echo "Production-Ready Blockchain Application"
echo "========================================="
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
pip install -r requirements.txt

# Create necessary directories
mkdir -p data logs

# Set environment variables
export FLASK_ENV=development
export MINING_DIFFICULTY=4

echo ""
echo "========================================="
echo "Starting Flask application..."
echo "========================================="
echo ""
echo "Access the application at: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
python run.py
