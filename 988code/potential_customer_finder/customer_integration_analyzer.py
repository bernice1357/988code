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
    
    def analyze_all_customer_types(self, product_name: str, all_classified_customers: List[Dict]) -> Dict:
        """
        分析所有客戶類型並整合結果
        
        Args:
            product_name: 產品名稱
            all_classified_customers: 已經分類好的所有客戶（包含purchase_status）
            
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
            
            # 直接從資料庫獲取推薦客戶
            recommended_customers = self._get_recommended_customers_from_db(db_manager, product_id)
            logger.info(f"找到 {len(recommended_customers)} 個推薦客戶")
            
            # 直接使用已經分類好的客戶，不需要重新檢查購買歷史
            integrated_customers = self._integrate_customers(
                all_classified_customers, [], recommended_customers
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
    
    def _get_recommended_customers_from_db(self, db_manager, product_id: str) -> List[Dict]:
        """直接從資料庫獲取推薦客戶"""
        try:
            # 查詢推薦客戶表
            query = """
            SELECT 
                recommended_customer_id_rank1,
                recommended_customer_id_rank2,
                recommended_customer_id_rank3,
                recommended_customer_id_rank4,
                recommended_customer_id_rank5,
                recommended_customer_id_rank6,
                recommended_customer_id_rank7
            FROM product_customer_recommendations 
            WHERE product_id = %s
            """
            
            result = db_manager.execute_query(query, (product_id,), fetch_all=False)
            
            if not result:
                logger.info(f"產品 {product_id} 沒有推薦客戶記錄")
                return []
            
            # 提取所有推薦客戶ID（rank1-7）
            recommended_customer_ids = []
            for i, customer_id in enumerate(result, 1):
                if customer_id:  # 排除空值
                    recommended_customer_ids.append({
                        'customer_id': customer_id,
                        'recommendation_rank': i
                    })
            
            if not recommended_customer_ids:
                logger.info(f"產品 {product_id} 的推薦客戶記錄都為空")
                return []
            
            # 批量查詢客戶名稱
            customer_ids = [item['customer_id'] for item in recommended_customer_ids]
            placeholders = ', '.join(['%s'] * len(customer_ids))
            customer_query = f"""
            SELECT customer_id, customer_name
            FROM customer
            WHERE customer_id IN ({placeholders})
            """
            
            customer_results = db_manager.execute_query(customer_query, tuple(customer_ids))
            customer_name_map = {r[0]: r[1] for r in customer_results}
            
            # 建立完整的推薦客戶資料
            recommended_customers = []
            for item in recommended_customer_ids:
                customer_id = item['customer_id']
                recommended_customers.append({
                    'customer_id': customer_id,
                    'customer_name': customer_name_map.get(customer_id, 'Unknown'),
                    'recommendation_rank': item['recommendation_rank']
                })
            
            logger.info(f"成功獲取 {len(recommended_customers)} 個推薦客戶")
            return recommended_customers
            
        except Exception as e:
            logger.error(f"從資料庫獲取推薦客戶失敗: {e}")
            return []
    
    def _integrate_customers(self, all_customers: List[Dict], 
                           purchased_customers: List[Dict], 
                           recommended_customers: List[Dict]) -> List[Dict]:
        """整合不同來源的客戶資料 - 根據來源分類設定客戶類型"""
        
        integrated = []
        customer_map = {}  # 用於去重的字典：customer_id -> 客戶資料
        
        # 處理所有客戶 - 根據來源分類設定正確的客戶類型
        for customer in all_customers:
            customer_id = customer.get('customer_id')
            customer_name = customer.get('customer_name', 'Unknown')
            source_classification = customer.get('source_classification', 'unknown')
            
            # 根據來源分類確定客戶類型
            if source_classification == 'already_purchased':
                customer_type = "已購買客戶"
            elif source_classification == 'can_process':
                customer_type = "曾詢問客戶"
            elif source_classification == 'cannot_process':
                customer_type = "潛在客戶(無ID)"
            else:
                # 向後兼容：如果沒有source_classification，使用舊邏輯
                if customer_id:
                    customer_type = "曾詢問客戶"  # 預設為曾詢問
                else:
                    customer_type = "潛在客戶(無ID)"
            
            # 使用customer_id作為主鍵，如果沒有則使用customer_name
            unique_key = customer_id if customer_id else f"no_id_{customer_name}"
                
            if unique_key not in customer_map:
                # 第一次遇到這個客戶
                customer_map[unique_key] = {
                    "customer_id": customer_id if customer_id else "",
                    "customer_name": customer_name,
                    "customer_type": customer_type,
                    "conversation_content": customer.get('message_content', ''),
                    "last_activity_date": customer.get('date_str', ''),
                    "inquiry_count": 1,
                    "source": "chat_analysis",
                    "all_conversations": [customer.get('message_content', '')],
                    "has_customer_id": bool(customer_id)
                }
            else:
                # 已經存在的客戶，合併對話內容
                existing = customer_map[unique_key]
                existing["inquiry_count"] += 1
                existing["all_conversations"].append(customer.get('message_content', ''))
                
                # 更新最新活動日期（選擇最新的日期）
                current_date = customer.get('date_str', '')
                if current_date > existing["last_activity_date"]:
                    existing["last_activity_date"] = current_date
                
                # 升級客戶類型（已購買 > 曾詢問 > 潛在客戶(無ID)）
                if customer_type == "已購買客戶" and existing["customer_type"] != "已購買客戶":
                    existing["customer_type"] = "已購買客戶"
                elif customer_type == "曾詢問客戶" and existing["customer_type"] == "潛在客戶(無ID)":
                    existing["customer_type"] = "曾詢問客戶"
        
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
            
        # 由於客戶已經分類好了，不需要重新處理購買客戶
        
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
            if customer_type in ["曾詢問客戶", "潛在客戶(無ID)"]:
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