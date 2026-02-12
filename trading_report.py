"""
Trading Report System - Beautiful HTML + Telegram Formats
"""
import json
import os
from datetime import datetime
from typing import Dict, List


class ReportFormatter:
    """美化报告格式"""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """格式化货币"""
        if amount >= 0:
            return f"${amount:,.2f}"
        else:
            return f"-${abs(amount):,.2f}"
    
    @staticmethod
    def format_pnl(pnl: float) -> str:
        """格式化盈亏"""
        if pnl >= 0:
            return f"[GREEN]+${pnl:,.2f}[/GREEN]"
        else:
            return f"[RED]-${abs(pnl):,.2f}[/RED]"
    
    @staticmethod
    def generate_html_report(
        account_balance: float,
        positions: Dict,
        trades: List[Dict],
        daily_pnl: float = 0,
        total_pnl: float = 0
    ) -> str:
        """生成美观的HTML报告"""
        
        # 头部
        header = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .subtitle {{ opacity: 0.8; font-size: 14px; }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        .summary-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .summary-card .label {{ font-size: 12px; opacity: 0.7; margin-bottom: 8px; text-transform: uppercase; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; }}
        .summary-card .value.positive {{ color: #00ff88; }}
        .summary-card .value.negative {{ color: #ff4757; }}
        .summary-card .value.neutral {{ color: #00d4ff; }}
        
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{ font-size: 18px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        
        .positions-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
        }}
        .positions-table th {{
            text-align: left;
            padding: 12px 15px;
            font-size: 11px;
            text-transform: uppercase;
            opacity: 0.6;
        }}
        .positions-table td {{
            padding: 15px;
            background: rgba(255,255,255,0.05);
        }}
        .positions-table tr td:first-child {{
            border-radius: 8px 0 0 8px;
        }}
        .positions-table tr td:last-child {{
            border-radius: 0 8px 8px 0;
        }}
        
        .symbol {{ font-weight: bold; font-size: 16px; }}
        .direction {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .direction.long {{ background: rgba(0, 255, 136, 0.2); color: #00ff88; }}
        .direction.short {{ background: rgba(255, 71, 87, 0.2); color: #ff4757; }}
        
        .price {{ font-family: 'SF Mono', Monaco, monospace; }}
        .pnl.positive {{ color: #00ff88; }}
        .pnl.negative {{ color: #ff4757; }}
        
        .trade-item {{
            display: flex;
            align-items: center;
            padding: 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        .trade-item:last-child {{ margin-bottom: 0; }}
        .trade-time {{ font-size: 12px; opacity: 0.5; min-width: 80px; }}
        .trade-symbol {{ font-weight: bold; min-width: 60px; }}
        .trade-action {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            min-width: 50px;
            text-align: center;
            margin: 0 15px;
        }}
        .trade-action.buy {{ background: rgba(0, 255, 136, 0.2); color: #00ff88; }}
        .trade-action.short {{ background: rgba(255, 71, 87, 0.2); color: #ff4757; }}
        .trade-qty {{ opacity: 0.7; }}
        .trade-price {{ margin-left: auto; font-family: 'SF Mono', Monaco, monospace; }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            opacity: 0.5;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Volatility Trading Report</h1>
            <div class="subtitle">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
"""
        
        # 账户摘要
        pnl_class = "positive" if daily_pnl >= 0 else "negative"
        pnl_icon = "🟢" if daily_pnl >= 0 else "🔴"
        
        summary = f"""
        <div class="summary-grid">
            <div class="summary-card">
                <div class="label">Account Balance</div>
                <div class="value neutral">{ReportFormatter.format_currency(account_balance)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Daily P&L</div>
                <div class="value {pnl_class}">{pnl_icon} {ReportFormatter.format_currency(daily_pnl)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Positions</div>
                <div class="value neutral">{len(positions)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Trades Today</div>
                <div class="value neutral">{len(trades)}</div>
            </div>
        </div>
"""
        
        # 持仓表格
        positions_html = ""
        if positions:
            for sym, pos in positions.items():
                direction = pos.get("direction", "")
                entry = pos.get("avg_cost", pos.get("entry", 0))
                current = pos.get("current_price", entry)
                qty = pos.get("quantity", 0)
                
                pnl = (current - entry) * qty if direction == "LONG" else (entry - current) * qty
                pnl_class = "positive" if pnl >= 0 else "negative"
                direction_class = "long" if direction == "LONG" else "short"
                direction_icon = "▲" if direction == "LONG" else "▼"
                
                positions_html += f"""
                <tr>
                    <td><span class="symbol">{sym}</span></td>
                    <td><span class="direction {direction_class}">{direction_icon} {direction}</span></td>
                    <td class="price">{qty}</td>
                    <td class="price">{ReportFormatter.format_currency(entry)}</td>
                    <td class="price">{ReportFormatter.format_currency(current)}</td>
                    <td class="price {pnl_class}">{ReportFormatter.format_currency(pnl)}</td>
                </tr>
                """
        else:
            positions_html = "<tr><td colspan='6' style='text-align:center;opacity:0.5;'>No active positions</td></tr>"
        
        positions_section = f"""
        <div class="section">
            <h2>📊 Current Positions</h2>
            <table class="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Direction</th>
                        <th>Qty</th>
                        <th>Entry</th>
                        <th>Current</th>
                        <th>P&L</th>
                    </tr>
                </thead>
                <tbody>{positions_html}</tbody>
            </table>
        </div>
"""
        
        # 最近交易
        trades_html = ""
        for trade in trades[-5:]:
            sym = trade.get("symbol", "")
            action = trade.get("action", "")
            qty = trade.get("quantity", 0)
            price = trade.get("price", 0)
            time = trade.get("time", "")[11:19]
            
            action_class = "buy" if action in ["BUY", "LONG"] else "short"
            action_icon = "▲" if action in ["BUY", "LONG"] else "▼"
            
            trades_html += f"""
            <div class="trade-item">
                <div class="trade-time">{time}</div>
                <div class="trade-symbol">{sym}</div>
                <div class="trade-action {action_class}">{action_icon} {action}</div>
                <div class="trade-qty">{qty} shares</div>
                <div class="trade-price">{ReportFormatter.format_currency(price)}</div>
            </div>
            """
        
        trades_section = f"""
        <div class="section">
            <h2>📝 Recent Trades</h2>
            {trades_html if trades_html else '<div style="opacity:0.5;text-align:center;padding:20px;">No trades today</div>'}
        </div>
"""
        
        footer = """
        <div class="footer">
            🤖 Automated Trading System • Paper Account
        </div>
    </div>
</body>
</html>
"""
        
        return header + summary + positions_section + trades_section + footer
    
    @staticmethod
    def generate_telegram_message(
        account_balance: float,
        positions: Dict,
        trades: List[Dict],
        daily_pnl: float = 0
    ) -> str:
        """生成简洁的 Telegram 消息"""
        
        pnl_emoji = "[GREEN]▲[/GREEN]" if daily_pnl >= 0 else "[RED]▼[/RED]"
        pnl_str = ReportFormatter.format_currency(daily_pnl)
        
        msg = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 [B]VOLATILITY TRADING[/B]
━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 [B]Account:[/B] {ReportFormatter.format_currency(account_balance)}
{pnl_emoji} [B]Daily P&L:[/B] {pnl_str}
📊 [B]Positions:[/B] {len(positions)}
📝 [B]Trades:[/B] {len(trades)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 [B]POSITIONS[/B]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for sym, pos in positions.items():
            direction = pos.get("direction", "")
            entry = pos.get("avg_cost", pos.get("entry", 0))
            current = pos.get("current_price", entry)
            qty = pos.get("quantity", 0)
            
            pnl = (current - entry) * qty if direction == "LONG" else (entry - current) * qty
            pnl_emoji = "[GREEN]+[/GREEN]" if pnl >= 0 else "[RED]-[/RED]"
            direction_icon = "▲" if direction == "LONG" else "▼"
            
            msg += f"{direction_icon} {sym}: {qty}@{ReportFormatter.format_currency(entry)} → {ReportFormatter.format_currency(current)} {pnl_emoji}{abs(pnl):,.2f}\n"
        
        if trades:
            last = trades[-1]
            msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 [B]LAST TRADE[/B]
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{last.get('symbol', '')} {last.get('action', '')} {last.get('quantity', 0)} @ {ReportFormatter.format_currency(last.get('price', 0))}
"""
        
        msg += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        return msg
    
    @staticmethod
    def generate_short_sms() -> str:
        """生成极简短信格式"""
        return f"[Trading] Positions updated. Check app for details."


class ReportSender:
    """报告发送器"""
    
    def __init__(self):
        self.config = {}
        self.enabled_channels = []
    
    def load_config(self, config_file: str = "report_config.json") -> dict:
        """加载配置"""
        default_config = {
            "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
            "email": {"enabled": False, "receiver_email": "lulgabc@gmail.com"},
            "sms": {"enabled": False, "method": "telegram"}
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        self.config = default_config
        self.enabled_channels = []
        
        if self.config.get("telegram", {}).get("enabled"):
            self.enabled_channels.append("telegram")
        if self.config.get("email", {}).get("enabled"):
            self.enabled_channels.append("email")
        
        return self.config
    
    def send_telegram(self, message: str) -> bool:
        """发送 Telegram"""
        if "telegram" not in self.enabled_channels:
            return False
        
        tg = self.config.get("telegram", {})
        bot_token = tg.get("bot_token", "")
        chat_id = tg.get("chat_id", "")
        
        if not bot_token or not chat_id:
            print("[Telegram] Not configured")
            return False
        
        try:
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            resp = requests.post(url, json=data, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"[Telegram Error] {e}")
            return False
    
    def send_all(
        self,
        html_report: str,
        telegram_msg: str,
        subject: str = "Trading Report"
    ) -> dict:
        """发送到所有渠道"""
        results = {}
        
        if "telegram" in self.enabled_channels:
            if self.send_telegram(telegram_msg):
                results["telegram"] = True
        
        # Email 暂时简化
        if "email" in self.enabled_channels:
            print(f"[Email] Would send: {subject}")
            results["email"] = True
        
        return results


def save_report(html_content: str, filename: str = None) -> str:
    """保存报告"""
    if filename is None:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    report_dir = "C:/Users/lulg/.openclaw/workspace/volatility_trading_system/reports"
    os.makedirs(report_dir, exist_ok=True)
    
    filepath = os.path.join(report_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filepath


if __name__ == "__main__":
    # 测试
    sample_positions = {
        "AAPL": {"direction": "LONG", "quantity": 25, "avg_cost": 275.70, "current_price": 275.82},
        "TSLA": {"direction": "SHORT", "quantity": 46, "avg_cost": 428.80, "current_price": 428.40},
        "NVDA": {"direction": "SHORT", "quantity": 57, "avg_cost": 190.33, "current_price": 190.24},
        "META": {"direction": "SHORT", "quantity": 15, "avg_cost": 668.85, "current_price": 669.34},
    }
    
    sample_trades = [
        {"time": "2026-02-11 21:55:34", "symbol": "AAPL", "action": "BUY", "quantity": 25, "price": 275.70},
        {"time": "2026-02-11 21:55:35", "symbol": "TSLA", "action": "SHORT", "quantity": 46, "price": 428.80},
    ]
    
    # HTML 报告
    html = ReportFormatter.generate_html_report(
        account_balance=1000000,
        positions=sample_positions,
        trades=sample_trades,
        daily_pnl=40.50
    )
    
    filepath = save_report(html)
    print(f"[OK] HTML Report: {filepath}")
    
    # Telegram 消息
    telegram = ReportFormatter.generate_telegram_message(
        account_balance=1000000,
        positions=sample_positions,
        trades=sample_trades,
        daily_pnl=40.50
    )
    
    print("\n[Telegram Preview]")
    print(telegram)
    
    print("\n[Done!]")
