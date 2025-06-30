@echo off
chcp 65001 >nul
echo Starting Amazon Restock Tool Deployment...
echo.

REM Check Python version
echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not installed, please install Python 3.7+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing project dependencies...
pip install -r requirements.txt
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "data" mkdir data
echo Directories created successfully
echo.

REM Check configuration file
echo Checking configuration file...
if not exist "config\server.env" (
    echo WARNING: Server configuration file not found
    echo Please edit config\server.env to configure server settings
) else (
    echo Server configuration file exists
)

REM Create .env symlink if it doesn't exist
if not exist ".env" (
    echo Creating .env link to config\server.env...
    copy "config\server.env" ".env" >nul
    echo .env file created
)
echo.

REM Test run
echo Testing program...
python main.py --help >nul 2>&1
if %errorlevel% equ 0 (
    echo Program test run successful
) else (
    echo WARNING: Program test run failed, please check configuration
)
echo.

echo Deployment completed!
echo.
echo Next steps:
echo 1. Edit config\server.env file to configure server settings
echo 2. Run interactive mode: python main.py --interactive
echo 3. Run server mode: python main.py --server
echo 4. Check environment: python main.py --check-env
echo 5. Test API connection: python main.py --test
echo.
echo Server will run on: http://192.168.0.99:8000
echo.
echo For more information, see README.md
echo.
pause