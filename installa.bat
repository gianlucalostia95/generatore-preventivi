@echo off
cd /d "%~dp0"

echo ============================================
echo   Generatore di Preventivi - Installazione
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERRORE: Python non trovato. Installa Python da https://www.python.org/downloads/
    echo Durante l'installazione, spunta l'opzione "Add python.exe to PATH".
    pause
    exit /b 1
)

echo Creazione ambiente virtuale in "venv"...
python -m venv venv

echo Installazione delle dipendenze...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
"%~dp0venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo ============================================
echo   Installazione completata!
echo ============================================
echo Per avviare l'app, fai doppio click su "avvia_preventivi.bat"
echo (oppure esegui "crea_icona_desktop.bat" per creare un'icona sul desktop).
echo.
pause
