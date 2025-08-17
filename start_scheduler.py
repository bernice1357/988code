#!/usr/bin/env python3
"""
988 Scheduler System Launcher
This script starts the integrated scheduler that runs tasks at scheduled times
"""

import sys
import os
import time
from datetime import datetime

# Add scheduler path to system
sys.path.append(os.path.join(os.path.dirname(__file__), '988code', 'scheduler'))

from integrated_scheduler import integrated_scheduler

def print_banner():
    """Print startup banner"""
    print("=" * 60)
    print("988 INTEGRATED SCHEDULER SYSTEM")
    print("=" * 60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print("\nScheduled Tasks:")
    print("\n[RESTOCK]")
    print("  - Saturday 08:00 - Prophet model training")
    print("  - Daily 22:00 - Daily prediction")
    print("  - Daily 02:00 - Trigger health check")
    print("\n[SALES]")
    print("  - Monthly 1st 00:30 - Sales reset")
    print("  - Monthly 1st 01:00 - Monthly prediction")
    print("  - Daily 06:00 - Sales change check")
    print("\n[RECOMMENDATION]")
    print("  - Sunday 02:00 - Weekly recommendation update")
    print("\n[CUSTOMER MANAGEMENT]")
    print("  - Daily 02:30 - Inactive customer check")
    print("  - Daily 04:00 - Repurchase reminder")
    print("-" * 60)
    print("\nScheduler will check database for enabled/disabled status")
    print("Use the web interface to enable/disable specific schedules")
    print("\nPress Ctrl+C to stop the scheduler")
    print("=" * 60)

def main():
    """Main execution function"""
    try:
        print_banner()
        
        # Start the integrated scheduler
        integrated_scheduler.start_scheduler()
        print("\n[INFO] Scheduler started successfully")
        print("[INFO] Monitoring for scheduled tasks...")
        
        # Keep running
        while True:
            time.sleep(60)  # Check every minute
            
            # Show status every hour
            if datetime.now().minute == 0:
                print(f"\n[STATUS] {datetime.now().strftime('%Y-%m-%d %H:%M')} - Scheduler running")
                
                # Show next scheduled jobs
                next_jobs = integrated_scheduler.get_next_jobs()
                if next_jobs:
                    print("[NEXT JOBS]")
                    for job in next_jobs[:5]:  # Show next 5 jobs
                        print(f"  - {job['next_run']}: {job['job']}")
                        
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopping scheduler...")
        integrated_scheduler.stop_scheduler()
        print("[INFO] Scheduler stopped successfully")
        
    except Exception as e:
        print(f"\n[ERROR] Scheduler error: {e}")
        integrated_scheduler.stop_scheduler()
        sys.exit(1)

if __name__ == "__main__":
    main()