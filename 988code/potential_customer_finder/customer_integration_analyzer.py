#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客戶整合分析器 - 簡化版本
"""

import logging
from typing import List, Dict, Optional
from database_manager import get_database_manager

logger = logging.getLogger(__name__)

class CustomerIntegrationAnalyzer:
    """客戶整合分析器 - 簡化版本"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_all_customer_types(self, product_name: str, inquiry_customers: List[Dict]) -> Dict:
        """
        分析所有客戶類型並整合結果
        
        Args:
            product_name: 產品名稱
            inquiry_customers: 詢問客戶列表
            
        Returns:
            Dict: 整合分析結果
        """
        try:
            db_manager = get_database_manager()
            
            # 獲取產品ID
            product_id = db_manager.get_product_id_by_name_zh(product_name)
            if not product_id:
                logger.warning(f"未找到產品 '{product_name}' 的 product_id")
                return self._create_empty_result(product_name)
            
            # 獲取已購買客戶
            purchased_customers = self._get_purchased_customers(db_manager, product_id)
            logger.info(f"找到 {len(purchased_customers)} 個曾購買同子類別客戶")
            
            # 獲取推薦客戶 - 檢查方法是否存在
            if hasattr(db_manager, 'get_recommended_customers_by_product_id'):
                recommended_customers = db_manager.get_recommended_customers_by_product_id(product_id)
                logger.info(f"找到 {len(recommended_customers)} 個推薦客戶")
            else:
                logger.warning("DatabaseManager 缺少 get_recommended_customers_by_product_id 方法，跳過推薦客戶分析")
                recommended_customers = []
            
            # 整合所有客戶資料
            integrated_customers = self._integrate_customers(
                inquiry_customers, purchased_customers, recommended_customers
            )
            
            # 生成統計摘要
            summary = self._generate_summary(integrated_customers)
            
            result = {
                "product_name": product_name,
                "product_id": product_id,
                "analysis_timestamp": "2025-08-19 15:37:21",
                "customers": integrated_customers,
                "summary": summary
            }
            
            return result
            
        except Exception as e:
            logger.error(f"客戶整合分析失敗: {e}")
            return self._create_empty_result(product_name)
    
    def _get_purchased_customers(self, db_manager, product_id: str) -> List[Dict]:
        """獲取已購買客戶資訊"""
        try:
            # 這裡可以實現獲取購買客戶的邏輯
            # 暫時返回空列表
            return []
        except Exception as e:
            logger.error(f"獲取購買客戶失敗: {e}")
            return []
    
    def _integrate_customers(self, inquiry_customers: List[Dict], 
                           purchased_customers: List[Dict], 
                           recommended_customers: List[Dict]) -> List[Dict]:
        """整合不同來源的客戶資料"""
        
        integrated = []
        customer_map = {}  # 用於去重的字典：customer_id -> 客戶資料
        
        # 處理詢問客戶（來自聊天記錄）- 需要按客戶ID去重並合併對話
        for customer in inquiry_customers:
            customer_id = customer.get('customer_id')
            if not customer_id:
                continue  # 跳過沒有ID的客戶
                
            if customer_id not in customer_map:
                # 第一次遇到這個客戶
                customer_map[customer_id] = {
                    "customer_id": customer_id,
                    "customer_name": customer.get('customer_name', 'Unknown'),
                    "customer_type": "曾詢問客戶",
                    "conversation_content": customer.get('message_content', ''),
                    "last_activity_date": customer.get('date_str', ''),
                    "inquiry_count": 1,
                    "source": "chat_analysis",
                    "all_conversations": [customer.get('message_content', '')]
                }
            else:
                # 已經存在的客戶，合併對話內容
                existing = customer_map[customer_id]
                existing["inquiry_count"] += 1
                existing["all_conversations"].append(customer.get('message_content', ''))
                
                # 更新最新活動日期（選擇最新的日期）
                current_date = customer.get('date_str', '')
                if current_date > existing["last_activity_date"]:
                    existing["last_activity_date"] = current_date
        
        # 整理對話內容（合併所有對話，去除重複）
        for customer_id, customer_data in customer_map.items():
            conversations = customer_data["all_conversations"]
            # 去除重複對話並限制長度
            unique_conversations = list(dict.fromkeys(conversations))  # 保持順序去重
            combined_content = "\n".join(unique_conversations[:5])  # 最多保留5個對話
            if len(combined_content) > 500:  # 限制總長度
                combined_content = combined_content[:500] + "..."
            customer_data["conversation_content"] = combined_content
            del customer_data["all_conversations"]  # 清理臨時字段
            
        # 不在這裡添加到integrated，等處理完所有客戶類型後再一次性添加
        
        # 處理已購買客戶 - 檢查是否已在詢問客戶中，如果是則更新客戶類型
        for customer in purchased_customers:
            customer_id = customer.get('customer_id')
            if not customer_id:
                continue
                
            if customer_id in customer_map:
                # 這個客戶已經在詢問客戶中，更新為"已購買客戶"（優先級更高）
                existing = customer_map[customer_id]
                existing["customer_type"] = "已購買客戶"
                existing["purchase_count"] = customer.get('total_orders', 0)
                existing["last_purchase_date"] = customer.get('last_purchase_date', '')
                # 保留原有的詢問記錄
            else:
                # 新的已購買客戶
                customer_map[customer_id] = {
                    "customer_id": customer_id,
                    "customer_name": customer.get('customer_name', 'Unknown'),
                    "customer_type": "已購買客戶",
                    "last_activity_date": customer.get('last_purchase_date', ''),
                    "purchase_count": customer.get('total_orders', 0),
                    "source": "purchase_history"
                }
        
        # 處理推薦客戶 - 只添加還未出現過的客戶
        for customer in recommended_customers:
            customer_id = customer.get('customer_id')
            if not customer_id:
                continue
                
            if customer_id not in customer_map:
                # 只有還未出現的客戶才加入為潛在需求客戶
                customer_map[customer_id] = {
                    "customer_id": customer_id,
                    "customer_name": customer.get('customer_name', 'Unknown'),
                    "customer_type": "潛在需求客戶",
                    "recommendation_rank": customer.get('recommendation_rank', 0),
                    "source": "recommendation_system"
                }
        
        # 返回所有去重後的客戶（從customer_map重新構建integrated列表）
        integrated = list(customer_map.values())
        return integrated
    
    def _generate_summary(self, customers: List[Dict]) -> Dict:
        """生成客戶統計摘要"""
        
        summary = {
            "total_customers": len(customers),
            "inquiry_customers": 0,
            "purchased_customers": 0, 
            "potential_customers": 0
        }
        
        for customer in customers:
            customer_type = customer.get('customer_type', '')
            if customer_type == "曾詢問客戶":
                summary["inquiry_customers"] += 1
            elif customer_type == "已購買客戶":
                summary["purchased_customers"] += 1
            elif customer_type == "潛在需求客戶":
                summary["potential_customers"] += 1
        
        return summary
    
    def _create_empty_result(self, product_name: str) -> Dict:
        """創建空的分析結果"""
        return {
            "product_name": product_name,
            "product_id": None,
            "analysis_timestamp": "2025-08-19 15:37:21",
            "customers": [],
            "summary": {
                "total_customers": 0,
                "inquiry_customers": 0,
                "purchased_customers": 0,
                "potential_customers": 0
            }
        }

def get_customer_integration_analyzer() -> CustomerIntegrationAnalyzer:
    """獲取客戶整合分析器實例"""
    return CustomerIntegrationAnalyzer()