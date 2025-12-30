@echo off
echo 🚀 Starting Twitter Agent Server...
echo.
echo 💡 This will start a persistent web server that keeps your Twitter agent running
echo 🌐 You can access it at: http://localhost:5000
echo 🔄 No need to restart - just refresh the browser!
echo.
echo ⚡ Starting in 3 seconds... (Press Ctrl+C to cancel)
timeout /t 3 /nobreak > nul

python server.py

echo.
echo 📡 Server stopped. Press any key to exit...
pause > nul 