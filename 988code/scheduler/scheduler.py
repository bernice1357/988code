#!/usr/bin/env python3
"""
排程系統模組
管理Prophet模型的週六訓練和每日預測排程
"""

import os
import time
import logging
import schedule
import pytz
from datetime import datetime, timedelta
# 新的目錄結構導入
from database_integration import DatabaseIntegration
from task_executor import execute_task
from config import DatabaseConfig, SchedulerConfig, LoggingConfig, get_db_config

# 原始任務模組導入 (需要時才導入)
try:
    from tasks.prophet_system import ProphetPredictionSystem
except ImportError:
    ProphetPredictionSystem = None

class PredictionScheduler:
    """預測排程管理系統"""
    
    def __init__(self):
        self.prophet_system = ProphetPredictionSystem()
        self.db_integration = DatabaseIntegration()
        
        # 設定時區（從配置文件讀取）
        self.timezone = pytz.timezone(SchedulerConfig.TIMEZONE)
        
        # 初始化月銷售預測系統（使用統一配置）
        self.db_config = get_db_config()
        self.monthly_system = HybridCVOptimizedSystem(self.db_config)
        self.monthly_db = MonthlyPredictionDB(self.db_config)
        self.recommendation_db = RecommendationDB(self.db_config)
        self.inactive_customer_manager = InactiveCustomerManager(self.db_config)
        self.repurchase_reminder = RepurchaseReminder(self.db_config)
        self.sales_change_manager = SalesChangeManager(self.db_config)
        self.trigger_health_monitor = TriggerHealthMonitor(self.db_config)
        
        self.setup_logging()
        
        print("=== Prophet預測排程系統 ===")
        print(f"系統時區: UTC+8 (Asia/Taipei)")
        print(f"當前時間: {self.get_current_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def get_current_time(self):
        """獲取當前UTC+8時間"""
        return datetime.now(self.timezone)
    
    def setup_logging(self):
        """設定日誌系統（使用統一配置）"""
        os.makedirs(LoggingConfig.LOG_DIR, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, LoggingConfig.LOG_LEVEL),
            format=LoggingConfig.LOG_FORMAT,
            handlers=[
                logging.FileHandler(LoggingConfig.get_log_file_path('scheduler'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def saturday_training_job(self):
        """週六訓練排程任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始週六模型訓練排程任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 執行Prophet模型訓練
            training_success = self.prophet_system.saturday_model_training()
            
            if not training_success:
                self.logger.error("Prophet模型訓練失敗")
                return False
            
            self.logger.info(f"訓練成功，模型數量: {len(self.prophet_system.prophet_models)}")
            
            # 2. 生成預測
            predictions = self.prophet_system.generate_daily_predictions(prediction_days=7)
            
            if not predictions or len(predictions) == 0:
                self.logger.warning("沒有生成預測")
                return False
            
            self.logger.info(f"生成預測數量: {len(predictions)}")
            
            # 3. 保存CSV備份
            csv_file = self.prophet_system.save_predictions_to_csv(
                predictions, 'saturday_training_predictions'
            )
            
            if not csv_file:
                self.logger.error("CSV保存失敗")
                return False
            
            # 4. 導入數據庫
            batch_id = f"saturday_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if self.db_integration.import_predictions_to_database(predictions, batch_id):
                self.logger.info("數據庫導入成功")
                
                # 5. 清理過期預測
                self.db_integration.cleanup_expired_predictions()
                
                # 6. 生成訓練報告
                self.generate_training_report(batch_id, len(predictions))
                
                return True
            else:
                self.logger.error("數據庫導入失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"週六訓練排程任務異常: {e}")
            return False
    
    def daily_prediction_job(self):
        """每日預測排程任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每日預測排程任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 載入最新模型
            if not self.prophet_system.load_latest_models():
                self.logger.error("無法載入模型")
                return False
            
            self.logger.info(f"載入模型數量: {len(self.prophet_system.prophet_models)}")
            
            # 2. 檢查昨日預測準確率
            yesterday_accuracy = self.db_integration.check_yesterday_accuracy()
            self.logger.info(f"昨日預測準確率: {yesterday_accuracy:.2%}")
            
            # 3. 生成今日預測
            predictions = self.prophet_system.generate_daily_predictions(prediction_days=1)
            
            if not predictions or len(predictions) == 0:
                self.logger.warning("沒有生成預測")
                return False
            
            self.logger.info(f"生成預測數量: {len(predictions)}")
            
            # 4. 保存CSV備份
            csv_file = self.prophet_system.save_predictions_to_csv(
                predictions, 'daily_predictions'
            )
            
            # 5. 導入數據庫
            batch_id = f"daily_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if self.db_integration.import_predictions_to_database(predictions, batch_id):
                self.logger.info("數據庫導入成功")
                
                # 6. 生成日報
                self.generate_daily_report(batch_id, len(predictions), yesterday_accuracy)
                
                return True
            else:
                self.logger.error("數據庫導入失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"每日預測排程任務異常: {e}")
            return False
    
    def monthly_sales_prediction_job(self):
        """每月銷售預測排程任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每月銷售預測排程任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 創建當月的預測系統（預測下個月）
            from dateutil.relativedelta import relativedelta
            next_month = current_time + relativedelta(months=1)
            self.monthly_system = HybridCVOptimizedSystem(self.db_config, prediction_month=next_month)
            
            # 2. 執行月銷售預測
            self.logger.info(f"執行混合CV優化兩階段預測系統 - 預測{next_month.strftime('%Y年%m月')}")
            subcategory_df, sku_df = self.monthly_system.run_prediction()
            
            if subcategory_df is None:
                self.logger.error("月銷售預測執行失敗")
                return False
            
            self.logger.info(f"預測完成: {len(subcategory_df)}個子類別, {len(sku_df)}個SKU")
            
            # 3. 上傳預測結果到資料庫
            batch_id = f"monthly_{next_month.strftime('%Y%m%d')}_{current_time.strftime('%H%M%S')}"
            self.logger.info(f"開始上傳預測結果到資料庫, batch_id: {batch_id}")
            
            upload_success = self.monthly_db.save_predictions(subcategory_df, sku_df, batch_id)
            
            if not upload_success:
                self.logger.error("預測結果上傳到資料庫失敗")
                # 即使上傳失敗，我們仍然繼續產生報告，因為CSV已經儲存
            else:
                self.logger.info("預測結果成功上傳到資料庫")
            
            # 4. 計算整體準確率
            total_sub_pred = subcategory_df['prediction'].sum()
            total_sub_actual = subcategory_df['actual'].sum()
            sub_accuracy = 1 - abs(total_sub_pred - total_sub_actual) / total_sub_actual if total_sub_actual > 0 else 0
            
            if len(sku_df) > 0:
                total_sku_pred = sku_df['prediction'].sum()
                total_sku_actual = sku_df['actual'].sum()
                sku_accuracy = 1 - abs(total_sku_pred - total_sku_actual) / total_sku_actual if total_sku_actual > 0 else 0
            else:
                sku_accuracy = 0
            
            # 5. 生成月報
            self.generate_monthly_report(
                len(subcategory_df),
                len(sku_df),
                sub_accuracy,
                sku_accuracy,
                batch_id,
                upload_success
            )
            
            self.logger.info(f"月銷售預測完成 - 子類別準確率: {sub_accuracy:.1%}, SKU準確率: {sku_accuracy:.1%}")
            return True
            
        except Exception as e:
            self.logger.error(f"月銷售預測排程任務異常: {e}")
            return False
    
    def generate_monthly_report(self, sub_count, sku_count, sub_accuracy, sku_accuracy, batch_id, upload_success):
        """生成月銷售預測報告"""
        current_time = self.get_current_time()
        from dateutil.relativedelta import relativedelta
        next_month = current_time + relativedelta(months=1)
        
        db_status = "成功" if upload_success else "失敗"
        
        report = f"""
月銷售預測完成報告
========================
時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)
預測月份: {next_month.strftime('%Y年%m月')}
批次ID: {batch_id}

預測統計:
- 子類別數量: {sub_count}
- SKU數量: {sku_count}

預測準確率:
- 子類別總準確率: {sub_accuracy:.1%}
- SKU總準確率: {sku_accuracy:.1%}

資料儲存:
- CSV檔案: 已儲存到 outputs/ 資料夾
- 資料庫上傳: {db_status}

系統: 混合CV優化兩階段預測系統
========================
"""
        
        # 保存報告
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        report_file = f"{report_dir}/monthly_report_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"月銷售報告已保存: {report_file}")
    
    def generate_training_report(self, batch_id, prediction_count):
        """生成訓練報告"""
        report = f"""
Prophet週六訓練完成報告
========================
時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
批次ID: {batch_id}
訓練模型數: {len(self.prophet_system.prophet_models)}
生成預測數: {prediction_count}
狀態: 成功
        """
        
        # 保存報告
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/training_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"訓練報告已保存: {report_file}")
    
    def generate_daily_report(self, batch_id, prediction_count, yesterday_accuracy):
        """生成每日報告"""
        report = f"""
Prophet每日預測報告
==================
時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
批次ID: {batch_id}
今日預測數: {prediction_count}
昨日準確率: {yesterday_accuracy:.2%}
狀態: 成功
        """
        
        # 保存報告
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"每日報告已保存: {report_file}")
    
    def weekly_recommendation_job(self):
        """每週推薦系統更新任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每週推薦系統更新任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 執行推薦系統
            self.logger.info("執行推薦系統計算 (Top 7)")
            customer_recs, product_recs = generate_recommendations(self.db_config)
            
            if customer_recs is None or product_recs is None:
                self.logger.error("推薦系統執行失敗")
                return False
            
            self.logger.info(f"推薦計算完成: {len(customer_recs)}個客戶推薦, {len(product_recs)}個產品推薦")
            
            # 2. 生成批次ID
            batch_id = f"recommend_{current_time.strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"開始上傳推薦結果到資料庫, batch_id: {batch_id}")
            
            # 3. 儲存到資料庫
            customer_upload_success = self.recommendation_db.save_customer_recommendations(customer_recs, batch_id)
            product_upload_success = self.recommendation_db.save_product_recommendations(product_recs, batch_id)
            
            if not customer_upload_success or not product_upload_success:
                self.logger.error("推薦結果上傳到資料庫失敗")
                return False
            else:
                self.logger.info("推薦結果成功上傳到資料庫")
            
            # 4. 生成推薦報告
            self.generate_recommendation_report(
                len(customer_recs),
                len(product_recs),
                customer_recs['customer_id'].nunique(),
                product_recs['product_id'].nunique(),
                batch_id,
                customer_upload_success and product_upload_success
            )
            
            self.logger.info(f"推薦系統更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"推薦系統排程任務異常: {e}")
            return False
    
    def generate_recommendation_report(self, customer_recs_count, product_recs_count, unique_customers, unique_products, batch_id, upload_success):
        """生成推薦系統報告"""
        current_time = self.get_current_time()
        
        db_status = "成功" if upload_success else "失敗"
        
        report = f"""
推薦系統更新完成報告
====================
時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)
批次ID: {batch_id}

推薦統計:
- 客戶推薦記錄數: {customer_recs_count}
- 產品推薦記錄數: {product_recs_count}
- 涉及客戶數: {unique_customers}
- 涉及產品數: {unique_products}

資料庫上傳: {db_status}
系統狀態: 正常
        """
        
        # 保存報告
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/recommendation_report_{current_time.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"推薦報告已保存: {report_file}")
    
    def daily_inactive_customer_job(self):
        """每日不活躍客戶檢查任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每日不活躍客戶檢查任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 初始化系統（確保表和觸發器存在）
            if not self.inactive_customer_manager.initialize_system():
                self.logger.error("不活躍客戶系統初始化失敗")
                return False
            
            # 2. 執行每日不活躍客戶檢查
            self.logger.info("執行不活躍客戶檢查")
            success = self.inactive_customer_manager.daily_check_inactive_customers()
            
            if not success:
                self.logger.error("不活躍客戶檢查失敗")
                return False
            
            # 3. 獲取統計資料
            stats = self.inactive_customer_manager.get_statistics()
            
            if stats:
                self.logger.info(f"不活躍客戶統計: 總計 {stats.get('total_inactive', 0)} 個")
                self.logger.info(f"今日新增: {stats.get('today_created', 0)} 個")
                self.logger.info(f"本月重新活躍: {stats.get('reactivated_this_month', 0)} 個")
                
                # 4. 生成不活躍客戶報告
                self.generate_inactive_customer_report(
                    stats.get('total_inactive', 0),
                    stats.get('today_created', 0),
                    stats.get('reactivated_this_month', 0),
                    stats
                )
            
            # 5. 清理過期記錄（90天前的重新活躍記錄）
            self.inactive_customer_manager.cleanup_old_records(90)
            
            self.logger.info("不活躍客戶檢查任務完成")
            return True
            
        except Exception as e:
            self.logger.error(f"不活躍客戶檢查任務異常: {e}")
            return False
    
    def generate_inactive_customer_report(self, total_inactive, today_created, reactivated_this_month, stats):
        """生成不活躍客戶報告"""
        current_time = self.get_current_time()
        
        day_stats_str = ""
        if 'day_stats' in stats and stats['day_stats']:
            for day_range, count in stats['day_stats'].items():
                day_stats_str += f"- {day_range}: {count} 筆\n"
        
        report = f"""
不活躍客戶檢查完成報告
====================
時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)

統計結果:
- 總不活躍客戶: {total_inactive}
- 今日新增記錄: {today_created}
- 本月重新活躍: {reactivated_this_month}

按天數分布:
{day_stats_str}
系統狀態: 正常
觸發器: 啟用（即時重新活躍偵測）
        """
        
        # 保存報告
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/inactive_customer_report_{current_time.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"不活躍客戶報告已保存: {report_file}")
    
    def daily_repurchase_reminder_job(self):
        """每日回購提醒維護任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每日回購提醒維護任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 建立索引（確保效能）
            self.repurchase_reminder.db.create_indexes()
            
            # 2. 執行回購提醒維護
            self.logger.info("執行回購提醒維護")
            
            # 建立新的提醒記錄
            new_count = self.repurchase_reminder.create_repurchase_reminder_records()
            
            # 更新現有提醒記錄的天數
            updated_count = self.repurchase_reminder.update_existing_reminders()
            
            # 處理已重新購買的客戶
            completed_count = self.repurchase_reminder.mark_completed_reminders()
            
            self.logger.info(f"回購提醒維護完成: 新增 {new_count} 筆, 更新 {updated_count} 筆, 完成 {completed_count} 筆")
            
            # 3. 獲取統計資料
            stats = self.repurchase_reminder.db.get_reminder_statistics()
            
            if stats:
                self.logger.info(f"回購提醒統計: 待處理 {stats.get('total_active_reminders', 0)} 筆")
                self.logger.info(f"今日新增: {stats.get('today_created', 0)} 筆")
                self.logger.info(f"本月完成: {stats.get('completed_this_month', 0)} 筆")
                
                # 4. 生成回購提醒報告
                self.generate_repurchase_reminder_report(
                    stats.get('total_active_reminders', 0),
                    stats.get('today_created', 0),
                    stats.get('completed_this_month', 0),
                    new_count,
                    updated_count,
                    completed_count,
                    stats
                )
            
            # 5. 清理過期記錄（90天前的已完成記錄）
            self.repurchase_reminder.db.cleanup_old_records(90)
            
            self.logger.info("回購提醒維護任務完成")
            return True
            
        except Exception as e:
            self.logger.error(f"回購提醒維護任務異常: {e}")
            return False
    
    def generate_repurchase_reminder_report(self, total_active, today_created, completed_this_month, 
                                           new_count, updated_count, completed_count, stats):
        """生成回購提醒報告"""
        current_time = self.get_current_time()
        
        day_stats_str = ""
        if 'day_stats' in stats and stats['day_stats']:
            for day_range, count in stats['day_stats'].items():
                day_stats_str += f"- {day_range}: {count} 筆\n"
        
        report = f"""
回購提醒維護完成報告
====================
時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)

執行結果:
- 新增提醒記錄: {new_count} 筆
- 更新天數: {updated_count} 筆
- 標記完成: {completed_count} 筆

統計資訊:
- 待處理提醒總數: {total_active}
- 今日新增記錄: {today_created}
- 本月完成數: {completed_this_month}

按天數分布:
{day_stats_str}
系統狀態: 正常
資料來源: temp_customer_records (新品購買記錄)
        """
        
        # 保存報告
        report_dir = 'reports'
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/repurchase_reminder_report_{current_time.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"回購提醒報告已保存: {report_file}")
    
    def daily_sales_change_job(self):
        """每日銷量變化檢查任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每日銷量變化檢查任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 1. 初始化系統（確保索引存在）
            if not self.sales_change_manager.initialize_system():
                self.logger.error("銷量變化系統初始化失敗")
                return False
            
            # 2. 執行每日資料一致性檢查
            self.logger.info("執行銷量變化資料一致性檢查")
            success = self.sales_change_manager.daily_consistency_check()
            
            if not success:
                self.logger.error("銷量變化資料一致性檢查失敗")
                return False
            
            # 3. 檢查異常銷量變化
            self.logger.info("檢查異常銷量變化")
            self.sales_change_manager.check_anomalies()
            
            # 4. 獲取統計資料
            stats = self.sales_change_manager.get_sales_statistics()
            
            if stats:
                self.logger.info(f"銷量變化統計: 總產品 {stats.get('total_products', 0)} 個")
                self.logger.info(f"異常變化: {stats.get('anomaly_count', 0)} 個")
                self.logger.info(f"缺貨產品: {stats.get('zero_stock_count', 0)} 個")
                
                # 5. 生成銷量變化報告
                self.generate_sales_change_report(
                    stats.get('total_products', 0),
                    stats.get('anomaly_count', 0),
                    stats.get('zero_stock_count', 0),
                    stats
                )
            
            self.logger.info("銷量變化檢查任務完成")
            return True
            
        except Exception as e:
            self.logger.error(f"銷量變化檢查任務異常: {e}")
            return False
    
    def monthly_sales_change_reset_job(self):
        """每月銷量重置任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每月銷量重置任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 執行月度重置
            self.logger.info("執行月度銷量重置")
            success = self.sales_change_manager.monthly_reset()
            
            if success:
                self.logger.info("月度銷量重置完成")
                
                # 重新初始化新月份資料
                self.sales_change_manager.initialize_new_month_data()
                
                # 生成重置報告
                stats = self.sales_change_manager.get_sales_statistics()
                if stats:
                    self.generate_monthly_sales_reset_report(
                        stats.get('total_products', 0),
                        current_time
                    )
                
                return True
            else:
                self.logger.error("月度銷量重置失敗")
                return False
                
        except Exception as e:
            self.logger.error(f"月度銷量重置任務異常: {e}")
            return False
    
    def generate_sales_change_report(self, total_products, anomaly_count, zero_stock_count, stats):
        """生成銷量變化報告"""
        current_time = self.get_current_time()
        
        change_dist_str = ""
        if 'change_distribution' in stats and stats['change_distribution']:
            for change_range, count in stats['change_distribution'].items():
                change_dist_str += f"- {change_range}: {count} 個\n"
        
        report = f"""
銷量變化檢查完成報告
====================
時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)

統計結果:
- 總監控產品數: {total_products}
- 異常變化產品: {anomaly_count}
- 缺貨產品: {zero_stock_count}
- 低庫存產品: {stats.get('low_stock_count', 0)}
- 平均庫存量: {stats.get('avg_stock_quantity', 0):.2f}

銷量變化分布:
{change_dist_str}

系統狀態: 正常
觸發器: 啟用（即時銷量更新）
        """
        
        # 保存報告
        report_dir = 'reports'
        import os
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/sales_change_report_{current_time.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"銷量變化報告已保存: {report_file}")
    
    def generate_monthly_sales_reset_report(self, total_products, reset_time):
        """生成月度銷量重置報告"""
        
        report = f"""
月度銷量重置完成報告
==================
時間: {reset_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)
重置月份: {reset_time.strftime('%Y年%m月')}

重置結果:
- 重置產品數: {total_products}
- 上月銷量 → 歷史銷量
- 當月銷量 → 重置為0
- 變化百分比 → 重新計算

系統狀態: 正常
新月份監控: 已啟動
        """
        
        # 保存報告
        report_dir = 'reports'
        import os
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/monthly_sales_reset_{reset_time.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"月度銷量重置報告已保存: {report_file}")
    
    def daily_trigger_health_check_job(self):
        """每日觸發器健康檢查任務"""
        current_time = self.get_current_time()
        self.logger.info(f"開始每日觸發器健康檢查任務 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        
        try:
            # 執行完整的觸發器健康檢查
            health_report = self.trigger_health_monitor.run_complete_health_check()
            
            # 記錄檢查結果
            overall_status = health_report.get('overall_status', 'unknown')
            self.logger.info(f"觸發器健康檢查完成，整體狀態: {overall_status}")
            
            # 統計結果
            existence_check = health_report.get('existence_check', {})
            functionality_test = health_report.get('functionality_test', {})
            alerts = health_report.get('alerts', [])
            
            missing_triggers = [name for name, exists in existence_check.items() if not exists]
            failed_triggers = [name for name, result in functionality_test.items() if not result.get('success', False)]
            
            # 記錄詳細結果
            if missing_triggers:
                self.logger.error(f"缺少觸發器: {missing_triggers}")
            
            if failed_triggers:
                self.logger.error(f"功能測試失敗的觸發器: {failed_triggers}")
            
            if alerts:
                self.logger.warning(f"發現 {len(alerts)} 個觸發器告警")
            
            # 生成健康檢查報告
            self.generate_trigger_health_report(health_report)
            
            # 根據狀態判斷是否成功
            success = overall_status in ['healthy', 'warning']
            
            if success:
                self.logger.info("觸發器健康檢查任務完成")
            else:
                self.logger.error("觸發器健康檢查發現嚴重問題")
            
            return success
            
        except Exception as e:
            self.logger.error(f"觸發器健康檢查任務異常: {e}")
            return False
    
    def generate_trigger_health_report(self, health_report):
        """生成觸發器健康檢查報告"""
        current_time = self.get_current_time()
        overall_status = health_report.get('overall_status', 'unknown')
        
        # 存在性檢查結果
        existence_check = health_report.get('existence_check', {})
        existence_summary = ""
        for trigger_name, exists in existence_check.items():
            status_icon = "✓" if exists else "✗"
            existence_summary += f"  {status_icon} {trigger_name}\n"
        
        # 功能性測試結果
        functionality_test = health_report.get('functionality_test', {})
        functionality_summary = ""
        for trigger_name, result in functionality_test.items():
            success = result.get('success', False)
            exec_time = result.get('execution_time_ms', 0)
            status_icon = "✓" if success else "✗"
            functionality_summary += f"  {status_icon} {trigger_name}: {exec_time:.2f}ms\n"
        
        # 效能統計
        performance_stats = health_report.get('performance_stats', {})
        performance_summary = ""
        for trigger_name, stats in performance_stats.items():
            success_rate = stats.get('success_rate', 0)
            avg_time = stats.get('avg_execution_time_ms', 0)
            performance_summary += f"  {trigger_name}: 成功率 {success_rate:.1f}%, 平均時間 {avg_time:.2f}ms\n"
        
        # 告警信息
        alerts = health_report.get('alerts', [])
        alerts_summary = ""
        if alerts:
            for alert in alerts:
                alerts_summary += f"  ⚠ {alert['trigger_name']}: {alert['error_message']}\n"
        else:
            alerts_summary = "  無告警\n"
        
        report = f"""
觸發器健康檢查完成報告
======================
時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)
整體狀態: {overall_status.upper()}

觸發器存在性檢查:
{existence_summary}

功能性測試結果:
{functionality_summary}

效能統計 (過去7天):
{performance_summary}

告警信息:
{alerts_summary}

系統狀態: {'正常' if overall_status == 'healthy' else '異常' if overall_status == 'critical' else '警告'}
檢查頻率: 每日 03:30 自動執行
        """
        
        # 保存報告
        report_dir = 'reports'
        import os
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = f"{report_dir}/trigger_health_report_{current_time.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"觸發器健康檢查報告已保存: {report_file}")
    
    def setup_schedule(self):
        """設定排程任務 (所有時間為UTC+8)"""
        # 週六早上8點執行模型訓練
        schedule.every().saturday.at("08:00").do(self.saturday_training_job)
        
        # 每天晚上10點執行預測生成（預測明天）
        schedule.every().day.at("22:00").do(self.daily_prediction_job)
        
        # 每月1號凌晨0點30分執行銷量重置（先重置再預測）
        schedule.every().day.at("00:30").do(self.check_and_run_monthly_sales_reset)
        
        # 每月1號凌晨1點執行月銷售預測
        schedule.every().day.at("01:00").do(self.check_and_run_monthly_prediction)
        
        # 每週日凌晨2點執行推薦系統更新
        schedule.every().sunday.at("02:00").do(self.weekly_recommendation_job)
        
        # 每天凌晨2點執行觸發器健康檢查
        schedule.every().day.at("02:00").do(self.daily_trigger_health_check_job)
        
        # 每天凌晨2點30分執行不活躍客戶檢查
        schedule.every().day.at("02:30").do(self.daily_inactive_customer_job)
        
        # 每天凌晨4點執行回購提醒維護
        schedule.every().day.at("04:00").do(self.daily_repurchase_reminder_job)
        
        # 每天早上6點執行銷量變化檢查
        schedule.every().day.at("06:00").do(self.daily_sales_change_job)
        
        self.logger.info("排程設定完成 (時區: UTC+8):")
        self.logger.info("- 每月1號 00:30: 銷量重置")
        self.logger.info("- 每月1號 01:00: 月銷售預測")
        self.logger.info("- 週日 02:00: 推薦系統更新")
        self.logger.info("- 每天 03:30: 觸發器健康檢查")
        self.logger.info("- 每天 05:00: 不活躍客戶檢查")
        self.logger.info("- 每天 06:00: 回購提醒維護")
        self.logger.info("- 每天 07:00: 銷量變化檢查")
        self.logger.info("- 週六 08:00: 模型訓練")
        self.logger.info("- 每天 22:00: 預測生成（預測明天）")
    
    def check_and_run_monthly_prediction(self):
        """檢查是否為每月1號並執行月銷售預測"""
        current_time = self.get_current_time()
        if current_time.day == 1:
            self.logger.info(f"今天是每月1號 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})，執行月銷售預測")
            return self.monthly_sales_prediction_job()
        return True
    
    def check_and_run_monthly_sales_reset(self):
        """檢查是否為每月1號並執行銷量重置"""
        current_time = self.get_current_time()
        if current_time.day == 1:
            self.logger.info(f"今天是每月1號 (UTC+8: {current_time.strftime('%Y-%m-%d %H:%M:%S')})，執行銷量重置")
            return self.monthly_sales_change_reset_job()
        return True
    
    def run_scheduler(self):
        """執行排程器"""
        self.setup_schedule()
        
        print("排程器啟動中...")
        print("按 Ctrl+C 停止排程器")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
                
        except KeyboardInterrupt:
            self.logger.info("排程器已停止")
            print("\n排程器已停止")
    
    def test_saturday_training(self):
        """測試週六訓練任務"""
        print("=== 測試週六訓練任務 ===")
        success = self.saturday_training_job()
        
        if success:
            print("✓ 週六訓練任務測試成功")
        else:
            print("✗ 週六訓練任務測試失敗")
        
        return success
    
    def test_daily_prediction(self):
        """測試每日預測任務"""
        print("=== 測試每日預測任務 ===")
        success = self.daily_prediction_job()
        
        if success:
            print("✓ 每日預測任務測試成功")
        else:
            print("✗ 每日預測任務測試失敗")
        
        return success
    
    def test_monthly_prediction(self):
        """測試月銷售預測任務"""
        print("=== 測試月銷售預測任務 ===")
        success = self.monthly_sales_prediction_job()
        
        if success:
            print("月銷售預測任務測試成功")
        else:
            print("月銷售預測任務測試失敗")
        
        return success
    
    def test_recommendation(self):
        """測試推薦系統任務"""
        print("=== 測試推薦系統任務 ===")
        success = self.weekly_recommendation_job()
        
        if success:
            print("✓ 推薦系統任務測試成功")
        else:
            print("✗ 推薦系統任務測試失敗")
        
        return success
    
    def test_inactive_customer(self):
        """測試不活躍客戶管理任務"""
        print("=== 測試不活躍客戶管理任務 ===")
        success = self.daily_inactive_customer_job()
        
        if success:
            print("不活躍客戶管理任務測試成功")
        else:
            print("不活躍客戶管理任務測試失敗")
        
        return success
    
    def test_repurchase_reminder(self):
        """測試回購提醒任務"""
        print("=== 測試回購提醒任務 ===")
        success = self.daily_repurchase_reminder_job()
        
        if success:
            print("✓ 回購提醒任務測試成功")
        else:
            print("✗ 回購提醒任務測試失敗")
        
        return success
    
    def test_sales_change_monitoring(self):
        """測試銷量變化監控任務"""
        print("=== 測試銷量變化監控任務 ===")
        success = self.daily_sales_change_job()
        
        if success:
            print("✓ 銷量變化監控任務測試成功")
        else:
            print("✗ 銷量變化監控任務測試失敗")
        
        return success
    
    def test_monthly_sales_reset(self):
        """測試月度銷量重置任務"""
        print("=== 測試月度銷量重置任務 ===")
        success = self.monthly_sales_change_reset_job()
        
        if success:
            print("✓ 月度銷量重置任務測試成功")
        else:
            print("✗ 月度銷量重置任務測試失敗")
        
        return success
    
    def test_trigger_health_check(self):
        """測試觸發器健康檢查任務"""
        print("=== 測試觸發器健康檢查任務 ===")
        success = self.daily_trigger_health_check_job()
        
        if success:
            print("✓ 觸發器健康檢查任務測試成功")
        else:
            print("✗ 觸發器健康檢查任務測試失敗")
        
        return success
    
    def test_complete_system(self):
        """測試完整系統"""
        print("=== Prophet排程系統完整測試 ===")
        
        # 1. 先確保數據庫架構存在
        print("\n[1] 檢查數據庫架構...")
        if not self.db_integration.create_database_schema():
            print("✗ 數據庫架構檢查失敗")
            return False
        
        if not self.db_integration.create_purchase_detection_trigger():
            print("✗ 觸發器檢查失敗")
            return False
        
        print("✓ 數據庫架構檢查完成")
        
        # 2. 測試週六訓練
        print("\n[2] 測試週六訓練任務...")
        if not self.test_saturday_training():
            print("✗ 週六訓練測試失敗")
            return False
        
        # 3. 測試每日預測
        print("\n[3] 測試每日預測任務...")
        if not self.test_daily_prediction():
            print("✗ 每日預測測試失敗")
            return False
        
        # 4. 系統狀態檢查
        print("\n[4] 系統狀態檢查...")
        self.db_integration.get_system_status()
        
        print("\n=== 完整系統測試成功 ===")
        print("系統功能:")
        print("- Prophet模型自動訓練")
        print("- 每日預測自動生成")
        print("- 數據庫自動存儲")
        print("- 購買偵測觸發器")
        print("- 審計日誌記錄")
        print("- 統計報表生成")
        
        return True

def main():
    """主函數"""
    print("=== Prophet預測排程系統 ===")
    
    scheduler = PredictionScheduler()
    
    # 選擇執行模式
    print("\n選擇執行模式:")
    print("1. 測試完整系統")
    print("2. 啟動排程器")
    print("3. 手動執行週六訓練")
    print("4. 手動執行每日預測")
    print("5. 手動執行月銷售預測")
    print("6. 手動執行推薦系統")
    print("7. 手動執行不活躍客戶檢查")
    print("8. 手動執行回購提醒維護")
    print("9. 手動執行銷量變化檢查")
    print("10. 手動執行月度銷量重置")
    print("11. 手動執行觸發器健康檢查")
    
    try:
        choice = input("\n請輸入選項 (1-11): ").strip()
        
        if choice == "1":
            scheduler.test_complete_system()
        elif choice == "2":
            scheduler.run_scheduler()
        elif choice == "3":
            scheduler.test_saturday_training()
        elif choice == "4":
            scheduler.test_daily_prediction()
        elif choice == "5":
            scheduler.test_monthly_prediction()
        elif choice == "6":
            scheduler.test_recommendation()
        elif choice == "7":
            scheduler.test_inactive_customer()
        elif choice == "8":
            scheduler.test_repurchase_reminder()
        elif choice == "9":
            scheduler.test_sales_change_monitoring()
        elif choice == "10":
            scheduler.test_monthly_sales_reset()
        elif choice == "11":
            scheduler.test_trigger_health_check()
        else:
            print("無效選項")
            
    except KeyboardInterrupt:
        print("\n程式已停止")

if __name__ == "__main__":
    main()