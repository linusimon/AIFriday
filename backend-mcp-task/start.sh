#!/bin/bash
echo "Starting Intelligent Task Routing Backend..."

# Load pyenv if available
if command -v pyenv &> /dev/null; then
    eval "$(pyenv init --path)" 2>/dev/null
    eval "$(pyenv init -)" 2>/dev/null
fi

# Activate virtual environment
source venv/bin/activate

# Start Flask application
echo "Starting Flask server on port 5004..."
python app.py

read -p "Press Enter to continue..."
