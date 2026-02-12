@echo off
REM Quick setup for scheduled tasks
REM Run this as Administrator

echo Creating scheduled tasks...

REM Start task (3:30 PM Paris = 9:30 AM ET)
echo Creating Start task...
schtasks /create /TN "TradingSystem\Start" /TR "python C:\Users\lulg\.openclaw\workspace\volatility_trading_system\market_hours_trader.py --loop" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 15:30 /RL HIGHEST /F 2>nul
echo Start task: Done

REM Stop task (10:00 PM Paris = 4:00 PM ET)
echo Creating Stop task...
schtasks /create /TN "TradingSystem\Stop" /TR "python C:\Users\lulg\.openclaw\workspace\volatility_trading_system\market_hours_trader.py --stop" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 22:00 /RL HIGHEST /F 2>nul
echo Stop task: Done

REM Health check every 5 minutes
echo Creating HealthCheck task...
schtasks /create /TN "TradingSystem\HealthCheck" /TR "python C:\Users\lulg\.openclaw\workspace\volatility_trading_system\health_check.py" /SC MINUTELY /MO 5 /D MON,TUE,WED,THU,FRI /ST 15:35 /ET 22:00 /RL HIGHEST /F 2>nul
echo HealthCheck task: Done

echo.
echo Tasks created!
echo.
echo Verifying...
schtasks /query /TN "TradingSystem" 2>nul | findstr /I /C:"TradingSystem" && (
    echo.
    echo All tasks are active!
) || (
    echo.
    echo Please run as Administrator
)
