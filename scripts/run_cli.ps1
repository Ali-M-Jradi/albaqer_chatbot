# ===================================================
# Run Chatbot - Command Line Interface
# ===================================================
# This script activates the virtual environment and runs the chatbot in CLI mode

Write-Host "🤖 Starting AlBaqer Chatbot (CLI)..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run command line chatbot
Write-Host "💬 Launching CLI..." -ForegroundColor Green
python main.py
