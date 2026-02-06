# ===================================================
# Run Chatbot - Streamlit UI
# ===================================================
# This script activates the virtual environment and runs the chatbot

Write-Host "🤖 Starting AlBaqer Chatbot..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& "..\venv\Scripts\Activate.ps1"

# Run Streamlit app
Write-Host "🌐 Launching Streamlit UI..." -ForegroundColor Green
Set-Location ..
streamlit run streamlit_ui_app.py
