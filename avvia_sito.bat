@echo off
cd /d "%~dp0"
start "Generatore Preventivi - sito web" /min "%~dp0venv\Scripts\python.exe" -m uvicorn webapp.main:app --host 127.0.0.1 --port 8443 --ssl-keyfile certs\localhost-key.pem --ssl-certfile certs\localhost-cert.pem
timeout /t 3 /nobreak >nul
start "" https://localhost:8443
