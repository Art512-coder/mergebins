#!/bin/bash

# Start BIN Search Bot - Linux/macOS

echo "Starting BIN Search Bot..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if required files exist
if [ ! -f "data/merged_bin_data.csv" ]; then
    echo "Error: BIN data file not found at data/merged_bin_data.csv"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using default configuration."
    echo "Please create .env file from .env.example for production use."
    echo
fi

# Install dependencies if needed
echo "Installing/updating dependencies..."
pip3 install -r requirements.txt

# Start the bot
echo
echo "Starting Telegram Bot..."
echo "Bot will run in the background. Press Ctrl+C to stop."
echo

python3 run_bot.py