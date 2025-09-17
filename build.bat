@echo off
echo Установка зависимостей...
pip install -r requirements.txt

echo Очистка старых файлов...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
del Achromatopsia.spec 2>nul

echo Сборка Achromatopsia...
pyinstaller --onefile ^
            --name=Achromatopsia ^
            --add-data "assets;assets" ^
            --add-data "scenes;scenes" ^
            --icon=assets/icon.ico ^
            --noconsole ^
            --hidden-import=PySide6 ^
            --hidden-import=PySide6.QtCore ^
            --hidden-import=PySide6.QtGui ^
            --hidden-import=PySide6.QtWidgets ^
            --hidden-import=PySide6.QtMultimedia ^
            --hidden-import=PySide6.QtSvgWidgets ^
            main.py

echo Сборка завершена!
dir dist
pause