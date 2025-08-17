import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sqlalchemy import create_engine
import urllib.parse

class SalesAnalyzer:
    def __init__(self, db_config):
        """
        初始化資料庫連接
        db_config = {
            'host': 'localhost',
            'database': 'your_db',
            'user': 'username',
            'password': 'password',
            'port': '5432'
        }
        """
        self.db_config = db_config
        self.engine = self._create_engine()
        
    def _create_engine(self):
        """建立SQLAlchemy引擎"""
        try:
            # URL編碼密碼以處理特殊字符
            password = urllib.parse.quote_plus(self.db_config['password'])
            
            # 建立連接字串
            connection_string = (
                f"postgresql://{self.db_config['user']}:{password}@"
                f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )
            
            engine = create_engine(connection_string)
            return engine
        except Exception as e:
            print(f"資料庫引擎建立失敗: {e}")
            return None
    
    def print_data_summary(self, df, filter_level, filter_values, start_date, end_date):
        """
        打印查詢資料的摘要資訊
        
        Parameters:
        df (DataFrame): 查詢結果資料
        filter_level (str): 篩選層級
        filter_values (list): 篩選值
        start_date (str): 開始日期
        end_date (str): 結束日期
        """
        level_names = {
            'category': '產品類別',
            'subcategory': '產品子類別', 
            'name_zh': '產品品項'
        }
        
        print(f"\n查詢條件:")
        print(f"   篩選層級: {level_names.get(filter_level, filter_level)}")
        print(f"   篩選項目: {', '.join(filter_values)}")
        print(f"   時間範圍: {start_date} 至 {end_date}")
        print(f"   狀態條件: 僅包含 is_active='active' 的資料")
        print(f"   找到資料筆數: {len(df)} 筆")
        
        # 計算各項目的總銷售額
        total_summary = df.groupby('filter_value')['total_amount'].sum().sort_values(ascending=False)
        
        print(f"\n各項目總銷售額:")
        for item, amount in total_summary.items():
            print(f"   {item}: NT$ {amount:,.0f}")
        
        print(f"\n月度銷售明細:")
        # 按月份和項目顯示明細
        for month in sorted(df['sales_month'].unique()):
            month_str = month.strftime('%Y-%m')
            month_data = df[df['sales_month'] == month]
            print(f"   {month_str}:")
            
            for _, row in month_data.iterrows():
                print(f"     {row['filter_value']}: NT$ {row['total_amount']:,.0f}")
        
        print(f"\n總計: NT$ {df['total_amount'].sum():,.0f}")
        print("-" * 50)
    
    def get_sales_data(self, filter_level, filter_values, start_date, end_date):
        """
        根據產品階層和日期範圍查詢銷售資料
        
        Parameters:
        filter_level (str): 篩選層級 'category', 'subcategory', 或 'name_zh'
        filter_values (list): 篩選值清單，如 ["白帶魚", "蝦類/蟹"] 或 ["白帶魚切塊", "白帶魚片"]
        start_date (str): 開始日期 'YYYY-MM-DD'
        end_date (str): 結束日期 'YYYY-MM-DD'
        
        Returns:
        pandas.DataFrame: 包含日期、篩選層級、銷售金額的資料
        """
        
        if self.engine is None:
            print("資料庫引擎未建立")
            return None
        
        # 將篩選值轉換為SQL IN子句格式
        filter_values_str = "'" + "','".join(filter_values) + "'"
        
        # 根據篩選層級建立不同的SQL查詢
        if filter_level == 'category':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                pm.category as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{start_date}'
                AND ot.transaction_date <= '{end_date}'
                AND ot.is_active = 'active'
                AND pm.category IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), pm.category
            ORDER BY sales_month, pm.category
            """
        elif filter_level == 'subcategory':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                pm.subcategory as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{start_date}'
                AND ot.transaction_date <= '{end_date}'
                AND ot.is_active = 'active'
                AND pm.subcategory IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), pm.subcategory
            ORDER BY sales_month, pm.subcategory
            """
        elif filter_level == 'name_zh':
            sql = f"""
            SELECT 
                DATE_TRUNC('month', ot.transaction_date) as sales_month,
                pm.name_zh as filter_value,
                SUM(ot.amount) as total_amount
            FROM order_transactions ot
            JOIN product_master pm ON ot.product_id = pm.product_id
            WHERE ot.document_type = '銷貨'
                AND ot.transaction_date >= '{start_date}'
                AND ot.transaction_date <= '{end_date}'
                AND ot.is_active = 'active'
                AND pm.name_zh IN ({filter_values_str})
            GROUP BY DATE_TRUNC('month', ot.transaction_date), pm.name_zh
            ORDER BY sales_month, pm.name_zh
            """
        else:
            raise ValueError("filter_level 必須是 'category', 'subcategory', 或 'name_zh'")
            
        try:
            # 執行查詢
            df = pd.read_sql_query(sql, self.engine)
            
            # 確保日期格式正確
            df['sales_month'] = pd.to_datetime(df['sales_month'])
            
            return df
            
        except Exception as e:
            print(f"查詢資料時發生錯誤: {e}")
            return None
    
    def get_product_hierarchy(self):
        """
        取得產品階層資料，方便查看有哪些選項可選
        
        Returns:
        dict: 包含各層級資料的字典
        """
        if self.engine is None:
            print("資料庫引擎未建立")
            return None
            
        sql = """
        SELECT DISTINCT category, subcategory, name_zh 
        FROM product_master 
        ORDER BY category, subcategory, name_zh
        """
            
        try:
            df = pd.read_sql_query(sql, self.engine)
            
            # 整理成階層結構
            hierarchy = {
                'categories': df['category'].unique().tolist(),
                'subcategories': df.groupby('category')['subcategory'].apply(list).to_dict(),
                'products': df.groupby(['category', 'subcategory'])['name_zh'].apply(list).to_dict()
            }
            
            return hierarchy
            
        except Exception as e:
            print(f"查詢產品階層時發生錯誤: {e}")
            return None
    
    def create_sales_chart(self, filter_level, filter_values, start_date, end_date, chart_title=None):
        """
        生成銷售趨勢折線圖
        
        Parameters:
        filter_level (str): 篩選層級 'category', 'subcategory', 或 'name_zh'
        filter_values (list): 篩選值清單
        start_date (str): 開始日期
        end_date (str): 結束日期 
        chart_title (str): 圖表標題，如果為None會自動生成
        
        Returns:
        plotly.graph_objects.Figure: Plotly圖表物件
        """
        
        # 定義層級名稱對應
        level_names = {
            'category': '產品類別',
            'subcategory': '產品子類別', 
            'name_zh': '產品品項'
        }
        
        # 取得資料
        df = self.get_sales_data(filter_level, filter_values, start_date, end_date)
        
        if df is None or df.empty:
            print("沒有找到符合條件的資料")
            return None
        
        # 顯示查詢到的資料摘要
        self.print_data_summary(df, filter_level, filter_values, start_date, end_date)
        
        # 自動生成標題
        if chart_title is None:
            chart_title = f"{level_names[filter_level]}銷售趨勢分析"
        
        # 建立折線圖
        fig = px.line(
            df, 
            x='sales_month', 
            y='total_amount', 
            color='filter_value',
            title=chart_title,
            labels={
                'sales_month': '銷售月份',
                'total_amount': '銷售金額 (元)',
                'filter_value': level_names.get(filter_level, filter_level)
            }
        )
        
        # 美化圖表
        fig.update_layout(
            xaxis_title="銷售月份",
            yaxis_title="銷售金額 (元)",
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=600
        )
        
        # 設定 hover 資訊
        fig.update_traces(
            mode='lines+markers',
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         '月份: %{x|%Y-%m}<br>' +
                         '銷售金額: NT$ %{y:,.0f}<extra></extra>'
        )
        
        return fig

# 便利函數：按產品類別分析
def analyze_by_category(db_config, categories, start_date, end_date, chart_title=None):
    """
    按產品類別分析銷售趨勢
    
    Parameters:
    db_config (dict): 資料庫連接設定
    categories (list): 產品類別清單，如 ["白帶魚", "蝦類/蟹"]
    start_date (str): 開始日期 'YYYY-MM-DD'
    end_date (str): 結束日期 'YYYY-MM-DD'
    chart_title (str): 圖表標題，預設為自動生成
    
    Returns:
    plotly.graph_objects.Figure: 圖表物件，可呼叫 .show() 顯示
    """
    analyzer = SalesAnalyzer(db_config)
    
    if analyzer.engine is None:
        print("資料庫連接失敗，請檢查連接設定")
        return None
    
    return analyzer.create_sales_chart(
        filter_level="category",
        filter_values=categories,
        start_date=start_date,
        end_date=end_date,
        chart_title=chart_title
    )

# 便利函數：按產品子類別分析
def analyze_by_subcategory(db_config, subcategories, start_date, end_date, chart_title=None):
    """
    按產品子類別分析銷售趨勢
    
    Parameters:
    db_config (dict): 資料庫連接設定
    subcategories (list): 產品子類別清單，如 ["白帶魚切塊", "白帶魚片"]
    start_date (str): 開始日期 'YYYY-MM-DD'
    end_date (str): 結束日期 'YYYY-MM-DD'
    chart_title (str): 圖表標題，預設為自動生成
    
    Returns:
    plotly.graph_objects.Figure: 圖表物件，可呼叫 .show() 顯示
    """
    analyzer = SalesAnalyzer(db_config)
    
    if analyzer.engine is None:
        print("資料庫連接失敗，請檢查連接設定")
        return None
    
    return analyzer.create_sales_chart(
        filter_level="subcategory",
        filter_values=subcategories,
        start_date=start_date,
        end_date=end_date,
        chart_title=chart_title
    )

# 便利函數：按具體商品分析
def analyze_by_product(db_config, products, start_date, end_date, chart_title=None):
    """
    按具體商品分析銷售趨勢
    
    Parameters:
    db_config (dict): 資料庫連接設定
    products (list): 具體商品清單，如 ["白帶魚切塊280/320-A", "白帶魚片(15K/箱)"]
    start_date (str): 開始日期 'YYYY-MM-DD'
    end_date (str): 結束日期 'YYYY-MM-DD'
    chart_title (str): 圖表標題，預設為自動生成
    
    Returns:
    plotly.graph_objects.Figure: 圖表物件，可呼叫 .show() 顯示
    """
    analyzer = SalesAnalyzer(db_config)
    
    if analyzer.engine is None:
        print("資料庫連接失敗，請檢查連接設定")
        return None
    
    return analyzer.create_sales_chart(
        filter_level="name_zh",
        filter_values=products,
        start_date=start_date,
        end_date=end_date,
        chart_title=chart_title
    )

# 使用範例
def main():
    # 資料庫設定 - 請根據實際環境修改
    db_config = {
        'host': 'your_host',
        'port': 5432,
        'database': 'your_database',
        'user': 'your_username',
        'password': 'your_password'
    }
    
    # 範例1: 按產品類別分析
    fig1 = analyze_by_category(
        db_config=db_config,
        categories=["白帶魚", "蝦類/蟹"],
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    if fig1:
        fig1.show()
    
    # 範例2: 按產品子類別分析
    fig2 = analyze_by_subcategory(
        db_config=db_config,
        subcategories=["白帶魚切塊", "白帶魚片"],
        start_date="2024-01-01",
        end_date="2024-12-31",
        chart_title="白帶魚切塊 vs 白帶魚片 銷售比較"
    )
    if fig2:
        fig2.show()
    
    # 範例3: 按具體商品分析
    fig3 = analyze_by_product(
        db_config=db_config,
        products=["白帶魚切塊280/320-A", "白帶魚片(15K/箱)"],
        start_date="2024-01-01",
        end_date="2024-12-31",
        chart_title="具體商品銷售比較"
    )
    if fig3:
        fig3.show()

if __name__ == "__main__":
    main()