@echo off
title Arret de Dry-Voice-Omni
echo Fermeture du serveur Dry-Voice-Omni en cours...

:: Termine tous les processus Python qui executent app.py
wmic process where "name='python.exe' and commandline like '%%app.py%%'" call terminate >nul 2>&1

echo.
echo Le serveur a ete arrete avec succes.
timeout /t 3 >nul
