"""
Market Hours Auto-Trader with Notifications & Health Check
Automatically runs during US market hours with restart capability
"""
import sys
import subprocess
import time
import requests
import os
from datetime import datetime, timedelta
from threading import Thread

# Telegram Configuration
TELEGRAM_TOKEN = "8574660647:AAF74d8rgkcgMdUtLcRlSenQjNmlPl_eZ8Y"
TELEGRAM_CHAT_ID = "8402314009"


def send_telegram(message: str):
    """Send notification to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data, timeout=10)
        print(f"[TELEGRAM] Sent: {message[:50]}...")
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


class MarketHoursTrader:
    """Auto-trader with notifications and health checks"""
    
    # US Market Hours (ET)
    MARKET_OPEN_ET = 9  # 9:30 AM
    MARKET_CLOSE_ET = 16  # 4:00 PM
    
    def __init__(self):
        self.process = None
        self.trading_active = False
        self.last_status = "unknown"
        self.check_interval = 60  # Check every 60 seconds
        self.script_path = "C:/Users/lulg/.openclaw/workspace/volatility_trading_system/realtime_trader.py"
        self.log_file = "C:/Users/lulg/.openclaw/workspace/volatility_trading_system/logs/market_hours.log"
    
    def is_market_open_et(self) -> tuple:
        """Check if US market is open (returns: is_open, hours, minutes_until_close)"""
        now_utc = datetime.utcnow()
        # ET is UTC-5 (standard) or UTC-4 (DST)
        # Paris is UTC+1, so ET = Paris - 6 hours
        now_et = now_utc - timedelta(hours=6)
        
        hour = now_et.hour
        minute = now_et.minute
        total_minutes = hour * 60 + minute
        
        # Market opens at 9:30 AM ET (570 minutes)
        # Market closes at 4:00 PM ET (960 minutes)
        open_minutes = 9 * 60 + 30  # 570
        close_minutes = 16 * 60  # 960
        
        is_open = total_minutes >= open_minutes and total_minutes < close_minutes
        
        if is_open:
            minutes_until_close = close_minutes - total_minutes
            return True, hour, minutes_until_close
        else:
            return False, hour, 0
    
    def is_process_running(self) -> bool:
        """Check if trading process is running"""
        if not self.process:
            return False
        if self.process.poll() is not None:
            return False  # Process ended
        return True
    
    def start_trading(self) -> bool:
        """Start the trading system"""
        if self.is_process_running():
            if self.trading_active:
                return False  # Already running
            
        try:
            print("="*60)
            print("  STARTING TRADING SYSTEM")
            print("="*60)
            
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                cwd=os.path.dirname(self.script_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.trading_active = True
            
            # Send notification
            message = """📈 *Trading System Started*

Market: US Stock Market
Session: Realtime Trading
Symbols: 268 stocks
Mode: Automatic

Ready for trading!"""
            send_telegram(message)
            
            self.log(f"Trading system started successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start trading: {e}")
            error_msg = f"""❌ *Trading System Error*

Failed to start trading system:
```
{e}
```

Please check manually."""
            send_telegram(error_msg)
            return False
    
    def stop_trading(self) -> bool:
        """Stop the trading system"""
        if not self.is_process_running():
            return False  # Already stopped
        
        try:
            print("="*60)
            print("  STOPPING TRADING SYSTEM")
            print("="*60)
            
            self.process.terminate()
            self.process.wait(timeout=30)
            
            self.trading_active = False
            
            # Send notification
            message = """📉 *Trading System Stopped*

Market: US Stock Market Closed
Time: 4:00 PM ET / 10:00 PM Paris

Trading session ended successfully."""
            send_telegram(message)
            
            self.log(f"Trading system stopped successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to stop trading: {e}")
            return False
    
    def check_and_manage(self) -> str:
        """Check market status and manage trading system"""
        is_open, et_hour, minutes_left = self.is_market_open_et()
        
        status = "unknown"
        
        if is_open:
            if self.is_process_running():
                # System is running, market is open - good!
                status = "running"
                if self.last_status != "running":
                    message = f"""✅ *Trading System Active*

Market: OPEN
Time: {et_hour}:00 ET
Session: Realtime Trading
Stocks: 268
Minutes until close: {minutes_left}

System is running normally."""
                    send_telegram(message)
                    self.log(f"Market open - trading active")
            else:
                # Market is open but system is NOT running - RESTART!
                status = "restarting"
                if self.last_status != "restarting":
                    message = """⚠️ *Trading System Restarting*

Market: OPEN (was closed)
Action: Auto-restarting trading system...

Please wait for confirmation."""
                    send_telegram(message)
                
                if self.start_trading():
                    self.log(f"Market open - auto-restarted trading")
                else:
                    self.log(f"Failed to auto-restart trading")
        
        else:
            # Market is closed
            if self.is_process_running():
                # System is running but market closed - STOP!
                status = "stopping"
                if self.last_status != "stopping":
                    self.stop_trading()
                    self.log(f"Market closed - stopped trading")
            else:
                status = "stopped"
                if self.last_status not in ["stopped", "unknown"]:
                    self.log(f"Market closed - already stopped")
        
        self.last_status = status
        return status
    
    def log(self, message: str):
        """Log to file"""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a") as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass
    
    def run_loop(self):
        """Main monitoring loop with notifications"""
        print("\n" + "="*60)
        print("  MARKET HOURS AUTO-TRADER")
        print("  With Notifications & Health Check")
        print("="*60)
        print(f"Script: {self.script_path}")
        print(f"Check Interval: {self.check_interval}s")
        print(f"Log: {self.log_file}")
        print("="*60)
        
        # Initial check
        is_open, et_hour, _ = self.is_market_open_et()
        print(f"\n[INIT] Market Status: {'OPEN' if is_open else 'CLOSED'} ({et_hour}:00 ET)")
        
        while True:
            try:
                status = self.check_and_manage()
                
                # Status display
                is_open, et_hour, minutes_left = self.is_market_open_et()
                now = datetime.now().strftime("%H:%M:%S")
                process_status = "running" if self.is_process_running() else "stopped"
                
                if is_open:
                    print(f"\r[{now}] Market: OPEN | Trading: {process_status} | {minutes_left}min until close | Status: {status}", end="")
                else:
                    print(f"\r[{now}] Market: CLOSED | Trading: {process_status} | Status: {status}", end="")
                
                sys.stdout.flush()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\n[STOPPING] User interrupt...")
                self.stop_trading()
                break
            
            except Exception as e:
                print(f"\n[ERROR] {e}")
                self.log(f"Error: {e}")
                time.sleep(self.check_interval)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Market Hours Auto-Trader with Notifications")
    parser.add_argument("--check", action="store_true", help="Run single check")
    parser.add_argument("--start", action="store_true", help="Start trading")
    parser.add_argument("--stop", action="store_true", help="Stop trading")
    parser.add_argument("--status", action="store_true", help="Check status")
    parser.add_argument("--loop", action="store_true", help="Run monitoring loop")
    
    args = parser.parse_args()
    
    trader = MarketHoursTrader()
    
    if args.check:
        status = trader.check_and_manage()
        print(f"Status: {status}")
    
    elif args.start:
        trader.start_trading()
    
    elif args.stop:
        trader.stop_trading()
    
    elif args.status:
        is_open, et_hour, minutes_left = trader.is_market_open_et()
        running = trader.is_process_running()
        print(f"Market: {'OPEN' if is_open else 'CLOSED'} ({et_hour}:00 ET)")
        print(f"Trading: {'RUNNING' if running else 'STOPPED'}")
        if is_open:
            print(f"Minutes until close: {minutes_left}")
    
    elif args.loop:
        trader.run_loop()
    
    else:
        print("Usage:")
        print("  --check   Run single health check")
        print("  --start   Start trading system")
        print("  --stop    Stop trading system")
        print("  --status  Show current status")
        print("  --loop    Run monitoring loop (auto-manage)")


if __name__ == "__main__":
    main()
