@echo off
:: Build TJ HubPush as a single-file Windows executable
:: Requirements: Python 3.9+ with venv at .venv\

echo.
echo ============================================================
echo   TJ HubPush - Build EXE
echo ============================================================
echo.

:: Check venv exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: .venv not found. Run setup.bat first.
    pause
    exit /b 1
)

:: Install PyInstaller if needed
echo [1/3] Checking PyInstaller...
.venv\Scripts\python.exe -c "import PyInstaller" 2>nul || (
    echo Installing PyInstaller...
    .venv\Scripts\pip.exe install pyinstaller --quiet
)

:: Build
echo [2/3] Building executable...
.venv\Scripts\pyinstaller.exe ^
    --onefile ^
    --windowed ^
    --name "TJHubPush" ^
    --add-data "output v2 all fields FULL.resume.xlsx;." ^
    hs_app.py

echo.
echo [3/3] Done.
echo.
echo Executable location: dist\TJHubPush.exe
echo.
pause
