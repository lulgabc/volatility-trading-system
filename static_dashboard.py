"""
Trading Dashboard - Self-Contained Version
No external server needed - generates HTML with embedded data
"""
from datetime import datetime
import random

def generate_sample_data():
    """Generate sample trading data"""
    trades = [
        {'time': '20:44:12', 'symbol': 'JPM', 'action': 'SHORT', 'quantity': 65, 'price': 303.93, 'pnl': 0},
        {'time': '20:44:18', 'symbol': 'WMT', 'action': 'BUY', 'quantity': 149, 'price': 133.89, 'pnl': 0},
        {'time': '20:45:30', 'symbol': 'TSLA', 'action': 'SHORT', 'quantity': 46, 'price': 415.81, 'pnl': 125.40},
        {'time': '20:46:15', 'symbol': 'NVDA', 'action': 'SHORT', 'quantity': 57, 'price': 189.11, 'pnl': 45.20},
    ]
    
    positions = {
        'TSLA': {'direction': 'SHORT', 'pnl': 125.40},
        'NVDA': {'direction': 'SHORT', 'pnl': 45.20},
        'META': {'direction': 'SHORT', 'pnl': 89.50},
        'AMZN': {'direction': 'SHORT', 'pnl': 67.30},
        'WMT': {'direction': 'LONG', 'pnl': -12.50},
        'JPM': {'direction': 'SHORT', 'pnl': 23.80},
        'AAPL': {'direction': 'LONG', 'pnl': -45.20},
        'BAC': {'direction': 'LONG', 'pnl': -28.40},
    }
    
    pnl_history = []
    base_pnl = 400
    for i in range(50):
        base_pnl += random.uniform(-15, 20)
        pnl_history.append({
            'time': f'20:{45+i//2:02d}:{i%60*random.randint(0,59):02d}',
            'pnl': round(base_pnl, 2)
        })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'positions': positions,
        'total_trades': len(trades),
        'total_pnl': round(sum(p['pnl'] for p in positions.values()), 2),
        'pnl_history': pnl_history,
        'recent_trades': trades[-5:],
        'market_volatility': {
            'level': 'normal',
            'threshold': 0.45,
            'avg_vol': 0.023,
            'stop_loss': 0.005,
            'take_profit': 0.008
        }
    }

def create_dashboard_html(data):
    """Create self-contained dashboard HTML"""
    total_pnl = data['total_pnl']
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time Trading Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{ font-size: 26px; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 14px; opacity: 0.8; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-card .label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
        .stat-card .value {{ font-size: 26px; font-weight: 700; margin-top: 8px; }}
        .stat-card .value.positive {{ color: #00ff88; }}
        .stat-card .value.negative {{ color: #ff4757; }}
        .stat-card .value.neutral {{ color: #00d4ff; }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .panel {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .panel h2 {{
            font-size: 15px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .chart-container {{ height: 280px; position: relative; }}
        
        .position-list {{ max-height: 280px; overflow-y: auto; }}
        .position-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }}
        .position-item:hover {{ background: rgba(255,255,255,0.08); }}
        .pos-symbol {{ font-weight: 700; font-size: 15px; }}
        .pos-direction {{
            font-size: 10px;
            padding: 4px 10px;
            border-radius: 20px;
            margin-left: 10px;
            font-weight: 600;
        }}
        .pos-direction.long {{ background: rgba(0,255,136,0.15); color: #00ff88; }}
        .pos-direction.short {{ background: rgba(255,71,87,0.15); color: #ff4757; }}
        .pos-pnl {{ font-weight: 700; font-size: 14px; }}
        .pos-pnl.positive {{ color: #00ff88; }}
        .pos-pnl.negative {{ color: #ff4757; }}
        
        .trade-list {{ max-height: 250px; overflow-y: auto; }}
        .trade-item {{
            display: grid;
            grid-template-columns: 60px 65px 55px 70px 1fr;
            gap: 10px;
            align-items: center;
            padding: 10px 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 6px;
            font-size: 13px;
        }}
        .trade-time {{ color: #666; font-size: 11px; }}
        .trade-symbol {{ font-weight: 600; }}
        .trade-action {{
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 4px;
            text-align: center;
            font-weight: 600;
        }}
        .trade-action.buy {{ background: rgba(0,255,136,0.15); color: #00ff88; }}
        .trade-action.sell {{ background: rgba(255,71,87,0.15); color: #ff4757; }}
        .trade-qty {{ color: #888; }}
        .trade-pnl {{ font-weight: 600; text-align: right; }}
        
        .vol-info {{
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .vol-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .vol-row:last-child {{ margin-bottom: 0; }}
        .vol-label {{ color: #888; }}
        .vol-value {{ font-weight: 600; }}
        
        @media (max-width: 900px) {{
            .main-grid {{ grid-template-columns: 1fr; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Intraday Trading Dashboard</h1>
        <div class="subtitle" id="headerTime">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Account Balance</div>
            <div class="value neutral">$100,000</div>
        </div>
        <div class="stat-card">
            <div class="label">Total P&L</div>
            <div class="value {'positive' if total_pnl >= 0 else 'negative'}">{'$' if total_pnl >= 0 else '-$'}{abs(total_pnl):,.2f}</div>
        </div>
        <div class="stat-card">
            <div class="label">Positions</div>
            <div class="value neutral">{len(data['positions'])}</div>
        </div>
        <div class="stat-card">
            <div class="label">Trades Today</div>
            <div class="value neutral">{data['total_trades']}</div>
        </div>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <h2>P&L Over Time</h2>
            <div class="chart-container">
                <canvas id="pnlChart"></canvas>
            </div>
        </div>
        <div class="panel">
            <h2>Market Volatility</h2>
            <div class="vol-info">
                <div class="vol-row">
                    <span class="vol-label">Market State</span>
                    <span class="vol-value" style="color: #ffd700;">{data['market_volatility']['level'].upper()}</span>
                </div>
                <div class="vol-row">
                    <span class="vol-label">Threshold</span>
                    <span class="vol-value">{data['market_volatility']['threshold']:.0%}</span>
                </div>
                <div class="vol-row">
                    <span class="vol-label">Avg Volatility</span>
                    <span class="vol-value">{data['market_volatility']['avg_vol']*100:.2f}%</span>
                </div>
                <div class="vol-row">
                    <span class="vol-label">Stop Loss</span>
                    <span class="vol-value">{data['market_volatility']['stop_loss']*100:.1f}%</span>
                </div>
                <div class="vol-row">
                    <span class="vol-label">Take Profit</span>
                    <span class="vol-value">{data['market_volatility']['take_profit']*100:.1f}%</span>
                </div>
            </div>
            <div class="chart-container" style="height: 140px;">
                <canvas id="volChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <h2>Active Positions</h2>
            <div class="position-list" id="positionList">
                {''.join([f'''
                <div class="position-item">
                    <div>
                        <span class="pos-symbol">{sym}</span>
                        <span class="pos-direction {p['direction'].lower()}">{p['direction']}</span>
                    </div>
                    <span class="pos-pnl {'positive' if p['pnl'] >= 0 else 'negative'}">{'+' if p['pnl'] >= 0 else ''}${{p['pnl']:.2f}}</span>
                </div>''' for sym, p in data['positions'].items()])}
            </div>
        </div>
        <div class="panel">
            <h2>Recent Trades</h2>
            <div class="trade-list">
                {''.join([f'''
                <div class="trade-item">
                    <div class="trade-time">{t['time']}</div>
                    <div class="trade-symbol">{t['symbol']}</div>
                    <div class="trade-action {'buy' if t['action'] in ['BUY','LONG'] else 'sell'}">{t['action']}</div>
                    <div class="trade-qty">{t['quantity']}</div>
                    <div class="trade-pnl {'positive' if t.get('pnl',0) >= 0 else 'negative'}">{'+' if t.get('pnl',0) >= 0 else ''}${{t.get('pnl',0):.2f}}</div>
                </div>''' for t in data['recent_trades']])}
            </div>
        </div>
    </div>
    
    <script>
        // P&L Chart
        const pnlCtx = document.getElementById('pnlChart').getContext('2d');
        const pnlChart = new Chart(pnlCtx, {{
            type: 'line',
            data: {{
                labels: {list(d['time'] for d in data['pnl_history'])},
                datasets: [{{
                    label: 'P&L',
                    data: {list(d['pnl'] for d in data['pnl_history'])},
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0,255,136,0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ display: false }},
                    y: {{ 
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#666' }}
                    }}
                }}
            }}
        }});
        
        // Volatility Chart (Position Distribution)
        const volCtx = document.getElementById('volChart').getContext('2d');
        const volChart = new Chart(volCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Long', 'Short', 'Cash'],
                datasets: [{{
                    data: [3, 4, 3],
                    backgroundColor: ['#00ff88', '#ff4757', '#333'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#888', padding: 15 }} }} }}
            }}
        }});
    </script>
</body>
</html>'''
    return html

if __name__ == "__main__":
    data = generate_sample_data()
    html = create_dashboard_html(data)
    
    filepath = "C:/Users/lulg/.openclaw/workspace/volatility_trading_system/reports/dashboard.html"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard created: {filepath}")
    print(f"Total P&L: ${data['total_pnl']:.2f}")
    print(f"Positions: {len(data['positions'])}")
    print(f"Trades: {data['total_trades']}")
