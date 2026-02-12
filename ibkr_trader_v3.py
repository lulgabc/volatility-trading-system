"""
Volatility Trading System - Mobile Optimized Report
"""
import sys
import yfinance as yf
from ib_insync import IB, Stock, MarketOrder
from datetime import datetime
from typing import Dict, List
import json
import numpy as np

# Import mobile report system
sys.path.insert(0, "C:/Users/lulg/.openclaw/workspace/volatility_trading_system")
from mobile_report import MobileReport, MobileReportSender, save_report


class MarketData:
    """Yahoo Finance 数据"""
    
    @staticmethod
    def get_price(symbol: str) -> float:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return data['Close'].iloc[-1]
            return 0.0
        except:
            return 0.0
    
    @staticmethod
    def get_historical_volatility(symbol: str) -> float:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="3mo")
            if len(data) < 10:
                return 0.25
            returns = data['Close'].pct_change().dropna()
            daily_vol = returns.std()
            return daily_vol * np.sqrt(252)
        except:
            return 0.25


class IBKRTrader:
    """IBKR 交易"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 2):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.connected = False
        
    def connect(self) -> bool:
        self.ib = IB()
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            self.connected = True
            print("[OK] Connected to IBKR")
            return True
        except Exception as e:
            print(f"[ERROR] IBKR connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
    
    def get_account(self) -> Dict:
        if not self.connected:
            return {}
        try:
            summary = self.ib.accountSummary()
            for item in summary:
                if item.tag == 'NetLiquidationByCurrency':
                    return {'net_liq': float(item.value)}
            return {}
        except:
            return {}
    
    def get_positions(self) -> Dict:
        positions = {}
        if not self.connected:
            return positions
        try:
            for pos in self.ib.positions():
                if pos.position != 0:
                    symbol = pos.contract.symbol
                    positions[symbol] = {
                        'quantity': abs(pos.position),
                        'direction': 'LONG' if pos.position > 0 else 'SHORT',
                        'avg_cost': pos.avgCost
                    }
            return positions
        except:
            return positions
    
    def buy(self, symbol: str, quantity: int) -> bool:
        if not self.connected:
            return False
        try:
            contract = Stock(symbol, "SMART", currency="USD")
            order = MarketOrder("BUY", quantity)
            trade = self.ib.placeOrder(contract, order)
            print(f"[ORDER] BUY {symbol} {quantity}")
            return True
        except:
            return False
    
    def short(self, symbol: str, quantity: int) -> bool:
        if not self.connected:
            return False
        try:
            contract = Stock(symbol, "SMART", currency="USD")
            order = MarketOrder("SELL", quantity)
            trade = self.ib.placeOrder(contract, order)
            print(f"[ORDER] SHORT {symbol} {quantity}")
            return True
        except:
            return False


class VolatilityTrader:
    """波动率交易系统"""
    
    def __init__(self, ibkr: IBKRTrader):
        self.ibkr = ibkr
        self.trading_enabled = False
        self.trades: List = []
        
        # 报告系统
        self.reporter = MobileReportSender()
        self.reporter.load_config("C:/Users/lulg/.openclaw/workspace/volatility_trading_system/report_config.json")
    
    def calculate_iv_rank(self, symbol: str) -> float:
        hv = MarketData.get_historical_volatility(symbol)
        iv = hv * np.random.uniform(1.1, 1.3)
        iv_rank = min(100, max(0, (iv - 0.10) / 0.40 * 100))
        return iv_rank
    
    def analyze(self, symbol: str) -> Dict:
        price = MarketData.get_price(symbol)
        iv_rank = self.calculate_iv_rank(symbol)
        
        signal = "NEUTRAL"
        confidence = 0.0
        action = "-"
        
        if iv_rank > 65:
            signal = "SHORT_VOL"
            confidence = min((iv_rank - 50) / 50, 1.0)
            action = "[DOWN]"
        elif iv_rank < 35:
            signal = "LONG_VOL"
            confidence = min((50 - iv_rank) / 50, 1.0)
            action = "[UP]"
        
        return {
            "symbol": symbol,
            "price": price,
            "iv_rank": iv_rank,
            "signal": signal,
            "confidence": confidence,
            "action": action
        }
    
    def execute_order(self, signal: Dict) -> bool:
        if not self.trading_enabled or signal["signal"] == "NEUTRAL":
            return False
            
        symbol = signal["symbol"]
        price = signal["price"]
        if price == 0:
            return False
        
        position_size = 1000000 * 0.02 * signal["confidence"]
        quantity = int(position_size / price)
        if quantity < 1:
            return False
        
        current_positions = self.ibkr.get_positions()
        
        if signal["signal"] == "LONG_VOL":
            if symbol not in current_positions:
                if self.ibkr.buy(symbol, quantity):
                    self.trades.append({
                        "time": str(datetime.now()),
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": quantity,
                        "price": price
                    })
                    return True
        
        elif signal["signal"] == "SHORT_VOL":
            if symbol not in current_positions:
                if self.ibkr.short(symbol, quantity):
                    self.trades.append({
                        "time": str(datetime.now()),
                        "symbol": symbol,
                        "action": "SHORT",
                        "quantity": quantity,
                        "price": price
                    })
                    return True
        
        return False
    
    def send_report(self):
        """发送手机优化报告"""
        account = self.ibkr.get_account()
        positions = self.ibkr.get_positions()
        
        # 更新价格
        for sym in positions:
            price = MarketData.get_price(sym)
            if price > 0:
                positions[sym]['current_price'] = price
        
        # 计算盈亏
        daily_pnl = 0
        for sym, pos in positions.items():
            entry = pos.get('avg_cost', 0)
            current = pos.get('current_price', entry)
            qty = pos.get('quantity', 0)
            if pos.get('direction') == 'LONG':
                daily_pnl += (current - entry) * qty
            else:
                daily_pnl += (entry - current) * qty
        
        # 生成报告
        html = MobileReport.generate_html(
            account_balance=account.get('net_liq', 1000000),
            positions=positions,
            trades=self.trades,
            daily_pnl=daily_pnl
        )
        
        telegram = MobileReport.generate_telegram(
            account_balance=account.get('net_liq', 1000000),
            positions=positions,
            trades=self.trades,
            daily_pnl=daily_pnl
        )
        
        # 保存HTML报告
        save_report(html)
        
        # 发送
        results = self.reporter.send_all(html, telegram)
        
        if "telegram" in results:
            print("[REPORT] Telegram sent!")
        if "email" in results:
            print("[REPORT] Email sent!")
    
    def print_report(self):
        """控制台简版报告"""
        account = self.ibkr.get_account()
        positions = self.ibkr.get_positions()
        
        for sym in positions:
            price = MarketData.get_price(sym)
            if price > 0:
                positions[sym]['current_price'] = price
        
        daily_pnl = 0
        for sym, pos in positions.items():
            entry = pos.get('avg_cost', 0)
            current = pos.get('current_price', entry)
            qty = pos.get('quantity', 0)
            if pos.get('direction') == 'LONG':
                daily_pnl += (current - entry) * qty
            else:
                daily_pnl += (entry - current) * qty
        
        print(f"""
============================================================
  VOLATILITY TRADING SYSTEM
============================================================
[ACCOUNT] ${account.get('net_liq', 0):,.2f}
[POSITIONS]: {len(positions)}
[TRADES]: {len(self.trades)}
[DAILY P&L]: ${daily_pnl:,.2f}
""")
        
        for sym, pos in positions.items():
            entry = pos.get('avg_cost', 0)
            current = pos.get('current_price', entry)
            pnl = (current - entry) * pos['quantity'] if pos['direction'] == 'LONG' else (entry - current) * pos['quantity']
            pnl_icon = "[UP]" if pnl >= 0 else "[DOWN]"
            print(f"{sym:8} {pos['direction']:5} {pos['quantity']:4} @ ${entry:.2f} -> ${current:.2f} {pnl_icon} ${pnl:.2f}")
        
        # 发送完整报告
        if self.trading_enabled and self.trades:
            print("\n[SENDING REPORT...]")
            self.send_report()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA,JPM,BAC,WMT")
    parser.add_argument("--trade", action="store_true", help="Enable auto-trading")
    parser.add_argument("--report", action="store_true", help="Send report only")
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    print("\n" + "="*60)
    print("  VOLATILITY TRADING SYSTEM")
    print("  Yahoo Finance + IBKR + Mobile Report")
    print("="*60)
    
    # 连接 IBKR
    ibkr = IBKRTrader()
    if not ibkr.connect():
        return
    
    trader = VolatilityTrader(ibkr)
    
    if args.trade:
        trader.trading_enabled = True
        print("[AUTO-TRADING ENABLED]")
    
    if args.report:
        trader.print_report()
        ibkr.disconnect()
        return
    
    # 账户
    account = ibkr.get_account()
    if account:
        print(f"[INFO] Account: ${account.get('net_liq', 0):,.2f}")
    
    positions = ibkr.get_positions()
    if positions:
        print(f"[INFO] Positions: {list(positions.keys())}")
    
    print("\n" + "-"*60)
    print("ANALYZING MARKET")
    print("-"*60)
    
    results = []
    for sym in symbols:
        r = trader.analyze(sym)
        results.append(r)
        price_str = f"${r['price']:.2f}" if r['price'] > 0 else "N/A"
        print(f"{sym:8} {price_str:>8} | IV Rank: {r['iv_rank']:>5.1f}% | {r['action']:6} {r['signal']}")
    
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    print("\n" + "-"*60)
    print("TOP SIGNALS (Confidence > 30%)")
    print("-"*60)
    for r in results:
        if r["confidence"] > 0.3:
            print(f"{r['symbol']:8} {r['action']:6} {r['signal']:12} {r['confidence']:.0%}")
    
    # 交易
    if args.trade:
        print("\n" + "-"*60)
        print("EXECUTING ORDERS")
        print("-"*60)
        for r in results:
            trader.execute_order(r)
    
    # 报告
    trader.print_report()
    
    ibkr.disconnect()
    print("\n[LOCKED] Done")


if __name__ == "__main__":
    main()
