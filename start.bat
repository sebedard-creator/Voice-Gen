@echo off
title Dry-Voice-Omni Server
cd /d "%~dp0"

:: Vérifier si FFmpeg local est installé, sinon lancer le setup
IF NOT EXIST "bin\ffmpeg.exe" (
    echo [Installation Initiale] Telechargement de FFmpeg local en cours...
    python setup_ffmpeg.py
)

:: Vérifier si les dépendances python sont installées
python -c "import anthropic, google.genai" >nul 2>&1
IF ERRORLEVEL 1 (
    echo [Installation Initiale] Installation / Mise a jour des dependances Python...
    pip install -r requirements.txt
)

echo.
echo ===================================================
echo   Lancement de Dry-Voice-Omni...
echo   Laissez cette fenetre ouverte pendant l'utilisation.
echo ===================================================
echo.

python app.py
pause
