import dash_bootstrap_components as dbc

def create_tabs(tab_configs):
    """
    創建通用tabs組件
    
    參數:
    tab_configs: list of dict, 每個dict包含:
        - content: tab內容
        - label: tab標籤文字
        - count: tab數量 (可選)
    """
    tabs_list = []
    for i, config in enumerate(tab_configs):
        label_content = config['label']
        if 'count' in config:
            label_content = f"{config['label']} {config['count']}"
            
        tabs_list.append(
            dbc.Tab(
                config['content'], 
                label=label_content,
                tab_id=f"tab-{i}",
                tab_style={
                    "color": "#6c757d",
                    "border": "none",
                    "border-radius": "0",
                    "padding": "0rem 1rem",
                    "background": "transparent"
                },
                active_tab_style={
                    "background-color": "transparent",
                    "border": "none",
                    "border-radius": "0",
                    "border-bottom": "3px solid #cc5500",
                    "margin-bottom": "-3px"
                },
                active_label_style={
                    "color": "#cc5500",
                    "font-weight": "bold"
                }
            )
        )
    
    return dbc.Tabs(
        tabs_list,
        active_tab="tab-0",
        className="my-tabs",
        style={
            "border-bottom": "3px solid #e0e0e0"
        }
    )