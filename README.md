# 📈 Volatility Trading System

Automated volatility trading system with IBKR integration and Telegram notifications.

## 🏗️ System Architecture

```
volatility_trading_system/
├── ibkr_trader_v3.py           # Main trading system
├── multi_strategy_v2.py         # 6-strategy voting system
├── intraday_v2.py              # Adaptive intraday trading
├── realtime_trader.py           # Real-time market scanner (268 stocks)
├── market_hours_trader.py      # Auto-start/stop during US market
├── health_check.py              # Health monitoring
├── trading_dashboard.py         # Web monitoring dashboard
├── mobile_report.py             # Mobile-optimized Telegram reports
└── quick_setup.bat             # Scheduled task setup
```

## 🎯 Features

### Strategies (6-Strategy Voting System)
- **IV Rank Strategy**: Based on implied volatility historical ranking
- **VIX Mean Reversion**: Counter-trend at VIX extremes
- **IV/HV Spread Strategy**: Implied vs historical volatility deviation
- **Momentum Strategy**: Trend-following signals
- **Contrarian Strategy**: Opposite of market direction
- **Trend Strategy**: Moving average based

### Auto-Trading
- **Market Hours**: 9:30 AM - 4:00 PM ET (3:30 PM - 10:00 PM Paris)
- **Auto-Start**: Launches at market open
- **Auto-Stop**: Closes at market close
- **Auto-Restart**: Recovers from crashes during trading hours

### Notifications
- Telegram bot: @Lulg_trading_bot
- Start/Stop notifications
- Error alerts
- Daily reports

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- IBKR Account (Paper or Live)
- Telegram Bot Token

### Install Dependencies
```bash
pip install ib_insync pandas numpy requests scipy
```

### Configuration
Edit `config.json`:
```json
{
    "mode": "paper",
    "initial_capital": 1000000,
    "symbols": ["AAPL", "MSFT", "GOOGL", ...]
}
```

### Run

**Auto-Trading (Recommended):**
```bash
python market_hours_trader.py --loop
```

**Manual Trading:**
```bash
python realtime_trader.py
```

## 📊 Strategy Weights

| Strategy | Weight |
|----------|--------|
| IV Rank | 1.0 |
| VIX Mean Reversion | 0.8 |
| IV/HV Spread | 0.7 |
| Momentum | 0.6 |
| Contrarian | 0.5 |
| Trend | 0.5 |

## ⚠️ Risk Warning

1. **For educational purposes only** - not investment advice
2. **Paper trading recommended** before live trading
3. Implement proper risk management
4. Monitor system performance

## 📄 License

MIT License

---

**Author**: grandmacro  
**Date**: 2026-02-12
