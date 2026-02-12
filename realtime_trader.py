"""
Real-Time Intraday Trading System
Continuous scanning without delays
"""
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
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


# Full market symbols - S&P 500 + NASDAQ-100 (379 stocks)
SP500_NASDAQ_SYMBOLS = [
    'AAL', 'AAP', 'AAPL', 'ABBV', 'ABMD', 'ABT', 'ACA', 'ACN', 'ADBE', 'ADI',
    'ADSK', 'AEE', 'AEP', 'AMAT', 'AMD', 'AMGN', 'AMZN', 'ANSS', 'ARW', 'ATO',
    'AVGO', 'AXP', 'BA', 'BAC', 'BAND', 'BG', 'BIDU', 'BLL', 'BMY', 'BRK.B',
    'CAG', 'CAT', 'CBOE', 'CCI', 'CDAY', 'CDNS', 'CDW', 'CHTR', 'CINF', 'CL',
    'CMA', 'CMCSA', 'CME', 'CNP', 'COF', 'COST', 'CPAY', 'CPRT', 'CREE', 'CRL',
    'CRM', 'CRWD', 'CSCO', 'CTAS', 'CTLT', 'CVS', 'CVX', 'CYBR', 'CZR', 'DDOG',
    'DGX', 'DHI', 'DHR', 'DISCA', 'DISCK', 'DISH', 'DLTR', 'DNKN', 'DOX', 'DPZ',
    'DRI', 'DVA', 'DXC', 'DXCM', 'E', 'EBAY', 'ED', 'EME', 'EMR', 'ENPH',
    'EPAM', 'EQR', 'ESS', 'ETN', 'EVRG', 'EW', 'EXC', 'EXPD', 'EXPE', 'F',
    'FANG', 'FAST', 'FCX', 'FDS', 'FDX', 'FICO', 'FIS', 'FISV', 'FITB', 'FIVE',
    'FLEX', 'FLT', 'FN', 'FOX', 'FOXA', 'FR', 'FRC', 'FSLR', 'FTNT', 'FTV',
    'GE', 'GEN', 'GHC', 'GILD', 'GNRC', 'GOOG', 'GOOGL', 'GPN', 'GPOR', 'GS',
    'HCA', 'HD', 'HIG', 'HON', 'HRL', 'HSIC', 'HST', 'HSY', 'HUBS', 'HUM',
    'IBM', 'ICUI', 'IDXX', 'IEX', 'IFF', 'ILMN', 'IMMU', 'INCY', 'INFO', 'INTC',
    'INTU', 'IP', 'IPG', 'IR', 'IRM', 'ISRG', 'IT', 'ITRI', 'ITW', 'IVZ',
    'J', 'JAZZ', 'JCI', 'JKHY', 'JLL', 'JNJ', 'JPM', 'K', 'KDP', 'KEY',
    'KHC', 'KLAC', 'KMB', 'KMX', 'KO', 'KR', 'L', 'LH', 'LHX', 'LLY',
    'LNT', 'LOW', 'LPLA', 'LRCX', 'LULU', 'LUV', 'LVS', 'LYV', 'M', 'MA',
    'MAA', 'MAR', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDLZ', 'META', 'MIK', 'MKC',
    'MLM', 'MMC', 'MPWR', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MTD', 'MU',
    'MUR', 'NCLH', 'NDAQ', 'NDSN', 'NEE', 'NET', 'NFLX', 'NKE', 'NOW', 'NSC',
    'NTAP', 'NTRS', 'NVDA', 'NVR', 'NWL', 'NYT', 'O', 'ODFL', 'OGN', 'OHI',
    'OKE', 'OKTA', 'ORCL', 'OTIS', 'OXY', 'OZK', 'PANW', 'PARA', 'PARE', 'PAYX',
    'PCAR', 'PCG', 'PEAK', 'PEP', 'PFG', 'PG', 'PHM', 'PK', 'PKG', 'PLD',
    'PNC', 'PNR', 'PODD', 'POOL', 'POST', 'PPG', 'PRU', 'PSTG', 'PVH', 'PWR',
    'PYPL', 'Q', 'QCOM', 'R', 'RCM', 'RDNT', 'REG', 'REGN', 'RF', 'RHI',
    'RMD', 'RNG', 'ROK', 'ROL', 'ROP', 'ROST', 'RRR', 'RS', 'RSG', 'RTX',
    'S', 'SAIA', 'SAVE', 'SBAC', 'SBH', 'SBNY', 'SBUX', 'SCHW', 'SE', 'SHOP',
    'SHW', 'SJM', 'SKX', 'SLB', 'SMCI', 'SNA', 'SNOW', 'SNPS', 'SO', 'SPG',
    'SPGI', 'SPLK', 'SQ', 'SRCL', 'SRE', 'STE', 'STLD', 'STT', 'SWAV', 'SWK',
    'SWKS', 'SWX', 'SYF', 'SYK', 'SYY', 'T', 'TAP', 'TDG', 'TEL', 'TFC',
    'TGT', 'TJX', 'TM', 'TME', 'TMO', 'TOST', 'TPR', 'TRMB', 'TROW', 'TRV',
    'TSLA', 'TT', 'TTD', 'TTEK', 'TTWO', 'TW', 'TWLO', 'TXN', 'TYL', 'U',
    'UAL', 'UBER', 'UHS', 'ULTA', 'UNH', 'UNM', 'UNP', 'UPS', 'URI', 'V',
    'VEEV', 'VFC', 'VLO', 'VMC', 'VMW', 'VRSK', 'VRSN', 'VRTX', 'VTR', 'W',
    'WAB', 'WAT', 'WBA', 'WCC', 'WDAY', 'WDC', 'WEC', 'WELL', 'WFC', 'WHR',
    'WM', 'WMB', 'WMT', 'WST', 'WTRG', 'WY', 'WYNN', 'XEL', 'XLNX', 'XOM',
    'XPO', 'XYL', 'Y', 'YUM', 'ZBH', 'ZBRA', 'ZEN', 'ZS', 'ZTS',
]


class RealtimeConfig:
    """实时交易配置"""
    
    # S&P 500 + NASDAQ-100 核心股票 (已验证)
    symbols = [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'TSLA', 'GOOGL', 'GOOG', 'AVGO', 'COST',
        'ADBE', 'CRM', 'NFLX', 'INTC', 'AMD', 'QCOM', 'TXN', 'AMAT', 'MU', 'LRCX',
        'PYPL', 'NOW', 'SHOP', 'UBER', 'SNPS', 'CDNS', 'PANW', 'FTNT', 'BIDU', 'ADI',
        'KLAC', 'MCHP', 'SMCI', 'FSLR', 'ENPH', 'VRTX', 'REGN', 'GILD', 'DXCM', 'ISRG',
        'MDLZ', 'KDP', 'KHC', 'MKC', 'CHTR', 'CMCSA', 'LULU', 'ROST', 'DLTR', 'ORCL',
        'WDAY', 'VRSK', 'CDW', 'EPAM', 'DDOG', 'SNOW', 'CRWD', 'NET', 'HUBS', 'TTD',
        'OKTA', 'VMW', 'INTU', 'VEEV', 'XEL', 'EXC', 'NVDA', 'AMD', 'MSFT', 'AAPL',
        'GOOGL', 'META', 'AMZN', 'TSLA', 'COST', 'ADBE', 'CRM', 'NFLX',
        'JPM', 'V', 'JNJ', 'WMT', 'PG', 'HD', 'MA', 'UNH', 'MRK', 'ABBV',
        'PEP', 'KO', 'TMO', 'CVX', 'LLY', 'BAC', 'WFC', 'CSCO', 'ACN', 'MCD',
        'DHR', 'ABT', 'NKE', 'IBM', 'GE', 'HON', 'UNP', 'BA', 'AMGN', 'BMY',
        'CVS', 'SLB', 'CAT', 'SPGI', 'GPN', 'HCA', 'HIG', 'HRL', 'HUM', 'IDXX',
        'ITW', 'JCI', 'KEY', 'KLAC', 'KMB', 'LOW', 'MET', 'NEE', 'NSC', 'O',
        'PHM', 'PLD', 'PNC', 'PRU', 'ROP', 'STT', 'TRV', 'UHS', 'VFC', 'WELL',
        'WM', 'AEE', 'AEP', 'AWK', 'ATO', 'CINF', 'CL', 'CME', 'COF', 'CTAS',
        'ED', 'EME', 'EMR', 'EQR', 'ESS', 'ETN', 'EVRG', 'EXPD', 'FAST', 'FDX',
        'FLT', 'FRC', 'FTV', 'GNRC', 'HSY', 'IFF', 'INFO', 'IP', 'IR', 'IRM',
        'IT', 'J', 'JLL', 'K', 'LH', 'LHX', 'LNT', 'LUV', 'LYV', 'MAA',
        'MAR', 'MCK', 'MCO', 'MLM', 'MMC', 'MPWR', 'MSI', 'MTD', 'NDAQ', 'NDSN',
        'NTAP', 'NTRS', 'NVR', 'ODFL', 'OHI', 'OKE', 'ORLY', 'OTIS', 'OXY', 'PAYX',
        'PCAR', 'PEAK', 'PFG', 'PKG', 'PODD', 'POOL', 'PPG', 'PWR', 'QCOM', 'REG',
        'RMD', 'ROK', 'ROL', 'RSG', 'RTX', 'SAIA', 'SBAC', 'SBUX', 'SCHW', 'SJM',
        'SNA', 'SO', 'SPG', 'STE', 'STLD', 'SWK', 'SWKS', 'SYF', 'SYK', 'SYY',
        'T', 'TAP', 'TDG', 'TEL', 'TGT', 'TJX', 'TROW', 'TTWO', 'TXN', 'TYL',
        'UAL', 'ULTA', 'UNM', 'UPS', 'URI', 'V', 'VLO', 'VMC', 'VRSK', 'VRSN',
        'VTR', 'WAB', 'WAT', 'WBA', 'WCC', 'WDC', 'WEC', 'WFC', 'WHR', 'WMB',
        'WST', 'WTRG', 'WY', 'WYNN', 'XEL', 'XOM', 'XYL', 'YUM', 'ZBH', 'ZBRA',
    ]
    
    # 交易参数
    min_confidence = 0.55
    position_size = 0.1
    max_positions = 5
    
    # 止损止盈
    stop_loss = 0.004
    take_profit = 0.006
    
    # 冷却时间
    cooldown_seconds = 15


class RealtimeAnalyzer:
    """实时分析器"""
    
    def __init__(self, config: RealtimeConfig):
        self.config = config
        self.price_cache = {}
        self.last_signal_time = {}
    
    def fetch_all_prices(self) -> Dict[str, Dict]:
        """并行获取所有股票数据"""
        data = {}
        
        for symbol in self.config.symbols:
            try:
                ticker = yf.Ticker(symbol)
                # 1分钟数据
                data_1m = ticker.history(period="1d", interval="1m", limit=5)
                # 5分钟数据
                data_5m = ticker.history(period="5d", interval="5m", limit=10)
                
                if data_1m.empty or len(data_1m) < 2:
                    continue
                
                current = data_1m['Close'].iloc[-1]
                
                # 计算指标
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
                avg_vol = data_1m['Volume'].rolling(10).mean().iloc[-1]
                vol_ratio = vol / avg_vol if avg_vol > 0 else 1
                
                # 布林带
                sma_bb = data_5m['Close'].rolling(20).mean().iloc[-1]
                std_bb = data_5m['Close'].rolling(20).std().iloc[-1]
                bb_upper = sma_bb + 2 * std_bb
                bb_lower = sma_bb - 2 * std_bb
                
                # 高低点
                high_5m = data_5m['High'].max()
                low_5m = data_5m['Low'].min()
                vwap = (data_1m['Close'] * data_1m['Volume']).sum() / data_1m['Volume'].sum()
                
                data[symbol] = {
                    'price': current,
                    'change_1m': change_1m,
                    'change_5m': change_5m,
                    'rsi': rsi,
                    'macd_hist': hist,
                    'volume_ratio': vol_ratio,
                    'bb_upper': bb_upper,
                    'bb_lower': bb_lower,
                    'high_5m': high_5m,
                    'low_5m': low_5m,
                    'vwap': vwap,
                }
                
            except Exception as e:
                continue
        
        return data
    
    def analyze_symbol(self, symbol: str, data: Dict) -> Optional[Signal]:
        """分析单个股票"""
        if symbol in self.last_signal_time:
            if (datetime.now() - self.last_signal_time[symbol]).seconds < self.config.cooldown_seconds:
                return None
        
        price = data.get('price', 0)
        if price == 0:
            return None
        
        scores = {'LONG': 0, 'SHORT': 0}
        signal_details = []
        
        # 动量信号
        if data['change_1m'] > 0.0008:
            scores['LONG'] += 0.35
            signal_details.append('M+')
        elif data['change_1m'] < -0.0008:
            scores['SHORT'] += 0.35
            signal_details.append('M-')
        
        # RSI信号
        if data['rsi'] < 35:
            scores['LONG'] += 0.25
            signal_details.append('RSI<35')
        elif data['rsi'] > 65:
            scores['SHORT'] += 0.25
            signal_details.append('RSI>65')
        
        # MACD信号
        if data['macd_hist'] > 0:
            scores['LONG'] += 0.15
        else:
            scores['SHORT'] += 0.15
        
        # 突破信号
        if price > data['high_5m']:
            scores['LONG'] += 0.4
            signal_details.append('HH')
        elif price < data['low_5m']:
            scores['SHORT'] += 0.4
            signal_details.append('LL')
        
        # 成交量信号
        if data['volume_ratio'] > 2 and abs(data['change_1m']) > 0.0005:
            direction = 'LONG' if data['change_1m'] > 0 else 'SHORT'
            scores[direction] += 0.25
            signal_details.append('VOL+')
        
        # 布林带信号
        if price < data['bb_lower']:
            scores['LONG'] += 0.2
            signal_details.append('BB-L')
        elif price > data['bb_upper']:
            scores['SHORT'] += 0.2
            signal_details.append('BB-U')
        
        # 决策
        total = scores['LONG'] + scores['SHORT']
        if total == 0:
            return None
        
        if scores['LONG'] > scores['SHORT']:
            confidence = scores['LONG'] / total
            direction = 'LONG'
        else:
            confidence = scores['SHORT'] / total
            direction = 'SHORT'
        
        if confidence < self.config.min_confidence:
            return None
        
        return Signal(
            symbol=symbol,
            direction=direction,
            entry_price=price,
            confidence=confidence,
            strategy=''.join(signal_details[:3]),
            timestamp=datetime.now()
        )
    
    def scan_market(self) -> List[Signal]:
        """扫描整个市场"""
        all_data = self.fetch_all_prices()
        signals = []
        
        for symbol, data in all_data.items():
            sig = self.analyze_symbol(symbol, data)
            if sig:
                signals.append(sig)
                self.last_signal_time[symbol] = datetime.now()
        
        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)
        return signals


class RealtimeTrader:
    """实时交易系统"""
    
    def __init__(self):
        self.config = RealtimeConfig()
        self.analyzer = RealtimeAnalyzer(self.config)
        self.positions: List[Position] = []
        self.pnl_history = []
        self.scan_count = 0
        self.start_time = datetime.now()
    
    def check_positions(self):
        """检查持仓状态"""
        close_signals = []
        
        for pos in self.positions:
            data = self.analyzer.fetch_all_prices().get(pos.symbol)
            if not data:
                continue
            
            current = data['price']
            
            if pos.direction == 'LONG':
                pnl_pct = (current - pos.entry_price) / pos.entry_price
            else:
                pnl_pct = (pos.entry_price - current) / pos.entry_price
            
            if pnl_pct >= self.config.take_profit:
                close_signals.append((pos, 'TAKE_PROFIT', current))
            elif pnl_pct <= -self.config.stop_loss:
                close_signals.append((pos, 'STOP_LOSS', current))
            elif (datetime.now() - pos.entry_time).seconds > 600:  # 10分钟强制平仓
                close_signals.append((pos, 'TIME_STOP', current))
        
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
        
        icon = '[+]' if pnl >= 0 else '[-]'
        print(f"{icon} CLOSE {position.symbol} {position.direction} @ ${exit_price:.2f} | P&L: ${pnl:.2f} | {reason}")
    
    def print_status(self):
        """打印状态"""
        uptime = datetime.now() - self.start_time
        minutes = uptime.seconds // 60
        seconds = uptime.seconds % 60
        
        total_pnl = sum(p['pnl'] for p in self.pnl_history)
        pnl_icon = '[+]' if total_pnl >= 0 else '[-]'
        
        print(f"\n{'='*70}")
        print(f"  REALTIME TRADING STATUS")
        print(f"{'='*70}")
        print(f"  Uptime: {minutes}m {seconds}s | Scans: {self.scan_count}")
        print(f"  Positions: {len(self.positions)} | Trades: {len(self.pnl_history)}")
        print(f"  Total P&L: {pnl_icon} ${total_pnl:.2f}")
        print(f"{'='*70}")
    
    def run(self, market_hours_only=True):
        """运行实时交易"""
        print("\n" + "="*70)
        print("  REALTIME INTRADAY TRADING SYSTEM")
        print("  Continuous Market Scanning")
        print(f"  Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        print(f"  Symbols: {len(self.config.symbols)}")
        print(f"  Min Confidence: {self.config.min_confidence:.0%}")
        print(f"  Stop Loss: {self.config.stop_loss:.1%} | Take Profit: {self.config.take_profit:.1%}")
        print("="*70)
        
        last_status_time = datetime.now()
        
        while True:
            now = datetime.now()
            
            # 收盘检查 (4:00 PM ET = 10:00 PM Paris)
            if market_hours_only and now.hour >= 22 and now.minute >= 0:
                print("\n[MARKET CLOSED] Stopping...")
                break
            
            # 检查持仓
            close_signals = self.check_positions()
            for pos, reason, price in close_signals:
                self.close_position(pos, reason, price)
            
            # 扫描市场
            signals = self.analyzer.scan_market()
            self.scan_count += 1
            
            # 打印信号
            for sig in signals[:3]:
                if len(self.positions) >= self.config.max_positions:
                    break
                
                # 检查是否已有持仓
                if any(p.symbol == sig.symbol for p in self.positions):
                    continue
                
                # 开仓
                quantity = int(10000 * self.config.position_size / sig.entry_price)
                if quantity < 1:
                    continue
                
                position = Position(
                    symbol=sig.symbol,
                    direction=sig.direction,
                    entry_price=sig.entry_price,
                    quantity=quantity,
                    entry_time=datetime.now(),
                    strategy=sig.strategy,
                    stop_loss=sig.entry_price * (1 - self.config.stop_loss) if sig.direction == 'LONG' 
                               else sig.entry_price * (1 + self.config.stop_loss),
                    take_profit=sig.entry_price * (1 + self.config.take_profit) if sig.direction == 'LONG'
                                else sig.entry_price * (1 - self.config.take_profit)
                )
                
                self.positions.append(position)
                
                action = 'BUY' if sig.direction == 'LONG' else 'SHORT'
                print(f"[OPEN] {sig.symbol} {action} {quantity}@{sig.entry_price:.2f} | {sig.strategy} | {sig.confidence:.0%}")
            
            # 每10秒打印状态
            if (now - last_status_time).seconds >= 10:
                self.print_status()
                last_status_time = now
            
            # 短暂休息
            time.sleep(1)
        
        # 日报
        print("\n" + "="*70)
        print("  DAY SUMMARY")
        print("="*70)
        total_pnl = sum(p['pnl'] for p in self.pnl_history)
        print(f"  Total Scans: {self.scan_count}")
        print(f"  Total Trades: {len(self.pnl_history)}")
        print(f"  Total P&L: ${total_pnl:.2f}")
        
        for trade in self.pnl_history:
            icon = '[+]' if trade['pnl'] >= 0 else '[-]'
            print(f"  {icon} {trade['symbol']} {trade['direction']} | {trade['quantity']}@{trade['entry_price']:.2f}->{trade['exit_price']:.2f} | ${trade['pnl']:.2f}")
        
        return self.pnl_history


def main():
    trader = RealtimeTrader()
    trader.run()


if __name__ == "__main__":
    main()
