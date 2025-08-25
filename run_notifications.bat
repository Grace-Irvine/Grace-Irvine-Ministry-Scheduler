@echo off
REM Grace Irvine Ministry Scheduler - Windows 批处理脚本
REM 用于生成微信群通知

echo ================================================
echo Grace Irvine Ministry Scheduler
echo ================================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查是否安装了依赖包
if not exist .venv (
    echo 正在创建虚拟环境...
    python -m venv .venv
)

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo 安装/更新依赖包...
pip install -r simple_requirements.txt

echo.
echo 选择要生成的通知类型:
echo 1. 周三确认通知
echo 2. 周六提醒通知  
echo 3. 月度总览通知
echo 4. 生成所有通知
echo 5. 数据验证
echo.

set /p choice="请输入选择 (1-5): "

if "%choice%"=="1" (
    python generate_notifications.py weekly
) else if "%choice%"=="2" (
    python generate_notifications.py sunday
) else if "%choice%"=="3" (
    python generate_notifications.py monthly
) else if "%choice%"=="4" (
    python generate_notifications.py all
) else if "%choice%"=="5" (
    python check_data.py
) else (
    echo 无效选择
)

echo.
echo 按任意键退出...
pause >nul
