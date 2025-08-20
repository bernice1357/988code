#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
組織化搜尋系統 - 將所有搜尋結果統一管理到專門資料夾
"""

import json
import csv
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from chat_analyzer import get_chat_analyzer
from keyword_generator import get_keyword_generator
from database_manager import get_database_manager
from customer_integration_analyzer import get_customer_integration_analyzer

# 設定統一日誌配置
from logging_setup import setup_logging
from progress_tracker import progress_tracker
logger = setup_logging(__name__)

# 主要搜尋結果資料夾 - 使用絕對路徑確保在API環境中正確保存
current_dir = Path(__file__).parent.parent  # 上一層目錄(988code)
SEARCH_RESULTS_DIR = current_dir / "customer_search_results"

def setup_search_results_directory():
    """初始化搜尋結果主資料夾結構"""
    print(f"正在創建搜尋結果目錄: {SEARCH_RESULTS_DIR.absolute()}")
    SEARCH_RESULTS_DIR.mkdir(exist_ok=True)
    
    # 創建子資料夾結構
    (SEARCH_RESULTS_DIR / "by_date").mkdir(exist_ok=True)
    (SEARCH_RESULTS_DIR / "by_product").mkdir(exist_ok=True)
    (SEARCH_RESULTS_DIR / "reports").mkdir(exist_ok=True)
    
    # 創建主說明檔案
    readme_content = """# 客戶搜尋結果管理系統

## 資料夾結構

```
customer_search_results/
├── by_date/           # 按日期分組的搜尋結果
├── by_product/        # 按產品分組的搜尋結果
├── reports/           # 綜合分析報告與搜尋索引
│   └── search_index.json  # 搜尋索引檔案
└── README.md          # 本說明檔案
```

## 使用說明

1. **by_date/**: 每次搜尋都會在此建立時間戳記資料夾
2. **by_product/**: 同一產品的搜尋結果會建立產品專用資料夾
3. **reports/**: 跨產品或跨時間的分析報告，包含搜尋索引檔案
   - **search_index.json**: 所有搜尋的索引和快速查詢

## 檔案格式

- **JSON**: 完整結構化數據，程式可讀
- **CSV**: Excel 可開啟的表格格式
- **TXT**: 人類可讀的統計報告

## 搜尋歷史

所有搜尋記錄都會被保存，可透過索引檔案快速查找特定時間或產品的搜尋結果。
"""
    
    readme_file = SEARCH_RESULTS_DIR / "README.md"
    if not readme_file.exists():
        readme_file.write_text(readme_content, encoding='utf-8')
    
    return SEARCH_RESULTS_DIR

def load_search_index():
    """載入搜尋索引"""
    # 確保 reports 資料夾存在
    reports_dir = SEARCH_RESULTS_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    index_file = reports_dir / "search_index.json"
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"searches": [], "products": {}, "statistics": {"total_searches": 0, "total_matches": 0}}

def save_search_index(index_data):
    """保存搜尋索引"""
    # 確保 reports 資料夾存在
    reports_dir = SEARCH_RESULTS_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    index_file = reports_dir / "search_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2, default=str)

def organized_complete_search(product_name: str):
    """組織化的完整搜尋系統"""
    
    # 開始進度追蹤
    task_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    progress_tracker.start_task(task_id, product_name)
    
    try:
        # 初始化搜尋結果目錄
        setup_search_results_directory()
        progress_tracker.update_step(1, "系統初始化", "搜尋結果目錄初始化完成")
        
        # 創建時間戳記
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 創建按日期和按產品的資料夾
        date_folder = SEARCH_RESULTS_DIR / "by_date" / f"search_{timestamp}"
        
        # 清理產品名稱中的 Windows 不支援字符
        clean_product_name = (product_name
                             .replace('/', '_')
                             .replace('\\', '_') 
                             .replace('*', '_')
                             .replace('?', '_')
                             .replace('"', '_')
                             .replace('<', '_')
                             .replace('>', '_')
                             .replace('|', '_')
                             .replace(':', '_')
                             .replace('(', '_')
                             .replace(')', '_')
                             .replace('[', '_')
                             .replace(']', '_')
                             .replace('±', '_')
                             .replace('%', '_')
                             .replace(' ', '_'))
        
        product_folder = SEARCH_RESULTS_DIR / "by_product" / clean_product_name
        
        date_folder.mkdir(exist_ok=True)
        product_folder.mkdir(exist_ok=True)
        
        print(f"搜尋結果將保存到:")
        print(f"   按日期: {date_folder}")
        print(f"   按產品: {product_folder}")
        print(f"正在進行完整搜尋產品: {product_name}")
        
        # 獲取關鍵詞
        print("生成關鍵詞...")
        progress_tracker.update_step(2, "關鍵詞生成", "正在使用AI生成產品相關關鍵詞...")
        generator = get_keyword_generator()
        keywords = generator.generate_keywords_for_product(product_name)
        print(f"生成了 {len(keywords)} 個關鍵詞")
        progress_tracker.update_step(3, "關鍵詞生成完成", f"成功生成 {len(keywords)} 個搜尋關鍵詞")
    
        # 進行完整搜尋
        print("開始完整搜尋所有檔案...")
        progress_tracker.update_step(4, "檔案搜尋中", "開始掃描所有聊天記錄檔案...")
        analyzer = get_chat_analyzer()
        
        all_results = []
        csv_files = list(analyzer.chat_dir.glob("*.csv"))
        total_files = len(csv_files)
        
        print(f"將搜尋 {total_files} 個檔案...")
        progress_tracker.add_message(f"發現 {total_files} 個聊天記錄檔案待處理")
        
        for i, csv_file in enumerate(csv_files, 1):
            # 更頻繁的進度更新：每50個檔案更新一次前端進度
            if i % 50 == 0 or i == total_files or (total_files - i < 10):
                step_message = f"搜尋進度: {i}/{total_files} ({i*100/total_files:.1f}%)"
                progress_tracker.update_step(4, "檔案搜尋中", step_message)
                print(f"   進度: {i}/{total_files} ({i*100/total_files:.1f}%)")
        
            try:
                chat_records = analyzer._read_chat_file(csv_file)
                
                for record in chat_records:
                    matches = analyzer._search_keywords_in_message(keywords, record['content'])
                    
                    if matches:
                        for match in matches:
                            result = {
                                'product_name': product_name,
                                'customer_name': record['customer_name'],
                                'customer_id': record.get('customer_id'),  # 加入 customer_id
                                'message_content': record['content'],
                                'message_date': record['date'],
                                'date_str': record['date_str'],
                                'sender_name': record['sender_name'],
                                'matched_keyword': match['keyword'],
                                'match_type': match['match_type'],
                                'match_score': match['confidence'],
                                'file_source': record['file_source']
                            }
                            all_results.append(result)
            
            except Exception as e:
                print(f"⚠️ 錯誤處理檔案 {csv_file.name}: {e}")
                continue
        
        print(f"\n搜尋完成！找到 {len(all_results)} 個匹配結果")
        progress_tracker.update_step(5, "資料分析", f"檔案搜尋完成，找到 {len(all_results)} 個匹配結果")
        
        # 新增：購買歷史檢查和客戶分類
        print("檢查客戶購買歷史和分類...")
        progress_tracker.add_message("正在檢查客戶購買歷史和分類...")
        classified_results = classify_customers_by_purchase_status(product_name, all_results)
    
        # 按分數排序
        all_results.sort(key=lambda x: x['match_score'], reverse=True)
        progress_tracker.add_message("客戶分類完成，正在整理分析結果...")
        
        # 準備檔案名稱（使用相同的清理邏輯）
        result_filename = f"{clean_product_name}_{timestamp}"
    
        # 保存到兩個位置的檔案
        progress_tracker.update_step(6, "保存結果", "正在保存分析結果和更新索引...")
        for folder in [date_folder, product_folder]:
            # JSON 檔案
            json_file = folder / f"{result_filename}_{len(all_results)}_matches.json"
            print(f"正在保存JSON檔案: {json_file.absolute()}")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'product_name': product_name,
                    'keywords_used': keywords,
                    'total_results': len(all_results),
                    'files_searched': total_files,
                    'search_timestamp': timestamp,
                    'search_date': date_str,
                    'search_type': 'complete_all_files_organized',
                    'classification_stats': classified_results['stats'],
                    'results': all_results
                }, f, ensure_ascii=False, indent=2, default=str)
            
            # CSV 檔案
            csv_file = folder / f"{result_filename}_{len(all_results)}_matches.csv"
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                if all_results:
                    fieldnames = [
                        '產品名稱', '客戶名稱', '客戶ID', '訊息內容', '訊息日期',
                        '匹配關鍵詞', '匹配類型', '匹配分數', '來源檔案',
                        '有客戶ID', '購買狀態', '可以處理'
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for result in all_results:
                        writer.writerow({
                            '產品名稱': result['product_name'],
                            '客戶名稱': result['customer_name'],
                            '客戶ID': result.get('customer_id', ''),
                            '訊息內容': result['message_content'],
                            '訊息日期': result['date_str'] or '',
                            '匹配關鍵詞': result['matched_keyword'],
                            '匹配類型': result['match_type'],
                            '匹配分數': f"{result['match_score']:.2f}",
                            '來源檔案': result['file_source'],
                            '有客戶ID': '是' if result.get('has_customer_id', False) else '否',
                            '購買狀態': result.get('purchase_status', 'unknown'),
                            '可以處理': '是' if result.get('can_process', False) else '否'
                        })
            
            # 關鍵詞檔案
            keywords_file = folder / f"{result_filename}_keywords.json"
            with open(keywords_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'product_name': product_name,
                    'keywords': keywords,
                    'count': len(keywords),
                    'generated_at': timestamp
                }, f, ensure_ascii=False, indent=2)
        
            # 客戶分類檔案
            classification_file = folder / f"{result_filename}_classification.json"
            with open(classification_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'product_name': product_name,
                    'classification_timestamp': timestamp,
                    'stats': classified_results['stats'],
                    'can_process_customers': [
                        {
                            'customer_name': r['customer_name'],
                            'customer_id': r['customer_id'],
                            'matched_keyword': r['matched_keyword'],
                            'message_content': r['message_content'][:100] + '...' if len(r['message_content']) > 100 else r['message_content'],
                            'file_source': r['file_source']
                        }
                        for r in classified_results['can_process']
                    ],
                    'already_purchased_customers': [
                        {
                            'customer_name': r['customer_name'],
                            'customer_id': r['customer_id'],
                            'matched_keyword': r['matched_keyword'],
                            'file_source': r['file_source']
                        }
                        for r in classified_results['already_purchased']
                    ],
                    'cannot_process_customers': [
                        {
                            'customer_name': r['customer_name'],
                            'matched_keyword': r['matched_keyword'],
                            'reason': '無客戶ID',
                            'file_source': r['file_source']
                        }
                        for r in classified_results['cannot_process']
                    ]
                }, f, ensure_ascii=False, indent=2)
    
        # 生成統計報告（只在按日期資料夾）
        stats_file = date_folder / f"{result_filename}_statistics.txt"
        generate_statistics_report(stats_file, product_name, timestamp, total_files, keywords, all_results, classified_results)
        
        # 更新搜尋索引
        index_data = load_search_index()
        
        search_entry = {
            'timestamp': timestamp,
            'date': date_str,
            'product_name': product_name,
            'keywords_count': len(keywords),
            'files_searched': total_files,
            'results_found': len(all_results),
            'date_folder': str(date_folder.name),
            'product_folder': str(product_folder.name),
            'json_file': f"{result_filename}_{len(all_results)}_matches.json",
            'csv_file': f"{result_filename}_{len(all_results)}_matches.csv"
        }
        
        index_data["searches"].append(search_entry)
        index_data["statistics"]["total_searches"] += 1
        index_data["statistics"]["total_matches"] += len(all_results)
        
        # 更新產品索引
        if product_name not in index_data["products"]:
            index_data["products"][product_name] = []
        index_data["products"][product_name].append(search_entry)
        
        save_search_index(index_data)
        
        # 新增：客戶整合分析 - 只分析可以處理的客戶和已購買的客戶
        print("\n正在進行客戶整合分析...")
        progress_tracker.update_step(7, "客戶整合分析", "正在進行深度客戶整合分析...")
        
        # 合併所有找到的客戶來進行完整的客戶整合分析
        # 包括：可以處理的客戶、已購買的客戶、無法處理的客戶（沒有customer_id但仍是潛在客戶）
        # 為每個客戶添加來源分類標記
        inquiry_customers_for_analysis = []
        
        # 添加可處理客戶（標記為 can_process）
        for customer in classified_results['can_process']:
            customer['source_classification'] = 'can_process'
            inquiry_customers_for_analysis.append(customer)
            
        # 添加已購買客戶（標記為 already_purchased）
        for customer in classified_results['already_purchased']:
            customer['source_classification'] = 'already_purchased'
            inquiry_customers_for_analysis.append(customer)
            
        # 添加無法處理客戶（標記為 cannot_process）
        for customer in classified_results['cannot_process']:
            customer['source_classification'] = 'cannot_process'
            inquiry_customers_for_analysis.append(customer)
        
        if inquiry_customers_for_analysis:
            # 如果有客戶資料，進行完整整合分析
            integration_result = generate_integrated_customer_analysis(
                product_name, inquiry_customers_for_analysis, date_folder, product_folder, result_filename, timestamp
            )
        else:
            # 如果沒有客戶資料，創建空的整合分析檔案
            print("沒有客戶資料需要整合分析，創建空結果檔案...")
            integrated_filename = f"{result_filename}_integrated_customers.json"
            empty_analysis_result = {
                "product_name": product_name,
                "analysis_timestamp": timestamp,
                "summary": {
                    "total_customers": 0,
                    "purchased_customers": 0,
                    "potential_customers": 0,
                    "inquiry_customers": 0
                },
                "customers": []
            }
            
            # 保存空結果到兩個位置
            for folder in [date_folder, product_folder]:
                integrated_file = folder / integrated_filename
                with open(integrated_file, 'w', encoding='utf-8') as f:
                    json.dump(empty_analysis_result, f, ensure_ascii=False, indent=2, default=str)
            
            integration_result = empty_analysis_result
        
        # 如果有舊的未組織檔案，移動到新系統中
        cleanup_old_search_files(timestamp)
        
        print(f"\n" + "=" * 60)
        print(f"搜尋完成！結果已組織化保存")
        print(f"總匹配數: {len(all_results)}")
        print(f"按日期資料夾: {date_folder}")
        print(f"按產品資料夾: {product_folder}")
        print(f"索引已更新: {SEARCH_RESULTS_DIR}/reports/search_index.json")
        print("=" * 60)
        
        # 構建完整的API返回結果
        customer_analysis = []
        for customer in classified_results['can_process']:
            customer_data = {
                'customer_name': customer['customer_name'],
                'customer_id': customer['customer_id'],
                'customer_type': '潛在需求客戶',
                'conversation_summary': customer['message_content'][:200] + '...' if len(customer['message_content']) > 200 else customer['message_content'],
                'last_purchase_date': '',
                'purchase_count': 0
            }
            customer_analysis.append(customer_data)
        
        # 準備最終結果
        final_result = {
            'date_folder': str(date_folder),
            'product_folder': str(product_folder),
            'results_count': len(all_results),
            'customer_analysis': customer_analysis,
            'classification_stats': classified_results['stats'],
            'can_process_customers': classified_results['can_process'],
            'purchased_customers': classified_results['already_purchased'],
            'potential_customers': classified_results.get('potential_customers', []),
            'cannot_process_customers': classified_results['cannot_process'],
            'files': {
                'json': f"{result_filename}_{len(all_results)}_matches.json",
                'csv': f"{result_filename}_{len(all_results)}_matches.csv",
                'keywords': f"{result_filename}_keywords.json",
                'statistics': f"{result_filename}_statistics.txt",
                'integrated_customers': f"{result_filename}_integrated_customers.json"
            }
        }
        
        # 完成任務並設置進度
        progress_tracker.complete_task(len(all_results), final_result)
        
        return final_result
        
    except Exception as e:
        # 錯誤處理
        logger.error(f"潛在客戶分析過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # 標記任務錯誤
        progress_tracker.error_task(str(e))
        
        # 重新拋出異常讓上層處理
        raise

def generate_statistics_report(stats_file, product_name, timestamp, total_files, keywords, all_results, classified_results):
    """生成統計報告"""
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("搜尋統計報告\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"產品名稱: {product_name}\n")
        f.write(f"搜尋時間: {timestamp}\n")
        f.write(f"搜尋檔案數: {total_files}\n")
        f.write(f"使用關鍵詞數: {len(keywords)}\n")
        f.write(f"總匹配數: {len(all_results)}\n\n")
        
        # 客戶分類統計
        stats = classified_results['stats']
        f.write("客戶分類統計:\n")
        f.write("-" * 40 + "\n")
        f.write(f"  總結果數: {stats['total_results']}\n")
        f.write(f"  有客戶ID: {stats['has_customer_id']} 個\n")
        f.write(f"  無客戶ID: {stats['no_customer_id']} 個\n")
        f.write(f"  已購買該產品: {stats['purchased_count']} 個\n")
        f.write(f"  未購買該產品: {stats['not_purchased_count']} 個\n")
        f.write(f"  🎯 可以處理的潛在客戶: {stats['can_process_count']} 個\n")
        f.write(f"  ❌ 不能處理的客戶: {stats['cannot_process_count']} 個\n\n")
        
        # 按關鍵詞分組統計
        keyword_stats = {}
        for result in all_results:
            keyword = result['matched_keyword']
            keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
        
        f.write("關鍵詞匹配分布:\n")
        f.write("-" * 40 + "\n")
        for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  '{keyword}': {count} 次\n")
        
        # 可以處理的客戶統計
        processable_customers = {}
        for result in classified_results['can_process']:
            customer = result['customer_name']
            processable_customers[customer] = processable_customers.get(customer, 0) + 1
        
        f.write("\n🎯 可以處理的潛在客戶 TOP 20:\n")
        f.write("-" * 40 + "\n")
        for customer, count in sorted(processable_customers.items(), key=lambda x: x[1], reverse=True)[:20]:
            f.write(f"  {customer}: {count} 次\n")
        
        # 已購買客戶統計
        purchased_customers = {}
        for result in classified_results['already_purchased']:
            customer = result['customer_name']
            purchased_customers[customer] = purchased_customers.get(customer, 0) + 1
        
        if purchased_customers:
            f.write("\n❌ 已購買該產品的客戶 TOP 10:\n")
            f.write("-" * 40 + "\n")
            for customer, count in sorted(purchased_customers.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {customer}: {count} 次\n")
        
        # 無法處理的客戶統計
        unprocessable_customers = {}
        for result in classified_results['cannot_process']:
            customer = result['customer_name']
            unprocessable_customers[customer] = unprocessable_customers.get(customer, 0) + 1
        
        if unprocessable_customers:
            f.write("\n⚠️ 無法處理的客戶（無客戶ID）TOP 10:\n")
            f.write("-" * 40 + "\n")
            for customer, count in sorted(unprocessable_customers.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {customer}: {count} 次\n")

def cleanup_old_search_files(current_timestamp):
    """清理舊的未組織搜尋檔案，移動到新系統"""
    current_dir = Path(".")
    old_files = list(current_dir.glob("search_results_*.json")) + list(current_dir.glob("full_search_results_*.json"))
    
    if old_files:
        print(f"\n🧹 發現 {len(old_files)} 個未組織的搜尋檔案，正在移動...")
        
        # 創建舊檔案備份資料夾
        archive_folder = SEARCH_RESULTS_DIR / "archived_searches"
        archive_folder.mkdir(exist_ok=True)
        
        for old_file in old_files:
            if current_timestamp not in old_file.name:  # 不移動當前產生的檔案
                try:
                    shutil.move(str(old_file), str(archive_folder / old_file.name))
                    print(f"   ✅ 已移動: {old_file.name}")
                except Exception as e:
                    print(f"   ⚠️ 無法移動 {old_file.name}: {e}")

def show_search_history():
    """顯示搜尋歷史"""
    if not (SEARCH_RESULTS_DIR / "reports" / "search_index.json").exists():
        print("[HISTORY] 尚無搜尋歷史記錄")
        return
    
    index_data = load_search_index()
    searches = index_data["searches"]
    
    if not searches:
        print("[HISTORY] 尚無搜尋歷史記錄")
        return
    
    print(f"\n[HISTORY] 搜尋歷史總覽 (共 {len(searches)} 次搜尋)")
    print("=" * 80)
    
    for i, search in enumerate(reversed(searches[-10:]), 1):  # 顯示最近10次
        print(f"{i}. [{search['date']}] {search['product_name']}")
        print(f"   [RESULTS] {search['results_found']} 個結果 | [FOLDER] {search['date_folder']}")
        print()

def classify_customers_by_purchase_status(product_name: str, results: list):
    """
    根據購買狀態分類客戶
    
    Args:
        product_name: 產品名稱
        results: 搜尋結果列表
        
    Returns:
        dict: 包含分類統計的字典
    """
    # 初始化分類統計
    classification = {
        'can_process': [],      # 可以處理的客戶（有customer_id且未購買）
        'cannot_process': [],   # 不能處理的客戶（無customer_id）
        'already_purchased': [],  # 已購買的客戶
        'not_purchased': [],    # 未購買的客戶
        'stats': {
            'total_results': len(results),
            'has_customer_id': 0,
            'no_customer_id': 0,
            'purchased_count': 0,
            'not_purchased_count': 0,
            'can_process_count': 0,
            'cannot_process_count': 0
        }
    }
    
    # 分離有無customer_id的結果
    results_with_id = []
    results_without_id = []
    customer_ids_map = {}
    
    for result in results:
        customer_id = result.get('customer_id')
        if customer_id:
            results_with_id.append(result)
            if customer_id not in customer_ids_map:
                customer_ids_map[customer_id] = []
            customer_ids_map[customer_id].append(result)
        else:
            # 無customer_id的結果，無法驗證購買歷史
            result['has_customer_id'] = False
            result['purchase_status'] = 'unknown'
            result['can_process'] = False
            results_without_id.append(result)
            classification['cannot_process'].append(result)
    
    # 更新統計
    classification['stats']['has_customer_id'] = len(results_with_id)
    classification['stats']['no_customer_id'] = len(results_without_id)
    classification['stats']['cannot_process_count'] = len(results_without_id)
    
    # 批量檢查購買歷史 - 使用子類別匹配
    if customer_ids_map:
        db_manager = get_database_manager()
        customer_ids = list(customer_ids_map.keys())
        purchased_customer_ids = db_manager.get_customers_who_purchased_by_subcategory(product_name, customer_ids)
        
        # 標記購買狀態並分類
        for result in results_with_id:
            customer_id = result['customer_id']
            result['has_customer_id'] = True
            
            if customer_id in purchased_customer_ids:
                result['purchase_status'] = 'purchased'
                result['can_process'] = False  # 已購買，不需要處理
                classification['already_purchased'].append(result)
            else:
                result['purchase_status'] = 'not_purchased'
                result['can_process'] = True   # 未購買，可以處理
                classification['not_purchased'].append(result)
                classification['can_process'].append(result)
        
        # 更新統計 - 修正：統計實際分類的記錄數而不是唯一客戶數
        classification['stats']['purchased_count'] = len(classification['already_purchased'])
        classification['stats']['not_purchased_count'] = len(classification['not_purchased'])
        classification['stats']['can_process_count'] = len(classification['can_process'])
        
        # 顯示分類統計
        print("客戶分類統計:")
        print(f"  總結果數: {classification['stats']['total_results']}")
        print(f"  有customer_id: {classification['stats']['has_customer_id']} 個")
        print(f"  無customer_id: {classification['stats']['no_customer_id']} 個")
        print(f"  已購買該產品: {classification['stats']['purchased_count']} 個")
        print(f"  未購買該產品: {classification['stats']['not_purchased_count']} 個")
        print(f"  可以處理的潛在客戶: {classification['stats']['can_process_count']} 個")
        print(f"  不能處理的客戶: {classification['stats']['cannot_process_count']} 個")
        
    return classification

def generate_integrated_customer_analysis(product_name: str, all_results: List[Dict], 
                                         date_folder: Path, product_folder: Path, 
                                         result_filename: str, timestamp: str) -> Dict:
    """
    生成客戶整合分析並保存統一格式的JSON檔案
    
    Args:
        product_name: 產品名稱
        all_results: 聊天記錄搜尋結果
        date_folder: 按日期分組的資料夾
        product_folder: 按產品分組的資料夾
        result_filename: 結果檔案名稱前綴
        timestamp: 時間戳記
        
    Returns:
        Dict: 整合分析結果
    """
    try:
        # 獲取客戶整合分析器
        integration_analyzer = get_customer_integration_analyzer()
        
        # 執行整合分析 - 傳入已經分類好的所有客戶
        analysis_result = integration_analyzer.analyze_all_customer_types(product_name, all_results)
        
        # 準備統一格式的JSON檔案名稱
        integrated_filename = f"{result_filename}_integrated_customers.json"
        
        # 保存到兩個位置
        for folder in [date_folder, product_folder]:
            integrated_file = folder / integrated_filename
            
            with open(integrated_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2, default=str)
        
        # 顯示整合分析結果摘要
        summary = analysis_result['summary']
        print("客戶整合分析結果:")
        print(f"  總客戶數: {summary['total_customers']} 個")
        print(f"  曾購買客戶: {summary['purchased_customers']} 個")
        print(f"  潛在需求客戶: {summary['potential_customers']} 個")
        print(f"  曾詢問客戶: {summary['inquiry_customers']} 個")
        
        # 顯示前幾個客戶作為範例
        if analysis_result['customers']:
            print(f"\n客戶範例 (前5個):")
            for i, customer in enumerate(analysis_result['customers'][:5], 1):
                customer_type = customer['customer_type']
                last_date = customer.get('last_activity_date', 'N/A')
                print(f"  {i}. {customer['customer_name']} ({customer_type}) - {last_date}")
        
        print(f"整合分析檔案已保存: {integrated_filename}")
        
        return analysis_result
        
    except Exception as e:
        print(f"客戶整合分析失敗: {e}")
        logger.error(f"客戶整合分析失敗: {e}")
        return {}

if __name__ == "__main__":
    # 顯示搜尋歷史
    show_search_history()
    
    # 接受命令行參數或提示用戶輸入
    import sys
    
    if len(sys.argv) > 1:
        # 使用命令行參數
        product_name = sys.argv[1]
        print(f"使用命令行參數搜尋產品: {product_name}")
    else:
        # 提示用戶輸入
        product_name = input("\n請輸入要搜尋的產品名稱: ").strip()
        
        if not product_name:
            print("未提供產品名稱，使用預設產品進行測試...")
            product_name = "白帶魚切塊3/4(有肚) 10K/箱-津湧"
    
    # 執行組織化搜尋
    result = organized_complete_search(product_name)
    print(f"\n🎉 搜尋完成！結果已組織化保存到專門的管理系統中")