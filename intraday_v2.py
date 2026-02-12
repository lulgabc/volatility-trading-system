"""
Intraday Trading System v2 - Auto-Adaptive Threshold
Automatically calculates trigger threshold based on market volatility
"""
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
import json


@dataclass
class Signal:
    symbol: str
    direction: str
    entry_price: float
    confidence: float
    strategy: str
    timestamp: datetime


@dataclass
class Position:
    symbol: str
    direction: str
    entry_price: float
    quantity: int
    entry_time: datetime
    strategy: str
    stop_loss: float
    take_profit: float


class AdaptiveConfig:
    """自适应配置"""
    
    symbols = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN', 'GOOGL', 'AMD', 'INTC', 'COIN']
    
    # 基础参数
    position_size = 0.1
    max_positions = 5
    cooldown_seconds = 30
    
    # 止损止盈（动态调整）
    base_stop_loss = 0.005
    base_take_profit = 0.008
    
    # 策略权重
    momentum_weight = 0.30
    mean_reversion_weight = 0.25
    breakouts_weight = 0.25
    volume_weight = 0.20
    
    # 波动率阈值映射
    volatility_thresholds = {
        'low': 0.35,    # 低波动市场：35%阈值
        'normal': 0.45, # 正常市场：45%阈值
        'high': 0.55,   # 高波动市场：55%阈值
        'extreme': 0.65 # 极端波动：65%阈值
    }


class MarketVolatility:
    """市场波动率分析器"""
    
    def __init__(self, config: AdaptiveConfig):
        self.config = config
        self.volatility_history = []
    
    def calculate_market_volatility(self) -> Dict:
        """计算当前市场整体波动率"""
        volatilities = []
        changes = []
        
        for symbol in self.config.symbols[:10]:  # 使用前10个股票
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d", interval="5m")
                
                if len(data) < 5:
                    continue
                
                # 5分钟收益率标准差
                returns = data['Close'].pct_change().dropna()
                if len(returns) > 1:
                    vol_5m = returns.std() * np.sqrt(12)  # 年化
                    volatilities.append(vol_5m)
                
                # 当日涨跌幅
                change = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
                changes.append(abs(change))
                
            except:
                continue
        
        if not volatilities:
            return {'level': 'normal', 'threshold': 0.45, 'avg_vol': 0.02, 'avg_change': 0.01}
        
        avg_vol = np.mean(volatilities)
        avg_change = np.mean(changes)
        
        # 确定波动率级别
        if avg_vol < 0.015:
            level = 'low'
        elif avg_vol < 0.03:
            level = 'normal'
        elif avg_vol < 0.05:
            level = 'high'
        else:
            level = 'extreme'
        
        # 动态调整止盈止损
        if level == 'low':
            stop_loss = 0.003
            take_profit = 0.005
        elif level == 'normal':
            stop_loss = 0.005
            take_profit = 0.008
        elif level == 'high':
            stop_loss = 0.008
            take_profit = 0.012
        else:
            stop_loss = 0.012
            take_profit = 0.018
        
        threshold = self.config.volatility_thresholds[level]
        
        return {
            'level': level,
            'threshold': threshold,
            'avg_vol': avg_vol,
            'avg_change': avg_change,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'symbol_vols': {s: v for s, v in zip(self.config.symbols[:len(volatilities)], volatilities)}
        }
    
    def print_volatility_report(self, vol_info: Dict):
        """打印波动率报告"""
        level_icons = {'low': '[CALM]', 'normal': '[NORMAL]', 'high': '[ACTIVE]', 'extreme': '[VOLATILE]'}
        
        print("\n" + "="*60)
        print(f"  MARKET VOLATILITY ANALYSIS")
        print("="*60)
        print(f"  Market State: {level_icons.get(vol_info['level'], '?')} {vol_info['level'].upper()}")
        print(f"  Avg Volatility: {vol_info['avg_vol']*100:.2f}%")
        print(f"  Avg Daily Change: {vol_info['avg_change']*100:.2f}%")
        print("-"*60)
        print(f"  [AUTO-CALCULATED PARAMETERS]")
        print(f"  Trigger Threshold: {vol_info['threshold']:.0%}")
        print(f"  Stop Loss: {vol_info['stop_loss']:.1%}")
        print(f"  Take Profit: {vol_info['take_profit']:.1%}")
        print("="*60)


class TechnicalAnalyzer:
    """技术分析"""
    
    @staticmethod
    def get_data(symbol: str) -> Dict:
        try:
            ticker = yf.Ticker(symbol)
            data_1m = ticker.history(period="1d", interval="1m")
            data_5m = ticker.history(period="5d", interval="5m")
            
            if data_1m.empty:
                return {}
            
            current = data_1m['Close'].iloc[-1]
            
            # 价格变化
            change_1m = (current - data_1m['Close'].iloc[-2]) / data_1m['Close'].iloc[-2] if len(data_1m) > 1 else 0
            change_5m = (current - data_5m['Close'].iloc[-1]) / data_5m['Close'].iloc[-1] if len(data_5m) > 0 else 0
            
            # RSI
            delta = data_5m['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD
            ema12 = data_5m['Close'].ewm(span=12).mean()
            ema26 = data_5m['Close'].ewm(span=26).mean()
            macd = (ema12 - ema26).iloc[-1]
            signal = macd.ewm(span=9).mean().iloc[-1]
            hist = macd - signal
            
            # 成交量
            vol = data_1m['Volume'].iloc[-1]
            avg_vol = data_1m['Volume'].rolling(20).mean().iloc[-1]
            vol_ratio = vol / avg_vol if avg_vol > 0 else 1
            
            # SMA
            sma5 = data_5m['Close'].rolling(5).mean().iloc[-1]
            sma20 = data_5m['Close'].rolling(20).mean().iloc[-1]
            
            # 布林带
            sma_bb = data_5m['Close'].rolling(20).mean().iloc[-1]
            std_bb = data_5m['Close'].rolling(20).std().iloc[-1]
            bb_upper = sma_bb + 2 * std_bb
            bb_lower = sma_bb - 2 * std_bb
            
            # 高低点
            high_5m = data_5m['High'].iloc[-1]
            low_5m = data_5m['Low'].iloc[-1]
            
            return {
                'symbol': symbol,
                'price': current,
                'change_1m': change_1m,
                'change_5m': change_5m,
                'rsi': rsi,
                'macd_hist': hist,
                'volume_ratio': vol_ratio,
                'sma_5': sma5,
                'sma_20': sma20,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower,
                'high_5m': high_5m,
                'low_5m': low_5m,
            }
        except:
            return {}
    
    @staticmethod
    def analyze(data: Dict, vol_info: Dict) -> Optional[Signal]:
        if not data:
            return None
        
        price = data['price']
        threshold = vol_info['threshold']
        
        scores = {'LONG': 0, 'SHORT': 0}
        signal_details = []
        
        # Momentum
        if data['change_1m'] > 0.001:
            scores['LONG'] += 0.3
            signal_details.append('MOM+')
        elif data['change_1m'] < -0.001:
            scores['SHORT'] += 0.3
            signal_details.append('MOM-')
        
        # RSI
        if data['rsi'] < 35:
            scores['LONG'] += 0.25
            signal_details.append('RSI<35')
        elif data['rsi'] > 65:
            scores['SHORT'] += 0.25
            signal_details.append('RSI>65')
        elif data['rsi'] < 45:
            scores['LONG'] += 0.15
        elif data['rsi'] > 55:
            scores['SHORT'] += 0.15
        
        # MACD
        if data['macd_hist'] > 0:
            scores['LONG'] += 0.15
        else:
            scores['SHORT'] += 0.15
        
        # Breakout
        if price > data['high_5m']:
            scores['LONG'] += 0.35
            signal_details.append('HH')
        elif price < data['low_5m']:
            scores['SHORT'] += 0.35
            signal_details.append('LL')
        
        # Volume
        if data['volume_ratio'] > 2 and abs(data['change_1m']) > 0.0005:
            direction = 'LONG' if data['change_1m'] > 0 else 'SHORT'
            scores[direction] += 0.2
            signal_details.append('VOL+')
        
        # Mean Reversion
        deviation = (price - data['sma_20']) / data['sma_20'] if data['sma_20'] > 0 else 0
        if deviation < -0.01:
            scores['LONG'] += 0.2
        elif deviation > 0.01:
            scores['SHORT'] += 0.2
        
        # BB
        if price < data['bb_lower']:
            scores['LONG'] += 0.2
        elif price > data['bb_upper']:
            scores['SHORT'] += 0.2
        
        # 最终决策
        total = scores['LONG'] + scores['SHORT']
        if total == 0:
            return None
        
        if scores['LONG'] > scores['SHORT']:
            confidence = scores['LONG'] / total
            direction = 'LONG'
        else:
            confidence = scores['SHORT'] / total
            direction = 'SHORT'
        
        if confidence < threshold:
            return None
        
        return Signal(
            symbol=data['symbol'],
            direction=direction,
            entry_price=price,
            confidence=confidence,
            strategy=','.join(signal_details[:3]) if signal_details else 'Mixed',
            timestamp=datetime.now()
        )


class AdaptiveIntradayTrader:
    """自适应日内交易系统"""
    
    def __init__(self):
        self.config = AdaptiveConfig()
        self.volatility = MarketVolatility(self.config)
        self.analyzer = TechnicalAnalyzer()
        self.positions: List[Position] = []
        self.pnl_history = []
        self.last_trade_time = {}
        self.vol_info = None
    
    def calculate_adaptive_params(self):
        """计算自适应参数"""
        self.vol_info = self.volatility.calculate_market_volatility()
        self.volatility.print_volatility_report(self.vol_info)
    
    def should_trade(self, symbol: str) -> bool:
        if symbol in self.last_trade_time:
            if (datetime.now() - self.last_trade_time[symbol]).seconds < self.config.cooldown_seconds:
                return False
        
        for pos in self.positions:
            if pos.symbol == symbol:
                return False
        
        if len(self.positions) >= self.config.max_positions:
            return False
        
        return True
    
    def check_positions(self) -> List[Tuple[Position, str, float]]:
        close_signals = []
        
        for pos in self.positions:
            data = self.analyzer.get_data(pos.symbol)
            if not data:
                continue
            
            current_price = data['price']
            
            if pos.direction == 'LONG':
                pnl_pct = (current_price - pos.entry_price) / pos.entry_price
            else:
                pnl_pct = (pos.entry_price - current_price) / pos.entry_price
            
            stop_loss = self.vol_info['stop_loss']
            take_profit = self.vol_info['take_profit']
            
            if pnl_pct >= take_profit:
                close_signals.append((pos, 'TAKE_PROFIT', current_price))
            elif pnl_pct <= -stop_loss:
                close_signals.append((pos, 'STOP_LOSS', current_price))
            elif (datetime.now() - pos.entry_time).seconds > 900:  # 15分钟强制平仓
                close_signals.append((pos, 'TIME_STOP', current_price))
        
        return close_signals
    
    def close_position(self, position: Position, reason: str, exit_price: float):
        if position.direction == 'LONG':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
        
        self.pnl_history.append({
            'symbol': position.symbol,
            'direction': position.direction,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'quantity': position.quantity,
            'pnl': pnl,
            'reason': reason,
            'duration': (datetime.now() - position.entry_time).seconds,
            'strategy': position.strategy
        })
        
        self.positions = [p for p in self.positions if p.symbol != position.symbol]
        self.last_trade_time[position.symbol] = datetime.now()
        
        print(f"[CLOSE] {position.symbol} {position.direction} @ {exit_price:.2f} | P&L: ${pnl:.2f} | {reason}")
    
    def run_scan(self) -> List[Signal]:
        signals = []
        
        for symbol in self.config.symbols:
            if not self.should_trade(symbol):
                continue
            
            data = self.analyzer.get_data(symbol)
            if not data:
                continue
            
            sig = self.analyzer.analyze(data, self.vol_info)
            if sig:
                signals.append(sig)
                icon = "[BUY]" if sig.direction == 'LONG' else "[SELL]"
                print(f"[SIGNAL] {symbol} {icon} @ ${sig.entry_price:.2f} | {sig.strategy} | {sig.confidence:.0%}")
        
        return signals
    
    def run(self):
        print("="*60)
        print("  ADAPTIVE INTRADAY TRADING SYSTEM v2")
        print(f"  Start: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 计算自适应参数
        self.calculate_adaptive_params()
        
        scan_count = 0
        
        while True:
            now = datetime.now()
            
            # 收盘检查
            if now.hour >= 15 and now.minute >= 45:
                print("\n[MARKET CLOSING] Closing all positions...")
                break
            
            # 检查持仓
            close_signals = self.check_positions()
            for pos, reason, price in close_signals:
                self.close_position(pos, reason, price)
            
            # 扫描
            if scan_count % 2 == 0:
                signals = self.run_scan()
                
                for sig in signals:
                    if len(self.positions) >= self.config.max_positions:
                        break
                    
                    quantity = int(10000 * self.config.position_size / sig.entry_price)
                    if quantity < 1:
                        continue
                    
                    sl_pct = self.vol_info['stop_loss']
                    tp_pct = self.vol_info['take_profit']
                    
                    position = Position(
                        symbol=sig.symbol,
                        direction=sig.direction,
                        entry_price=sig.entry_price,
                        quantity=quantity,
                        entry_time=datetime.now(),
                        strategy=sig.strategy,
                        stop_loss=sig.entry_price * (1 - sl_pct) if sig.direction == 'LONG' else sig.entry_price * (1 + sl_pct),
                        take_profit=sig.entry_price * (1 + tp_pct) if sig.direction == 'LONG' else sig.entry_price * (1 - tp_pct)
                    )
                    
                    self.positions.append(position)
                    self.last_trade_time[sig.symbol] = datetime.now()
                    
                    action = "BUY" if sig.direction == 'LONG' else "SHORT"
                    print(f"[OPEN] {sig.symbol} {action} {quantity}@{sig.entry_price:.2f} | {sig.strategy}")
            
            scan_count += 1
            time.sleep(30)
        
        # 日报
        print("\n" + "="*60)
        print("  DAY SUMMARY")
        print("="*60)
        
        total_pnl = sum(p['pnl'] for p in self.pnl_history)
        print(f"Trades: {len(self.pnl_history)} | P&L: ${total_pnl:.2f}")
        
        for trade in self.pnl_history:
            icon = "[+]" if trade['pnl'] >= 0 else "[-]"
            print(f"{icon} {trade['symbol']} {trade['direction']} | {trade['quantity']}@{trade['entry_price']:.2f}->{trade['exit_price']:.2f} | ${trade['pnl']:.2f} | {trade['strategy']}")
        
        return self.pnl_history


def main():
    trader = AdaptiveIntradayTrader()
    
    # 先扫描一次，显示参数
    trader.calculate_adaptive_params()
    
    # 然后运行
    # trader.run()


if __name__ == "__main__":
    main()
