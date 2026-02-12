"""
Market Health Check - Scheduled Task Script
Runs every 5 minutes to ensure trading system is running during market hours
"""
import sys
import os
import subprocess
import requests
import json
from datetime import datetime, timedelta

# Configuration
TELEGRAM_TOKEN = "8574660647:AAF74d8rgkcgMdUtLcRlSenQjNmlPl_eZ8Y"
TELEGRAM_CHAT_ID = "8402314009"
SCRIPT_PATH = "C:/Users/lulg/.openclaw/workspace/volatility_trading_system/realtime_trader.py"
LOG_PATH = "C:/Users/lulg/.openclaw/workspace/volatility_trading_system/logs/health_check.log"


def log(message: str):
    """Log to file"""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


def send_telegram(message: str):
    """Send Telegram notification"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=data, timeout=10)
        print(f"[TELEGRAM] Sent: {message[:80]}...")
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


def is_market_open() -> tuple:
    """Check if US market is open"""
    now_utc = datetime.utcnow()
    # Paris is UTC+1, ET is UTC-5
    now_et = now_utc - timedelta(hours=6)
    
    hour = now_et.hour
    minute = now_et.minute
    total_minutes = hour * 60 + minute
    
    # Market: 9:30 AM - 4:00 PM ET
    open_minutes = 9 * 60 + 30  # 570
    close_minutes = 16 * 60  # 960
    
    is_open = total_minutes >= open_minutes and total_minutes < close_minutes
    
    minutes_until_close = 0
    if is_open:
        minutes_until_close = close_minutes - total_minutes
    
    return is_open, hour, minutes_until_close


def is_process_running() -> bool:
    """Check if trading process is running"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            capture_output=True, text=True
        )
        # Check if realtime_trader.py is in the command line
        for line in result.stdout.split('\n'):
            if 'python.exe' in line and 'realtime_trader' in line:
                return True
        return False
    except:
        return False


def start_trading():
    """Start the trading system"""
    try:
        log("Starting trading system...")
        
        process = subprocess.Popen(
            [sys.executable, SCRIPT_PATH],
            cwd=os.path.dirname(SCRIPT_PATH),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        message = """🔄 *Trading System Restarted*

Issue: System was not running during market hours
Action: Auto-restarted successfully

Please monitor for normal operation."""
        send_telegram(message)
        log("Trading system started")
        
        return True
        
    except Exception as e:
        log(f"Failed to start trading: {e}")
        error_msg = f"""❌ *Trading System Error*

Failed to auto-restart:
```
{e}
```

Manual intervention required."""
        send_telegram(error_msg)
        return False


def stop_trading():
    """Stop the trading system"""
    try:
        subprocess.run(
            ['taskkill', '/F', '/FI', 'COMMANDLINE eq *realtime_trader*'],
            capture_output=True
        )
        log("Trading system stopped")
        return True
    except:
        return False


def main():
    """Main health check"""
    print("="*60)
    print("  MARKET HEALTH CHECK")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    is_open, et_hour, minutes_left = is_market_open()
    running = is_process_running()
    
    print(f"\nMarket Status: {'OPEN' if is_open else 'CLOSED'} ({et_hour}:00 ET)")
    print(f"Trading Running: {'YES' if running else 'NO'}")
    
    action_taken = "none"
    
    if is_open:
        if not running:
            print("\n⚠️  MARKET OPEN but trading NOT running!")
            print("Starting trading system...")
            if start_trading():
                action_taken = "started"
            else:
                action_taken = "start_failed"
        else:
            print("\n✅ Market open, trading is running - all good!")
            action_taken = "healthy"
    else:
        if running:
            print("\n⚠️  MARKET CLOSED but trading still running!")
            print("Stopping trading system...")
            if stop_trading():
                action_taken = "stopped"
            else:
                action_taken = "stop_failed"
        else:
            print("\n✅ Market closed, trading is stopped - all good!")
            action_taken = "healthy"
    
    # Log result
    status = "healthy" if action_taken == "healthy" else action_taken
    log(f"Status: {status}")
    
    print(f"\nAction: {action_taken}")
    print("="*60)
    
    # Return exit code for scheduled task
    if action_taken in ["start_failed", "stop_failed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
