#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的搜尋測試 - 避免使用複雜的整合分析器
"""

import sys
import os
# 添加上層目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from datetime import datetime
from potential_customer_finder.chat_analyzer import get_chat_analyzer
from potential_customer_finder.keyword_generator import get_keyword_generator

def simple_product_search(product_name: str):
    """簡化的產品搜尋測試"""
    print(f"開始測試搜尋產品: {product_name}")
    
    try:
        # 1. 生成關鍵詞
        print("1. 生成關鍵詞...")
        generator = get_keyword_generator()
        keywords = generator.generate_keywords_for_product(product_name)
        print(f"   生成了 {len(keywords)} 個關鍵詞")
        
        # 2. 搜尋聊天記錄
        print("2. 搜尋聊天記錄...")
        analyzer = get_chat_analyzer()
        csv_files = list(analyzer.chat_dir.glob("*.csv"))
        print(f"   將搜尋 {len(csv_files)} 個檔案")
        
        all_results = []
        for i, csv_file in enumerate(csv_files[:10]):  # 只測試前10個檔案
            try:
                chat_records = analyzer._read_chat_file(csv_file)
                for record in chat_records:
                    matches = analyzer._search_keywords_in_message(keywords, record['content'])
                    if matches:
                        for match in matches:
                            result = {
                                'customer_name': record['customer_name'],
                                'content': record['content'],
                                'matched_keyword': match['keyword'],
                                'file_source': record['file_source']
                            }
                            all_results.append(result)
                            
            except Exception as e:
                print(f"   錯誤處理檔案 {csv_file.name}: {e}")
                continue
        
        print(f"3. 搜尋完成，找到 {len(all_results)} 個匹配結果")
        
        # 4. 測試檔案寫入
        print("4. 測試檔案寫入...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 清理產品名稱
        clean_name = product_name.replace('/', '_').replace(' ', '_').replace('(', '_').replace(')', '_')
        
        # 創建測試目錄
        test_dir = Path("test_results")
        test_dir.mkdir(exist_ok=True)
        
        # 寫入測試檔案
        test_file = test_dir / f"{clean_name}_{timestamp}_test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({
                'product_name': product_name,
                'timestamp': timestamp,
                'results_count': len(all_results),
                'results': all_results  # 保存所有結果
            }, f, ensure_ascii=False, indent=2)
        
        print(f"5. 測試檔案已保存: {test_file}")
        print("測試成功完成！")
        
        return True
        
    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 測試簡單的產品搜尋
    test_product = " 台灣薄鹽鯖魚"
    simple_product_search(test_product)