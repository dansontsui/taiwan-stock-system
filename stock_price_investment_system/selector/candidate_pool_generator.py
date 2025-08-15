# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 候選池生成器
Stock Price Investment System - Candidate Pool Generator
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
import json
from pathlib import Path

from ..config.settings import get_config

logger = logging.getLogger(__name__)

class CandidatePoolGenerator:
    """候選池生成器 - 根據Walk-forward結果生成候選股票池"""
    
    def __init__(self):
        """初始化候選池生成器"""
        self.config = get_config()
        self.selection_config = self.config['selection']
        self.thresholds = self.selection_config['candidate_pool_thresholds']
        
        logger.info("CandidatePoolGenerator initialized")
    
    def generate_candidate_pool(self, 
                              walk_forward_results: Dict[str, Any],
                              custom_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """
        生成候選股票池
        
        Args:
            walk_forward_results: Walk-forward驗證結果
            custom_thresholds: 自訂門檻值
            
        Returns:
            候選池結果字典
        """
        logger.info("Generating candidate pool from walk-forward results")
        
        # 使用自訂門檻或預設門檻
        thresholds = custom_thresholds or self.thresholds
        
        stock_statistics = walk_forward_results.get('stock_statistics', {})
        
        if not stock_statistics:
            logger.warning("No stock statistics found in walk-forward results")
            return {
                'success': False,
                'error': 'No stock statistics available',
                'candidate_pool': [],
                'rejected_stocks': []
            }
        
        candidate_stocks = []
        rejected_stocks = []
        
        # 評估每檔股票
        for stock_id, stats in stock_statistics.items():
            evaluation = self._evaluate_stock(stock_id, stats, thresholds)
            
            if evaluation['qualified']:
                candidate_stocks.append({
                    'stock_id': stock_id,
                    'stock_score': evaluation['stock_score'],
                    'statistics': evaluation['statistics'],
                    'qualification_reasons': evaluation['reasons']
                })
            else:
                rejected_stocks.append({
                    'stock_id': stock_id,
                    'stock_score': evaluation['stock_score'],
                    'statistics': evaluation['statistics'],
                    'rejection_reasons': evaluation['reasons']
                })
        
        # 排序候選股票（按stock_score降序）
        candidate_stocks.sort(key=lambda x: x['stock_score'], reverse=True)
        
        # 生成報告
        report = self._generate_pool_report(
            candidate_stocks, rejected_stocks, thresholds, walk_forward_results
        )
        
        result = {
            'success': True,
            'candidate_pool': candidate_stocks,
            'rejected_stocks': rejected_stocks,
            'pool_size': len(candidate_stocks),
            'total_evaluated': len(stock_statistics),
            'qualification_rate': len(candidate_stocks) / len(stock_statistics) if stock_statistics else 0,
            'thresholds_used': thresholds,
            'report': report,
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Candidate pool generated: {len(candidate_stocks)} qualified out of {len(stock_statistics)} stocks")
        return result
    
    def _evaluate_stock(self, 
                       stock_id: str,
                       stats: Dict[str, Any],
                       thresholds: Dict[str, float]) -> Dict[str, Any]:
        """
        評估單檔股票是否符合候選池條件
        
        Args:
            stock_id: 股票代碼
            stats: 股票統計資料
            thresholds: 門檻值
            
        Returns:
            評估結果字典
        """
        reasons = []
        qualified = True
        
        # 檢查基本統計是否存在
        required_stats = ['win_rate', 'profit_loss_ratio', 'total_trades', 'fold_count']
        for stat in required_stats:
            if stat not in stats:
                qualified = False
                reasons.append(f"缺少統計資料: {stat}")
        
        if not qualified:
            return {
                'qualified': False,
                'stock_score': 0,
                'statistics': stats,
                'reasons': reasons
            }
        
        # 1. 勝率檢查
        win_rate = stats.get('win_rate', 0)
        if win_rate < thresholds['min_win_rate']:
            qualified = False
            reasons.append(f"勝率過低: {win_rate:.2%} < {thresholds['min_win_rate']:.2%}")
        else:
            reasons.append(f"勝率符合: {win_rate:.2%}")
        
        # 2. 盈虧比檢查
        profit_loss_ratio = stats.get('profit_loss_ratio', 0)
        if profit_loss_ratio < thresholds['min_profit_loss_ratio']:
            qualified = False
            reasons.append(f"盈虧比過低: {profit_loss_ratio:.2f} < {thresholds['min_profit_loss_ratio']:.2f}")
        else:
            reasons.append(f"盈虧比符合: {profit_loss_ratio:.2f}")
        
        # 3. 交易次數檢查
        total_trades = stats.get('total_trades', 0)
        if total_trades < thresholds['min_trade_count']:
            qualified = False
            reasons.append(f"交易次數過少: {total_trades} < {thresholds['min_trade_count']}")
        else:
            reasons.append(f"交易次數符合: {total_trades}")
        
        # 4. 有交易的fold數檢查
        fold_count = stats.get('fold_count', 0)
        if fold_count < thresholds['min_folds_with_trades']:
            qualified = False
            reasons.append(f"有交易的fold數過少: {fold_count} < {thresholds['min_folds_with_trades']}")
        else:
            reasons.append(f"fold數符合: {fold_count}")
        
        # 5. 最大回撤檢查（如果有的話）
        max_drawdown = abs(stats.get('min_return', 0))  # 使用最小報酬作為最大回撤的近似
        if max_drawdown > thresholds['max_drawdown_threshold']:
            qualified = False
            reasons.append(f"最大回撤過大: {max_drawdown:.2%} > {thresholds['max_drawdown_threshold']:.2%}")
        else:
            reasons.append(f"最大回撤可接受: {max_drawdown:.2%}")
        
        # 計算stock_score
        stock_score = self._calculate_stock_score(stats)
        
        return {
            'qualified': qualified,
            'stock_score': stock_score,
            'statistics': stats,
            'reasons': reasons
        }
    
    def _calculate_stock_score(self, stats: Dict[str, Any]) -> float:
        """
        計算股票分數
        
        Args:
            stats: 股票統計資料
            
        Returns:
            股票分數 (0-100)
        """
        try:
            # 基礎分數組件
            win_rate = stats.get('win_rate', 0)
            profit_loss_ratio = stats.get('profit_loss_ratio', 0)
            sharpe_ratio = stats.get('sharpe_ratio', 0)
            average_return = stats.get('average_return', 0)
            total_trades = stats.get('total_trades', 0)
            fold_count = stats.get('fold_count', 0)
            
            # 分數計算（加權平均）
            score_components = {
                'win_rate': min(win_rate * 100, 100) * 0.25,  # 勝率權重25%
                'profit_loss_ratio': min(profit_loss_ratio * 20, 100) * 0.20,  # 盈虧比權重20%
                'sharpe_ratio': min(max(sharpe_ratio * 50 + 50, 0), 100) * 0.15,  # 夏普比率權重15%
                'average_return': min(max(average_return * 500 + 50, 0), 100) * 0.20,  # 平均報酬權重20%
                'stability': min(fold_count * 10, 100) * 0.10,  # 穩定性權重10%
                'activity': min(total_trades * 2, 100) * 0.10  # 活躍度權重10%
            }
            
            total_score = sum(score_components.values())
            
            # 確保分數在0-100範圍內
            return max(0, min(100, total_score))
            
        except Exception as e:
            logger.warning(f"Error calculating stock score: {e}")
            return 0
    
    def _generate_pool_report(self, 
                            candidate_stocks: List[Dict],
                            rejected_stocks: List[Dict],
                            thresholds: Dict[str, float],
                            walk_forward_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成候選池報告"""
        report = {
            'summary': {
                'total_stocks_evaluated': len(candidate_stocks) + len(rejected_stocks),
                'qualified_stocks': len(candidate_stocks),
                'rejected_stocks': len(rejected_stocks),
                'qualification_rate': len(candidate_stocks) / (len(candidate_stocks) + len(rejected_stocks)) if (candidate_stocks or rejected_stocks) else 0
            },
            'thresholds_applied': thresholds,
            'top_candidates': candidate_stocks[:10] if candidate_stocks else [],
            'rejection_analysis': self._analyze_rejections(rejected_stocks),
            'score_distribution': self._analyze_score_distribution(candidate_stocks + rejected_stocks)
        }
        
        return report
    
    def _analyze_rejections(self, rejected_stocks: List[Dict]) -> Dict[str, Any]:
        """分析被拒絕股票的原因"""
        if not rejected_stocks:
            return {}
        
        rejection_reasons = {}
        
        for stock in rejected_stocks:
            for reason in stock['rejection_reasons']:
                if '勝率過低' in reason:
                    rejection_reasons['low_win_rate'] = rejection_reasons.get('low_win_rate', 0) + 1
                elif '盈虧比過低' in reason:
                    rejection_reasons['low_profit_loss_ratio'] = rejection_reasons.get('low_profit_loss_ratio', 0) + 1
                elif '交易次數過少' in reason:
                    rejection_reasons['insufficient_trades'] = rejection_reasons.get('insufficient_trades', 0) + 1
                elif 'fold數過少' in reason:
                    rejection_reasons['insufficient_folds'] = rejection_reasons.get('insufficient_folds', 0) + 1
                elif '最大回撤過大' in reason:
                    rejection_reasons['excessive_drawdown'] = rejection_reasons.get('excessive_drawdown', 0) + 1
        
        return {
            'reason_counts': rejection_reasons,
            'most_common_reason': max(rejection_reasons.items(), key=lambda x: x[1]) if rejection_reasons else None,
            'total_rejected': len(rejected_stocks)
        }
    
    def _analyze_score_distribution(self, all_stocks: List[Dict]) -> Dict[str, Any]:
        """分析分數分布"""
        if not all_stocks:
            return {}
        
        scores = [stock['stock_score'] for stock in all_stocks]
        
        return {
            'mean_score': np.mean(scores),
            'median_score': np.median(scores),
            'std_score': np.std(scores),
            'min_score': np.min(scores),
            'max_score': np.max(scores),
            'score_ranges': {
                '90-100': sum(1 for s in scores if s >= 90),
                '80-89': sum(1 for s in scores if 80 <= s < 90),
                '70-79': sum(1 for s in scores if 70 <= s < 80),
                '60-69': sum(1 for s in scores if 60 <= s < 70),
                '50-59': sum(1 for s in scores if 50 <= s < 60),
                '0-49': sum(1 for s in scores if s < 50)
            }
        }
    
    def save_candidate_pool(self, 
                          candidate_pool_result: Dict[str, Any],
                          filepath: str = None) -> str:
        """
        儲存候選池結果
        
        Args:
            candidate_pool_result: 候選池結果
            filepath: 儲存路徑
            
        Returns:
            儲存的檔案路徑
        """
        out_paths = get_config('output')['paths']
        out_dir = Path(out_paths['candidate_pools'])
        out_dir.mkdir(parents=True, exist_ok=True)

        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = out_dir / f"candidate_pool_{timestamp}.json"
        else:
            filepath = out_dir / filepath

        with open(filepath, 'w', encoding='utf-8-sig') as f:
            json.dump(candidate_pool_result, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Candidate pool saved to {filepath}")
        return str(filepath)
    
    def export_candidate_pool_csv(self, 
                                candidate_pool_result: Dict[str, Any],
                                filepath: str = None) -> str:
        """
        匯出候選池為CSV格式
        
        Args:
            candidate_pool_result: 候選池結果
            filepath: 儲存路徑
            
        Returns:
            儲存的檔案路徑
        """
        out_paths = get_config('output')['paths']
        out_dir = Path(out_paths['candidate_pools'])
        out_dir.mkdir(parents=True, exist_ok=True)

        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = out_dir / f"candidate_pool_{timestamp}.csv"
        else:
            filepath = out_dir / filepath

        candidate_stocks = candidate_pool_result.get('candidate_pool', [])

        if not candidate_stocks:
            logger.warning("No candidate stocks to export")
            return ""

        # 準備CSV資料 - 中文化欄位
        csv_data = []
        for stock in candidate_stocks:
            stats = stock['statistics']
            csv_data.append({
                '股票代碼': stock['stock_id'],
                '股票分數': f"{stock['stock_score']:.2f}",
                '勝率': f"{stats.get('win_rate', 0):.2%}",
                '盈虧比': f"{stats.get('profit_loss_ratio', 0):.2f}",
                '平均報酬': f"{stats.get('average_return', 0):.2%}",
                '總交易次數': stats.get('total_trades', 0),
                '夏普比率': f"{stats.get('sharpe_ratio', 0):.3f}",
                '最大報酬': f"{stats.get('max_return', 0):.2%}",
                '最小報酬': f"{stats.get('min_return', 0):.2%}",
                '報酬標準差': f"{stats.get('return_std', 0):.3f}",
                '有效Fold數量': stats.get('fold_count', 0),
                '總報酬': f"{stats.get('total_return', 0):.2%}",
                '獲利交易數': stats.get('winning_trades', 0)
            })

        df = pd.DataFrame(csv_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

        logger.info(f"Candidate pool CSV exported to {filepath}")
        return str(filepath)
    
    def load_candidate_pool(self, filepath: str) -> Dict[str, Any]:
        """
        載入候選池結果
        
        Args:
            filepath: 檔案路徑
            
        Returns:
            候選池結果字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            logger.info(f"Candidate pool loaded from {filepath}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to load candidate pool from {filepath}: {e}")
            return {}
