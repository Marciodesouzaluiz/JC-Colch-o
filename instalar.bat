@echo off
echo ============================================
echo  Portal JC Colchao - Iniciando
echo ============================================
echo.

cd /d %~dp0
echo Pasta: %CD%
echo.

echo Verificando Python do portal...
set PYTHON=C:\Users\ameri\AppData\Local\Programs\Python\Python313\python.exe
if not exist "%PYTHON%" (
    echo [ERRO] Python nao encontrado em:
    echo   %PYTHON%
    echo.
    pause
    exit /b 1
)
echo [OK] Python encontrado.
echo.

echo Verificando app.py...
if not exist "app.py" (
    echo [ERRO] app.py nao encontrado!
    echo Este .bat deve estar na mesma pasta que app.py
    echo.
    pause
    exit /b 1
)
echo [OK] app.py encontrado.
echo.

echo ============================================
echo  Iniciando servidor...
echo.
echo  Abra no navegador:
echo    Portal:  http://localhost:5000
echo    Admin:   http://localhost:5000/admin/login
echo.
echo  Login do admin:
echo    Email: admin@jccolchao.com.br
echo    Senha: admin@123
echo.
echo  Pressione CTRL+C para encerrar.
echo ============================================
echo.

%PYTHON% app.py

echo.
echo [INFO] Servidor encerrado.
pause
