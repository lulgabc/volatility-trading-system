# Volatility Trading System - Quick Reference Card

## 🚀 Quick Start

```bash
# Daily trading (21:00 Paris)
python ibkr_trader_v3.py --trade

# Intraday (US market hours)
python intraday_v2.py

# Real-time scanning
python realtime_trader.py
```

---

## 📊 6 Strategies at a Glance

| # | Strategy | Weight | Key Signal |
|---|----------|---------|------------|
| 1 | IV Rank | 1.0 | IV Rank > 65% = SHORT |
| 2 | VIX Reversion | 0.8 | VIX > 25 = SHORT |
| 3 | IV/HV Spread | 0.7 | Spread > 30% = SHORT |
| 4 | Momentum | 0.6 | Strong uptrend = LONG |
| 5 | Contrarian | 0.5 | Oversold + High IV = LONG |
| 6 | Trend | 0.5 | Price > SMA20 > SMA50 = LONG |

---

## 🎯 Decision Formula

```
BUY_SCORE = Σ (LONG_signals × weights)
SELL_SCORE = Σ (SHORT_signals × weights)

IF BUY > SELL × 1.2 → LONG
IF SELL > BUY × 1.2 → SHORT
ELSE → NO TRADE
```

---

## 💰 Position Sizing

```
Position = Account × 2% × Confidence
Quantity = Position / Stock_Price
```

**Example:** $1M account, 70% confidence → $14,000 position

---

## 🛡️ Risk Rules

| Type | Stop-Loss | Take-Profit |
|------|-----------|-------------|
| Daily | -5% | +8% |
| Intraday | -0.4% | +0.6% |
| Max Positions | 5 | |
| Min Cooldown | 30 sec | |

---

## 📈 Market Conditions

| Condition | IV | Action |
|-----------|-----|---------|
| Panic selling | High | Sell puts |
| Complacent rally | Low | Buy puts |
| Normal | Medium | IV Rank |

---

## ⏰ Market Hours

| Timezone | Open | Close |
|----------|------|--------|
| New York | 9:30 AM | 4:00 PM |
| Paris | 3:30 PM | 10:00 PM |

---

## 🔧 Configuration

| Setting | Value |
|---------|-------|
| IBKR Port | 7497 |
| Telegram | @Lulg_trading_bot |
| Account | Paper $1,000,000 |

---

## 📁 Files

- `ibkr_trader_v3.py` - Daily system
- `multi_strategy_v2.py` - Multi-strategy
- `intraday_v2.py` - Intraday adaptive
- `realtime_trader.py` - Real-time scanner

---

*Keep this card handy for quick reference!*
