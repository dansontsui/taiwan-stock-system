# -*- coding: utf-8 -*-
"""
回測結果視覺化模組
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import logging

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class BacktestCharts:
    """回測圖表生成器"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path("results/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_holdout_charts(self, trades_df: pd.DataFrame, summary: Dict[str, Any]) -> Dict[str, str]:
        """創建外層回測圖表"""
        charts = {}
        
        if trades_df.empty:
            logger.warning("交易資料為空，無法生成圖表")
            return charts
        
        # 1. 累積報酬曲線
        nav_chart = self._create_nav_curve(trades_df)
        if nav_chart:
            charts['nav_curve'] = nav_chart
        
        # 2. 月度報酬分布
        monthly_chart = self._create_monthly_returns(trades_df)
        if monthly_chart:
            charts['monthly_returns'] = monthly_chart
        
        # 3. 交易統計圖
        stats_chart = self._create_trade_statistics(trades_df)
        if stats_chart:
            charts['trade_statistics'] = stats_chart
        
        # 4. 個股表現圖
        stock_chart = self._create_stock_performance(trades_df)
        if stock_chart:
            charts['stock_performance'] = stock_chart
        
        return charts
    
    def _create_nav_curve(self, trades_df: pd.DataFrame) -> str:
        """創建淨值曲線圖"""
        try:
            # 按日期排序
            df = trades_df.copy()
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            df = df.sort_values('entry_date')
            
            # 計算累積報酬
            df['cumulative_return'] = (1 + df['actual_return']).cumprod()
            
            # 創建圖表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 上圖：淨值曲線
            ax1.plot(df['entry_date'], df['cumulative_return'], 
                    linewidth=2, color='blue', label='投資組合淨值')
            ax1.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='基準線')
            ax1.set_title('投資組合淨值曲線', fontsize=16, fontweight='bold')
            ax1.set_ylabel('累積報酬倍數', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 下圖：回撤曲線
            running_max = df['cumulative_return'].cummax()
            drawdown = (df['cumulative_return'] / running_max - 1) * 100
            ax2.fill_between(df['entry_date'], drawdown, 0, 
                           color='red', alpha=0.3, label='回撤')
            ax2.set_title('回撤曲線', fontsize=14)
            ax2.set_ylabel('回撤 (%)', fontsize=12)
            ax2.set_xlabel('日期', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 格式化日期軸
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # 儲存圖表
            chart_path = self.output_dir / f"nav_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"淨值曲線圖已生成: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"生成淨值曲線圖失敗: {e}")
            return ""
    
    def _create_monthly_returns(self, trades_df: pd.DataFrame) -> str:
        """創建月度報酬分布圖"""
        try:
            df = trades_df.copy()
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            df['year_month'] = df['entry_date'].dt.to_period('M')
            
            # 計算月度報酬
            monthly_returns = df.groupby('year_month')['actual_return'].mean()
            
            # 創建圖表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 左圖：月度報酬柱狀圖
            colors = ['green' if x > 0 else 'red' for x in monthly_returns.values]
            ax1.bar(range(len(monthly_returns)), monthly_returns.values * 100, 
                   color=colors, alpha=0.7)
            ax1.set_title('月度平均報酬率', fontsize=14, fontweight='bold')
            ax1.set_ylabel('報酬率 (%)', fontsize=12)
            ax1.set_xlabel('月份', fontsize=12)
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax1.grid(True, alpha=0.3)
            
            # 設定x軸標籤
            ax1.set_xticks(range(0, len(monthly_returns), max(1, len(monthly_returns)//6)))
            ax1.set_xticklabels([str(monthly_returns.index[i]) for i in 
                               range(0, len(monthly_returns), max(1, len(monthly_returns)//6))], 
                               rotation=45)
            
            # 右圖：報酬率分布直方圖
            ax2.hist(df['actual_return'] * 100, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax2.set_title('交易報酬率分布', fontsize=14, fontweight='bold')
            ax2.set_xlabel('報酬率 (%)', fontsize=12)
            ax2.set_ylabel('交易次數', fontsize=12)
            ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='損益平衡點')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 儲存圖表
            chart_path = self.output_dir / f"monthly_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"月度報酬圖已生成: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"生成月度報酬圖失敗: {e}")
            return ""
    
    def _create_trade_statistics(self, trades_df: pd.DataFrame) -> str:
        """創建交易統計圖"""
        try:
            df = trades_df.copy()
            
            # 計算統計數據
            total_trades = len(df)
            winning_trades = len(df[df['actual_return'] > 0])
            losing_trades = len(df[df['actual_return'] < 0])
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            
            avg_win = df[df['actual_return'] > 0]['actual_return'].mean() * 100 if winning_trades > 0 else 0
            avg_loss = df[df['actual_return'] < 0]['actual_return'].mean() * 100 if losing_trades > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            # 創建圖表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 左上：勝負比例餅圖
            labels = ['獲利交易', '虧損交易']
            sizes = [winning_trades, losing_trades]
            colors = ['green', 'red']
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title(f'交易勝負比例\n(勝率: {win_rate:.1f}%)', fontsize=12, fontweight='bold')
            
            # 右上：模型類型分布
            model_counts = df['model_type'].value_counts()
            ax2.bar(model_counts.index, model_counts.values, color='skyblue', alpha=0.7)
            ax2.set_title('模型類型分布', fontsize=12, fontweight='bold')
            ax2.set_ylabel('交易次數', fontsize=10)
            ax2.tick_params(axis='x', rotation=45)
            
            # 左下：持有天數分布
            ax3.hist(df['holding_days'], bins=15, alpha=0.7, color='orange', edgecolor='black')
            ax3.set_title('持有天數分布', fontsize=12, fontweight='bold')
            ax3.set_xlabel('持有天數', fontsize=10)
            ax3.set_ylabel('交易次數', fontsize=10)
            ax3.grid(True, alpha=0.3)
            
            # 右下：統計數據表
            ax4.axis('off')
            stats_data = [
                ['總交易次數', f'{total_trades}'],
                ['獲利交易', f'{winning_trades}'],
                ['虧損交易', f'{losing_trades}'],
                ['勝率', f'{win_rate:.1f}%'],
                ['平均獲利', f'{avg_win:.2f}%'],
                ['平均虧損', f'{avg_loss:.2f}%'],
                ['盈虧比', f'{profit_factor:.2f}']
            ]
            
            table = ax4.table(cellText=stats_data, 
                            colLabels=['統計項目', '數值'],
                            cellLoc='center',
                            loc='center',
                            colWidths=[0.6, 0.4])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2)
            ax4.set_title('交易統計摘要', fontsize=12, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # 儲存圖表
            chart_path = self.output_dir / f"trade_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"交易統計圖已生成: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"生成交易統計圖失敗: {e}")
            return ""
    
    def _create_stock_performance(self, trades_df: pd.DataFrame) -> str:
        """創建個股表現圖"""
        try:
            df = trades_df.copy()
            
            # 計算個股統計
            stock_stats = df.groupby('stock_id').agg({
                'actual_return': ['count', 'mean', 'sum'],
                'predicted_return': 'mean'
            }).round(4)
            
            stock_stats.columns = ['交易次數', '平均報酬率', '總報酬率', '平均預測報酬率']
            stock_stats = stock_stats.sort_values('總報酬率', ascending=False)
            
            # 創建圖表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 左圖：個股總報酬率
            colors = ['green' if x > 0 else 'red' for x in stock_stats['總報酬率']]
            bars1 = ax1.bar(range(len(stock_stats)), stock_stats['總報酬率'] * 100, 
                           color=colors, alpha=0.7)
            ax1.set_title('個股總報酬率', fontsize=14, fontweight='bold')
            ax1.set_ylabel('總報酬率 (%)', fontsize=12)
            ax1.set_xlabel('股票代碼', fontsize=12)
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax1.grid(True, alpha=0.3)
            
            # 設定x軸標籤
            ax1.set_xticks(range(len(stock_stats)))
            ax1.set_xticklabels(stock_stats.index, rotation=45)
            
            # 在柱子上顯示數值
            for i, bar in enumerate(bars1):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top')
            
            # 右圖：預測 vs 實際報酬率散點圖
            ax2.scatter(df['predicted_return'] * 100, df['actual_return'] * 100, 
                       alpha=0.6, s=50, color='blue')
            ax2.plot([-10, 10], [-10, 10], 'r--', alpha=0.7, label='完美預測線')
            ax2.set_title('預測 vs 實際報酬率', fontsize=14, fontweight='bold')
            ax2.set_xlabel('預測報酬率 (%)', fontsize=12)
            ax2.set_ylabel('實際報酬率 (%)', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 儲存圖表
            chart_path = self.output_dir / f"stock_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"個股表現圖已生成: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"生成個股表現圖失敗: {e}")
            return ""
