@echo off
title EduPath - Personalized Tutoring Agent (FastAPI + React)
echo ========================================================
echo Starting EduPath: FastAPI Backend + React Frontend
echo ========================================================

echo [1/2] Launching FastAPI Backend on http://localhost:8000...
start "EduPath Backend (FastAPI)" cmd /k "call "%USERPROFILE%\anaconda3\Scripts\activate.bat" langgraph_env && uvicorn server:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Launching React Vite Frontend on http://localhost:5173...
start "EduPath Frontend (React)" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul
echo.
echo ========================================================
echo EduPath is running!
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo ========================================================
pause
