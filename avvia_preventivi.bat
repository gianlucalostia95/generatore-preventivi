@echo off
cd /d "%~dp0"
start "Generatore Preventivi - server" /min "%~dp0venv\Scripts\python.exe" -m streamlit run "%~dp0Generazione_Preventivo.py" --server.headless true --server.port 8501 --browser.gatherUsageStats false
timeout /t 3 /nobreak >nul
start "" http://localhost:8501
