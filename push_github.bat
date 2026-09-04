@echo off
echo ============================================
echo   PUSH DO PORTAL JC COLCHAO PARA O GITHUB
echo ============================================
echo.

set PATH=%LOCALAPPDATA%\PortableGit\bin;%LOCALAPPDATA%\PortableGit\mingw64\bin;%PATH%

cd /d "C:\Users\ameri\Documents\jccolchao_portal"

echo Enviando codigo para o GitHub...
echo Uma janela de login pode aparecer. Faca o login!
echo.

git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ============================================
    echo   SUCESSO! Codigo enviado para o GitHub!
    echo ============================================
) else (
    echo ============================================
    echo   ERRO ao enviar. Verifique o login.
    echo ============================================
)
echo.
pause
