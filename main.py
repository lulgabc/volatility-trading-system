"""
波动率交易系统 - 主程序
=======================
整合策略、扫描器、交易执行

使用方法:
    python main.py --mode paper     # 模拟交易
    python main.py --mode live      # 实盘交易

作者: AI Trading System
日期: 2026-02-10
"""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path

from strategy.volatility_strategy import (
    VolatilityStrategy, StrategyConfig, StrategyType, SignalDirection
)
from screener.stock_screener import StockScreener, ScreenerConfig, MockDataProvider
from executor.trading_executor import (
    IBKRTrader, PaperTrader, Order, OrderType, OrderAction
)


class VolatilityTradingSystem:
    """波动率交易系统"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.strategy = self._init_strategy()
        self.screener = self._init_screener()
        self.trader = self._init_trader()
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置"""
        default_config = {
            "mode": "paper",
            "initial_capital": 1_000_000,
            "ibkr_host": "127.0.0.1",
            "ibkr_port": 7497,
            "client_id": 1,
            "symbols": [
                "AAPL", "MSFT", "GOOGL", "AMZN", "META",
                "NVDA", "TSLA", "JPM", "BAC", "WMT"
            ],
            "strategy": {
                "type": "volatility_contrarian",
                "iv_rank_threshold_high": 70,
                "iv_rank_threshold_low": 30,
                "vix_overbought": 20,
                "vix_oversold": 12,
                "position_size": 0.02,
                "max_positions": 5
            }
        }
        
        if Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def _init_strategy(self) -> VolatilityStrategy:
        """初始化策略"""
        strat_config = self.config.get("strategy", {})
        
        type_map = {
            "iv_rank": StrategyType.IV_RANK,
            "vix_mean_reversion": StrategyType.VIX_MEAN_REVERSION,
            "iv_hv_diff": StrategyType.IV_HV_DIFF,
            "volatility_contrarian": StrategyType.VOLATILITY_CONTRARIAN
        }
        
        config = StrategyConfig(
            name="波动率交易策略",
            strategy_type=type_map.get(
                strat_config.get("type", "volatility_contrarian"),
                StrategyType.VOLATILITY_CONTRARIAN
            ),
            iv_rank_threshold_high=strat_config.get("iv_rank_threshold_high", 70),
            iv_rank_threshold_low=strat_config.get("iv_rank_threshold_low", 30),
            vix_overbought=strat_config.get("vix_overbought", 20),
            vix_oversold=strat_config.get("vix_oversold", 12),
            position_size=strat_config.get("position_size", 0.02),
            max_positions=strat_config.get("max_positions", 5)
        )
        
        return VolatilityStrategy(config)
    
    def _init_screener(self) -> StockScreener:
        """初始化扫描器"""
        return StockScreener()
    
    def _init_trader(self):
        """初始化交易器"""
        if self.config.get("mode") == "live":
            return IBKRTrader(
                host=self.config.get("ibkr_host", "127.0.0.1"),
                port=self.config.get("ibkr_port", 7497),
                client_id=self.config.get("client_id", 1),
                paper_mode=False
            )
        else:
            return PaperTrader(
                initial_capital=self.config.get("initial_capital", 1_000_000)
            )
    
    async def run_scan(self) -> dict:
        """运行扫描"""
        print("\n" + "="*60)
        print("Volatility Scanner")
        print("="*60)
        
        # 获取市场数据（使用模拟数据）
        symbols = self.config.get("symbols", StockScreener.WATCHLIST)
        market_data = MockDataProvider.generate_mock_data(symbols)
        
        # 扫描
        results = self.screener.scan(market_data)
        
        # 打印报告
        print(self.screener.generate_watchlist_report())
        
        return {
            "scan_time": datetime.now(),
            "results": results.to_dict(orient="records") if not results.empty else []
        }
    
    async def run_strategy(self, market_data: dict = None):
        """运行策略"""
        print("\n" + "="*60)
        print("Volatility Strategy Execution")
        print("="*60)
        
        if market_data is None:
            symbols = self.config.get("symbols", StockScreener.WATCHLIST)
            market_data = MockDataProvider.generate_mock_data(symbols)
        
        signals = []
        
        for symbol, data in market_data.items():
            signal = self.strategy.generate_signal(data)
            
            if signal["direction"] != SignalDirection.NEUTRAL:
                print(f"SIGNAL {symbol}: {signal['direction'].name} | {signal['reason']}")
                signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "data": data
                })
                
                # 执行交易
                await self.execute_trade(symbol, signal, data)
        
        print(f"\nGenerated {len(signals)} trading signals")
        return signals
    
    async def execute_trade(self, symbol: str, signal: dict, data: dict):
        """执行交易"""
        if not self.trader:
            print("ERROR: No trader initialized")
            return
            
        price = data.get("price", 100)
        confidence = signal["confidence"]
        
        # 计算仓位
        if hasattr(self.trader, 'get_portfolio_value'):
            portfolio_value = self.trader.get_portfolio_value()
        else:
            portfolio_value = self.config.get("initial_capital", 1_000_000)
            
        quantity = int(portfolio_value * 0.02 * confidence / price)
        quantity = max(quantity, 1)
        
        # 创建订单
        action = OrderAction.BUY if signal["direction"] == SignalDirection.LONG else OrderAction.SELL
        
        order = Order(
            symbol=symbol,
            action=action,
            quantity=quantity,
            order_type=OrderType.MARKET,
            limit_price=price * 1.02 if action == OrderAction.BUY else price * 0.98
        )
        
        self.trader.submit_order(order)
    
    async def run_full_system(self):
        """运行完整系统"""
        print("\n" + "="*60)
        print("  Volatility Trading System v1.0")
        print("  Mode:", self.config.get("mode", "paper").upper())
        print("="*60)
        
        # 1. Scan
        scan_results = await self.run_scan()
        
        # 2. Strategy
        signals = await self.run_strategy()
        
        # 3. Output
        if hasattr(self.trader, 'get_status'):
            print(self.trader.get_status())
        
        return {"scan": scan_results, "signals": signals}
    
    def shutdown(self):
        """Shutdown system"""
        if self.trader and hasattr(self.trader, 'disconnect'):
            self.trader.disconnect()
        print("[LOCKED] System closed")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Volatility Trading System")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper",
                        help="Trading mode: paper=simulation, live=real")
    parser.add_argument("--config", default="config.json",
                        help="Config file path")
    args = parser.parse_args()
    
    # Create system
    system = VolatilityTradingSystem(config_path=args.config)
    
    # Override mode if specified
    if args.mode:
        system.config["mode"] = args.mode
    
    try:
        # Run
        await system.run_full_system()
    except KeyboardInterrupt:
        print("\n[STOPPED] User interrupted")
    finally:
        system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
