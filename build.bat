@echo off
echo === Conversor de fotos iPhone a PNG - script de compilacion ===
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python en el PATH. Instala Python 3.10+ desde python.org
    echo y marca la opcion "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo Creando entorno virtual...
python -m venv venv
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt

echo Compilando el ejecutable (puede tardar varios minutos)...
pyinstaller --onefile --windowed --name "ConversorFotos" --collect-all tkinterdnd2 --collect-all pillow_heif app.py

echo.
echo Listo. El ejecutable quedo en dist\ConversorFotos.exe
pause
