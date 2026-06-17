@echo off
echo.
echo ============================================
echo  Copiloto Administrativo UdeA
echo ============================================
echo.
echo [1/2] Iniciando backend FastAPI en puerto 8000...
start "Backend UdeA" cmd /k "cd /d %~dp0 && py -m uvicorn backend.main:app --reload --port 8000"

echo [2/2] Iniciando frontend React en puerto 5173...
timeout /t 3 /nobreak > nul
start "Frontend UdeA" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Abriendo navegador en 8 segundos...
timeout /t 8 /nobreak > nul
start http://localhost:5173
echo.
echo Sistema iniciado. Cierra las ventanas para detenerlo.
