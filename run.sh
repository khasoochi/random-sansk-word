#!/bin/bash

# Flask App Runner Script

echo "🕉️  Random Sanskrit Word Generator"
echo "===================================="
echo ""

# Check if dictionary files exist
if [ ! -f "sanskrit_dictionary.json" ]; then
    echo "📚 Dictionary files not found. Parsing Babylon dictionaries..."
    python3 parse_dictionaries.py
    echo ""
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip install --user Flask Werkzeug
    echo ""
fi

echo "🚀 Starting Flask server..."
echo "📱 Open your browser and visit: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
