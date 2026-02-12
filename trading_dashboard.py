"""
Real-Time Intraday Trading Dashboard
Web-based monitoring with live charts
"""
import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Trading data storage
class TradingData:
    def __init__(self):
        self.positions = {}
        self.trades = []
        self.pnl_history = []
        self.market_volatility = {}
        self.start_time = datetime.now()
        
    def add_trade(self, trade: dict):
        self.trades.append(trade)
        self.pnl_history.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'pnl': self.calculate_total_pnl()
        })
    
    def calculate_total_pnl(self) -> float:
        return sum(t.get('pnl', 0) for t in self.trades)
    
    def get_status(self) -> dict:
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'positions': self.positions,
            'total_trades': len(self.trades),
            'total_pnl': self.calculate_total_pnl(),
            'pnl_history': self.pnl_history[-50:],  # Last 50 points
            'recent_trades': self.trades[-10:],
            'market_volatility': self.market_volatility
        }
    
    def update_position(self, symbol: str, data: dict):
        self.positions[symbol] = data
    
    def set_volatility(self, vol: dict):
        self.market_volatility = vol


# Global data store
data = TradingData()


class TradingDashboardHandler(SimpleHTTPRequestHandler):
    """Web请求处理器"""
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/status':
            self.send_json_response(data.get_status())
        elif parsed.path == '/api/trade':
            # 模拟一笔交易
            trade = {
                'symbol': 'TSLA',
                'action': 'BUY',
                'quantity': 10,
                'price': 415.50,
                'pnl': 12.50,
                'time': datetime.now().strftime('%H:%M:%S')
            }
            data.add_trade(trade)
            self.send_json_response({'status': 'ok', 'trade': trade})
        elif parsed.path == '/api/update':
            # 更新数据（模拟）
            params = parse_qs(parsed.query)
            if 'symbol' in params:
                symbol = params['symbol'][0]
                data.update_position(symbol, {
                    'price': float(params.get('price', [0])[0]),
                    'pnl': float(params.get('pnl', [0])[0]),
                    'change': float(params.get('change', [0])[0])
                })
            self.send_json_response({'status': 'ok'})
        elif parsed.path == '/' or parsed.path == '/dashboard':
            self.serve_file('templates/dashboard.html')
        elif parsed.path == '/chart':
            self.serve_file('templates/chart.html')
        else:
            super().do_GET()
    
    def send_json_response(self, obj):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
    
    def serve_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404, 'File not found')


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """多线程HTTP服务器"""
    allow_reuse_address = True


def run_server(port=8080):
    """启动服务器"""
    # 创建模板目录
    os.makedirs('templates', exist_ok=True)
    
    # 创建仪表板HTML
    create_dashboard_html()
    create_chart_html()
    
    server = ThreadedHTTPServer(('0.0.0.0', port), TradingDashboardHandler)
    print(f"="*60)
    print(f"  TRADING DASHBOARD SERVER")
    print(f"  http://localhost:{port}")
    print(f"  http://localhost:{port}/dashboard")
    print(f"  http://localhost:{port}/chart")
    print("="*60)
    
    server.serve_forever()


def create_dashboard_html():
    """创建主仪表板页面"""
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intraday Trading Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }
        
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header .time { font-size: 14px; opacity: 0.8; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .stat-card .label { font-size: 12px; color: #888; text-transform: uppercase; }
        .stat-card .value { font-size: 28px; font-weight: bold; margin-top: 8px; }
        .stat-card .value.positive { color: #00ff88; }
        .stat-card .value.negative { color: #ff4757; }
        .stat-card .value.neutral { color: #00d4ff; }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .panel {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .panel h2 {
            font-size: 16px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .position-list { max-height: 300px; overflow-y: auto; }
        
        .position-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .position-item:last-child { margin-bottom: 0; }
        
        .pos-symbol { font-weight: bold; font-size: 16px; }
        .pos-direction {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 12px;
            margin-left: 8px;
        }
        .pos-direction.long { background: rgba(0,255,136,0.2); color: #00ff88; }
        .pos-direction.short { background: rgba(255,71,87,0.2); color: #ff4757; }
        
        .pos-pnl { font-weight: bold; }
        .pos-pnl.positive { color: #00ff88; }
        .pos-pnl.negative { color: #ff4757; }
        
        .trade-list { max-height: 250px; overflow-y: auto; }
        
        .trade-item {
            display: grid;
            grid-template-columns: 60px 70px 60px 80px 1fr;
            gap: 10px;
            align-items: center;
            padding: 10px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 6px;
            font-size: 13px;
        }
        
        .trade-time { color: #666; }
        .trade-symbol { font-weight: bold; }
        .trade-action {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            text-align: center;
        }
        .trade-action.buy { background: rgba(0,255,136,0.2); color: #00ff88; }
        .trade-action.sell { background: rgba(255,71,87,0.2); color: #ff4757; }
        
        .trade-pnl { font-weight: bold; }
        
        .chart-container {
            height: 300px;
            position: relative;
        }
        
        .volatility-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .vol-bar {
            flex: 1;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .vol-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #ffd700, #ff4757);
            transition: width 0.5s ease;
        }
        
        .vol-label { font-size: 12px; color: #888; min-width: 60px; }
        
        @media (max-width: 768px) {
            .main-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Intraday Trading Dashboard</h1>
        <div class="time" id="headerTime"></div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Account Balance</div>
            <div class="value neutral" id="accountBalance">$100,000</div>
        </div>
        <div class="stat-card">
            <div class="label">Total P&L</div>
            <div class="value" id="totalPnl">$0.00</div>
        </div>
        <div class="stat-card">
            <div class="label">Positions</div>
            <div class="value neutral" id="positionCount">0</div>
        </div>
        <div class="stat-card">
            <div class="label">Trades Today</div>
            <div class="value neutral" id="tradeCount">0</div>
        </div>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <h2>Real-Time P&L Chart</h2>
            <div class="chart-container">
                <canvas id="pnlChart"></canvas>
            </div>
        </div>
        
        <div class="panel">
            <h2>Market Volatility</h2>
            <div id="volatilityInfo" style="margin-bottom: 15px;"></div>
            <div class="chart-container">
                <canvas id="volChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <h2>Active Positions</h2>
            <div class="position-list" id="positionList">
                <div style="text-align: center; color: #666; padding: 40px;">
                    No active positions
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>Recent Trades</h2>
            <div class="trade-list" id="tradeList">
                <div style="text-align: center; color: #666; padding: 40px;">
                    No trades yet
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Charts
        let pnlChart, volChart;
        
        // Initialize charts
        function initCharts() {
            const pnlCtx = document.getElementById('pnlChart').getContext('2d');
            pnlChart = new Chart(pnlCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'P&L',
                        data: [],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0,255,136,0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { display: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { display: true, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
            
            const volCtx = document.getElementById('volChart').getContext('2d');
            volChart = new Chart(volCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Long', 'Short', 'Cash'],
                    datasets: [{
                        data: [0, 0, 100],
                        backgroundColor: ['#00ff88', '#ff4757', '#00d4ff']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }
        
        // Format currency
        function formatCurrency(value) {
            const sign = value >= 0 ? '' : '-';
            return sign + '$' + Math.abs(value).toFixed(2);
        }
        
        // Update UI
        function updateUI(data) {
            document.getElementById('headerTime').textContent = new Date(data.timestamp).toLocaleString();
            
            // Stats
            const pnlEl = document.getElementById('totalPnl');
            pnlEl.textContent = formatCurrency(data.total_pnl);
            pnlEl.className = 'value ' + (data.total_pnl >= 0 ? 'positive' : 'negative');
            
            document.getElementById('positionCount').textContent = Object.keys(data.positions).length;
            document.getElementById('tradeCount').textContent = data.total_trades;
            
            // P&L Chart
            pnlChart.data.labels = data.pnl_history.map(p => p.time);
            pnlChart.data.datasets[0].data = data.pnl_history.map(p => p.pnl);
            pnlChart.data.datasets[0].borderColor = data.total_pnl >= 0 ? '#00ff88' : '#ff4757';
            pnlChart.update('none');
            
            // Positions
            const posList = document.getElementById('positionList');
            const positions = Object.entries(data.positions);
            if (positions.length > 0) {
                posList.innerHTML = positions.map(([sym, p]) => `
                    <div class="position-item">
                        <div>
                            <span class="pos-symbol">${sym}</span>
                            <span class="pos-direction ${p.direction.toLowerCase()}">${p.direction}</span>
                        </div>
                        <div class="pos-pnl ${p.pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(p.pnl)}</div>
                    </div>
                `).join('');
            }
            
            // Trades
            const tradeList = document.getElementById('tradeList');
            if (data.recent_trades.length > 0) {
                tradeList.innerHTML = data.recent_trades.reverse().map(t => `
                    <div class="trade-item">
                        <div class="trade-time">${t.time}</div>
                        <div class="trade-symbol">${t.symbol}</div>
                        <div class="trade-action ${t.action.toLowerCase()}">${t.action}</div>
                        <div class="trade-qty">${t.quantity}</div>
                        <div class="trade-pnl ${t.pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(t.pnl)}</div>
                    </div>
                `).join('');
            }
            
            // Volatility
            const vol = data.market_volatility;
            if (vol.level) {
                const volInfo = document.getElementById('volatilityInfo');
                volInfo.innerHTML = `
                    <div class="volatility-bar">
                        <span class="vol-label">${vol.level.toUpperCase()}</span>
                        <div class="vol-bar">
                            <div class="vol-fill" style="width: ${Math.min(vol.avg_vol * 1000, 100)}%"></div>
                        </div>
                        <span style="font-size: 12px;">${(vol.avg_vol * 100).toFixed(1)}%</span>
                    </div>
                    <div style="font-size: 12px; color: #888;">
                        Threshold: ${(vol.threshold * 100).toFixed(0)}% | 
                        Stop: ${(vol.stop_loss * 100).toFixed(1)}% | 
                        Target: ${(vol.take_profit * 100).toFixed(1)}%
                    </div>
                `;
            }
        }
        
        // Fetch data
        async function fetchData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateUI(data);
            } catch (e) {
                console.error('Fetch error:', e);
            }
        }
        
        // Simulate trading (for demo)
        function simulateTrading() {
            fetch('/api/trade');
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            fetchData();
            setInterval(fetchData, 2000);  // Update every 2 seconds
        });
    </script>
</body>
</html>'''
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)


def create_chart_html():
    """创建独立图表页面"""
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Trading Chart</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0d0d0d;
            color: #fff;
            padding: 20px;
            font-family: 'SF Mono', Monaco, monospace;
        }
        .chart-box {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .chart-title {
            font-size: 14px;
            color: #888;
            margin-bottom: 15px;
        }
        .chart-container {
            height: 300px;
        }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value { font-size: 24px; font-weight: bold; }
        .stat-label { font-size: 11px; color: #888; margin-top: 5px; }
        .positive { color: #00ff88; }
        .negative { color: #ff4757; }
    </style>
</head>
<body>
    <div class="stats">
        <div class="stat">
            <div class="stat-value neutral" id="balance">$100,000</div>
            <div class="stat-label">Balance</div>
        </div>
        <div class="stat">
            <div class="stat-value" id="pnl">$0.00</div>
            <div class="stat-label">Total P&L</div>
        </div>
        <div class="stat">
            <div class="stat-value neutral" id="trades">0</div>
            <div class="stat-label">Trades</div>
        </div>
        <div class="stat">
            <div class="stat-value neutral" id="winrate">0%</div>
            <div class="stat-label">Win Rate</div>
        </div>
    </div>
    
    <div class="grid-2">
        <div class="chart-box">
            <div class="chart-title">P&L Over Time</div>
            <div class="chart-container">
                <canvas id="pnlChart"></canvas>
            </div>
        </div>
        <div class="chart-box">
            <div class="chart-title">Position Distribution</div>
            <div class="chart-container">
                <canvas id="pieChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="chart-box">
        <div class="chart-title">Trade History</div>
        <div class="chart-container">
            <canvas id="tradeChart"></canvas>
        </div>
    </div>
    
    <script>
        let pnlChart, pieChart, tradeChart;
        
        function initCharts() {
            pnlChart = new Chart(document.getElementById('pnlChart'), {
                type: 'line',
                data: { labels: [], datasets: [{ 
                    data: [],
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0,255,136,0.1)',
                    fill: true,
                    tension: 0.4
                }] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { display: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { display: true, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
            
            pieChart = new Chart(document.getElementById('pieChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Long', 'Short', 'Cash'],
                    datasets: [{ data: [0, 0, 100], backgroundColor: ['#00ff88', '#ff4757', '#333'] }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
            
            tradeChart = new Chart(document.getElementById('tradeChart'), {
                type: 'bar',
                data: { labels: [], datasets: [{
                    data: [],
                    backgroundColor: [],
                    borderRadius: 4
                }] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { display: true, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { display: true, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
        }
        
        async function update() {
            try {
                const r = await fetch('/api/status');
                const d = await r.json();
                
                document.getElementById('pnl').textContent = (d.total_pnl >= 0 ? '+' : '') + '$' + d.total_pnl.toFixed(2);
                document.getElementById('pnl').className = 'stat-value ' + (d.total_pnl >= 0 ? 'positive' : 'negative');
                document.getElementById('trades').textContent = d.total_trades;
                
                pnlChart.data.labels = d.pnl_history.map(p => p.time);
                pnlChart.data.datasets[0].data = d.pnl_history.map(p => p.pnl);
                pnlChart.data.datasets[0].borderColor = d.total_pnl >= 0 ? '#00ff88' : '#ff4757';
                pnlChart.update('none');
                
                const wins = d.recent_trades.filter(t => t.pnl > 0).length;
                const rate = d.total_trades > 0 ? (wins / d.total_trades * 100).toFixed(0) : 0;
                document.getElementById('winrate').textContent = rate + '%';
                
                // Position distribution
                let long = 0, short = 0;
                Object.values(d.positions).forEach(p => {
                    if (p.direction === 'LONG') long++;
                    else short++;
                });
                pieChart.data.datasets[0].data = [long, short, 5 - long - short];
                pieChart.update('none');
                
                // Trade bars
                tradeChart.data.labels = d.recent_trades.map(t => t.symbol + ' ' + t.time);
                tradeChart.data.datasets[0].data = d.recent_trades.map(t => t.pnl);
                tradeChart.data.datasets[0].backgroundColor = d.recent_trades.map(t => t.pnl >= 0 ? '#00ff88' : '#ff4757');
                tradeChart.update('none');
                
            } catch (e) { console.error(e); }
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            update();
            setInterval(update, 2000);
        });
    </script>
</body>
</html>'''
    
    with open('templates/chart.html', 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
