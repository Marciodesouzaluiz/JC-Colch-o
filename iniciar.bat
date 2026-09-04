@echo off
echo ============================================
echo  Portal JC Colchao - Iniciando
echo ============================================

set PYTHON=C:\Users\ameri\AppData\Local\Programs\Python\Python313\python.exe

echo Iniciando o servidor na porta 5000...
start "Servidor JC Colchao" "%PYTHON%" app.py

echo Aguardando o servidor iniciar...
timeout /t 3 /nobreak >nul

echo Abrindo o portal no navegador...
start msedge --user-data-dir="%TEMP%\jccolchao_profile" --proxy-bypass-list="localhost,127.0.0.1,::1" "http://localhost:5000/admin/login"

echo.
echo ============================================
echo  O servidor foi iniciado em uma nova janela.
echo  O navegador ja deve ter sido aberto.
echo ============================================
pause
