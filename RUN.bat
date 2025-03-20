@echo off
setlocal enabledelayedexpansion

REM 获取当前目录（自动处理结尾反斜杠）
set "current_dir=%~dp0"
if "%current_dir:~-1%"=="\" set "current_dir=%current_dir:~0,-1%"

REM 配置参数文件路径
set "ini_file=%current_dir%\config.ini"

REM 设置默认参数值
set "WD_MODEL=wd14-large"
set "WD_THRESHOLD=0.85"

REM 从INI文件读取参数
if exist "%ini_file%" (
    for /f "tokens=1,* delims== " %%a in ('type "%ini_file%" ^| findstr /i /c:"wd_model"') do (
        if /i "%%a"=="wd_model" set "WD_MODEL=%%b"
    )
    for /f "tokens=1,* delims== " %%a in ('type "%ini_file%" ^| findstr /i /c:"wd_threshold"') do (
        if /i "%%a"=="wd_threshold" set "WD_THRESHOLD=%%b"
    )
)

REM 启动API服务器窗口
start "WD14 Tagger API Server" cmd /k "call conda activate "%current_dir%\env" && cd /d "%current_dir%\wd14-tagger-api-server" && python -m wd14_tagger_api -d gpu -wdm %WD_MODEL% -wdt %WD_THRESHOLD%"

REM 等待服务启动
REM 等待服务启动
echo Waiting for API server initialization...
timeout /t 4 /nobreak >nul


REM 启动控制器程序
start "Tagger Controller" cmd /k "cd /d "%current_dir%" && python controller.py"

endlocal