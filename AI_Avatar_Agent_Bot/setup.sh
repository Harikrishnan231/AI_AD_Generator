#!/bin/bash

echo "🔧 Starting setup..."

# Optional: Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create necessary folders
mkdir -p images outputs temp

echo "✅ Setup complete!"
echo "🚀 Run your app with: streamlit run New.py"
