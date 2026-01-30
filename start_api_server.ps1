# ===================================================
# Start Chatbot API Server for Flutter Integration
# ===================================================

Write-Host "🤖 Starting AlBaqer Chatbot API Server..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Show server info
Write-Host "📡 Server Configuration:" -ForegroundColor Green
Write-Host "   Local:            http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "   Network:          http://192.168.179.1:8000" -ForegroundColor Yellow
Write-Host "   Android Emulator: http://10.0.2.2:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "📱 Flutter is configured to use: http://192.168.179.1:8000/api" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 API Endpoints:" -ForegroundColor Green
Write-Host "   Health:  GET  /api/health" -ForegroundColor Gray
Write-Host "   Chat:    POST /api/chat" -ForegroundColor Gray
Write-Host "   History: GET  /api/chat/history/{user_id}" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Starting server..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start the FastAPI server
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
