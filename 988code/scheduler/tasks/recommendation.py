import pandas as pd
import numpy as np
import psycopg2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
from scipy import stats
import warnings
import os
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# 載入環境變數
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

class RecommendationSystem:
    def __init__(self, db_config):
        """初始化推薦系統"""
        self.db_config = db_config
        self.conn = None
        self.customer_product_matrix = None
        self.product_similarity_matrix = None
        self.products_df = None
        self.transactions_df = None
        self.customer_price_profiles = None  # 客戶分類別價格檔案
        self.category_price_stats = None     # 各類別價格統計
        
    def connect_db(self):
        """連接到PostgreSQL數據庫"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("數據庫連接成功!")
            return True
        except Exception as e:
            print(f"數據庫連接失敗: {e}")
            return False
    
    def load_data(self):
        """從數據庫載入數據（只包含活躍客戶和活躍產品）"""
        if not self.conn:
            print("請先連接數據庫")
            return False
            
        try:
            # 載入交易數據（只包含活躍客戶的交易記錄）
            transaction_query = """
            SELECT customer_id, product_id, amount, quantity
            FROM order_transactions 
            WHERE customer_id IS NOT NULL 
            AND product_id IS NOT NULL 
            AND amount IS NOT NULL 
            AND quantity IS NOT NULL 
            AND quantity > 0
            AND is_active = 'active'
            """
            self.transactions_df = pd.read_sql(transaction_query, self.conn)
            
            print(f"載入活躍客戶交易數據: {len(self.transactions_df)} 筆記錄")
            
            # 載入產品主數據（只包含活躍產品）
            product_query = """
            SELECT product_id, category, subcategory, specification, process_type
            FROM product_master
            WHERE product_id IS NOT NULL
            AND is_active= 'active'
            """
            self.products_df = pd.read_sql(product_query, self.conn)
            print(f"載入活躍產品數據: {len(self.products_df)} 筆記錄")
            
            # 合併數據，只保留有活躍產品資訊的交易
            initial_transaction_count = len(self.transactions_df)
            self.transactions_df = self.transactions_df.merge(
                self.products_df, on='product_id', how='inner'
            )
            final_transaction_count = len(self.transactions_df)
            
            print(f"合併後有效交易數據: {final_transaction_count} 筆記錄")
            if initial_transaction_count > final_transaction_count:
                filtered_count = initial_transaction_count - final_transaction_count
                print(f"已過濾掉 {filtered_count} 筆非活躍產品的交易記錄")
            
            # 計算單價
            self.transactions_df['unit_price'] = self.transactions_df['amount'] / self.transactions_df['quantity']
            
            # 移除異常價格（可能是錯誤數據）
            price_q95 = self.transactions_df['unit_price'].quantile(0.95)
            price_q05 = self.transactions_df['unit_price'].quantile(0.05)
            self.transactions_df = self.transactions_df[
                (self.transactions_df['unit_price'] >= price_q05) & 
                (self.transactions_df['unit_price'] <= price_q95)
            ]
            
            print(f"清理異常價格後最終數據: {len(self.transactions_df)} 筆記錄")
            
            # 顯示活躍數據統計
            unique_customers = self.transactions_df['customer_id'].nunique()
            unique_products = self.transactions_df['product_id'].nunique()
            print(f"活躍客戶數量: {unique_customers}")
            print(f"活躍產品數量: {unique_products}")
            
            return True
            
        except Exception as e:
            print(f"數據載入失敗: {e}")
            return False
    
    def calculate_customer_price_profiles(self):
        """計算客戶在各類別的價格檔案（僅基於活躍產品）"""
        print("計算活躍客戶價格檔案...")
        
        # 計算每個客戶在每個類別的平均單價
        customer_category_prices = self.transactions_df.groupby(
            ['customer_id', 'category']
        )['unit_price'].agg(['mean', 'std', 'count']).reset_index()
        
        # 只保留有足夠購買記錄的數據（至少2次購買）
        customer_category_prices = customer_category_prices[
            customer_category_prices['count'] >= 2
        ]
        
        # 計算各類別的整體價格統計
        self.category_price_stats = self.transactions_df.groupby('category')['unit_price'].agg([
            'mean', 'std', 'min', 'max', 'count'
        ]).reset_index()
        
        print("活躍產品類別價格統計:")
        print(self.category_price_stats.to_string(index=False))
        
        # 建立客戶價格檔案
        self.customer_price_profiles = {}
        
        for _, row in customer_category_prices.iterrows():
            customer_id = row['customer_id']
            category = row['category']
            
            if customer_id not in self.customer_price_profiles:
                self.customer_price_profiles[customer_id] = {}
            
            # 計算客戶在該類別的價格水平（標準化分數）
            category_stats = self.category_price_stats[
                self.category_price_stats['category'] == category
            ].iloc[0]
            
            # 使用Z-score標準化
            z_score = (row['mean'] - category_stats['mean']) / category_stats['std']
            
            self.customer_price_profiles[customer_id][category] = {
                'avg_price': row['mean'],
                'price_std': row['std'],
                'purchase_count': row['count'],
                'z_score': z_score,
                'price_level': self._classify_price_level(z_score)
            }
        
        print(f"建立了 {len(self.customer_price_profiles)} 個活躍客戶的價格檔案")
        return True
    
    def _classify_price_level(self, z_score):
        """根據Z-score分類價格水平"""
        if z_score > 1:
            return 'high'
        elif z_score > -1:
            return 'medium'
        else:
            return 'low'
    
    def calculate_price_similarity(self, customer_id, product_id):
        """計算客戶與產品的價格相似度（僅限活躍產品）"""
        # 獲取產品信息（已確保是活躍產品）
        product_info = self.products_df[self.products_df['product_id'] == product_id]
        if product_info.empty:
            return 0.5  # 默認中等相似度
        
        product_category = product_info.iloc[0]['category']
        
        # 獲取產品的平均價格
        product_prices = self.transactions_df[
            self.transactions_df['product_id'] == product_id
        ]['unit_price']
        
        if product_prices.empty:
            return 0.5  # 新產品，默認中等相似度
        
        product_avg_price = product_prices.mean()
        
        # 獲取客戶在該類別的價格檔案
        if (customer_id not in self.customer_price_profiles or 
            product_category not in self.customer_price_profiles[customer_id]):
            return 0.5  # 客戶沒有該類別的購買歷史
        
        customer_profile = self.customer_price_profiles[customer_id][product_category]
        customer_avg_price = customer_profile['avg_price']
        
        # 獲取類別價格統計
        category_stats = self.category_price_stats[
            self.category_price_stats['category'] == product_category
        ].iloc[0]
        
        # 計算價格相似度（使用高斯分佈）
        # 以客戶平均價格為中心，類別標準差為參考
        price_diff = abs(product_avg_price - customer_avg_price)
        category_std = category_stats['std']
        
        # 使用高斯函數計算相似度
        if category_std > 0:
            similarity = np.exp(-0.5 * (price_diff / category_std) ** 2)
        else:
            similarity = 1.0 if price_diff == 0 else 0.5
        
        return similarity
    
    def calculate_product_similarity(self):
        """計算產品間的相似度（僅限活躍產品）"""
        print("開始計算活躍產品相似度...")
        
        # 處理缺失值
        self.products_df = self.products_df.fillna('unknown')
        
        # 為類別特徵編碼
        le_category = LabelEncoder()
        le_subcategory = LabelEncoder()
        le_specification = LabelEncoder()
        le_process = LabelEncoder()
        
        # 編碼各個特徵
        category_encoded = le_category.fit_transform(self.products_df['category'].astype(str))
        subcategory_encoded = le_subcategory.fit_transform(self.products_df['subcategory'].astype(str))
        specification_encoded = le_specification.fit_transform(self.products_df['specification'].astype(str))
        process_encoded = le_process.fit_transform(self.products_df['process_type'].astype(str))
        
        # 計算各個特徵的相似度矩陣
        n_products = len(self.products_df)
        
        # 類別相似度
        category_similarity = np.zeros((n_products, n_products))
        for i in range(n_products):
            for j in range(n_products):
                category_similarity[i][j] = 1 if category_encoded[i] == category_encoded[j] else 0
        
        # 子類別相似度
        subcategory_similarity = np.zeros((n_products, n_products))
        for i in range(n_products):
            for j in range(n_products):
                subcategory_similarity[i][j] = 1 if subcategory_encoded[i] == subcategory_encoded[j] else 0
        
        # 規格相似度
        specification_similarity = np.zeros((n_products, n_products))
        for i in range(n_products):
            for j in range(n_products):
                specification_similarity[i][j] = 1 if specification_encoded[i] == specification_encoded[j] else 0
        
        # 處理方式相似度
        process_similarity = np.zeros((n_products, n_products))
        for i in range(n_products):
            for j in range(n_products):
                process_similarity[i][j] = 1 if process_encoded[i] == process_encoded[j] else 0
        
        # 價格相似度矩陣
        print("計算活躍產品價格相似度矩陣...")
        price_similarity = np.zeros((n_products, n_products))
        
        # 獲取每個產品的平均價格
        product_avg_prices = {}
        for product_id in self.products_df['product_id']:
            product_prices = self.transactions_df[
                self.transactions_df['product_id'] == product_id
            ]['unit_price']
            if not product_prices.empty:
                product_avg_prices[product_id] = product_prices.mean()
        
        # 計算產品間價格相似度
        for i in range(n_products):
            for j in range(n_products):
                product_i = self.products_df.iloc[i]['product_id']
                product_j = self.products_df.iloc[j]['product_id']
                category_i = self.products_df.iloc[i]['category']
                category_j = self.products_df.iloc[j]['category']
                
                if category_i != category_j:
                    price_similarity[i][j] = 0  # 不同類別的產品價格不比較
                elif product_i in product_avg_prices and product_j in product_avg_prices:
                    # 在同類別內比較價格
                    price_i = product_avg_prices[product_i]
                    price_j = product_avg_prices[product_j]
                    
                    # 獲取類別標準差
                    category_stats = self.category_price_stats[
                        self.category_price_stats['category'] == category_i
                    ]
                    
                    if not category_stats.empty and category_stats.iloc[0]['std'] > 0:
                        price_diff = abs(price_i - price_j)
                        category_std = category_stats.iloc[0]['std']
                        # 使用高斯函數
                        price_similarity[i][j] = np.exp(-0.5 * (price_diff / category_std) ** 2)
                    else:
                        price_similarity[i][j] = 1.0 if price_i == price_j else 0.5
                else:
                    price_similarity[i][j] = 0.5  # 默認值
        
        # 綜合相似度（5個因子的平均）
        self.product_similarity_matrix = (
            category_similarity + 
            subcategory_similarity + 
            specification_similarity + 
            process_similarity +
            price_similarity
        ) / 5.0
        
        print("活躍產品相似度計算完成! (包含5個因子: category, subcategory, specification, process, price)")
        
        # 顯示相似度統計
        print(f"相似度矩陣統計:")
        print(f"- 平均相似度: {self.product_similarity_matrix.mean():.4f}")
        print(f"- 相似度標準差: {self.product_similarity_matrix.std():.4f}")
        print(f"- 最高相似度: {self.product_similarity_matrix.max():.4f}")
        print(f"- 最低相似度: {self.product_similarity_matrix.min():.4f}")
        
        return True
    
    def create_user_item_matrix(self):
        """創建用戶-物品矩陣（僅包含活躍客戶和活躍產品）"""
        print("創建活躍用戶-物品矩陣...")
        
        # 創建用戶-物品矩陣（客戶是否購買過該產品）
        user_item = self.transactions_df.groupby(['customer_id', 'product_id']).size().reset_index(name='purchase_count')
        
        # 轉換為矩陣形式
        self.customer_product_matrix = user_item.pivot(
            index='customer_id', 
            columns='product_id', 
            values='purchase_count'
        ).fillna(0)
        
        # 將購買次數轉為二進制（購買過為1，沒購買過為0）
        self.customer_product_matrix = (self.customer_product_matrix > 0).astype(int)
        
        print(f"活躍用戶-物品矩陣大小: {self.customer_product_matrix.shape}")
        print(f"包含 {self.customer_product_matrix.shape[0]} 個活躍客戶")
        print(f"包含 {self.customer_product_matrix.shape[1]} 個活躍產品")
        return True
    
    def recommend_products_for_customers(self, top_n=7):
        """為每個活躍客戶推薦活躍產品（包含價格匹配），每個subcategory最多推薦1個產品"""
        print("為活躍客戶推薦活躍產品...")
        
        recommendations = []
        
        # 建立產品ID到索引的映射
        product_ids = list(self.products_df['product_id'])
        product_id_to_idx = {pid: idx for idx, pid in enumerate(product_ids)}
        
        for customer_id in self.customer_product_matrix.index:
            # 獲取客戶已購買的產品
            purchased_products = self.customer_product_matrix.loc[customer_id]
            purchased_product_ids = purchased_products[purchased_products > 0].index.tolist()
            
            # 獲取客戶已購買產品的subcategory
            purchased_subcategories = set()
            for pid in purchased_product_ids:
                product_info = self.products_df[self.products_df['product_id'] == pid]
                if not product_info.empty:
                    subcategory = product_info.iloc[0]['subcategory']
                    if pd.notna(subcategory) and subcategory != 'unknown':
                        purchased_subcategories.add(subcategory)
            
            # 按subcategory分組計算推薦分數
            subcategory_recommendations = {}
            
            for product_id in product_ids:
                if product_id in purchased_product_ids:
                    continue  # 跳過已購買的產品
                
                # 檢查產品的subcategory是否已購買過
                product_info = self.products_df[self.products_df['product_id'] == product_id]
                if not product_info.empty:
                    product_subcategory = product_info.iloc[0]['subcategory']
                    if (pd.notna(product_subcategory) and 
                        product_subcategory != 'unknown' and 
                        product_subcategory in purchased_subcategories):
                        continue  # 跳過相同subcategory的產品
                    
                    # 初始化subcategory分組
                    if product_subcategory not in subcategory_recommendations:
                        subcategory_recommendations[product_subcategory] = []
                    
                if product_id not in product_id_to_idx:
                    continue
                    
                product_idx = product_id_to_idx[product_id]
                score = 0
                count = 0
                
                # 基於已購買產品的相似度計算推薦分數
                for purchased_id in purchased_product_ids:
                    if purchased_id in product_id_to_idx:
                        purchased_idx = product_id_to_idx[purchased_id]
                        similarity = self.product_similarity_matrix[product_idx][purchased_idx]
                        score += similarity
                        count += 1
                
                # 加入價格匹配度
                price_match = self.calculate_price_similarity(customer_id, product_id)
                
                if count > 0:
                    # 綜合分數：相似度 * 價格匹配度
                    final_score = (score / count) * price_match
                    
                    # 計算詳細分數組成
                    base_similarity = score / count
                    
                    # 加入到對應的subcategory分組
                    if product_info.iloc[0]['subcategory'] in subcategory_recommendations:
                        subcategory_recommendations[product_info.iloc[0]['subcategory']].append({
                            'product_id': product_id,
                            'final_score': final_score,
                            'base_similarity': base_similarity,
                            'price_match': price_match
                        })
            
            # 每個subcategory選出最佳的1個產品
            subcategory_best = []
            for subcategory, products in subcategory_recommendations.items():
                if products:
                    # 選出該subcategory中分數最高的產品
                    best_product = max(products, key=lambda x: x['final_score'])
                    best_product['subcategory'] = subcategory
                    subcategory_best.append(best_product)
            
            # 從各subcategory的最佳產品中選出top_n個
            if subcategory_best:
                top_products = sorted(subcategory_best, 
                                    key=lambda x: x['final_score'], reverse=True)[:top_n]
                
                for rank, product_data in enumerate(top_products, 1):
                    recommendations.append({
                        'customer_id': customer_id,
                        'recommended_product_id': product_data['product_id'],
                        'rank': rank,
                        'similarity_score': round(product_data['base_similarity'], 4),
                        'price_match_score': round(product_data['price_match'], 4),
                        'final_score': round(product_data['final_score'], 4),
                        'subcategory': product_data['subcategory']
                    })
        
        customer_recommendations_df = pd.DataFrame(recommendations)
        print(f"為 {len(self.customer_product_matrix)} 個活躍客戶生成推薦 (每個subcategory最多1個活躍產品)")
        return customer_recommendations_df
    
    def recommend_customers_for_products(self, top_n=7):
        """為每個活躍產品推薦活躍客戶（包含價格匹配），避免推薦給已購買相同subcategory的客戶"""
        print("為活躍產品推薦活躍客戶...")
        
        recommendations = []
        
        for product_id in self.customer_product_matrix.columns:
            # 獲取已購買該產品的客戶
            product_customers = self.customer_product_matrix[product_id]
            purchased_customers = product_customers[product_customers > 0].index.tolist()
            
            # 獲取當前產品的subcategory
            current_product_info = self.products_df[self.products_df['product_id'] == product_id]
            if current_product_info.empty:
                continue
                
            current_subcategory = current_product_info.iloc[0]['subcategory']
            
            # 計算推薦分數
            recommendation_scores = {}
            
            for customer_id in self.customer_product_matrix.index:
                if customer_id in purchased_customers:
                    continue  # 跳過已購買的客戶
                
                # 獲取客戶的購買歷史
                customer_products = self.customer_product_matrix.loc[customer_id]
                customer_purchased = customer_products[customer_products > 0].index.tolist()
                
                if not customer_purchased:
                    continue  # 跳過沒有購買歷史的客戶
                
                # 檢查客戶是否已購買過相同subcategory的產品
                has_same_subcategory = False
                if pd.notna(current_subcategory) and current_subcategory != 'unknown':
                    for purchased_id in customer_purchased:
                        purchased_product_info = self.products_df[self.products_df['product_id'] == purchased_id]
                        if not purchased_product_info.empty:
                            purchased_subcategory = purchased_product_info.iloc[0]['subcategory']
                            if (pd.notna(purchased_subcategory) and 
                                purchased_subcategory == current_subcategory):
                                has_same_subcategory = True
                                break
                
                if has_same_subcategory:
                    continue  # 跳過已購買相同subcategory產品的客戶
                
                # 基於產品相似度計算推薦分數
                if product_id in self.products_df['product_id'].values:
                    product_idx = list(self.products_df['product_id']).index(product_id)
                    score = 0
                    count = 0
                    
                    for purchased_id in customer_purchased:
                        if purchased_id in list(self.products_df['product_id']):
                            purchased_idx = list(self.products_df['product_id']).index(purchased_id)
                            similarity = self.product_similarity_matrix[product_idx][purchased_idx]
                            score += similarity
                            count += 1
                    
                    # 加入價格匹配度
                    price_match = self.calculate_price_similarity(customer_id, product_id)
                    
                    if count > 0:
                        # 綜合分數：相似度 * 價格匹配度
                        final_score = (score / count) * price_match
                        recommendation_scores[customer_id] = final_score
            
            # 選擇top_n個推薦客戶
            if recommendation_scores:
                top_customers = sorted(recommendation_scores.items(), 
                                     key=lambda x: x[1], reverse=True)[:top_n]
                
                for rank, (customer_id, score) in enumerate(top_customers, 1):
                    # 計算詳細分數
                    customer_products = self.customer_product_matrix.loc[customer_id]
                    customer_purchased = customer_products[customer_products > 0].index.tolist()
                    
                    base_similarity = 0
                    count = 0
                    product_idx = list(self.products_df['product_id']).index(product_id)
                    
                    for purchased_id in customer_purchased:
                        if purchased_id in list(self.products_df['product_id']):
                            purchased_idx = list(self.products_df['product_id']).index(purchased_id)
                            base_similarity += self.product_similarity_matrix[product_idx][purchased_idx]
                            count += 1
                    
                    base_similarity = base_similarity / count if count > 0 else 0
                    price_match = self.calculate_price_similarity(customer_id, product_id)
                    
                    recommendations.append({
                        'product_id': product_id,
                        'recommended_customer_id': customer_id,
                        'rank': rank,
                        'similarity_score': round(base_similarity, 4),
                        'price_match_score': round(price_match, 4),
                        'final_score': round(score, 4)
                    })
        
        product_recommendations_df = pd.DataFrame(recommendations)
        print(f"為 {len(self.customer_product_matrix.columns)} 個活躍產品生成推薦")
        return product_recommendations_df
    
    def save_recommendations_to_csv(self, customer_recs, product_recs):
        """保存推薦結果到CSV文件"""
        print("保存推薦結果...")
        
        # 為客戶推薦添加產品詳細信息
        # 先移除可能衝突的subcategory列
        customer_recs_clean = customer_recs.drop('subcategory', axis=1, errors='ignore')
        
        customer_recs_detailed = customer_recs_clean.merge(
            self.products_df[['product_id', 'category', 'subcategory', 'specification', 'process_type']], 
            left_on='recommended_product_id', 
            right_on='product_id', 
            how='left'
        ).drop('product_id', axis=1)
        
        # 添加產品價格信息
        product_avg_prices = self.transactions_df.groupby('product_id')['unit_price'].mean().reset_index()
        product_avg_prices.columns = ['recommended_product_id', 'avg_unit_price']
        customer_recs_detailed = customer_recs_detailed.merge(
            product_avg_prices, on='recommended_product_id', how='left'
        )
        
        # 保存客戶推薦
        customer_recs_detailed.to_csv('active_customer_product_recommendations.csv', index=False, encoding='utf-8-sig')
        print("活躍客戶產品推薦已保存到: active_customer_product_recommendations.csv")
        
        # 為產品推薦添加產品詳細信息
        product_recs_detailed = product_recs.merge(
            self.products_df[['product_id', 'category', 'subcategory', 'specification', 'process_type']], 
            on='product_id', 
            how='left'
        )
        
        # 添加產品價格信息
        product_avg_prices_2 = self.transactions_df.groupby('product_id')['unit_price'].mean().reset_index()
        product_avg_prices_2.columns = ['product_id', 'avg_unit_price']
        product_recs_detailed = product_recs_detailed.merge(
            product_avg_prices_2, on='product_id', how='left'
        )
        
        # 保存產品推薦
        product_recs_detailed.to_csv('active_product_customer_recommendations.csv', index=False, encoding='utf-8-sig')
        print("活躍產品客戶推薦已保存到: active_product_customer_recommendations.csv")
        
        # 保存客戶價格檔案
        if self.customer_price_profiles:
            price_profiles_data = []
            for customer_id, categories in self.customer_price_profiles.items():
                for category, profile in categories.items():
                    price_profiles_data.append({
                        'customer_id': customer_id,
                        'category': category,
                        'avg_price': round(profile['avg_price'], 2),
                        'price_std': round(profile['price_std'], 2),
                        'purchase_count': profile['purchase_count'],
                        'z_score': round(profile['z_score'], 4),
                        'price_level': profile['price_level']
                    })
            
            price_profiles_df = pd.DataFrame(price_profiles_data)
            price_profiles_df.to_csv('active_customer_price_profiles.csv', index=False, encoding='utf-8-sig')
            print("活躍客戶價格檔案已保存到: active_customer_price_profiles.csv")
        
        # 顯示統計信息
        print(f"\n=== 活躍用戶推薦結果統計 ===")
        print(f"客戶推薦記錄數: {len(customer_recs)}")
        print(f"產品推薦記錄數: {len(product_recs)}")
        print(f"涵蓋活躍客戶數: {customer_recs['customer_id'].nunique()}")
        print(f"涵蓋活躍產品數: {product_recs['product_id'].nunique()}")
        print(f"活躍客戶價格檔案數: {len(self.customer_price_profiles)}")
        
        # 顯示價格分析統計
        if len(customer_recs) > 0:
            print(f"\n=== 價格匹配分析 ===")
            print(f"平均價格匹配分數: {customer_recs['price_match_score'].mean():.4f}")
            print(f"價格匹配分數標準差: {customer_recs['price_match_score'].std():.4f}")
        
        # 顯示過濾邏輯說明
        print(f"\n=== 活躍推薦邏輯說明 ===")
        print("✓ 僅使用 order_transactions 中 is_active = 'active' 的歷史數據")
        print("✓ 僅推薦 product_master 中 is_active = 'active' 的產品")
        print("✓ 5個相似度因子: category、subcategory、specification、process_type、price")
        print("✓ 分類別高斯分佈價格建模")
        print("✓ 不推薦客戶已購買過的相同subcategory產品")
        print("✓ 不推薦給已購買過相同subcategory產品的客戶")
        print("✓ 每個subcategory最多推薦1個產品（避免重複推薦同類產品）")
        print("✓ 綜合分數 = 產品相似度 × 價格匹配度")
        
        # 顯示前幾筆推薦範例
        if len(customer_recs_detailed) > 0:
            print(f"\n=== 活躍客戶推薦範例 ===")
            display_cols = ['customer_id', 'recommended_product_id', 'rank', 'similarity_score', 
                          'price_match_score', 'final_score', 'category', 'subcategory', 'avg_unit_price']
            available_cols = [col for col in display_cols if col in customer_recs_detailed.columns]
            print(customer_recs_detailed[available_cols].head(3).to_string(index=False))
            
        if len(product_recs_detailed) > 0:
            print(f"\n=== 活躍產品推薦範例 ===")
            display_cols = ['product_id', 'recommended_customer_id', 'rank', 'similarity_score', 
                          'price_match_score', 'final_score', 'category', 'subcategory', 'avg_unit_price']
            available_cols = [col for col in display_cols if col in product_recs_detailed.columns]
            print(product_recs_detailed[available_cols].head(3).to_string(index=False))
        
    def close_connection(self):
        """關閉數據庫連接"""
        if self.conn:
            self.conn.close()
            print("數據庫連接已關閉")

def generate_recommendations(db_config=None):
    """生成推薦結果，返回DataFrame"""
    # 使用傳入的數據庫配置或從環境變數讀取
    if db_config is None:
        db_env = os.getenv('DB_ENVIRONMENT', 'local')
        db_config = {
            'host': os.getenv(f'{db_env.upper()}_DB_HOST', 'localhost'),
            'port': int(os.getenv(f'{db_env.upper()}_DB_PORT', 5432)),
            'database': os.getenv(f'{db_env.upper()}_DB_NAME', '988'),
            'user': os.getenv(f'{db_env.upper()}_DB_USER', 'postgres'),
            'password': os.getenv(f'{db_env.upper()}_DB_PASSWORD', '988988')
        }

    # 創建推薦系統實例
    recommender = RecommendationSystem(db_config)
    
    try:
        # 1. 連接數據庫
        if not recommender.connect_db():
            return
        
        # 2. 載入數據（僅活躍客戶和活躍產品）
        if not recommender.load_data():
            return
        
        # 3. 計算客戶價格檔案
        if not recommender.calculate_customer_price_profiles():
            return
        
        # 4. 計算產品相似度（包含價格）
        if not recommender.calculate_product_similarity():
            return
        
        # 5. 創建用戶-物品矩陣
        if not recommender.create_user_item_matrix():
            return
        
        # 6. 生成推薦 (Top 7)
        print("\n=== 開始生成活躍推薦 (Top 7) ===")
        customer_recommendations = recommender.recommend_products_for_customers(top_n=7)
        product_recommendations = recommender.recommend_customers_for_products(top_n=7)
        
        print(f"\n=== 活躍推薦系統運行完成! ===")
        print(f"客戶推薦記錄數: {len(customer_recommendations)}")
        print(f"產品推薦記錄數: {len(product_recommendations)}")
        
        return customer_recommendations, product_recommendations
        
    except Exception as e:
        print(f"程序運行出錯: {e}")
        import traceback
        traceback.print_exc()
        return None, None
        
    finally:
        # 8. 關閉數據庫連接
        try:
            recommender.close_connection()
        except:
            pass

def main():
    """主函數 - 用於獨立執行時的測試"""
    customer_recs, product_recs = generate_recommendations()
    if customer_recs is not None and product_recs is not None:
        print("\n推薦系統測試成功!")
        print(f"生成了 {len(customer_recs)} 個客戶推薦和 {len(product_recs)} 個產品推薦")
    else:
        print("\n推薦系統測試失敗!")

if __name__ == "__main__":
    main()