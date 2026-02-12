"""
Mobile-Optimized Trading Report
"""
import json
import os
from datetime import datetime
from typing import Dict, List


class MobileReport:
    """手机优化报告"""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        if amount >= 0:
            return f"${amount:,.2f}"
        return f"-${abs(amount):,.2f}"
    
    @staticmethod
    def generate_html(
        account_balance: float,
        positions: Dict,
        trades: List[Dict],
        daily_pnl: float = 0
    ) -> str:
        """手机优化HTML"""
        
        pnl_color = "#00ff88" if daily_pnl >= 0 else "#ff4757"
        pnl_icon = "+" if daily_pnl >= 0 else ""
        
        positions_html = ""
        for sym, pos in positions.items():
            direction = pos.get("direction", "")
            entry = pos.get("avg_cost", pos.get("entry", 0))
            current = pos.get("current_price", entry)
            qty = pos.get("quantity", 0)
            
            pnl = (current - entry) * qty if direction == "LONG" else (entry - current) * qty
            pnl_color = "#00ff88" if pnl >= 0 else "#ff4757"
            pnl_icon = "+" if pnl >= 0 else ""
            
            direction_bg = "#00ff88" if direction == "LONG" else "#ff4757"
            direction_icon = "▲" if direction == "LONG" else "▼"
            
            positions_html += f"""
            <div class="pos-card">
                <div class="pos-header">
                    <span class="pos-symbol">{sym}</span>
                    <span class="pos-direction" style="background:{direction_bg}">{direction_icon} {direction}</span>
                </div>
                <div class="pos-main">
                    <div class="pos-price">
                        <span class="label">Current</span>
                        <span class="value">{MobileReport.format_currency(current)}</span>
                    </div>
                    <div class="pos-qty">
                        <span class="label">Qty</span>
                        <span class="value">{qty}</span>
                    </div>
                    <div class="pos-pnl" style="color:{pnl_color}">
                        <span class="label">P&L</span>
                        <span class="value">{pnl_icon}{MobileReport.format_currency(pnl)}</span>
                    </div>
                </div>
            </div>
            """
        
        if not positions_html:
            positions_html = '<div class="empty">No active positions</div>'
        
        trades_html = ""
        for trade in trades[-5:]:
            sym = trade.get("symbol", "")
            action = trade.get("action", "")
            qty = trade.get("quantity", 0)
            price = trade.get("price", 0)
            time = trade.get("time", "")[11:16]
            strategies = trade.get("strategies", [])
            strategy_str = f" ({', '.join(strategies)})" if strategies else ""
            
            action_bg = "#00ff88" if action in ["BUY", "LONG"] else "#ff4757"
            action_icon = "▲" if action in ["BUY", "LONG"] else "▼"
            
            trades_html += f"""
            <div class="trade-row">
                <div class="trade-time">{time}</div>
                <div class="trade-symbol">{sym}</div>
                <div class="trade-action" style="background:{action_bg}">{action_icon} {action}</div>
                <div class="trade-qty">{qty}</div>
                <div class="trade-price">{MobileReport.format_currency(price)}{strategy_str}</div>
            </div>
            """
        
        if not trades_html:
            trades_html = '<div class="empty">No trades today</div>'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d0d0d;
            color: #fff;
            padding: 15px;
            min-height: 100vh;
        }}
        
        /* 头部 */
        .header {{
            text-align: center;
            padding: 20px 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .header .time {{
            font-size: 13px;
            opacity: 0.8;
        }}
        
        /* 摘要卡片 */
        .summary {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background: #1a1a1a;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
        }}
        .summary-card .label {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .summary-card .value {{
            font-size: 20px;
            font-weight: 700;
        }}
        .summary-card.main {{
            grid-column: span 2;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .summary-card.main .value {{
            font-size: 28px;
        }}
        
        /* 盈亏 */
        .pnl-positive {{ color: #00ff88; }}
        .pnl-negative {{ color: #ff4757; }}
        
        /* 持仓卡片 */
        .section {{
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 12px;
            padding: 0 5px;
        }}
        .pos-card {{
            background: #1a1a1a;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .pos-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .pos-symbol {{
            font-size: 18px;
            font-weight: 700;
        }}
        .pos-direction {{
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            color: #fff;
        }}
        .pos-main {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            text-align: center;
        }}
        .pos-main .label {{
            font-size: 10px;
            color: #666;
            margin-bottom: 4px;
        }}
        .pos-main .value {{
            font-size: 14px;
            font-weight: 600;
        }}
        .pos-pnl .value {{
            font-size: 16px;
        }}
        
        /* 交易记录 */
        .trade-row {{
            display: grid;
            grid-template-columns: 50px 70px 70px 1fr 80px;
            gap: 8px;
            align-items: center;
            padding: 12px;
            background: #1a1a1a;
            border-radius: 10px;
            margin-bottom: 8px;
        }}
        .trade-time {{
            font-size: 12px;
            color: #666;
        }}
        .trade-symbol {{
            font-size: 14px;
            font-weight: 600;
        }}
        .trade-action {{
            font-size: 10px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            color: #fff;
            text-align: center;
        }}
        .trade-qty {{
            font-size: 12px;
            color: #888;
        }}
        .trade-price {{
            font-size: 13px;
            text-align: right;
        }}
        
        .empty {{
            padding: 30px;
            text-align: center;
            color: #666;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #444;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <!-- 头部 -->
    <div class="header">
        <h1>📈 Trading Report</h1>
        <div class="time">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    
    <!-- 摘要 -->
    <div class="summary">
        <div class="summary-card main">
            <div class="label">Account Balance</div>
            <div class="value">{MobileReport.format_currency(account_balance)}</div>
        </div>
        <div class="summary-card">
            <div class="label">Daily P&L</div>
            <div class="value pnl-positive">{pnl_icon}{MobileReport.format_currency(daily_pnl)}</div>
        </div>
        <div class="summary-card">
            <div class="label">Positions</div>
            <div class="value">{len(positions)}</div>
        </div>
    </div>
    
    <!-- 持仓 -->
    <div class="section">
        <div class="section-title">📋 Positions</div>
        {positions_html}
    </div>
    
    <!-- 交易 -->
    <div class="section">
        <div class="section-title">📝 Recent Trades</div>
        {trades_html}
    </div>
    
    <div class="footer">
        🤖 Automated Trading System
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def generate_telegram(
        account_balance: float,
        positions: Dict,
        trades: List[Dict],
        daily_pnl: float = 0
    ) -> str:
        """Telegram 简洁格式"""
        
        pnl_emoji = "🟢" if daily_pnl >= 0 else "🔴"
        
        msg = f"""📈 *Trading Report*

💰 *Account:* {MobileReport.format_currency(account_balance)}
{pnl_emoji} *Daily:* {MobileReport.format_currency(daily_pnl)}
📊 *Positions:* {len(positions)}

━━━━━━━━━━━━━━━
📋 *POSITIONS*
━━━━━━━━━━━━━━━
"""
        
        for sym, pos in positions.items():
            direction = pos.get("direction", "")
            entry = pos.get("avg_cost", 0)
            current = pos.get("current_price", entry)
            qty = pos.get("quantity", 0)
            pnl = (current - entry) * qty if direction == "LONG" else (entry - current) * qty
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            dir_icon = "▲" if direction == "LONG" else "▼"
            
            msg += f"{dir_icon} *{sym}* {qty}@{MobileReport.format_currency(entry)} → {MobileReport.format_currency(current)} {pnl_emoji}{MobileReport.format_currency(pnl)}\n"
        
        if trades:
            last = trades[-1]
            strategies = last.get('strategies', [])
            strategy_str = f" ({', '.join(strategies)})" if strategies else ""
            msg += f"""
━━━━━━━━━━━━━━━
📝 *LAST TRADE*
━━━━━━━━━━━━━━━
{last.get('symbol', '')} {last.get('action', '')} {last.get('quantity', 0)} @{last.get('price', 0):.2f}{strategy_str}
"""
        
        msg += f"\n_{datetime.now().strftime('%Y-%m-%d %H:%M')}_"
        
        return msg


class MobileReportSender:
    """发送器"""
    
    def __init__(self):
        self.config = {}
    
    def load_config(self, config_file: str = "report_config.json") -> dict:
        default_config = {
            "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
            "email": {"enabled": False, "receiver_email": ""}
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        self.config = default_config
        return self.config
    
    def send_telegram(self, message: str) -> bool:
        tg = self.config.get("telegram", {})
        if not tg.get("enabled", False):
            return False
        
        bot_token = tg.get("bot_token", "")
        chat_id = tg.get("chat_id", "")
        
        if not bot_token or not chat_id:
            return False
        
        try:
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            resp = requests.post(url, json=data, timeout=10)
            return resp.status_code == 200
        except:
            return False
    
    def send_all(self, html: str, telegram: str) -> dict:
        results = {}
        if self.send_telegram(telegram):
            results["telegram"] = True
        return results


def save_report(html: str) -> str:
    filename = f"mobile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join("C:/Users/lulg/.openclaw/workspace/volatility_trading_system/reports", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath


if __name__ == "__main__":
    # 测试
    positions = {
        "AAPL": {"direction": "LONG", "quantity": 25, "avg_cost": 275.70, "current_price": 275.82},
        "TSLA": {"direction": "SHORT", "quantity": 46, "avg_cost": 428.80, "current_price": 428.40},
        "NVDA": {"direction": "SHORT", "quantity": 57, "avg_cost": 190.33, "current_price": 190.24},
    }
    
    trades = [
        {"time": "2026-02-11 21:55:34", "symbol": "AAPL", "action": "BUY", "quantity": 25, "price": 275.70},
        {"time": "2026-02-11 21:55:35", "symbol": "TSLA", "action": "SHORT", "quantity": 46, "price": 428.80},
    ]
    
    # HTML
    html = MobileReport.generate_html(
        account_balance=1000000,
        positions=positions,
        trades=trades,
        daily_pnl=40.50
    )
    
    filepath = save_report(html)
    print(f"[OK] Mobile Report: {filepath}")
    
    # Telegram
    telegram = MobileReport.generate_telegram(
        account_balance=1000000,
        positions=positions,
        trades=trades,
        daily_pnl=40.50
    )
    
    print("\n[Telegram Preview]")
    print(telegram)
    print("\n[Done!]")
