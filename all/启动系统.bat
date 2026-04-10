@echo off
echo 正在启动微小型无人机智能风场测试评估系统...
echo.

REM 激活my_env环境
call D:\ProgramData\Anaconda3\Scripts\activate.bat my_env

REM 切换到项目目录
cd /d F:\A-User\cliff\allin\all

REM 启动程序
python main.py

pause
