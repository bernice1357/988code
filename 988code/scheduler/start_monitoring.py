#!/usr/bin/env python3
"""
排程器監控系統啟動腳本
提供簡單的命令行介面來啟動各種監控功能
"""

import os
import sys
import argparse
import subprocess
import threading
import time

def print_banner():
    """顯示橫幅"""
    print("=" * 60)
    print("           排程器健康監控系統")
    print("=" * 60)
    print("功能:")
    print("  1. 單次健康檢查")
    print("  2. 持續監控")
    print("  3. Web 儀表板")
    print("  4. 系統測試")
    print("=" * 60)

def run_health_check():
    """執行單次健康檢查"""
    print("\n正在執行排程器健康檢查...")
    try:
        # 直接導入和調用模組，避免 subprocess 編碼問題
        from scheduler_health_monitor import SchedulerHealthMonitor
        
        monitor = SchedulerHealthMonitor()
        health_data = monitor.run_health_check()
        
        print("[成功] 健康檢查完成")
        print(f"詳細結果已保存到: {health_data['report_file']}")
        
        # 顯示摘要統計
        summary = health_data['summary']
        print("\n狀態摘要:")
        print(f"  總排程器數量: {summary['total']}")
        print(f"  健康: {summary['healthy']}")
        print(f"  警告: {summary['warning']}")
        print(f"  嚴重: {summary['critical']}")
        print(f"  錯誤: {summary['error']}")
        
        # 如果有問題，顯示問題排程器
        if summary['critical'] > 0 or summary['warning'] > 0:
            print("\n需要關注的排程器:")
            for result in health_data['results']:
                if result['status'] in ['critical', 'warning']:
                    status_label = '嚴重' if result['status'] == 'critical' else '警告'
                    print(f"  [{status_label}] {result['name']}: {', '.join(result['issues'])}")
            
    except Exception as e:
        print(f"[錯誤] 執行健康檢查時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def run_continuous_monitoring(interval=30):
    """啟動持續監控"""
    print(f"\n正在啟動持續監控 (檢查間隔: {interval} 分鐘)...")
    print("按 Ctrl+C 停止監控")
    
    try:
        subprocess.run([
            sys.executable, "continuous_monitor.py", 
            "--interval", str(interval)
        ])
    except KeyboardInterrupt:
        print("\n監控已停止")
    except Exception as e:
        print(f"[錯誤] 啟動持續監控時發生錯誤: {e}")

def run_web_dashboard(port=5000):
    """啟動 Web 儀表板"""
    print(f"\n正在啟動 Web 儀表板 (端口: {port})...")
    print(f"訪問地址: http://localhost:{port}")
    print("按 Ctrl+C 停止服務")
    
    try:
        subprocess.run([
            sys.executable, "web_dashboard.py",
            "--port", str(port)
        ])
    except KeyboardInterrupt:
        print("\nWeb 儀表板已停止")
    except Exception as e:
        print(f"[錯誤] 啟動 Web 儀表板時發生錯誤: {e}")

def run_system_test():
    """執行系統測試"""
    print("\n正在執行系統測試...")
    
    try:
        import locale
        system_encoding = locale.getpreferredencoding()
        
        result = subprocess.run([
            sys.executable, "test_monitoring.py"
        ], capture_output=True, text=True, encoding=system_encoding, errors='replace')
        
        if result.returncode == 0:
            print("[成功] 系統測試完成")
            # 顯示測試結果的最後幾行
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                print("\n測試結果摘要:")
                # 尋找關鍵的摘要行
                summary_lines = []
                for line in lines:
                    if any(keyword in line for keyword in ['測試總結', '[OK]', '[WARN]', '[SUCCESS]', '[ERR]', '健康檢查:', '報告生成:']):
                        summary_lines.append(line.strip())
                
                # 顯示摘要或最後10行
                display_lines = summary_lines[-10:] if summary_lines else lines[-10:]
                for line in display_lines:
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"[錯誤] 系統測試失敗")
            if result.stderr:
                print(f"錯誤詳情: {result.stderr[:200]}...")
            
    except Exception as e:
        print(f"[錯誤] 執行系統測試時發生錯誤: {e}")

def interactive_menu():
    """互動式選單"""
    while True:
        print_banner()
        print("\n請選擇操作:")
        print("1. 執行單次健康檢查")
        print("2. 啟動持續監控")
        print("3. 啟動 Web 儀表板")
        print("4. 執行系統測試")
        print("5. 退出")
        
        choice = input("\n請輸入選項 (1-5): ").strip()
        
        if choice == "1":
            run_health_check()
            input("\n按 Enter 繼續...")
            
        elif choice == "2":
            interval = input("請輸入檢查間隔時間 (分鐘，預設30): ").strip()
            try:
                interval = int(interval) if interval else 30
            except ValueError:
                interval = 30
            run_continuous_monitoring(interval)
            
        elif choice == "3":
            port = input("請輸入Web服務器端口 (預設5000): ").strip()
            try:
                port = int(port) if port else 5000
            except ValueError:
                port = 5000
            run_web_dashboard(port)
            
        elif choice == "4":
            run_system_test()
            input("\n按 Enter 繼續...")
            
        elif choice == "5":
            print("再見！")
            break
            
        else:
            print("無效選項，請重新選擇")
            time.sleep(1)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='排程器監控系統啟動腳本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python start_monitoring.py                    # 互動式選單
  python start_monitoring.py --check            # 單次健康檢查
  python start_monitoring.py --monitor          # 持續監控 (30分鐘間隔)
  python start_monitoring.py --monitor --interval 15  # 持續監控 (15分鐘間隔)
  python start_monitoring.py --web              # 啟動Web儀表板
  python start_monitoring.py --web --port 8080  # 啟動Web儀表板 (端口8080)
  python start_monitoring.py --test             # 執行系統測試
        """
    )
    
    parser.add_argument('--check', action='store_true',
                       help='執行單次健康檢查')
    parser.add_argument('--monitor', action='store_true',
                       help='啟動持續監控')
    parser.add_argument('--web', action='store_true',
                       help='啟動Web儀表板')
    parser.add_argument('--test', action='store_true',
                       help='執行系統測試')
    parser.add_argument('--interval', type=int, default=30,
                       help='持續監控的檢查間隔時間(分鐘)，預設30')
    parser.add_argument('--port', type=int, default=5000,
                       help='Web儀表板端口，預設5000')
    
    args = parser.parse_args()
    
    # 檢查是否在正確的目錄中
    required_files = [
        'scheduler_health_monitor.py',
        'continuous_monitor.py',
        'web_dashboard.py',
        'test_monitoring.py'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("[錯誤] 缺少必要文件:")
        for f in missing_files:
            print(f"  - {f}")
        print("\n請確保在正確的目錄中運行此腳本")
        return 1
    
    # 根據參數執行相應功能
    if args.check:
        run_health_check()
    elif args.monitor:
        run_continuous_monitoring(args.interval)
    elif args.web:
        run_web_dashboard(args.port)
    elif args.test:
        run_system_test()
    else:
        # 沒有指定參數，進入互動式選單
        try:
            interactive_menu()
        except KeyboardInterrupt:
            print("\n\n程序已退出")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())