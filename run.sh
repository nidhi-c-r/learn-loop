#!/bin/bash

echo "==============================="
echo "  LearnLoop - Starting up..."
echo "==============================="

# Check for .env
if [ ! -f .env ]; then
  echo "⚠  No .env file found. Creating one..."
  echo "ANTHROPIC_API_KEY=your_key_here" > .env
  echo "Please add your Anthropic API key to .env then rerun this script."
  exit 1
fi

# Install spacy model if not present
python -m spacy info en_core_web_sm &>/dev/null || {
  echo "Downloading spaCy model..."
  python -m spacy download en_core_web_sm
}

echo "Starting FastAPI backend on port 8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "Starting Streamlit frontend on port 8501..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "✅ LearnLoop is running!"
echo "   Frontend → http://localhost:8501"
echo "   API docs → http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
