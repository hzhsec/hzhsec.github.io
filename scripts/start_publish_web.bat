@echo off
chcp 65001 > nul
cd /d "%~dp0.."
start "Obsidian ???" cmd /k "python scripts\publish_web.py"
timeout /t 2 /nobreak > nul
start "" "http://10.22.167.164:8765/"
