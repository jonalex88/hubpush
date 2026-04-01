@echo off
:: First-time setup for TJ HubPush
:: Installs Python dependencies into a local .venv
echo.
echo ============================================================
echo   TJ HubPush - Setup
echo ============================================================
echo.

where python >nul 2>&1 || (
    echo ERROR: Python not found. Install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
) else (
    echo [1/3] Virtual environment already exists.
)

echo [2/3] Installing dependencies...
.venv\Scripts\pip.exe install --quiet ^
    openpyxl ^
    pypdf ^
    PyMuPDF ^
    pytesseract ^
    Pillow ^
    requests

echo [3/3] Setup complete.
echo.
echo ============================================================
echo   Next Steps
echo ============================================================
echo.
echo To run the app:
echo   Double-click TJHubPush.bat
echo.
echo To build a standalone .exe:
echo   Run build_exe.bat
echo.
echo For cloud sync (Phase 2):
echo   1. See VERCEL_API_SPEC.md for Vercel deployment
echo   2. Once deployed, copy cloud.env.example to cloud.env
echo   3. Set HUBPUSH_CLOUD_BASE_URL and HUBPUSH_CLOUD_API_KEY
echo   4. Run: .\.venv\Scripts\python.exe phase2_sync.py --mode check --backend remote
echo.
echo For HubSpot push (Phase 3):
echo   1. Configure HubSpot API token in environment
echo   2. Run: .\.venv\Scripts\python.exe phase3_hubspot_examples.py (dry-run demo)
echo   3. See phase3_hubspot_examples.py for usage patterns
echo.
echo ============================================================
echo.
pause
