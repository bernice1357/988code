#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合CV優化預測系統 (Scheduler整合版)
結合 full_product_unified_predictor 和 two_stage_prediction_system 的優勢
CV <= 0.8 使用 full_product_unified_predictor 的方法
CV > 0.8 使用 two_stage_prediction_system 的方法
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import psycopg2
from prophet import Prophet
import warnings
import os
import logging
warnings.filterwarnings('ignore')

class HybridCVOptimizedSystem:
    """混合CV優化兩階段預測系統"""
    
    def __init__(self, db_config, prediction_month=None):
        """
        初始化
        Args:
            db_config: 資料庫配置
            prediction_month: 預測月份 (datetime格式)，如果為None則預測下個月
        """
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        
        # 設定預測月份
        if prediction_month is None:
            # 預設預測下個月
            self.prediction_month = datetime.now() + relativedelta(months=1)
        else:
            self.prediction_month = prediction_month
        
        # 設定時間範圍
        self.current_month = self.prediction_month - relativedelta(months=1)  # 當前月
        self.history_start = self.prediction_month - relativedelta(months=18)  # 18個月歷史
        self.recent_3_months_start = self.prediction_month - relativedelta(months=4)  # 最近3個月開始
        
        self.logger.info("=== 混合CV優化預測系統 ===")
        self.logger.info(f"預測月份: {self.prediction_month.strftime('%Y年%m月')}")
        self.logger.info(f"歷史數據範圍: {self.history_start.strftime('%Y-%m')} 至 {self.current_month.strftime('%Y-%m')}")
        self.logger.info("-" * 50)
        self.logger.info("預測策略:")
        self.logger.info("CV <= 0.4 (低波動): 使用Prophet模型")
        self.logger.info("0.4 < CV <= 0.8 (中波動): 使用EWMA+趨勢")
        self.logger.info("CV > 0.8 (高波動): 使用中位數")
        self.logger.info("=" * 50)
        
    def get_database_connection(self):
        """建立數據庫連接"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            self.logger.error(f"數據庫連接失敗: {str(e)}")
            return None
    
    def get_subcategory_data(self):
        """獲取子類別數據"""
        self.logger.info("第一階段：子類別預測")
        self.logger.info("-" * 50)
        
        conn = self.get_database_connection()
        if conn is None:
            return None
        
        try:
            query = """
            WITH subcategory_stats AS (
                SELECT 
                    pm.subcategory,
                    DATE_TRUNC('month', ot.transaction_date) as month,
                    SUM(ot.quantity) as quantity
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE pm.is_active = 'active'
                  AND ot.transaction_date >= %s::date
                  AND ot.transaction_date < %s::date
                  AND ot.document_type = '銷貨'
                  AND ot.quantity > 0
                GROUP BY pm.subcategory, DATE_TRUNC('month', ot.transaction_date)
            ),
            recent_months AS (
                -- 最近3個月的銷量
                SELECT 
                    pm.subcategory,
                    SUM(CASE WHEN DATE_TRUNC('month', ot.transaction_date) = %s::date THEN ot.quantity ELSE 0 END) as month_minus_3,
                    SUM(CASE WHEN DATE_TRUNC('month', ot.transaction_date) = %s::date THEN ot.quantity ELSE 0 END) as month_minus_2,
                    SUM(CASE WHEN DATE_TRUNC('month', ot.transaction_date) = %s::date THEN ot.quantity ELSE 0 END) as month_minus_1
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE pm.is_active = 'active'
                  AND ot.transaction_date >= %s::date
                  AND ot.transaction_date < %s::date
                  AND ot.document_type = '銷貨'
                  AND ot.quantity > 0
                GROUP BY pm.subcategory
            ),
            cv_calculation AS (
                SELECT 
                    subcategory,
                    COUNT(month) as month_count,
                    AVG(quantity) as avg_quantity,
                    STDDEV(quantity) as std_quantity,
                    CASE 
                        WHEN AVG(quantity) > 0 THEN STDDEV(quantity) / AVG(quantity)
                        ELSE 999
                    END as cv,
                    SUM(quantity) as total_quantity
                FROM subcategory_stats
                GROUP BY subcategory
                HAVING COUNT(month) >= 3  -- 至少3個月歷史
            )
            SELECT 
                c.subcategory,
                c.month_count,
                c.avg_quantity,
                c.std_quantity,
                c.cv,
                c.total_quantity,
                COALESCE(r.month_minus_3, 0) as month_minus_3,
                COALESCE(r.month_minus_2, 0) as month_minus_2,
                COALESCE(r.month_minus_1, 0) as month_minus_1,
                CASE 
                    WHEN c.cv <= 0.4 THEN '低波動'
                    WHEN c.cv <= 0.8 THEN '中波動'
                    ELSE '高波動'
                END as volatility_group
            FROM cv_calculation c
            LEFT JOIN recent_months r ON c.subcategory = r.subcategory
            WHERE c.avg_quantity > 0  -- 排除零銷售
            ORDER BY c.total_quantity DESC
            """
            
            # 準備查詢參數
            month_minus_3 = self.prediction_month - relativedelta(months=3)
            month_minus_2 = self.prediction_month - relativedelta(months=2)
            month_minus_1 = self.prediction_month - relativedelta(months=1)
            
            params = (
                self.history_start.strftime('%Y-%m-%d'),  # 歷史開始
                self.prediction_month.strftime('%Y-%m-%d'),  # 預測月份
                month_minus_3.strftime('%Y-%m-01'),  # 3個月前
                month_minus_2.strftime('%Y-%m-01'),  # 2個月前
                month_minus_1.strftime('%Y-%m-01'),  # 1個月前
                self.recent_3_months_start.strftime('%Y-%m-%d'),  # 最近3個月開始
                self.prediction_month.strftime('%Y-%m-%d')  # 預測月份
            )
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            self.logger.info(f"找到 {len(df)} 個活躍子類別")
            
            # 統計各組分布
            for group in ['低波動', '中波動', '高波動']:
                count = len(df[df['volatility_group'] == group])
                if count > 0:
                    self.logger.info(f"  {group}: {count} 個子類別")
            
            return df
            
        except Exception as e:
            self.logger.error(f"獲取子類別數據失敗: {e}")
            if conn:
                conn.close()
            return None
    
    def get_monthly_history(self, subcategory):
        """獲取月度歷史數據"""
        conn = self.get_database_connection()
        if conn is None:
            return None
        
        try:
            query = """
            WITH monthly_sales AS (
                SELECT 
                    DATE_TRUNC('month', ot.transaction_date) as ds,
                    SUM(ot.quantity) as quantity
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE pm.subcategory = %s
                  AND pm.is_active = 'active'
                  AND ot.transaction_date >= %s::date
                  AND ot.transaction_date < %s::date
                  AND ot.document_type = '銷貨'
                  AND ot.quantity > 0
                GROUP BY DATE_TRUNC('month', ot.transaction_date)
            ),
            month_series AS (
                SELECT generate_series(
                    %s::date,
                    %s::date,
                    '1 month'::interval
                )::date as ds
            )
            SELECT 
                ms.ds,
                COALESCE(s.quantity, 0) as y
            FROM month_series ms
            LEFT JOIN monthly_sales s ON ms.ds = s.ds
            ORDER BY ms.ds
            """
            
            # 準備查詢參數
            params = (
                subcategory,
                self.history_start.strftime('%Y-%m-%d'),  # 歷史開始
                self.prediction_month.strftime('%Y-%m-%d'),  # 預測月份
                self.history_start.strftime('%Y-%m-01'),  # 系列開始
                self.current_month.strftime('%Y-%m-01')  # 系列結束（當前月）
            )
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            if conn:
                conn.close()
            return None
    
    def predict_ultra_stable(self, subcategory, history):
        """超穩定產品預測 (CV <= 0.3)"""
        # 使用最近3個月平均
        recent_data = history[history['y'] > 0].tail(3)
        if len(recent_data) >= 3:
            return recent_data['y'].mean()
        return history[history['y'] > 0]['y'].mean()
    
    def predict_stable(self, subcategory, history):
        """穩定產品預測 (0.3 < CV <= 0.5)"""
        # 移除零值月份
        history_clean = history[history['y'] > 0].copy()
        
        if len(history_clean) >= 6:
            try:
                # 使用Prophet
                model = Prophet(
                    changepoint_prior_scale=0.01,  # 低變點敏感度
                    seasonality_prior_scale=1.0,
                    yearly_seasonality=False,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    interval_width=0.95
                )
                
                model.fit(history_clean)
                future = model.make_future_dataframe(periods=1, freq='MS')
                forecast = model.predict(future)
                
                prediction = forecast['yhat'].iloc[-1]
                
                # 約束範圍
                avg = history_clean['y'].mean()
                return np.clip(prediction, avg * 0.5, avg * 1.5)
                
            except:
                pass
        
        # 退回到加權平均
        return history_clean['y'].tail(6).mean()
    
    def predict_medium_volatility(self, subcategory, history):
        """中等波動預測 (0.5 < CV <= 0.8)"""
        # 移除零值
        history_clean = history[history['y'] > 0].copy()
        
        if len(history_clean) < 3:
            return history_clean['y'].mean() if len(history_clean) > 0 else 0
        
        predictions = []
        
        # EWMA
        if len(history_clean) >= 3:
            alpha = 0.3
            ewma = history_clean['y'].ewm(alpha=alpha, adjust=False).mean()
            predictions.append(ewma.iloc[-1])
        
        # 最近趨勢
        if len(history_clean) >= 4:
            recent = history_clean['y'].tail(3).mean()
            predictions.append(recent * 1.05)  # 微調
        
        # 中位數
        predictions.append(history_clean['y'].median())
        
        return np.median(predictions) if predictions else history_clean['y'].mean()
    
    def predict_high_volatility(self, subcategory, history):
        """高波動預測 (CV > 0.8)"""
        # 移除零值
        history_clean = history[history['y'] > 0].copy()
        
        if len(history_clean) < 2:
            # 使用保守估計
            return history_clean['y'].mean() * 0.8 if len(history_clean) > 0 else 0
        
        # 使用中位數（更穩健）
        if len(history_clean) >= 4:
            return history_clean['y'].median()
        
        return history_clean['y'].mean()
    
    def predict_subcategory(self, row):
        """預測子類別"""
        subcategory = row['subcategory']
        cv = row['cv']
        volatility_group = row['volatility_group']
        
        # 檢查前2個月是否都是0
        if row['month_minus_2'] == 0 and row['month_minus_1'] == 0:
            return 0
        
        # 獲取歷史數據
        history = self.get_monthly_history(subcategory)
        if history is None or len(history[history['y'] > 0]) == 0:
            return row['avg_quantity']
        
        # 根據CV選擇預測方法
        if volatility_group == '低波動':
            return self.predict_stable(subcategory, history)  # 使用Prophet
        elif volatility_group == '中波動':
            return self.predict_medium_volatility(subcategory, history)  # 使用EWMA
        else:  # 高波動
            return self.predict_high_volatility(subcategory, history)  # 使用中位數
    
    def get_sku_allocation_factors(self, subcategory):
        """獲取SKU分配因子"""
        conn = self.get_database_connection()
        if conn is None:
            return None
        
        try:
            # 使用更長的歷史期間來計算分配比例
            query = """
            WITH sku_sales AS (
                SELECT 
                    pm.product_id,
                    MAX(ot.product_name) as product_name,  -- 取最常見的名稱
                    SUM(ot.quantity) as total_quantity,
                    COUNT(DISTINCT DATE_TRUNC('month', ot.transaction_date)) as active_months,
                    AVG(ot.quantity) as avg_quantity
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE pm.subcategory = %s
                  AND pm.is_active = 'active'
                  AND ot.transaction_date >= %s::date
                  AND ot.transaction_date < %s::date
                  AND ot.document_type = '銷貨'
                  AND ot.quantity > 0
                GROUP BY pm.product_id
            ),
            recent_sales AS (
                -- 最近5個月的銷售權重
                SELECT 
                    pm.product_id,
                    SUM(ot.quantity) as recent_quantity,
                    SUM(CASE WHEN DATE_TRUNC('month', ot.transaction_date) = %s::date THEN ot.quantity ELSE 0 END) as month_minus_3,
                    SUM(CASE WHEN DATE_TRUNC('month', ot.transaction_date) = %s::date THEN ot.quantity ELSE 0 END) as month_minus_2,
                    SUM(CASE WHEN DATE_TRUNC('month', ot.transaction_date) = %s::date THEN ot.quantity ELSE 0 END) as month_minus_1
                FROM order_transactions ot
                JOIN product_master pm ON ot.product_id = pm.product_id
                WHERE pm.subcategory = %s
                  AND pm.is_active = 'active'
                  AND ot.transaction_date >= %s::date
                  AND ot.transaction_date < %s::date
                  AND ot.document_type = '銷貨'
                  AND ot.quantity > 0
                GROUP BY pm.product_id
            )
            SELECT 
                s.product_id,
                s.product_name,
                s.total_quantity,
                s.active_months,
                s.avg_quantity,
                COALESCE(r.recent_quantity, 0) as recent_quantity,
                COALESCE(r.month_minus_3, 0) as month_minus_3,
                COALESCE(r.month_minus_2, 0) as month_minus_2,
                COALESCE(r.month_minus_1, 0) as month_minus_1,
                -- 使用最近銷售的比例，如果沒有則使用歷史比例
                CASE 
                    WHEN SUM(COALESCE(r.recent_quantity, 0)) OVER() > 0 
                    THEN COALESCE(r.recent_quantity, 0)::float / SUM(COALESCE(r.recent_quantity, 0)) OVER()
                    ELSE s.total_quantity::float / NULLIF(SUM(s.total_quantity) OVER(), 0)
                END as allocation_ratio
            FROM sku_sales s
            LEFT JOIN recent_sales r ON s.product_id = r.product_id
            WHERE s.total_quantity > 0
            ORDER BY COALESCE(r.recent_quantity, s.total_quantity) DESC
            """
            
            # 準備查詢參數
            month_minus_3 = self.prediction_month - relativedelta(months=3)
            month_minus_2 = self.prediction_month - relativedelta(months=2)
            month_minus_1 = self.prediction_month - relativedelta(months=1)
            recent_5_months_start = self.prediction_month - relativedelta(months=5)
            
            params = (
                subcategory,  # 子類別
                self.history_start.strftime('%Y-%m-%d'),  # 歷史開始
                self.prediction_month.strftime('%Y-%m-%d'),  # 預測月份
                month_minus_3.strftime('%Y-%m-01'),  # 3個月前
                month_minus_2.strftime('%Y-%m-01'),  # 2個月前
                month_minus_1.strftime('%Y-%m-01'),  # 1個月前
                subcategory,  # 子類別（第二次）
                recent_5_months_start.strftime('%Y-%m-%d'),  # 最近5個月開始
                self.prediction_month.strftime('%Y-%m-%d')  # 預測月份
            )
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"獲取SKU分配因子失敗: {e}")
            if conn:
                conn.close()
            return None
    
    def allocate_to_skus(self, subcategory, subcategory_prediction):
        """分配預測到SKU"""
        # 獲取分配因子
        sku_factors = self.get_sku_allocation_factors(subcategory)
        
        if sku_factors is None or len(sku_factors) == 0:
            return []
        
        results = []
        for _, sku in sku_factors.iterrows():
            # 檢查SKU前2個月是否都是0
            if sku['month_minus_2'] == 0 and sku['month_minus_1'] == 0:
                sku_prediction = 0
            else:
                sku_prediction = subcategory_prediction * sku['allocation_ratio']
            
            results.append({
                'product_id': sku['product_id'],
                'product_name': sku['product_name'],
                'subcategory': subcategory,
                'month_minus_3': sku['month_minus_3'],
                'month_minus_2': sku['month_minus_2'],
                'month_minus_1': sku['month_minus_1'],
                'prediction': sku_prediction,
                'allocation_ratio': sku['allocation_ratio'],
                'historical_avg': sku['avg_quantity']
            })
        
        return results
    
    def get_actual_values(self):
        """獲取預測月份的實際值"""
        conn = self.get_database_connection()
        if conn is None:
            return {}
        
        try:
            query = """
            SELECT 
                pm.subcategory,
                pm.product_id,
                SUM(ot.quantity) as actual_quantity
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE pm.is_active = 'active'
              AND DATE_TRUNC('month', ot.transaction_date) = %s::date
              AND ot.document_type = '銷貨'
              AND ot.quantity > 0
            GROUP BY pm.subcategory, pm.product_id
            """
            
            # 使用預測月份作為參數
            params = (self.prediction_month.strftime('%Y-%m-01'),)
            
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            
            # 建立查找字典
            subcategory_actuals = df.groupby('subcategory')['actual_quantity'].sum().to_dict()
            sku_actuals = df.set_index('product_id')['actual_quantity'].to_dict()
            
            return {'subcategory': subcategory_actuals, 'sku': sku_actuals}
            
        except Exception as e:
            if conn:
                conn.close()
            return {}
    
    def run_prediction(self):
        """執行完整預測"""
        self.logger.info("開始混合CV優化預測...")
        self.logger.info("=" * 50)
        
        # 第一階段：子類別預測
        subcategories = self.get_subcategory_data()
        if subcategories is None or len(subcategories) == 0:
            self.logger.error("沒有找到符合條件的子類別")
            return None, None
        
        subcategory_results = []
        sku_results = []
        
        total = len(subcategories)
        for idx, row in subcategories.iterrows():
            if (idx + 1) % 10 == 0:
                self.logger.info(f"進度: {idx + 1}/{total}")
            
            # 預測子類別
            subcategory_pred = self.predict_subcategory(row)
            
            subcategory_results.append({
                'subcategory': row['subcategory'],
                'cv': row['cv'],
                'volatility_group': row['volatility_group'],
                'month_minus_3': row['month_minus_3'],
                'month_minus_2': row['month_minus_2'],
                'month_minus_1': row['month_minus_1'],
                'prediction': subcategory_pred,
                'historical_avg': row['avg_quantity']
            })
            
            # 第二階段：分配到SKU
            sku_allocations = self.allocate_to_skus(row['subcategory'], subcategory_pred)
            sku_results.extend(sku_allocations)
        
        # 獲取實際值
        self.logger.info(f"獲取{self.prediction_month.strftime('%Y年%m月')}實際值...")
        actuals = self.get_actual_values()
        
        # 添加實際值和計算誤差
        for result in subcategory_results:
            actual = actuals['subcategory'].get(result['subcategory'], 0)
            result['actual'] = actual
            if actual > 0:
                result['mape'] = abs(result['prediction'] - actual) / actual
            else:
                result['mape'] = 0 if result['prediction'] == 0 else 999
        
        for result in sku_results:
            actual = actuals['sku'].get(result['product_id'], 0)
            result['actual'] = actual
            if actual > 0:
                result['mape'] = abs(result['prediction'] - actual) / actual
            else:
                result['mape'] = 0 if result['prediction'] == 0 else 999
        
        # 轉換為DataFrame
        subcategory_df = pd.DataFrame(subcategory_results)
        sku_df = pd.DataFrame(sku_results)
        
        # 分析結果
        self.analyze_results(subcategory_df, sku_df)
        
        # 嘗試保存結果到outputs目錄
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            outputs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'outputs')
            os.makedirs(outputs_dir, exist_ok=True)
            
            subcategory_path = os.path.join(outputs_dir, f'hybrid_subcategory_{timestamp}.csv')
            sku_path = os.path.join(outputs_dir, f'hybrid_sku_{timestamp}.csv')
            
            subcategory_df.to_csv(subcategory_path, index=False, encoding='utf-8-sig')
            sku_df.to_csv(sku_path, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"結果已保存到: {subcategory_path}, {sku_path}")
        except Exception as e:
            self.logger.warning(f"保存CSV文件失敗: {e}")
        
        return subcategory_df, sku_df
    
    def analyze_results(self, subcategory_df, sku_df):
        """分析預測結果"""
        self.logger.info("=" * 70)
        self.logger.info("混合CV優化預測結果分析")
        self.logger.info("=" * 70)
        
        # 子類別分析
        self.logger.info("【子類別預測結果】")
        self.logger.info(f"總子類別數: {len(subcategory_df)}")
        
        valid_sub = subcategory_df[subcategory_df['mape'] < 999]
        if len(valid_sub) > 0:
            self.logger.info(f"平均MAPE: {valid_sub['mape'].mean():.1%}")
            self.logger.info(f"中位數MAPE: {valid_sub['mape'].median():.1%}")
            
            under_20 = len(valid_sub[valid_sub['mape'] < 0.2])
            under_30 = len(valid_sub[valid_sub['mape'] < 0.3])
            self.logger.info(f"<20%誤差: {under_20}/{len(valid_sub)} ({under_20/len(valid_sub)*100:.1f}%)")
            self.logger.info(f"<30%誤差: {under_30}/{len(valid_sub)} ({under_30/len(valid_sub)*100:.1f}%)")
        
        # 按CV組分析
        self.logger.info("【按CV組表現】")
        self.logger.info(f"{'CV組':<15} {'數量':<8} {'平均MAPE':<12} {'<30%誤差'}")
        self.logger.info("-" * 50)
        
        for group in ['低波動', '中波動', '高波動']:
            group_data = subcategory_df[subcategory_df['volatility_group'] == group]
            if len(group_data) > 0:
                valid = group_data[group_data['mape'] < 999]
                if len(valid) > 0:
                    avg_mape = valid['mape'].mean()
                    under_30 = len(valid[valid['mape'] < 0.3])
                    self.logger.info(f"{group:<15} {len(group_data):<8} {avg_mape:<12.1%} "
                          f"{under_30}/{len(valid)} ({under_30/len(valid)*100:.0f}%)")
        
        # SKU分析
        self.logger.info("【SKU預測結果】")
        self.logger.info(f"總SKU數: {len(sku_df)}")
        
        if len(sku_df) > 0 and 'mape' in sku_df.columns:
            valid_sku = sku_df[sku_df['mape'] < 999]
            if len(valid_sku) > 0:
                self.logger.info(f"平均MAPE: {valid_sku['mape'].mean():.1%}")
                self.logger.info(f"中位數MAPE: {valid_sku['mape'].median():.1%}")
                
                under_20 = len(valid_sku[valid_sku['mape'] < 0.2])
                under_30 = len(valid_sku[valid_sku['mape'] < 0.3])
                self.logger.info(f"<20%誤差: {under_20}/{len(valid_sku)} ({under_20/len(valid_sku)*100:.1f}%)")
                self.logger.info(f"<30%誤差: {under_30}/{len(valid_sku)} ({under_30/len(valid_sku)*100:.1f}%)")
        else:
            self.logger.info("SKU預測為空或缺少數據")
        
        # 總結
        self.logger.info("=" * 70)
        total_pred_sub = subcategory_df['prediction'].sum()
        total_actual_sub = subcategory_df['actual'].sum()
        total_error_sub = abs(total_pred_sub - total_actual_sub) / total_actual_sub if total_actual_sub > 0 else 0
        
        self.logger.info(f"子類別總誤差: {total_error_sub:.1%}")
        
        if len(sku_df) > 0 and 'prediction' in sku_df.columns:
            total_pred_sku = sku_df['prediction'].sum()
            total_actual_sku = sku_df['actual'].sum()
            total_error_sku = abs(total_pred_sku - total_actual_sku) / total_actual_sku if total_actual_sku > 0 else 0
            self.logger.info(f"SKU總誤差: {total_error_sku:.1%}")
        
        self.logger.info("=" * 70)


def main():
    """主程序"""
    print("混合CV優化預測系統 (Scheduler版)")
    print("=" * 70)
    
    # 數據庫配置
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': '988',
        'user': 'postgres',
        'password': '1234'
    }
    
    # 創建預測器
    predictor = HybridCVOptimizedSystem(db_config)
    
    # 執行預測
    try:
        subcategory_df, sku_df = predictor.run_prediction()
        
        if subcategory_df is not None:
            print("預測完成！")
            print(f"處理了 {len(subcategory_df)} 個子類別")
            print(f"生成了 {len(sku_df)} 個SKU預測")
        
    except Exception as e:
        print(f"預測過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()