"""
改进版：使用 IBKR 真实数据
"""
import asyncio
from ib_insync import IB, Stock, Option, MarketOrder, LimitOrder, Trade
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import json

@dataclass
class IBKRDataProvider:
    """IBKR 数据提供者"""
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    
    def __post_init__(self):
        self.ib = None
        self.connected = False
        
    def connect(self) -> bool:
        """连接 IBKR"""
        self.ib = IB()
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            self.connected = True
            print("[OK] Connected to IBKR")
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            
    def get_stock_price(self, symbol: str) -> float:
        """获取股票价格"""
        if not self.connected:
            return 0.0
        try:
            contract = Stock(symbol, "SMART", currency="USD")
            ticker = self.ib.reqMktData(contract, "", False, False)
            self.ib.sleep(0.5)
            price = ticker.last if ticker.last > 0 else ticker.close
            return price if price > 0 else 0.0
        except Exception as e:
            print(f"[ERROR] Get price failed for {symbol}: {e}")
            return 0.0
    
    def get_option_iv(self, symbol: str, expiry: str = "", strike: float = None) -> float:
        """获取期权隐含波动率"""
        if not self.connected:
            return 0.0
        try:
            # 简化：返回模拟 IV (实际应查询期权链)
            # IBKR 需要更复杂的期权链查询
            return 0.25  # 默认 25% IV
        except Exception as e:
            print(f"[ERROR] Get IV failed: {e}")
            return 0.0
    
    def get_account_summary(self) -> Dict:
        """获取账户摘要"""
        if not self.connected:
            return {}
        try:
            summary = self.ib.accountSummary()
            result = {}
            for item in summary:
                if item.tag == 'NetLiquidationByCurrency':
                    result['net_liquidation'] = float(item.value)
                elif item.tag == 'CashBalance':
                    result['cash'] = float(item.value)
                elif item.tag == 'UnrealizedPnL':
                    result['unrealized_pnl'] = float(item.value)
            return result
        except Exception as e:
            print(f"[ERROR] Get account failed: {e}")
            return {}
    
    def get_positions(self) -> Dict[str, Dict]:
        """获取持仓"""
        if not self.connected:
            return {}
        try:
            positions = {}
            for pos in self.ib.positions():
                if pos.position != 0:
                    symbol = pos.contract.symbol
                    positions[symbol] = {
                        'quantity': abs(pos.position),
                        'direction': 'LONG' if pos.position > 0 else 'SHORT',
                        'avg_cost': pos.avgCost
                    }
            return positions
        except Exception as e:
            print(f"[ERROR] Get positions failed: {e}")
            return {}


class VolatilitySimulator:
    """波动率交易模拟器"""
    
    def __init__(self, data_provider: IBKRDataProvider, initial_capital: float = 1000000):
        self.data = data_provider
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.trade_log: List[Dict] = []
        self.trading_enabled = False  # 默认关闭，等用户确认
        
    def calculate_iv_rank(self, symbol: str, window: int = 30) -> float:
        """计算 IV Rank (简化版：基于价格波动)"""
        # 实际应获取历史 IV 数据
        # 这里用价格波动模拟
        price = self.data.get_stock_price(symbol)
        if price == 0:
            return 50  # 默认中性
        
        # 简化的 IV Rank 计算
        # 实际需要: (当前IV - 最低IV) / (最高IV - 最低IV) * 100
        return np.random.uniform(30, 80)  # 模拟值
        
    def calculate_hv(self, symbol: str, window: int = 30) -> float:
        """计算历史波动率"""
        price = self.data.get_stock_price(symbol)
        if price == 0:
            return 0.20
        # 简化：返回基于价格的波动率
        return 0.15 + np.random.uniform(0, 0.15)
    
    def generate_signal(self, symbol: str) -> Dict:
        """生成交易信号"""
        iv_rank = self.calculate_iv_rank(symbol)
        hv = self.calculate_hv(symbol)
        price = self.data.get_stock_price(symbol)
        
        signal = {
            "symbol": symbol,
            "iv_rank": iv_rank,
            "hv": hv,
            "iv_hv_diff": iv_rank - hv * 100,
            "price": price,
            "direction": "NEUTRAL",
            "confidence": 0.0,
            "reason": ""
        }
        
        # 波动率策略
        if iv_rank > 70:
            signal["direction"] = "SHORT_VOL"
            signal["confidence"] = min((iv_rank - 50) / 50, 1.0)
            signal["reason"] = f"IV Rank {iv_rank:.1f}% > 70% - 做空波动率"
        elif iv_rank < 30:
            signal["direction"] = "LONG_VOL"
            signal["confidence"] = min((50 - iv_rank) / 50, 1.0)
            signal["reason"] = f"IV Rank {iv_rank:.1f}% < 30% - 做多波动率"
        else:
            signal["reason"] = f"IV Rank {iv_rank:.1f}% 在中性区间"
            
        return signal
    
    def execute_trade(self, signal: Dict) -> bool:
        """执行交易（模拟）"""
        if not self.trading_enabled or signal["direction"] == "NEUTRAL":
            return False
            
        symbol = signal["symbol"]
        price = signal["price"]
        direction = signal["direction"]
        confidence = signal["confidence"]
        
        if price == 0:
            return False
            
        # 计算仓位 (2% 基础仓位 * 置信度)
        position_size = self.cash * 0.02 * confidence
        quantity = int(position_size / price)
        quantity = max(quantity, 1)
        
        # 执行交易
        cost = quantity * price
        
        if direction == "LONG_VOL" and cost <= self.cash:
            self.cash -= cost
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'direction': 'LONG',
                'confidence': confidence
            }
            self.trade_log.append({
                'time': datetime.now(),
                'symbol': symbol,
                'action': 'BUY',
                'quantity': quantity,
                'price': price,
                'signal': signal['reason']
            })
            print(f"[TRADE] BUY {symbol} {quantity} @ ${price:.2f}")
            return True
            
        elif direction == "SHORT_VOL" and cost <= self.cash * 2:  # 允许2倍做空
            self.cash -= cost
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'direction': 'SHORT',
                'confidence': confidence
            }
            self.trade_log.append({
                'time': datetime.now(),
                'symbol': symbol,
                'action': 'SHORT',
                'quantity': quantity,
                'price': price,
                'signal': signal['reason']
            })
            print(f"[TRADE] SHORT {symbol} {quantity} @ ${price:.2f}")
            return True
            
        return False
    
    def enable_trading(self):
        """启用交易"""
        self.trading_enabled = True
        print("[OK] Trading enabled")
    
    def disable_trading(self):
        """禁用交易"""
        self.trading_enabled = False
        print("[WARNING] Trading disabled")
    
    def get_status(self) -> str:
        """获取状态"""
        portfolio_value = self.cash
        for symbol, pos in self.positions.items():
            current_price = self.data.get_stock_price(symbol)
            if current_price > 0:
                if pos['direction'] == 'LONG':
                    portfolio_value += pos['quantity'] * current_price
                else:
                    portfolio_value += pos['quantity'] * pos['entry_price'] - pos['quantity'] * current_price
        
        return f"""
============================================================
  VOLATILITY TRADING SIMULATOR
============================================================
[CASH] Cash: ${self.cash:,.2f}
[PORTFOLIO] Est. Portfolio Value: ${portfolio_value:,.2f}
[POSITIONS] Active Positions: {len(self.positions)}
[TRADES] Total Trades: {len(self.trade_log)}
[TRADING] Auto-Trading: {'ENABLED' if self.trading_enabled else 'DISABLED'}

Active Positions:
"""
        
    def get_positions_report(self) -> str:
        """获取持仓报告"""
        if not self.positions:
            return "No active positions\n"
        
        report = "-" * 60 + "\n"
        for symbol, pos in self.positions.items():
            current_price = self.data.get_stock_price(symbol)
            pnl = (current_price - pos['entry_price']) * pos['quantity'] if pos['direction'] == 'LONG' else (pos['entry_price'] - current_price) * pos['quantity']
            pnl_pct = (current_price - pos['entry_price']) / pos['entry_price'] * 100 if pos['direction'] == 'LONG' else (pos['entry_price'] - current_price) / pos['entry_price'] * 100
            
            direction_icon = "[UP]" if pos['direction'] == 'LONG' else "[DOWN]"
            pnl_icon = "[UP]" if pnl >= 0 else "[DOWN]"
            
            report += f"{symbol:8} {direction_icon} {pos['quantity']:4} @ ${pos['entry_price']:.2f} | Current: ${current_price:.2f} | {pnl_icon} ${pnl:.2f} ({pnl_pct:.1f}%)\n"
        
        return report


async def run_simulation(symbols: List[str], enable_trading: bool = False):
    """运行模拟"""
    print("\n" + "="*60)
    print("  VOLATILITY TRADING SIMULATOR")
    print("  Paper Mode - Using Real IBKR Data")
    print("="*60)
    
    # 连接 IBKR
    data = IBKRDataProvider()
    if not data.connect():
        print("[ERROR] Failed to connect to IBKR")
        return
    
    simulator = VolatilitySimulator(data)
    
    if enable_trading:
        simulator.enable_trading()
    
    # 获取账户信息
    account = data.get_account_summary()
    if account:
        print(f"[INFO] Account Net Liquidation: ${account.get('net_liquidation', 0):,.2f}")
    
    print("\n" + "-"*60)
    print("SCANNING FOR OPPORTUNITIES")
    print("-"*60)
    
    signals = []
    for symbol in symbols:
        signal = simulator.generate_signal(symbol)
        signals.append(signal)
        print(f"{symbol:8} IV Rank: {signal['iv_rank']:5.1f}% | {signal['direction']:12} | {signal['reason']}")
    
    # 按置信度排序
    signals.sort(key=lambda x: x['confidence'], reverse=True)
    
    print("\n" + "-"*60)
    print("TOP SIGNALS")
    print("-"*60)
    for sig in signals[:5]:
        if sig['confidence'] > 0:
            print(f"{sig['symbol']:8} {sig['direction']:12} Confidence: {sig['confidence']:.0%} | {sig['reason']}")
    
    # 执行交易
    if enable_trading:
        print("\n" + "-"*60)
        print("EXECUTING TRADES")
        print("-"*60)
        for signal in signals:
            if signal['confidence'] > 0.3:  # 只交易置信度 > 30% 的信号
                if simulator.execute_trade(signal):
                    pass  # execute_trade 已经打印了
    
    # 显示状态
    print(simulator.get_status())
    print(simulator.get_positions_report())
    
    # 保存交易日志
    if simulator.trade_log:
        filename = f"trade_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(simulator.trade_log, f, default=str, indent=2)
        print(f"[INFO] Trade log saved to: {filename}")
    
    data.disconnect()
    print("\n[LOCKED] Simulation complete")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Volatility Trading Simulator")
    parser.add_argument("--symbols", default="AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA,JPM,BAC,WMT",
                       help="Comma-separated list of symbols")
    parser.add_argument("--trade", action="store_true", help="Enable auto-trading")
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    await run_simulation(symbols, enable_trading=args.trade)


if __name__ == "__main__":
    asyncio.run(main())
