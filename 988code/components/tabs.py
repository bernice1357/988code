import dash_bootstrap_components as dbc

def create_tabs(tab_configs):
    """
    創建通用tabs組件
    
    參數:
    tab_configs: list of dict, 每個dict包含:
        - content: tab內容
        - label: tab標籤文字
    """
    tabs_list = []
    for config in tab_configs:
        tabs_list.append(
            dbc.Tab(
                config['content'], 
                label=config['label']
            )
        )
    
    return dbc.Tabs(
        tabs_list,
        active_tab="tab-0",
        className="my-tabs",
        style={
            "border": "1px solid #dee2e6",
            "borderRadius": "0.375rem",
            "--bs-nav-tabs-link-active-bg": "#000000",
            "--bs-nav-tabs-link-active-color": "white",
            "--bs-nav-tabs-link-active-border-color": "#000000"
        }
    )