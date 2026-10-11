@echo off
echo Arresto del sito web Generatore di Preventivi in corso...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8443 ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>&1
echo Fatto.
pause
