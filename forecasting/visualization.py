from __future__ import annotations
import os
import pandas as pd
from .config import cfg, ensure_dirs

# 嘗試載入 matplotlib；若不可用則改用 SVG 簡易回退，避免外部依賴
try:
    import matplotlib  # type: ignore
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore
    _HAS_MPL = True
except Exception:
    plt = None  # type: ignore
    _HAS_MPL = False


def _save_svg(filename: str, title: str) -> str:
    ensure_dirs()
    base, _ = os.path.splitext(filename)
    path = os.path.join(cfg.output_dir, base + ".svg")
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='800' height='400'>
      <rect width='100%' height='100%' fill='white'/>
      <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-size='20' fill='black'>{title}</text>
      <text x='50%' y='60%' dominant-baseline='middle' text-anchor='middle' font-size='12' fill='gray'>matplotlib 不可用，顯示簡易佔位圖</text>
    </svg>
    """
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(svg)
    return path


def save_fig(fig, filename: str):
    ensure_dirs()
    if _HAS_MPL and fig is not None:
        path = os.path.join(cfg.output_dir, filename)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        import matplotlib.pyplot as _plt  # type: ignore
        _plt.close(fig)
        return path
    # fallback
    return _save_svg(filename, filename)


def plot_history_vs_forecast(hist_df: pd.DataFrame, forecast_df: pd.DataFrame, title: str = "Historical vs Forecast Revenue") -> str:
    if _HAS_MPL:
        fig, ax = plt.subplots(figsize=(10, 5))  # type: ignore
        if not hist_df.empty:
            ax.plot(hist_df["date"], hist_df["revenue"], label="Historical Revenue", linewidth=2)
        if not forecast_df.empty:
            ax.plot(forecast_df["date"], forecast_df["forecast_value"], label="Forecast (Baseline)",
                   marker='o', linewidth=2, color='red')
            if "lower_bound" in forecast_df.columns and "upper_bound" in forecast_df.columns:
                ax.fill_between(
                    forecast_df["date"], forecast_df["lower_bound"], forecast_df["upper_bound"],
                    color="orange", alpha=0.2, label="95% Confidence Interval"
                )
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Revenue (TWD)", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        return save_fig(fig, "history_vs_forecast.png")
    # fallback
    return _save_svg("history_vs_forecast.png", title)


def plot_errors(metrics_df: pd.DataFrame) -> str:
    if _HAS_MPL:
        fig, ax = plt.subplots(figsize=(10, 4))  # type: ignore
        if not metrics_df.empty:
            models = metrics_df["model"].tolist()
            mape_values = metrics_df["MAPE"].tolist()
            rmse_values = metrics_df["RMSE"].tolist()

            x = range(len(models))
            width = 0.35

            ax.bar([i - width/2 for i in x], mape_values, width, label='MAPE (%)', alpha=0.8)
            ax.bar([i + width/2 for i in x], [v/1000000 for v in rmse_values], width, label='RMSE (M)', alpha=0.8)

            ax.set_xlabel('Models', fontsize=12)
            ax.set_ylabel('Error Values', fontsize=12)
            ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(models)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
        return save_fig(fig, "errors.png")
    # fallback
    return _save_svg("errors.png", "Model Performance Comparison")


def plot_scenarios(scenarios_df: pd.DataFrame) -> str:
    if _HAS_MPL:
        fig, ax = plt.subplots(figsize=(10, 5))  # type: ignore
        if not scenarios_df.empty:
            colors = {'conservative': 'blue', 'baseline': 'green', 'optimistic': 'red'}
            for name, g in scenarios_df.groupby("scenario"):
                color = colors.get(name, 'gray')
                ax.plot(g["date"], g["forecast_value"], label=name.capitalize(),
                       marker='o', linewidth=2, color=color)
                if "lower_bound" in g.columns and "upper_bound" in g.columns:
                    ax.fill_between(g["date"], g["lower_bound"], g["upper_bound"],
                                  color=color, alpha=0.1)
        ax.set_title("Forecast Scenarios Comparison", fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Revenue (TWD)", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        return save_fig(fig, "scenarios.png")
    # fallback
    return _save_svg("scenarios.png", "Forecast Scenarios Comparison")


def plot_backtest_history(backtest_data: dict, stock_id: str, model_name: str = "Best") -> str:
    """繪製回測歷史紀錄圖表"""
    if not _HAS_MPL:
        filename = f"{stock_id}_{model_name}_backtest_history.png"
        return _save_svg(filename, "Backtest History")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # 上圖：預測 vs 實際值
    if backtest_data.get('predictions') and backtest_data.get('actuals'):
        predictions = backtest_data['predictions']
        actuals = backtest_data['actuals']
        dates = range(len(predictions))  # 簡化為序號

        ax1.plot(dates, actuals, 'o-', label='Actual', linewidth=2, markersize=4, color='blue')
        ax1.plot(dates, predictions, 's-', label='Predicted', linewidth=2, markersize=4, color='red')
        ax1.set_title(f'{stock_id} {model_name} Model: Predicted vs Actual Revenue', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Test Period', fontsize=12)
        ax1.set_ylabel('Revenue (TWD)', fontsize=12)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)

        # 格式化 Y 軸為億元
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e8:.1f}億'))

    # 下圖：誤差分析
    if backtest_data.get('predictions') and backtest_data.get('actuals'):
        errors = [(p - a) / a * 100 for p, a in zip(predictions, actuals)]  # 百分比誤差

        colors = ['red' if e > 0 else 'blue' for e in errors]
        bars = ax2.bar(dates, errors, alpha=0.7, color=colors)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.8, linewidth=1)
        ax2.set_title(f'{model_name} Model Prediction Error (%)', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Test Period', fontsize=12)
        ax2.set_ylabel('Error (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)

        # 添加誤差統計資訊
        mean_error = sum(errors) / len(errors)
        ax2.text(0.02, 0.98, f'Mean Error: {mean_error:.2f}%', transform=ax2.transAxes,
                fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    filename = f"{stock_id}_{model_name}_backtest_history.png"
    return save_fig(fig, filename)

