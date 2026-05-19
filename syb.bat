@echo off
python -m syb_game %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 按任意键退出...
    pause >nul
)