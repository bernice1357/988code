#!/usr/bin/env python3
"""
排程器監控 Web 儀表板
提供簡單的 Web 介面查看排程器健康狀態
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import threading
import time

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(__file__))

from scheduler_health_monitor import SchedulerHealthMonitor
from continuous_monitor import ContinuousMonitor

app = Flask(__name__)

# HTML 模板
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>排程器監控儀表板</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        .healthy { color: #28a745; }
        .warning { color: #ffc107; }
        .critical { color: #dc3545; }
        .error { color: #6f42c1; }
        
        .schedulers {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .scheduler-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #ddd;
        }
        .scheduler-card.healthy { border-left-color: #28a745; }
        .scheduler-card.warning { border-left-color: #ffc107; }
        .scheduler-card.critical { border-left-color: #dc3545; }
        .scheduler-card.error { border-left-color: #6f42c1; }
        
        .scheduler-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .scheduler-name {
            font-size: 18px;
            font-weight: bold;
        }
        .scheduler-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .scheduler-status.healthy { background: #d4edda; color: #155724; }
        .scheduler-status.warning { background: #fff3cd; color: #856404; }
        .scheduler-status.critical { background: #f8d7da; color: #721c24; }
        .scheduler-status.error { background: #e2e3f1; color: #383d41; }
        
        .scheduler-info {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .scheduler-issues {
            margin-top: 10px;
        }
        .issue {
            background: #fff3cd;
            color: #856404;
            padding: 5px 8px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 13px;
        }
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .refresh-btn:hover {
            background: #0056b3;
        }
        .last-update {
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>排程器監控儀表板</h1>
            <p>即時監控所有排程器的健康狀態</p>
            <button class="refresh-btn" onclick="refreshData()">刷新數據</button>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number healthy" id="healthy-count">-</div>
                <div class="stat-label">健康</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning" id="warning-count">-</div>
                <div class="stat-label">警告</div>
            </div>
            <div class="stat-card">
                <div class="stat-number critical" id="critical-count">-</div>
                <div class="stat-label">嚴重</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error" id="error-count">-</div>
                <div class="stat-label">錯誤</div>
            </div>
        </div>
        
        <div class="schedulers" id="schedulers-container">
            <div style="text-align: center; padding: 40px; color: #666;">
                載入中...
            </div>
        </div>
        
        <div class="last-update" id="last-update">
            最後更新: -
        </div>
    </div>

    <script>
        function formatTime(timeStr) {
            if (!timeStr || timeStr === '無記錄') return timeStr;
            try {
                const date = new Date(timeStr);
                return date.toLocaleString('zh-TW');
            } catch (e) {
                return timeStr;
            }
        }
        
        function refreshData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // 更新統計
                    document.getElementById('healthy-count').textContent = data.summary.healthy;
                    document.getElementById('warning-count').textContent = data.summary.warning;
                    document.getElementById('critical-count').textContent = data.summary.critical;
                    document.getElementById('error-count').textContent = data.summary.error;
                    
                    // 更新排程器列表
                    const container = document.getElementById('schedulers-container');
                    container.innerHTML = '';
                    
                    data.results.forEach(scheduler => {
                        const card = document.createElement('div');
                        card.className = 'scheduler-card ' + scheduler.status;
                        
                        let issuesHtml = '';
                        if (scheduler.issues && scheduler.issues.length > 0) {
                            issuesHtml = '<div class="scheduler-issues">' +
                                scheduler.issues.map(issue => '<div class="issue">' + issue + '</div>').join('') +
                                '</div>';
                        }
                        
                        card.innerHTML = `
                            <div class="scheduler-header">
                                <div class="scheduler-name">${scheduler.name}</div>
                                <div class="scheduler-status ${scheduler.status}">${scheduler.status}</div>
                            </div>
                            <div class="scheduler-info">
                                <div>表格: ${scheduler.table}</div>
                                <div>頻率: ${scheduler.frequency}</div>
                                <div>最後更新: ${formatTime(scheduler.last_update)}</div>
                                <div>下次預期: ${formatTime(scheduler.next_expected)}</div>
                                <div>最近記錄數: ${scheduler.recent_records}</div>
                                ${scheduler.delay_hours > 0 ? '<div>延遲時間: ' + scheduler.delay_hours + ' 小時</div>' : ''}
                            </div>
                            ${issuesHtml}
                        `;
                        
                        container.appendChild(card);
                    });
                    
                    // 更新時間
                    document.getElementById('last-update').textContent = 
                        '最後更新: ' + new Date().toLocaleString('zh-TW');
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('schedulers-container').innerHTML = 
                        '<div style="text-align: center; padding: 40px; color: #dc3545;">載入失敗: ' + error.message + '</div>';
                });
        }
        
        // 頁面載入時自動刷新
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            // 每30秒自動刷新
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
"""

class WebDashboard:
    """Web 儀表板"""
    
    def __init__(self, port=5000):
        self.port = port
        self.monitor = SchedulerHealthMonitor()
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """設置路由"""
        
        @self.app.route('/')
        def dashboard():
            """主儀表板頁面"""
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/api/status')
        def api_status():
            """API: 獲取排程器狀態"""
            try:
                results = self.monitor.check_all_schedulers()
                
                summary = {
                    "total": len(results),
                    "healthy": len([r for r in results if r["status"] == "healthy"]),
                    "warning": len([r for r in results if r["status"] == "warning"]),
                    "critical": len([r for r in results if r["status"] == "critical"]),
                    "error": len([r for r in results if r["status"] == "error"])
                }
                
                return jsonify({
                    "success": True,
                    "results": results,
                    "summary": summary,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/health')
        def api_health():
            """API: 健康檢查"""
            return jsonify({
                "status": "ok",
                "timestamp": datetime.now().isoformat()
            })
    
    def run(self, debug=False, host='0.0.0.0'):
        """運行 Web 服務器"""
        print(f"啟動排程器監控儀表板...")
        print(f"訪問地址: http://localhost:{self.port}")
        print(f"API 地址: http://localhost:{self.port}/api/status")
        
        self.app.run(debug=debug, host=host, port=self.port, threaded=True)

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='排程器監控 Web 儀表板')
    parser.add_argument('--port', type=int, default=5000, help='Web 服務器端口，預設5000')
    parser.add_argument('--host', default='0.0.0.0', help='Web 服務器地址，預設0.0.0.0')
    parser.add_argument('--debug', action='store_true', help='啟用除錯模式')
    
    args = parser.parse_args()
    
    dashboard = WebDashboard(port=args.port)
    
    try:
        dashboard.run(debug=args.debug, host=args.host)
    except KeyboardInterrupt:
        print("\n服務器已停止")

if __name__ == "__main__":
    main()