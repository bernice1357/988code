#!/usr/bin/env python3
"""
排程器監控工具
用於監控排程器運行狀態和即將執行的任務
"""

import os
import schedule
import pytz
from datetime import datetime, timedelta
import time

class SchedulerMonitor:
    """排程器監控器"""
    
    def __init__(self):
        self.timezone = pytz.timezone('Asia/Taipei')
        self.setup_test_schedules()
    
    def get_current_time(self):
        """獲取當前UTC+8時間"""
        return datetime.now(self.timezone)
    
    def setup_test_schedules(self):
        """設定與實際排程器相同的排程（用於監控）"""
        # 每日任務
        schedule.every().day.at("02:00").do(lambda: None).tag('觸發器健康檢查')
        schedule.every().day.at("02:30").do(lambda: None).tag('不活躍客戶檢查')
        schedule.every().day.at("04:00").do(lambda: None).tag('回購提醒維護')
        schedule.every().day.at("06:00").do(lambda: None).tag('銷量變化檢查')
        schedule.every().day.at("22:00").do(lambda: None).tag('每日預測生成')
        
        # 每週任務
        schedule.every().saturday.at("08:00").do(lambda: None).tag('Prophet模型訓練')
        schedule.every().sunday.at("02:00").do(lambda: None).tag('推薦系統更新')
    
    def get_next_jobs(self, hours=24):
        """獲取未來N小時內的任務"""
        current_time = self.get_current_time()
        future_time = current_time + timedelta(hours=hours)
        
        # 移除時區信息進行比較
        current_naive = current_time.replace(tzinfo=None)
        future_naive = future_time.replace(tzinfo=None)
        
        next_jobs = []
        for job in schedule.jobs:
            # 獲取任務的下次執行時間
            next_run = job.next_run
            if next_run and next_run <= future_naive:
                # 獲取任務標籤
                tags = list(job.tags) if job.tags else ['未命名任務']
                next_jobs.append({
                    'name': tags[0] if tags else '未命名任務',
                    'next_run': next_run,
                    'time_until': next_run - current_naive
                })
        
        # 按執行時間排序
        next_jobs.sort(key=lambda x: x['next_run'])
        return next_jobs
    
    def display_status(self):
        """顯示排程器狀態"""
        current_time = self.get_current_time()
        
        print("\n" + "="*60)
        print("排程器監控狀態")
        print("="*60)
        print(f"當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")
        print("-"*60)
        
        # 顯示今日將執行的任務
        print("\n【今日任務】")
        today_jobs = self.get_next_jobs(24)
        today_count = 0
        current_date = current_time.date()
        
        for job in today_jobs:
            if job['next_run'].date() == current_date:
                today_count += 1
                hours = job['time_until'].total_seconds() / 3600
                if hours < 0:
                    status = "已過期"
                elif hours < 1:
                    status = f"{int(job['time_until'].total_seconds() / 60)}分鐘後"
                else:
                    status = f"{hours:.1f}小時後"
                print(f"  {job['next_run'].strftime('%H:%M')} - {job['name']} ({status})")
        
        if today_count == 0:
            print("  今日無待執行任務")
        
        # 顯示明日任務
        print("\n【明日任務】")
        tomorrow_date = (current_time + timedelta(days=1)).date()
        tomorrow_count = 0
        for job in self.get_next_jobs(48):
            if job['next_run'].date() == tomorrow_date:
                tomorrow_count += 1
                print(f"  {job['next_run'].strftime('%H:%M')} - {job['name']}")
        
        if tomorrow_count == 0:
            print("  明日無待執行任務")
        
        # 顯示下一個即將執行的任務
        print("\n【下一個任務】")
        if today_jobs:
            next_job = today_jobs[0]
            print(f"  任務: {next_job['name']}")
            print(f"  執行時間: {next_job['next_run'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            total_seconds = next_job['time_until'].total_seconds()
            if total_seconds > 0:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                print(f"  倒計時: {hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                print("  狀態: 已過期，等待執行")
        else:
            print("  無待執行任務")
        
        print("-"*60)
    
    def check_log_files(self):
        """檢查日誌文件"""
        log_dir = 'logs'
        if os.path.exists(log_dir):
            log_files = os.listdir(log_dir)
            if log_files:
                print("\n【日誌文件】")
                for log_file in log_files[-5:]:  # 顯示最新5個
                    file_path = os.path.join(log_dir, log_file)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"  {log_file} ({file_size:.1f}KB) - {file_time.strftime('%Y-%m-%d %H:%M')}")
            else:
                print("\n【日誌文件】無日誌文件")
        else:
            print("\n【日誌文件】日誌目錄不存在")
    
    def run_monitor(self, refresh_seconds=60):
        """運行監控器"""
        print("排程器監控已啟動")
        print(f"每{refresh_seconds}秒刷新一次狀態")
        print("按 Ctrl+C 停止監控")
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # 清屏
                self.display_status()
                self.check_log_files()
                
                # 顯示刷新倒計時
                for i in range(refresh_seconds, 0, -1):
                    print(f"\r下次刷新: {i:2d}秒", end='', flush=True)
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n監控已停止")

def main():
    """主函數"""
    print("=== 排程器監控工具 ===")
    print("\n選擇功能:")
    print("1. 顯示當前狀態")
    print("2. 持續監控（每60秒刷新）")
    print("3. 快速監控（每10秒刷新）")
    print("4. 顯示未來48小時任務")
    
    monitor = SchedulerMonitor()
    
    try:
        choice = input("\n請輸入選項 (1-4): ").strip()
        
        if choice == "1":
            monitor.display_status()
            monitor.check_log_files()
        elif choice == "2":
            monitor.run_monitor(60)
        elif choice == "3":
            monitor.run_monitor(10)
        elif choice == "4":
            print("\n未來48小時任務列表:")
            print("-"*60)
            for job in monitor.get_next_jobs(48):
                print(f"{job['next_run'].strftime('%Y-%m-%d %H:%M')} - {job['name']}")
        else:
            print("無效選項")
    
    except KeyboardInterrupt:
        print("\n程式已停止")

if __name__ == "__main__":
    main()