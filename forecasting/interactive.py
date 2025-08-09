from __future__ import annotations
import os
import json
import pandas as pd
from typing import Dict, List


def create_interactive_backtest_html(stock_id: str, all_model_results: Dict, output_dir: str) -> str:
    """創建高互動性的回測歷史HTML，包含所有模型的折線圖和分頁表格"""
    out_html = os.path.join(output_dir, f"{stock_id}_interactive_backtest.html")

    try:
        # 準備所有模型的數據
        models_data = {}
        for model_name, result in all_model_results.items():
            history = result.get('history', [])
            if history:
                models_data[model_name] = {
                    'history': history,
                    'mape': result.get('mape', 0),
                    'trend_accuracy': result.get('trend_accuracy', 0)
                }

        if not models_data:
            return ""

        # 生成HTML
        html_content = generate_html_template(stock_id, models_data)

        with open(out_html, "w", encoding="utf-8-sig") as f:
            f.write(html_content)

        return out_html
    except Exception as e:
        print(f"HTML生成錯誤: {e}")
        return ""


def generate_html_template(stock_id: str, models_data: Dict) -> str:
    """生成完整的HTML模板"""

    # 準備圖表數據
    chart_data = prepare_chart_data(models_data)

    html = f"""<!DOCTYPE html>
<html lang='zh-Hant'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>{stock_id} 互動式回測分析</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f8f9fa;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .tabs {{
            display: flex;
            background: #e9ecef;
            border-bottom: 1px solid #dee2e6;
        }}
        .tab {{
            flex: 1;
            padding: 15px 20px;
            background: #e9ecef;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        .tab:hover {{
            background: #dee2e6;
        }}
        .tab.active {{
            background: white;
            border-bottom: 3px solid #667eea;
            color: #667eea;
        }}
        .tab-content {{
            display: none;
            padding: 30px;
        }}
        .tab-content.active {{
            display: block;
        }}
        .chart-container {{
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        .model-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        tr:hover {{
            background: #f1f7ff;
        }}
        .num {{
            font-variant-numeric: tabular-nums;
        }}
        .error-positive {{
            color: #dc3545;
        }}
        .error-negative {{
            color: #28a745;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{stock_id} 互動式回測分析</h1>
            <p>所有模型的預測表現與詳細歷史</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">📊 總覽</button>"""

    # 為每個模型添加分頁
    for model_name in models_data.keys():
        html += f"""
            <button class="tab" onclick="showTab('{model_name.lower()}')">{get_model_emoji(model_name)} {model_name}</button>"""

    html += """
        </div>

        <!-- 總覽頁面 -->
        <div id="overview" class="tab-content active">
            <h2>📈 所有模型預測對比</h2>
            <div class="chart-container">
                <div id="comparison-chart" style="height: 600px;"></div>
            </div>

            <div class="model-stats">"""

    # 添加模型統計卡片
    for model_name, data in models_data.items():
        html += f"""
                <div class="stat-card">
                    <div class="stat-value">{data['mape']:.2f}%</div>
                    <div class="stat-label">{model_name} MAPE</div>
                </div>
                <div class=\"stat-card\">
                    <div class=\"stat-value\">{(data.get('trend_accuracy', 0) or 0) * 100:.1f}%</div>
                    <div class=\"stat-label\">{model_name} 趨勢準確率</div>
                </div>"""

    html += """
            </div>
        </div>"""

    # 為每個模型添加詳細頁面
    for model_name, data in models_data.items():
        html += generate_model_tab(model_name, data, stock_id)

    # 添加JavaScript
    html += f"""
    </div>

    <script>
        // 圖表數據
        const chartData = {json.dumps(chart_data, ensure_ascii=False)};

        // 初始化圖表
        initializeCharts();

        function showTab(tabName) {{
            // 隱藏所有內容
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.remove('active');
            }});
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // 顯示選中的內容
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');

            // 重新渲染圖表（Plotly需要）
            setTimeout(() => {{
                Plotly.Plots.resize();
            }}, 100);
        }}

        function initializeCharts() {{
            // 總覽對比圖
            createComparisonChart();

            // 各模型詳細圖
            {generate_chart_js(models_data)}
        }}

        function createComparisonChart() {{
            const traces = [];

            // 實際值（只需要一條線）
            if (chartData.actual && chartData.actual.length > 0) {{
                traces.push({{
                    x: chartData.periods,
                    y: chartData.actual,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: '實際值',
                    line: {{ color: '#2E86AB', width: 3 }},
                    marker: {{ size: 6 }}
                }});
            }}

            // 各模型預測值
            const colors = ['#A23B72', '#F18F01', '#C73E1D', '#7209B7'];
            let colorIndex = 0;

            Object.keys(chartData.models).forEach(modelName => {{
                const modelData = chartData.models[modelName];
                traces.push({{
                    x: chartData.periods,
                    y: modelData.predictions,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: `${{modelName}} 預測`,
                    line: {{ color: colors[colorIndex % colors.length], width: 2, dash: 'dot' }},
                    marker: {{ size: 4 }}
                }});
                colorIndex++;
            }});

            const layout = {{
                title: '所有模型預測對比',
                xaxis: {{ title: '回測期數' }},
                yaxis: {{
                    title: '營收 (億元)',
                    tickformat: '.1f'
                }},
                hovermode: 'x unified',
                showlegend: true,
                legend: {{ x: 0, y: 1 }}
            }};

            Plotly.newPlot('comparison-chart', traces, layout, {{responsive: true}});
        }}

        {generate_individual_chart_functions(models_data)}
    </script>
</body>
</html>"""

    return html


def prepare_chart_data(models_data: Dict) -> Dict:
    # 將資料整理成繪圖用格式
    periods = []
    actual = []
    models = {}
    # 取第一個模型的歷史作為期間索引
    for model_name, data in models_data.items():
        hist = data.get('history', [])
        if hist:
            periods = [h.get('test_date', str(i+1)) for i, h in enumerate(hist)]
            actual = [h.get('actual', h.get('actual_value')) for h in hist]
            break
    # 加入各模型預測
    for model_name, data in models_data.items():
        hist = data.get('history', [])
        preds = [h.get('predicted', h.get('predicted_value')) for h in hist]
        models[model_name] = { 'predictions': preds }
    return { 'periods': periods, 'actual': actual, 'models': models }


def get_model_emoji(model_name: str) -> str:
    return {
        'Prophet': '📐',
        'XGBoost': '🌲',
        'LSTM': '🧠'
    }.get(model_name, '🤖')


def generate_model_tab(model_name: str, data: Dict, stock_id: str) -> str:
    # 單一模型分頁：圖＋表
    hist = data.get('history', [])
    table_rows = []
    for h in hist:
        period = h.get('period')
        test_date = h.get('test_date')
        pred = h.get('predicted', h.get('predicted_value'))
        act = h.get('actual', h.get('actual_value'))
        errp = h.get('error_pct', h.get('error_percentage'))
        table_rows.append({
            'period': period,
            'test_date': test_date,
            'predicted': pred,
            'actual': act,
            'error_pct': errp
        })

    table_json = json.dumps(table_rows, ensure_ascii=False)
    div_id = f"{model_name.lower()}-chart"
    tab_id = model_name.lower()

    return f"""
        <div id="{tab_id}" class="tab-content">
            <h2>{get_model_emoji(model_name)} {model_name} 詳細分析</h2>
            <div class="model-stats">
                <div class="stat-card">
                    <div class="stat-value">{data.get('mape', 0):.2f}%</div>
                    <div class="stat-label">MAPE</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{(data.get('trend_accuracy', 0) or 0) * 100:.1f}%</div>
                    <div class="stat-label">趨勢準確率</div>
                </div>
            </div>
            <div class="chart-container">
                <div id="{div_id}" style="height: 500px;"></div>
            </div>
            <h3>詳細回測歷史</h3>
            <div style="max-height: 400px; overflow: auto; border: 1px solid #eee;">
                <table>
                    <thead>
                        <tr>
                            <th>期數</th>
                            <th>回測年月</th>
                            <th>預測數據</th>
                            <th>實際數據</th>
                            <th>誤差(%)</th>
                        </tr>
                    </thead>
                    <tbody id="{tab_id}-tbody"></tbody>
                </table>
            </div>
            <script>
                (function() {{
                    const rows = {table_json};
                    const tbody = document.getElementById('{tab_id}-tbody');
                    rows.forEach(r => {{
                        const tr = document.createElement('tr');
                        function td(v) {{ const d = document.createElement('td'); d.textContent = (typeof v==='number')? v.toLocaleString(): v; d.title = v; d.className='num'; return d; }}
                        tr.appendChild(td(r.period));
                        tr.appendChild(td(r.test_date));
                        tr.appendChild(td(r.predicted));
                        tr.appendChild(td(r.actual));
                        const e = td(r.error_pct);
                        e.className += (r.error_pct>=0 ? ' error-positive' : ' error-negative');
                        tr.appendChild(e);
                        tbody.appendChild(tr);
                    }});
                }})()
            </script>
        </div>
    """


def generate_chart_js(models_data: Dict) -> str:
    # 產生為每個模型建立圖表的JS呼叫
    js = []
    for model_name in models_data.keys():
        js.append(f"createModelChart('{model_name}');")
    return "\n            ".join(js)


def generate_individual_chart_functions(models_data: Dict) -> str:
    # 提供 createModelChart 函數，依據 chartData 渲染單模型圖
    return """
        function createModelChart(modelName) {
            const divId = modelName.toLowerCase() + '-chart';
            const preds = chartData.models[modelName]?.predictions || [];
            const traces = [];

            if (chartData.actual && chartData.actual.length > 0) {
                traces.push({
                    x: chartData.periods,
                    y: chartData.actual.map(v => v/1e8),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: '實際值',
                    line: { color: '#2E86AB', width: 3 },
                    marker: { size: 6 }
                });
            }

            traces.push({
                x: chartData.periods,
                y: preds.map(v => v/1e8),
                type: 'scatter',
                mode: 'lines+markers',
                name: modelName + ' 預測',
                line: { color: '#A23B72', width: 2, dash: 'dot' },
                marker: { size: 4 }
            });

            const layout = {
                title: modelName + ' 模型：預測 vs 實際',
                xaxis: { title: '回測年月' },
                yaxis: { title: '營收 (億元)' },
                hovermode: 'x unified',
                showlegend: true,
                legend: { x: 0, y: 1 }
            };
            Plotly.newPlot(divId, traces, layout, {responsive: true});
        }
    """


# 相容用：保留舊的單模型HTML輸出API（由CSV轉HTML）
def save_backtest_history_html(stock_id: str, model_name: str, history_csv_path: str) -> str:
    try:
        import pandas as pd
        df = pd.read_csv(history_csv_path, encoding='utf-8-sig')
        # 轉換為 models_data 結構給新模板
        history = []
        for _, r in df.iterrows():
            history.append({
                'period': int(r.get('period', 0)),
                'test_date': str(r.get('test_date', '')),
                'predicted': float(r.get('predicted_value', r.get('predicted', 0)) or 0),
                'actual': float(r.get('actual_value', r.get('actual', 0)) or 0),
                'error_pct': float(r.get('error_percentage', r.get('error_pct', 0)) or 0),
            })
        models_data = {
            model_name: {
                'history': history,
                'mape': 0.0,
                'trend_accuracy': 0.0,
            }
        }
        html = generate_html_template(stock_id, models_data)
        out_html = os.path.join(os.path.dirname(history_csv_path), f"{stock_id}_{model_name}_backtest_history.html")
        with open(out_html, 'w', encoding='utf-8-sig') as f:
            f.write(html)
        return out_html
    except Exception:
        return ''


