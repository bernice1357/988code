#!/usr/bin/env python3
"""
設置資料庫觸發器的執行腳本
執行這個腳本來創建必要的觸發器和狀態表
"""

import sys
import os
import psycopg2
from pathlib import Path

# 加入專案路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '988code'))

try:
    from database_config import get_db_connection
    from env_loader import load_env_file
    load_env_file()
except ImportError as e:
    print(f"無法導入模組: {e}")
    print("請確保在正確的目錄下執行此腳本")
    sys.exit(1)

def setup_database_triggers():
    """設置資料庫觸發器"""
    sql_file = Path(__file__).parent / "setup_order_triggers.sql"

    if not sql_file.exists():
        print(f"找不到 SQL 檔案: {sql_file}")
        return False

    try:
        # 讀取 SQL 檔案
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 執行 SQL
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 分割 SQL 語句並逐一執行
                statements = sql_content.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            cursor.execute(statement)
                            print(f"✓ 執行成功: {statement[:50]}...")
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                print(f"✗ 執行失敗: {statement[:50]}... - {e}")
                            else:
                                print(f"✓ 已存在: {statement[:50]}...")

                conn.commit()
                print("\n✅ 資料庫觸發器設置完成！")

                # 檢查設置結果
                cursor.execute("SELECT * FROM order_update_status WHERE table_name = 'temp_customer_records'")
                result = cursor.fetchone()
                if result:
                    print(f"✅ 狀態表初始化成功，當前記錄數: {result[3]}")
                else:
                    print("⚠️  狀態表未找到記錄，可能需要手動初始化")

        return True

    except Exception as e:
        print(f"❌ 設置觸發器失敗: {e}")
        return False

def test_trigger():
    """測試觸發器是否正常工作"""
    print("\n🔍 測試觸發器功能...")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 檢查觸發器是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_trigger
                        WHERE tgname = 'trigger_order_update'
                    )
                """)
                trigger_exists = cursor.fetchone()[0]

                if trigger_exists:
                    print("✅ 觸發器 'trigger_order_update' 存在")
                else:
                    print("❌ 觸發器 'trigger_order_update' 不存在")

                # 檢查狀態表
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_name = 'order_update_status'
                """)
                table_exists = cursor.fetchone()[0] > 0

                if table_exists:
                    print("✅ 狀態表 'order_update_status' 存在")

                    # 顯示當前狀態
                    cursor.execute("SELECT * FROM order_update_status WHERE table_name = 'temp_customer_records'")
                    status = cursor.fetchone()
                    if status:
                        print(f"📊 當前狀態 - 最後更新: {status[2]}, 記錄數: {status[3]}")
                else:
                    print("❌ 狀態表 'order_update_status' 不存在")

        print("✅ 觸發器測試完成")
        return True

    except Exception as e:
        print(f"❌ 觸發器測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始設置訂單自動刷新觸發器...")
    print("=" * 50)

    success = setup_database_triggers()
    if success:
        test_trigger()
        print("\n" + "=" * 50)
        print("🎉 設置完成！現在當 temp_customer_records 表有新資料時，前端會自動刷新")
        print("📝 刷新間隔：每 5 秒檢查一次")
        print("📊 可以在 order_update_status 表查看更新狀態")
    else:
        print("\n❌ 設置失敗，請檢查錯誤訊息")
        sys.exit(1)