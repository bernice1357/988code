from .common import *

# 假的歷史購買紀錄（視覺化用）
purchase_dates = pd.to_datetime([
    "2025-02-05", "2025-02-19", "2025-03-05", "2025-03-19",
    "2025-04-02", "2025-04-16", "2025-04-23"
])
timeline_df = pd.DataFrame({"購買日期": purchase_dates})

y_center = 10

@app.callback(
    Output("button-container", "children"),
    Input("data-table", "data")
)
def create_buttons(rows):
    buttons = []
    for i, row in enumerate(rows):
        buttons.append(
            html.Button("查看", id={'type': 'view-button', 'index': i}, n_clicks=0, style={"margin": "5px"})
        )
    return buttons

@app.callback(
    Output("modal-body", "children"),   # Modal 內容
    Output("detail-modal", "is_open"),  # Modal 開關狀態
    Input({"type": "view-button", "index": dash.ALL}, "n_clicks"),
    State("data-table", "data"),
    prevent_initial_call=True  # 防止初始化時觸發
)
def show_modal(view_clicks, table_data):
    
    # print(view_clicks)
    # 觸發了哪個按鈕？
    triggered = ctx.triggered_id
    # print(triggered)

    is_all_zero = all(v == 0 for v in view_clicks)
    if not is_all_zero and triggered is not None:
        
        idx = triggered["index"]
        row = table_data[idx]

        # 生成 Modal 的內容
        content = html.Div([
            html.H1([
                f"{row['客戶名稱']} - {row['補貨品項']}",
                html.Br(),
                "購買週期圖表"
            ]),
            dcc.Graph(
                id="purchase-timeline",
                figure=go.Figure()
                .add_trace(
                    go.Scatter(
                        x=timeline_df["購買日期"], 
                        y=[y_center] * len(timeline_df),  # 所有點放在同一條水平線上
                        mode="markers+text",  # 顯示點和文字
                        text=[f"{d.year}<br>{d.strftime('%m/%d')}" for d in timeline_df["購買日期"]],
                        textfont=dict(size=16),  # 調整文字大小
                        textposition="top center",  # 日期顯示在點的上方
                        marker=dict(size=12, color="#564dff", symbol="circle")
                    )
                )
                .add_trace(
                    go.Scatter(
                        x=timeline_df["購買日期"], 
                        y=[y_center] * len(timeline_df),  # 把水平線放在點的正中央
                        mode="lines", 
                        name="中心線", 
                        line=dict(color="#564dff", width=2)  # 紅色虛線作為中心線
                    )
                )
                .update_layout(
                    showlegend=False,
                    yaxis=dict(showticklabels=False, range=[0, 20]),  # 隱藏y軸刻度，並設定y軸範圍
                    xaxis=dict(showticklabels=False),
                    height=300,
                    plot_bgcolor="white",  # 設定圖表區域的背景顏色為白色
                    paper_bgcolor="white"  # 設定整個畫布的背景顏色為白色
                )
            ),
            html.H3(f"平均週期 XX天"),  # 這裡可以換成計算結果
            html.Hr(),
            html.Div(
                dbc.Button("關閉", id="close-modal", n_clicks=0, className="ms-auto")
            )
        ], style={'textAlign': 'center'})

        # 打開 Modal 並顯示內容
        return content, True

    # 如果沒有觸發任何查看按鈕，則返回不更新
    return dash.no_update, False
