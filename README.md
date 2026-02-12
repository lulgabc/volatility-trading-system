# 📈 波动率交易系统

自动化波动率交易策略系统，连接 Interactive Brokers 进行股票交易。

## 🏗️ 系统架构

```
volatility_trading_system/
├── 📁 strategy/              # 1. 交易策略
│   └── volatility_strategy.py
├── 📁 screener/             # 2. 股票扫描器
│   └── stock_screener.py
├── 📁 executor/              # 3. 交易执行
│   └── trading_executor.py
├── 📁 data/                  # 数据存储
├── main.py                   # 主程序
└── config.json               # 配置文件
```

## 🎯 功能特性

### 1. 交易策略 (Strategy)
- **IV Rank 策略**: 基于隐含波动率历史排名
- **VIX 均值回归**: VIX极端值时反向交易
- **IV/HV 偏离**: 隐含波动率 vs 实际波动率
- **波动率逆向**: 综合多指标信号

### 2. 股票扫描器 (Screener)
- 自动扫描美国市场
- 筛选高期权活跃度股票
- IV Rank + IV/HV 偏离度评分
- 按交易价值排序

### 3. 交易执行 (Executor)
- **Paper模式**: 模拟交易（无需IBKR）
- **Live模式**: 实盘交易（需IBKR连接）
- 订单管理：市价/限价/止损单
- 持仓监控与风险控制

## 🚀 快速开始

### 前置条件
- Python 3.12+
- IBKR 账户（Paper 或实盘）

### 安装依赖
```bash
pip install ib_insync pandas numpy scipy matplotlib
```

### 配置
编辑 `config.json`:
```json
{
    "mode": "paper",        // paper 或 live
    "initial_capital": 1000000,
    "symbols": ["AAPL", "MSFT", ...]
}
```

### 运行

**模拟交易:**
```bash
python main.py --mode paper
```

**实盘交易:**
```bash
# 先启动IBKR Gateway/TWS
python main.py --mode live
```

## 📊 策略说明

### IV Rank 策略
- IV Rank > 70% → **做空波动率**（期权贵）
- IV Rank < 30% → **做多波动率**（期权便宜）

### VIX 策略
- VIX > 20 → 做多波动率（恐慌买入）
- VIX < 12 → 做空波动率（平静卖出）

## ⚠️ 风险提示

1. **仅供学习研究**，不构成投资建议
2. **实盘交易有亏损风险**
3. 建议先用 Paper 模式充分测试
4. 注意仓位管理和止损

## 📝 TODO

- [ ] 集成真实市场数据API
- [ ] 添加机器学习预测模型
- [ ] 增加仓位优化算法
- [ ] 支持期货/期权交易
- [ ] 添加回测模块

## 📄 许可证

MIT License

---

**作者**: AI Trading System  
**日期**: 2026-02-10
