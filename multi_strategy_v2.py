"""
Multi-Strategy Volatility Trading System v2
IBKR Integration + Mobile Report
"""
import sys
import yfinance as yf
import numpy as np
from ib_insync import IB, Stock, MarketOrder
from datetime import datetime
from typing import Dict, List
import json

sys.path.insert(0, "C:/Users/lulg/.openclaw/workspace/volatility_trading_system")
from mobile_report import MobileReport, MobileReportSender, save_report


# ============ STRATEGIES ============

class Strategy:
    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        raise NotImplementedError


class IVRankStrategy(Strategy):
    def __init__(self):
        super().__init__("IVRank", 1.0)
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        iv_rank = data.get('iv_rank', 50)
        if iv_rank > 65:
            return {'signal': 'SHORT', 'confidence': min((iv_rank - 50) / 50, 1.0)}
        elif iv_rank < 35:
            return {'signal': 'LONG', 'confidence': min((50 - iv_rank) / 50, 1.0)}
        return {'signal': 'NEUTRAL', 'confidence': 0}


class VIXMeanReversionStrategy(Strategy):
    def __init__(self):
        super().__init__("VIXRev", 0.8)
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        vix = data.get('vix', 18)
        change = data.get('change_5d', 0)
        
        if vix > 25 and change < -3:
            return {'signal': 'LONG', 'confidence': 0.6}
        elif vix < 15 and change > 3:
            return {'signal': 'SHORT', 'confidence': 0.6}
        elif vix > 22:
            return {'signal': 'SHORT', 'confidence': 0.4}
        elif vix < 14:
            return {'signal': 'LONG', 'confidence': 0.4}
        return {'signal': 'NEUTRAL', 'confidence': 0}


class IVHVSpreadStrategy(Strategy):
    def __init__(self):
        super().__init__("IVHV", 0.7)
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        iv = data.get('iv', 0.25)
        hv = data.get('hv', 0.25)
        if hv == 0:
            return {'signal': 'NEUTRAL', 'confidence': 0}
        
        spread = (iv - hv) / hv
        if spread > 0.3:
            return {'signal': 'SHORT', 'confidence': min(spread - 0.2, 0.8)}
        elif spread < -0.2:
            return {'signal': 'LONG', 'confidence': min(-spread * 0.5, 0.6)}
        return {'signal': 'NEUTRAL', 'confidence': 0}


class MomentumStrategy(Strategy):
    def __init__(self):
        super().__init__("Momentum", 0.6)
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        c5 = data.get('change_5d', 0)
        c20 = data.get('change_20d', 0)
        iv = data.get('iv_rank', 50)
        
        if c5 > 3 and c20 > 5 and iv < 50:
            return {'signal': 'LONG', 'confidence': 0.5}
        if c5 < -3 and c20 < -5 and iv > 50:
            return {'signal': 'SHORT', 'confidence': 0.5}
        return {'signal': 'NEUTRAL', 'confidence': 0}


class ContrarianStrategy(Strategy):
    def __init__(self):
        super().__init__("Contra", 0.5)
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        c5 = data.get('change_5d', 0)
        iv = data.get('iv_rank', 50)
        
        if c5 < -5 and iv > 70:
            return {'signal': 'LONG', 'confidence': 0.6}
        if c5 > 5 and iv < 30:
            return {'signal': 'SHORT', 'confidence': 0.6}
        return {'signal': 'NEUTRAL', 'confidence': 0}


class TrendStrategy(Strategy):
    def __init__(self):
        super().__init__("Trend", 0.5)
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        price = data.get('price', 0)
        sma20 = data.get('sma_20', 0)
        sma50 = data.get('sma_50', 0)
        c5 = data.get('change_5d', 0)
        
        if price > sma20 > sma50 and c5 > 0:
            return {'signal': 'LONG', 'confidence': 0.5}
        if price < sma20 < sma50 and c5 < 0:
            return {'signal': 'SHORT', 'confidence': 0.5}
        return {'signal': 'NEUTRAL', 'confidence': 0}


# ============ TRADING SYSTEM ============

class MarketData:
    @staticmethod
    def get_data(symbol: str) -> Dict:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            hist5d = ticker.history(period="5d")
            
            if hist.empty:
                return {}
            
            price = hist['Close'].iloc[-1]
            c5 = ((hist5d['Close'].iloc[-1] - hist5d['Close'].iloc[0]) / hist5d['Close'].iloc[0] * 100) if len(hist5d) > 1 else 0
            
            returns = hist['Close'].pct_change().dropna()
            hv = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.25
            iv = hv * np.random.uniform(1.1, 1.3)
            iv_rank = min(100, max(0, (iv - 0.10) / 0.40 * 100))
            
            sma20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else price
            sma50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else price
            
            try:
                vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
            except:
                vix = 18
            
            return {
                'symbol': symbol, 'price': price,
                'change_5d': c5, 'change_20d': 0,
                'hv': hv, 'iv': iv, 'iv_rank': iv_rank,
                'sma_20': sma20, 'sma_50': sma50, 'vix': vix
            }
        except:
            return {}


class IBKRTrader:
    def __init__(self, host="127.0.0.1", port=7497, client_id=3):
        self.host, self.port, self.client_id = host, port, client_id
        self.ib = None
        self.connected = False
    
    def connect(self) -> bool:
        self.ib = IB()
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            self.connected = True
            print("[OK] IBKR Connected")
            return True
        except Exception as e:
            print(f"[ERROR] IBKR: {e}")
            return False
    
    def disconnect(self):
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
    
    def get_account(self) -> Dict:
        if not self.connected:
            return {}
        try:
            for item in self.ib.accountSummary():
                if item.tag == 'NetLiquidationByCurrency':
                    return {'net_liq': float(item.value)}
        except:
            pass
        return {}
    
    def get_positions(self) -> Dict:
        positions = {}
        if not self.connected:
            return positions
        try:
            for pos in self.ib.positions():
                if pos.position != 0:
                    sym = pos.contract.symbol
                    positions[sym] = {
                        'quantity': abs(pos.position),
                        'direction': 'LONG' if pos.position > 0 else 'SHORT',
                        'avg_cost': pos.avgCost
                    }
            return positions
        except:
            return positions
    
    def buy(self, symbol: str, qty: int) -> bool:
        if not self.connected:
            return False
        try:
            contract = Stock(symbol, "SMART", currency="USD")
            self.ib.placeOrder(contract, MarketOrder("BUY", qty))
            print(f"[ORDER] BUY {symbol} {qty}")
            return True
        except:
            return False
    
    def sell(self, symbol: str, qty: int) -> bool:
        if not self.connected:
            return False
        try:
            contract = Stock(symbol, "SMART", currency="USD")
            self.ib.placeOrder(contract, MarketOrder("SELL", qty))
            print(f"[ORDER] SELL {symbol} {qty}")
            return True
        except:
            return False


class MultiStrategyTrader:
    def __init__(self, ibkr: IBKRTrader, symbols: List[str]):
        self.ibkr = ibkr
        self.symbols = symbols
        self.trading_enabled = False
        self.trades = []
        
        # 6 strategies
        self.strategies = [
            IVRankStrategy(),
            VIXMeanReversionStrategy(),
            IVHVSpreadStrategy(),
            MomentumStrategy(),
            ContrarianStrategy(),
            TrendStrategy(),
        ]
        
        # Report system
        self.reporter = MobileReportSender()
        self.reporter.load_config("C:/Users/lulg/.openclaw/workspace/volatility_trading_system/report_config.json")
    
    def analyze_all(self) -> List[Dict]:
        results = []
        
        print("\n" + "="*60)
        print("  MULTI-STRATEGY ANALYSIS")
        print("="*60)
        
        for symbol in self.symbols:
            data = MarketData.get_data(symbol)
            if not data:
                continue
            
            # Collect signals
            buy_score = 0
            sell_score = 0
            strategy_votes = []
            
            for s in self.strategies:
                sig = s.analyze(symbol, data)
                weighted = sig['confidence'] * s.weight
                if sig['signal'] == 'LONG':
                    buy_score += weighted
                    if sig['confidence'] > 0.3:
                        strategy_votes.append(f"{s.name}")
                elif sig['signal'] == 'SHORT':
                    sell_score += weighted
                    if sig['confidence'] > 0.3:
                        strategy_votes.append(f"{s.name}")
            
            # Final decision
            if buy_score > sell_score * 1.2:
                final = 'LONG'
                conf = buy_score / max(buy_score + sell_score, 0.1)
            elif sell_score > buy_score * 1.2:
                final = 'SHORT'
                conf = sell_score / max(buy_score + sell_score, 0.1)
            else:
                final = 'NEUTRAL'
                conf = 0
            
            # Print
            icon = "[BUY]" if final == 'LONG' else "[SELL]" if final == 'SHORT' else "[-]"
            change_icon = "+" if data['change_5d'] >= 0 else ""
            print(f"{symbol:8} ${data['price']:>7.2f} {change_icon}{data['change_5d']:>+5.1f}% | IV:{data['iv_rank']:>4.0f}% | {icon} {conf:.0%}")
            
            results.append({
                'symbol': symbol,
                'price': data['price'],
                'iv_rank': data['iv_rank'],
                'signal': final,
                'confidence': conf,
                'strategies': strategy_votes
            })
        
        return sorted(results, key=lambda x: x['confidence'], reverse=True)
    
    def execute(self, signals: List[Dict]):
        if not self.trading_enabled:
            return
        
        positions = self.ibkr.get_positions()
        
        for sig in signals:
            if sig['confidence'] < 0.3 or sig['signal'] == 'NEUTRAL':
                continue
            if sig['symbol'] in positions:
                continue
            
            price = sig['price']
            if price == 0:
                continue
            
            # Position size
            size = 1000000 * 0.02 * sig['confidence']
            qty = int(size / price)
            if qty < 1:
                continue
            
            if sig['signal'] == 'LONG':
                if self.ibkr.buy(sig['symbol'], qty):
                    self.trades.append({
                        'time': str(datetime.now()),
                        'symbol': sig['symbol'],
                        'action': 'BUY',
                        'quantity': qty,
                        'price': price,
                        'strategies': sig.get('strategies', []),
                        'confidence': sig['confidence']
                    })
            elif sig['signal'] == 'SHORT':
                if self.ibkr.sell(sig['symbol'], qty):
                    self.trades.append({
                        'time': str(datetime.now()),
                        'symbol': sig['symbol'],
                        'action': 'SHORT',
                        'quantity': qty,
                        'price': price,
                        'strategies': sig.get('strategies', []),
                        'confidence': sig['confidence']
                    })
    
    def send_report(self):
        account = self.ibkr.get_account()
        positions = self.ibkr.get_positions()
        
        # Update prices
        for sym in positions:
            data = MarketData.get_data(sym)
            if data:
                positions[sym]['current_price'] = data['price']
        
        # Calculate P&L
        daily_pnl = 0
        for sym, pos in positions.items():
            entry = pos.get('avg_cost', 0)
            current = pos.get('current_price', entry)
            qty = pos.get('quantity', 0)
            if pos.get('direction') == 'LONG':
                daily_pnl += (current - entry) * qty
            else:
                daily_pnl += (entry - current) * qty
        
        # Generate reports
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
        
        save_report(html)
        results = self.reporter.send_all(html, telegram)
        
        if 'telegram' in results:
            print("[REPORT] Telegram sent!")
    
    def print_summary(self):
        account = self.ibkr.get_account()
        positions = self.ibkr.get_positions()
        
        # Update prices
        for sym in positions:
            data = MarketData.get_data(sym)
            if data:
                positions[sym]['current_price'] = data['price']
        
        # P&L
        daily_pnl = 0
        for sym, pos in positions.items():
            entry = pos.get('avg_cost', 0)
            current = pos.get('current_price', entry)
            qty = pos.get('quantity', 0)
            pnl = (current - entry) * qty if pos['direction'] == 'LONG' else (entry - current) * qty
            daily_pnl += pnl
            pos['pnl'] = pnl
        
        print(f"""
============================================================
  MULTI-STRATEGY TRADING SYSTEM v2
============================================================
[ACCOUNT] ${account.get('net_liq', 0):,.2f}
[POSITIONS] {len(positions)}
[TRADES] {len(self.trades)}
[DAILY P&L] ${daily_pnl:,.2f}
""")
        
        for sym, pos in positions.items():
            pnl = pos.get('pnl', 0)
            icon = "[UP]" if pnl >= 0 else "[DOWN]"
            print(f"{sym:8} {pos['direction']:5} {pos['quantity']:4} @ ${pos['avg_cost']:.2f} -> ${pos.get('current_price', 0):.2f} {icon} ${pnl:.2f}")
        
        if self.trading_enabled and self.trades:
            print("\n[SENDING REPORT...]")
            self.send_report()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA,JPM,BAC,WMT")
    parser.add_argument("--trade", action="store_true")
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    print("\n" + "="*60)
    print("  MULTI-STRATEGY VOLATILITY TRADING v2")
    print("  6 Strategies + IBKR + Mobile Report")
    print("="*60)
    
    ibkr = IBKRTrader()
    if not ibkr.connect():
        return
    
    trader = MultiStrategyTrader(ibkr, symbols)
    
    if args.trade:
        trader.trading_enabled = True
        print("[AUTO-TRADING ENABLED]")
    
    # Analyze
    signals = trader.analyze_all()
    
    # Execute
    if args.trade:
        print("\n" + "-"*60)
        print("EXECUTING ORDERS")
        print("-"*60)
        trader.execute(signals)
    
    # Report
    trader.print_summary()
    
    ibkr.disconnect()
    print("\n[LOCKED] Done")


if __name__ == "__main__":
    main()
