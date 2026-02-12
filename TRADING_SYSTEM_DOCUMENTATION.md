# Volatility Trading System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Strategy Components](#strategy-components)
3. [Trading Logic](#trading-logic)
4. [Risk Management](#risk-management)
5. [Technical Implementation](#technical-implementation)
6. [Usage Guide](#usage-guide)

---

## System Overview

### Purpose
Automated volatility-based trading system using Yahoo Finance data and Interactive Brokers (IBKR) paper account.

### Key Features
- **Multi-Strategy Approach**: Combines 6 different volatility strategies
- **Adaptive Parameters**: Auto-adjusts thresholds based on market volatility
- **Real-Time Scanning**: Monitors 268+ stocks continuously
- **Risk Management**: Built-in stop-loss and take-profit mechanisms
- **Notifications**: Telegram alerts for all trades

### File Structure
```
volatility_trading_system/
├── ibkr_trader_v3.py         # Main daily trading system
├── multi_strategy_v2.py     # Multi-strategy analyzer
├── intraday_v2.py           # Adaptive intraday trading
├── realtime_trader.py        # Real-time scanning system
├── mobile_report.py          # Report generation
├── trading_dashboard.py      # Web dashboard
└── reports/                  # HTML reports
```

---

## Strategy Components

### 1. IV Rank Strategy (权重: 1.0)
**核心策略 - 隐含波动率排名**

**Logic:**
- Calculate historical volatility (HV) from past prices
- Estimate implied volatility (IV) using HV × random factor
- Compute IV Rank = (IV - IV_low) / (IV_high - IV_low) × 100

**Signals:**
| IV Rank | Signal | Action |
|---------|--------|--------|
| > 65% | HIGH_IV | SELL options / SHORT stock |
| < 35% | LOW_IV | BUY options / LONG stock |
| 35-65% | NEUTRAL | No position |

**Example:**
```
AAPL IV Rank: 30% → LONG_VOL signal
NVDA IV Rank: 85% → SHORT_VOL signal
```

---

### 2. VIX Mean Reversion Strategy (权重: 0.8)
**VIX均值回归策略**

**Logic:**
- Monitor overall market volatility (VIX)
- VIX tends to mean-revert: high VIX → market oversold → potential bounce
- Low VIX → market overconfident → potential pullback

**Signals:**
| VIX Level | Market Condition | Signal |
|-----------|-----------------|--------|
| VIX > 25 + Drop > 3% | Panic selling | LONG_VOL |
| VIX < 15 + Rally > 3% | Complacent rally | SHORT_VOL |
| VIX > 22 | Elevated fear | SHORT_VOL |
| VIX < 14 | Complacency | LONG_VOL |

---

### 3. IV/HV Spread Strategy (权重: 0.7)
**隐含波动率与历史波动率价差**

**Logic:**
- Compare IV (implied) vs HV (historical)
- IV > HV by significant margin → options overpriced → SELL
- IV < HV by significant margin → options cheap → BUY

**Calculation:**
```
Spread = (IV - HV) / HV
```

**Signals:**
| Spread | Signal | Confidence |
|--------|--------|------------|
| > 30% | SHORT_VOL | (Spread - 20%) capped at 80% |
| < -20% | LONG_VOL | (-Spread × 50%) capped at 60% |
| -20% to 30% | NEUTRAL | - |

---

### 4. Momentum Strategy (权重: 0.6)
**动量策略**

**Logic:**
- Trend following: buy winners, sell losers
- Momentum confirms direction

**Signals:**
| Condition | Signal | Confidence |
|-----------|--------|------------|
| 5-day rise > 3% + 20-day rise > 5% + IV < 50% | LONG_VOL | 50% |
| 5-day drop > 3% + 20-day drop > 5% + IV > 50% | SHORT_VOL | 50% |

---

### 5. Contrarian Strategy (权重: 0.5)
**反向策略**

**Logic:**
- Fade extreme moves
- Buy when everyone is selling (oversold)
- Sell when everyone is buying (overbought)

**Signals:**
| Condition | Signal | Confidence |
|-----------|--------|------------|
| Drop > 5% + IV > 70% | LONG_VOL (dip buying) | 60% |
| Rally > 5% + IV < 30% | SHORT_VOL (fade rally) | 60% |

---

### 6. Trend Following Strategy (权重: 0.5)
**趋势跟踪策略**

**Logic:**
- Price above SMA20 > SMA50 = Uptrend
- Price below SMA20 < SMA50 = Downtrend

**Signals:**
| Condition | Signal | Confidence |
|-----------|--------|------------|
| Price > SMA20 > SMA50 + 5-day rise | LONG_VOL | 50% |
| Price < SMA20 < SMA50 + 5-day drop | SHORT_VOL | 50% |

---

## Trading Logic

### Multi-Strategy Scoring System

Each strategy votes with weighted confidence:

```
Final Score = Σ (Strategy_Confidence × Strategy_Weight)
```

**Decision Rules:**
| Condition | Action |
|-----------|--------|
| BUY_SCORE > SELL_SCORE × 1.2 | LONG position |
| SELL_SCORE > BUY_SCORE × 1.2 | SHORT position |
| Otherwise | No trade |

**Example Calculation:**
```
AAPL:
  - IV Rank Strategy: LONG 40% × 1.0 = 0.40
  - VIX Reversion: NEUTRAL × 0.8 = 0
  - Momentum: LONG 50% × 0.6 = 0.30
  - Contrarian: NEUTRAL × 0.5 = 0
  - Trend: LONG 50% × 0.5 = 0.25
  
  TOTAL: LONG = 0.95, SHORT = 0
  RESULT: LONG signal with 100% confidence
```

---

### Position Sizing

**Formula:**
```
Position_Size = Account × 2% × Confidence
```

**Example:**
- Account: $1,000,000
- Confidence: 70%
- Position: $1,000,000 × 0.02 × 0.70 = $14,000

**Quantity:**
```
Quantity = Position_Size / Stock_Price
```

---

## Risk Management

### Stop-Loss Rules
| Strategy | Stop-Loss |
|----------|-----------|
| Daily (Multi-Strategy) | -5% |
| Intraday | -0.4% to -0.8% (adaptive) |
| Time Stop | 15-20 minutes |

### Take-Profit Rules
| Strategy | Take-Profit |
|----------|-------------|
| Daily (Multi-Strategy) | +8% |
| Intraday | +0.6% to +1.2% (adaptive) |

### Position Limits
- Maximum 5 simultaneous positions per strategy
- Maximum 10% of account per single position
- Minimum 30-second cooldown between trades on same symbol

---

## Technical Implementation

### Market Data Sources
| Data | Source |
|------|--------|
| Prices | Yahoo Finance (real-time) |
| Volume | Yahoo Finance |
| Historical Prices | Yahoo Finance (3-month) |
| VIX | Yahoo Finance (^VIX) |

### IBKR Integration
| Parameter | Value |
|-----------|-------|
| Host | 127.0.0.1 |
| Port | 7497 |
| Client ID | 1-3 |
| Account | Paper ($1,000,000) |

### Telegram Notifications
| Setting | Value |
|---------|-------|
| Bot | @Lulg_trading_bot |
| Token | 8574660647:AAF74d8rgkcgMdUtLcRlSenQjNmlPl_eZ8Y |
| Chat ID | 8402314009 |

---

## Usage Guide

### Daily Trading (Main Session - 21:00 Paris)

```bash
# Analyze only
python volatility_trading_system/ibkr_trader_v3.py

# Analyze + Execute trades
python volatility_trading_system/ibkr_trader_v3.py --trade

# Multi-strategy analysis
python volatility_trading_system/multi_strategy_v2.py --trade
```

### Intraday Trading (US Market Hours)

**Market Hours:**
- New York: 9:30 AM - 4:00 PM ET
- Paris: 3:30 PM - 10:00 PM

```bash
# Adaptive intraday (auto-threshold)
python volatility_trading_system/intraday_v2.py

# Real-time scanner (continuous)
python volatility_trading_system/realtime_trader.py

# Market hours auto-trader
python volatility_trading_system/market_hours_trader.py --loop
```

### Monitoring

```bash
# Web dashboard
python volatility_trading_system/trading_dashboard.py 8080

# Scan market for opportunities
python volatility_trading_system/intraday_scanner.py
```

---

## Strategy Performance Summary

| Strategy | Weight | Best For |
|----------|--------|----------|
| IV Rank | 1.0 | Core strategy, always active |
| VIX Reversion | 0.8 | Market regime changes |
| IV/HV Spread | 0.8 | Options premium valuation |
| Momentum | 0.6 | Trending markets |
| Contrarian | 0.5 | Reversals at extremes |
| Trend | 0.5 | Clear trends |

---

## Quick Reference Card

### Signal Interpretation
```
BUY/SHORT = Long/Short volatility
          = Buy/Sell the underlying stock

HIGH IV + LOW HV = Options expensive = Sell options
LOW IV + HIGH HV = Options cheap = Buy options
```

### Market Conditions
| Condition | IV | Recommended Action |
|-----------|-----|------------------|
| Panic selling | High | Sell puts / Short stock |
| Complacent rally | Low | Buy puts / Long stock |
| Normal market | Medium | IV Rank strategy |
| Earnings season | Varies | Higher confidence |

---

*Last Updated: 2026-02-12*
*System Version: 3.0*
