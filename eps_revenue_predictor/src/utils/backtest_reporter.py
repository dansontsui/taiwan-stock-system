# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Backtest Reporter
回測結果報告生成器
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from config.settings import PROJECT_ROOT
from src.utils.logger import get_logger

logger = get_logger('backtest_reporter')

class BacktestReporter:
    """回測結果報告生成器"""
    
    def __init__(self):
        self.reports_dir = PROJECT_ROOT / 'reports' / 'backtest'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("BacktestReporter initialized")
    
    def generate_comprehensive_report(self, backtest_results: Dict) -> Dict:
        """生成全面的回測報告"""
        try:
            stock_id = backtest_results.get('stock_id', 'Unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            report = {
                'report_info': {
                    'stock_id': stock_id,
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'backtest_periods': backtest_results.get('backtest_periods', 0),
                    'report_id': f"{stock_id}_{timestamp}"
                },
                'executive_summary': self._create_executive_summary(backtest_results),
                'detailed_analysis': self._create_detailed_analysis(backtest_results),
                'performance_metrics': self._create_performance_metrics(backtest_results),
                'improvement_recommendations': backtest_results.get('improvement_suggestions', [])
            }
            
            # 保存報告
            report_file = self.reports_dir / f"backtest_report_{stock_id}_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Comprehensive report generated: {report_file}")
            
            return {
                'success': True,
                'report': report,
                'report_file': str(report_file)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_executive_summary(self, backtest_results: Dict) -> Dict:
        """創建執行摘要"""
        try:
            revenue_stats = backtest_results.get('results', {}).get('revenue', {}).get('statistics', {})
            eps_stats = backtest_results.get('results', {}).get('eps', {}).get('statistics', {})
            overall_stats = backtest_results.get('overall_statistics', {})
            
            # 計算整體評級
            overall_grade = self._calculate_overall_grade(revenue_stats, eps_stats)
            
            summary = {
                'overall_grade': overall_grade,
                'key_findings': [],
                'performance_highlights': {}
            }
            
            # 營收表現摘要
            if revenue_stats:
                revenue_direction_acc = revenue_stats.get('direction_accuracy', 0)
                revenue_mape = revenue_stats.get('avg_revenue_mape', 0)
                
                summary['performance_highlights']['revenue'] = {
                    'direction_accuracy': f"{revenue_direction_acc:.1%}",
                    'average_mape': f"{revenue_mape:.1f}%",
                    'periods_tested': revenue_stats.get('total_periods', 0)
                }
                
                if revenue_direction_acc >= 0.7:
                    summary['key_findings'].append("營收趨勢預測方向準確度良好")
                elif revenue_direction_acc >= 0.5:
                    summary['key_findings'].append("營收趨勢預測方向準確度中等")
                else:
                    summary['key_findings'].append("營收趨勢預測方向準確度需要改善")
            
            # EPS表現摘要
            if eps_stats:
                eps_direction_acc = eps_stats.get('direction_accuracy', 0)
                eps_mape = eps_stats.get('avg_eps_mape', 0)
                
                summary['performance_highlights']['eps'] = {
                    'direction_accuracy': f"{eps_direction_acc:.1%}",
                    'average_mape': f"{eps_mape:.1f}%",
                    'periods_tested': eps_stats.get('total_periods', 0)
                }
                
                if eps_direction_acc >= 0.7:
                    summary['key_findings'].append("EPS趨勢預測方向準確度良好")
                elif eps_direction_acc >= 0.5:
                    summary['key_findings'].append("EPS趨勢預測方向準確度中等")
                else:
                    summary['key_findings'].append("EPS趨勢預測方向準確度需要改善")
            
            # 綜合表現
            combined_perf = overall_stats.get('combined_performance', {})
            if combined_perf:
                avg_direction_acc = combined_perf.get('avg_direction_accuracy', 0)
                if avg_direction_acc >= 0.7:
                    summary['key_findings'].append("整體預測模型表現優秀")
                elif avg_direction_acc >= 0.6:
                    summary['key_findings'].append("整體預測模型表現良好")
                else:
                    summary['key_findings'].append("整體預測模型需要優化")
            
            return summary
            
        except Exception as e:
            logger.warning(f"Failed to create executive summary: {e}")
            return {}
    
    def _create_detailed_analysis(self, backtest_results: Dict) -> Dict:
        """創建詳細分析"""
        try:
            analysis = {
                'revenue_analysis': {},
                'eps_analysis': {},
                'confidence_analysis': {},
                'temporal_analysis': {}
            }
            
            # 營收詳細分析
            revenue_results = backtest_results.get('results', {}).get('revenue', {})
            if revenue_results.get('success'):
                analysis['revenue_analysis'] = self._analyze_revenue_performance(revenue_results)
            
            # EPS詳細分析
            eps_results = backtest_results.get('results', {}).get('eps', {})
            if eps_results.get('success'):
                analysis['eps_analysis'] = self._analyze_eps_performance(eps_results)
            
            # 信心水準分析
            analysis['confidence_analysis'] = self._analyze_confidence_levels(backtest_results)
            
            # 時間序列分析
            analysis['temporal_analysis'] = self._analyze_temporal_patterns(backtest_results)
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to create detailed analysis: {e}")
            return {}
    
    def _create_performance_metrics(self, backtest_results: Dict) -> Dict:
        """創建性能指標"""
        try:
            metrics = {
                'accuracy_metrics': {},
                'error_metrics': {},
                'consistency_metrics': {}
            }
            
            revenue_stats = backtest_results.get('results', {}).get('revenue', {}).get('statistics', {})
            eps_stats = backtest_results.get('results', {}).get('eps', {}).get('statistics', {})
            
            # 準確度指標
            if revenue_stats or eps_stats:
                metrics['accuracy_metrics'] = {
                    'revenue_direction_accuracy': revenue_stats.get('direction_accuracy', 0),
                    'eps_direction_accuracy': eps_stats.get('direction_accuracy', 0),
                    'combined_direction_accuracy': (
                        revenue_stats.get('direction_accuracy', 0) + 
                        eps_stats.get('direction_accuracy', 0)
                    ) / 2 if revenue_stats and eps_stats else 0
                }
            
            # 誤差指標
            if revenue_stats or eps_stats:
                metrics['error_metrics'] = {
                    'revenue_mape': revenue_stats.get('avg_revenue_mape', 0),
                    'eps_mape': eps_stats.get('avg_eps_mape', 0),
                    'revenue_rmse': revenue_stats.get('rmse_growth', 0),
                    'eps_rmse': eps_stats.get('rmse_growth', 0)
                }
            
            # 一致性指標
            metrics['consistency_metrics'] = self._calculate_consistency_metrics(backtest_results)
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Failed to create performance metrics: {e}")
            return {}
    
    def _calculate_overall_grade(self, revenue_stats: Dict, eps_stats: Dict) -> str:
        """計算整體評級"""
        try:
            scores = []
            
            # 營收評分
            if revenue_stats:
                revenue_direction = revenue_stats.get('direction_accuracy', 0)
                revenue_mape = revenue_stats.get('avg_revenue_mape', 100)
                
                revenue_score = (revenue_direction * 0.6 + 
                               max(0, (20 - revenue_mape) / 20) * 0.4)
                scores.append(revenue_score)
            
            # EPS評分
            if eps_stats:
                eps_direction = eps_stats.get('direction_accuracy', 0)
                eps_mape = eps_stats.get('avg_eps_mape', 100)
                
                eps_score = (eps_direction * 0.6 + 
                           max(0, (25 - eps_mape) / 25) * 0.4)
                scores.append(eps_score)
            
            if not scores:
                return 'N/A'
            
            avg_score = np.mean(scores)
            
            if avg_score >= 0.8:
                return 'A (優秀)'
            elif avg_score >= 0.7:
                return 'B (良好)'
            elif avg_score >= 0.6:
                return 'C (中等)'
            elif avg_score >= 0.5:
                return 'D (需改善)'
            else:
                return 'F (不及格)'
                
        except Exception as e:
            logger.warning(f"Failed to calculate overall grade: {e}")
            return 'N/A'
    
    def _analyze_revenue_performance(self, revenue_results: Dict) -> Dict:
        """分析營收表現"""
        try:
            backtest_data = revenue_results.get('backtest_results', [])
            statistics = revenue_results.get('statistics', {})
            
            analysis = {
                'total_predictions': len(backtest_data),
                'successful_predictions': len([r for r in backtest_data if r.get('accuracy')]),
                'average_metrics': {
                    'growth_rate_mape': statistics.get('avg_growth_mape', 0),
                    'revenue_mape': statistics.get('avg_revenue_mape', 0),
                    'direction_accuracy': statistics.get('direction_accuracy', 0)
                },
                'best_prediction': None,
                'worst_prediction': None
            }
            
            # 找出最佳和最差預測
            if backtest_data:
                valid_predictions = [r for r in backtest_data if r.get('accuracy')]
                if valid_predictions:
                    # 按方向準確度和MAPE排序
                    sorted_by_performance = sorted(
                        valid_predictions,
                        key=lambda x: (
                            x['accuracy'].get('direction_correct', False),
                            -x['accuracy'].get('revenue_mape', 100)
                        ),
                        reverse=True
                    )
                    
                    analysis['best_prediction'] = {
                        'period': sorted_by_performance[0]['period'],
                        'date': sorted_by_performance[0].get('target_date'),
                        'metrics': sorted_by_performance[0]['accuracy']
                    }
                    
                    analysis['worst_prediction'] = {
                        'period': sorted_by_performance[-1]['period'],
                        'date': sorted_by_performance[-1].get('target_date'),
                        'metrics': sorted_by_performance[-1]['accuracy']
                    }
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to analyze revenue performance: {e}")
            return {}
    
    def _analyze_eps_performance(self, eps_results: Dict) -> Dict:
        """分析EPS表現"""
        try:
            backtest_data = eps_results.get('backtest_results', [])
            statistics = eps_results.get('statistics', {})
            
            analysis = {
                'total_predictions': len(backtest_data),
                'successful_predictions': len([r for r in backtest_data if r.get('accuracy')]),
                'average_metrics': {
                    'growth_rate_mape': statistics.get('avg_growth_mape', 0),
                    'eps_mape': statistics.get('avg_eps_mape', 0),
                    'direction_accuracy': statistics.get('direction_accuracy', 0)
                },
                'best_prediction': None,
                'worst_prediction': None
            }
            
            # 找出最佳和最差預測
            if backtest_data:
                valid_predictions = [r for r in backtest_data if r.get('accuracy')]
                if valid_predictions:
                    sorted_by_performance = sorted(
                        valid_predictions,
                        key=lambda x: (
                            x['accuracy'].get('direction_correct', False),
                            -x['accuracy'].get('eps_mape', 100)
                        ),
                        reverse=True
                    )
                    
                    analysis['best_prediction'] = {
                        'period': sorted_by_performance[0]['period'],
                        'quarter': sorted_by_performance[0].get('target_quarter'),
                        'metrics': sorted_by_performance[0]['accuracy']
                    }
                    
                    analysis['worst_prediction'] = {
                        'period': sorted_by_performance[-1]['period'],
                        'quarter': sorted_by_performance[-1].get('target_quarter'),
                        'metrics': sorted_by_performance[-1]['accuracy']
                    }
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to analyze EPS performance: {e}")
            return {}

    def _analyze_confidence_levels(self, backtest_results: Dict) -> Dict:
        """分析信心水準表現"""
        try:
            revenue_conf = backtest_results.get('results', {}).get('revenue', {}).get('statistics', {}).get('confidence_analysis', {})
            eps_conf = backtest_results.get('results', {}).get('eps', {}).get('statistics', {}).get('confidence_analysis', {})

            analysis = {
                'revenue_confidence': revenue_conf,
                'eps_confidence': eps_conf,
                'insights': []
            }

            # 分析信心水準與準確度的關係
            for conf_type in ['High', 'Medium', 'Low']:
                revenue_data = revenue_conf.get(conf_type, {})
                eps_data = eps_conf.get(conf_type, {})

                if revenue_data.get('count', 0) > 0:
                    revenue_acc = revenue_data.get('direction_accuracy', 0)
                    analysis['insights'].append(
                        f"營收{conf_type}信心預測: {revenue_data['count']}次, "
                        f"方向準確度{revenue_acc:.1%}"
                    )

                if eps_data.get('count', 0) > 0:
                    eps_acc = eps_data.get('direction_accuracy', 0)
                    analysis['insights'].append(
                        f"EPS{conf_type}信心預測: {eps_data['count']}次, "
                        f"方向準確度{eps_acc:.1%}"
                    )

            return analysis

        except Exception as e:
            logger.warning(f"Failed to analyze confidence levels: {e}")
            return {}

    def _analyze_temporal_patterns(self, backtest_results: Dict) -> Dict:
        """分析時間模式"""
        try:
            revenue_data = backtest_results.get('results', {}).get('revenue', {}).get('backtest_results', [])
            eps_data = backtest_results.get('results', {}).get('eps', {}).get('backtest_results', [])

            analysis = {
                'revenue_temporal': {},
                'eps_temporal': {},
                'trends': []
            }

            # 分析營收時間模式
            if revenue_data:
                revenue_errors = [r['accuracy'].get('revenue_mape', 0) for r in revenue_data if r.get('accuracy')]
                if len(revenue_errors) > 1:
                    # 檢查誤差趨勢
                    if revenue_errors[-1] < revenue_errors[0]:
                        analysis['trends'].append("營收預測準確度隨時間改善")
                    elif revenue_errors[-1] > revenue_errors[0]:
                        analysis['trends'].append("營收預測準確度隨時間下降")

                    analysis['revenue_temporal'] = {
                        'first_period_mape': revenue_errors[0],
                        'last_period_mape': revenue_errors[-1],
                        'improvement': revenue_errors[0] - revenue_errors[-1]
                    }

            # 分析EPS時間模式
            if eps_data:
                eps_errors = [r['accuracy'].get('eps_mape', 0) for r in eps_data if r.get('accuracy')]
                if len(eps_errors) > 1:
                    if eps_errors[-1] < eps_errors[0]:
                        analysis['trends'].append("EPS預測準確度隨時間改善")
                    elif eps_errors[-1] > eps_errors[0]:
                        analysis['trends'].append("EPS預測準確度隨時間下降")

                    analysis['eps_temporal'] = {
                        'first_period_mape': eps_errors[0],
                        'last_period_mape': eps_errors[-1],
                        'improvement': eps_errors[0] - eps_errors[-1]
                    }

            return analysis

        except Exception as e:
            logger.warning(f"Failed to analyze temporal patterns: {e}")
            return {}

    def _calculate_consistency_metrics(self, backtest_results: Dict) -> Dict:
        """計算一致性指標"""
        try:
            revenue_data = backtest_results.get('results', {}).get('revenue', {}).get('backtest_results', [])
            eps_data = backtest_results.get('results', {}).get('eps', {}).get('backtest_results', [])

            metrics = {}

            # 營收一致性
            if revenue_data:
                revenue_mapes = [r['accuracy'].get('revenue_mape', 0) for r in revenue_data if r.get('accuracy')]
                if revenue_mapes:
                    metrics['revenue_consistency'] = {
                        'std_deviation': np.std(revenue_mapes),
                        'coefficient_of_variation': np.std(revenue_mapes) / (np.mean(revenue_mapes) + 1e-8),
                        'min_mape': min(revenue_mapes),
                        'max_mape': max(revenue_mapes)
                    }

            # EPS一致性
            if eps_data:
                eps_mapes = [r['accuracy'].get('eps_mape', 0) for r in eps_data if r.get('accuracy')]
                if eps_mapes:
                    metrics['eps_consistency'] = {
                        'std_deviation': np.std(eps_mapes),
                        'coefficient_of_variation': np.std(eps_mapes) / (np.mean(eps_mapes) + 1e-8),
                        'min_mape': min(eps_mapes),
                        'max_mape': max(eps_mapes)
                    }

            return metrics

        except Exception as e:
            logger.warning(f"Failed to calculate consistency metrics: {e}")
            return {}

    def display_backtest_summary(self, backtest_results: Dict) -> None:
        """顯示回測摘要 (終端機友善格式)"""
        try:
            stock_id = backtest_results.get('stock_id', 'Unknown')

            print(f"\n{'='*60}")
            print(f"📊 {stock_id} 回測結果摘要")
            print(f"{'='*60}")

            # 基本資訊
            periods = backtest_results.get('backtest_periods', 0)
            start_time = backtest_results.get('start_time', 'Unknown')
            end_time = backtest_results.get('end_time', 'Unknown')

            print(f"🕒 回測期間: {periods} 個月")
            print(f"⏰ 執行時間: {start_time} ~ {end_time}")

            # 營收結果
            revenue_results = backtest_results.get('results', {}).get('revenue', {})
            if revenue_results.get('success'):
                revenue_stats = revenue_results.get('statistics', {})
                print(f"\n💰 營收預測結果:")
                print(f"   📈 測試期數: {revenue_stats.get('total_periods', 0)}")
                print(f"   🎯 方向準確度: {revenue_stats.get('direction_accuracy', 0):.1%}")
                print(f"   📊 平均MAPE: {revenue_stats.get('avg_revenue_mape', 0):.1f}%")
                print(f"   📉 RMSE: {revenue_stats.get('rmse_growth', 0):.4f}")
            else:
                print(f"\n💰 營收預測結果: ❌ 失敗")
                print(f"   錯誤: {revenue_results.get('error', 'Unknown')}")

            # EPS結果
            eps_results = backtest_results.get('results', {}).get('eps', {})
            if eps_results.get('success'):
                eps_stats = eps_results.get('statistics', {})
                print(f"\n📈 EPS預測結果:")
                print(f"   📈 測試期數: {eps_stats.get('total_periods', 0)}")
                print(f"   🎯 方向準確度: {eps_stats.get('direction_accuracy', 0):.1%}")
                print(f"   📊 平均MAPE: {eps_stats.get('avg_eps_mape', 0):.1f}%")
                print(f"   📉 RMSE: {eps_stats.get('rmse_growth', 0):.4f}")
            else:
                print(f"\n📈 EPS預測結果: ❌ 失敗")
                print(f"   錯誤: {eps_results.get('error', 'Unknown')}")

            # 整體統計
            overall_stats = backtest_results.get('overall_statistics', {})
            combined_perf = overall_stats.get('combined_performance', {})
            if combined_perf:
                print(f"\n🎯 整體表現:")
                print(f"   📊 綜合方向準確度: {combined_perf.get('avg_direction_accuracy', 0):.1%}")
                print(f"   📈 總預測次數: {combined_perf.get('total_predictions', 0)}")

            # 改進建議
            suggestions = backtest_results.get('improvement_suggestions', [])
            if suggestions:
                print(f"\n💡 改進建議:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"   {i}. {suggestion}")

            print(f"\n{'='*60}")

        except Exception as e:
            logger.error(f"Failed to display backtest summary: {e}")
            print(f"❌ 無法顯示回測摘要: {e}")

    def display_detailed_backtest_results(self, backtest_results: Dict) -> None:
        """顯示詳細的回測結果 (每期預測vs實際)"""
        try:
            stock_id = backtest_results.get('stock_id', 'Unknown')

            print(f"\n{'='*80}")
            print(f"📊 {stock_id} 詳細回測結果")
            print(f"{'='*80}")

            # 營收詳細結果
            revenue_results = backtest_results.get('results', {}).get('revenue', {})
            if revenue_results.get('success'):
                print(f"\n💰 營收預測詳細結果:")
                print(f"{'='*100}")

                backtest_data = revenue_results.get('backtest_results', [])
                if backtest_data:
                    # 表頭 - 添加實際月份欄位
                    header = f"{'期數':<4} {'目標月份':<10} {'實際月份':<10} {'預測營收(億)':<12} {'實際營收(億)':<12} {'預測成長率':<12} {'實際成長率':<12} {'方向正確':<8} {'MAPE':<8}"
                    print(header)
                    print(f"{'-'*110}")

                    for result in backtest_data:
                        period = result.get('period', 0)
                        target_date = result.get('target_date', 'N/A')
                        target_month = result.get('target_month', target_date[:7] if target_date != 'N/A' else 'N/A')  # 顯示年月

                        prediction = result.get('prediction', {})
                        actual = result.get('actual', {})
                        accuracy = result.get('accuracy', {})

                        # 預測值
                        pred_revenue = prediction.get('predicted_revenue', 0) / 1e8  # 轉換為億
                        pred_growth_rate = prediction.get('growth_rate', 0)
                        pred_growth = (pred_growth_rate * 100) if pred_growth_rate is not None else 0

                        # 實際值和實際月份
                        actual_revenue = actual.get('actual_revenue', 0)
                        actual_month = actual.get('actual_month', 'N/A')
                        actual_growth_rate = actual.get('actual_growth_rate', 0)
                        actual_growth = (actual_growth_rate * 100) if actual_growth_rate is not None else 0
                        data_available = actual.get('data_available', True)

                        # 處理無資料情況
                        if not data_available or actual_revenue is None or actual_growth_rate is None:
                            actual_revenue_str = "無資料"
                            actual_growth_str = "N/A"
                            if actual_month == 'N/A':
                                actual_month = "無資料"
                            direction_correct = "❓"
                            mape_str = "N/A"
                        else:
                            actual_revenue_str = f"{actual_revenue / 1e8:>10.1f}"
                            actual_growth_str = f"{actual_growth:>8.1f}%"
                            direction_correct = "✅" if accuracy.get('direction_correct', False) else "❌"
                            mape = accuracy.get('revenue_mape', 0)
                            mape_str = f"{mape:>6.1f}%" if mape is not None else "N/A"

                        # 格式化數字，確保對齊
                        pred_growth_str = f"{pred_growth:>8.1f}%"

                        print(f"{period:<4} {target_month:<10} {actual_month:<10} {pred_revenue:>10.1f}  {actual_revenue_str:<12}  "
                              f"{pred_growth_str:<12} {actual_growth_str:<12} {direction_correct:<8} {mape_str:<8}")

                # 統計摘要
                stats = revenue_results.get('statistics', {})
                print(f"\n📈 營收統計摘要:")
                print(f"   平均MAPE: {stats.get('avg_revenue_mape', 0):.1f}%")
                print(f"   方向準確度: {stats.get('direction_accuracy', 0):.1%}")
                print(f"   RMSE: {stats.get('rmse_growth', 0):.4f}")

            # EPS詳細結果
            eps_results = backtest_results.get('results', {}).get('eps', {})
            if eps_results.get('success'):
                print(f"\n📈 EPS預測詳細結果:")
                print(f"{'='*100}")

                backtest_data = eps_results.get('backtest_results', [])
                if backtest_data:
                    # 表頭 - 調整欄位寬度確保對齊
                    header = f"{'期數':<4} {'目標季度':<12} {'預測EPS':<10} {'實際EPS':<10} {'預測成長率':<12} {'實際成長率':<12} {'方向正確':<8} {'MAPE':<8}"
                    print(header)
                    print(f"{'-'*100}")

                    for result in backtest_data:
                        period = result.get('period', 0)
                        target_quarter = result.get('target_quarter', 'N/A')

                        prediction = result.get('prediction', {})
                        actual = result.get('actual', {})
                        accuracy = result.get('accuracy', {})

                        # 預測值
                        pred_eps = prediction.get('predicted_eps', 0)
                        pred_growth_rate = prediction.get('growth_rate', 0)
                        pred_growth = (pred_growth_rate * 100) if pred_growth_rate is not None else 0

                        # 實際值
                        actual_eps = actual.get('actual_eps', 0)
                        actual_growth_rate = actual.get('actual_growth_rate', 0)
                        actual_growth = (actual_growth_rate * 100) if actual_growth_rate is not None else 0

                        # 準確度
                        direction_correct = "✅" if accuracy.get('direction_correct', False) else "❌"
                        mape = accuracy.get('eps_mape', 0)

                        # 格式化數字，確保對齊
                        pred_growth_str = f"{pred_growth:>8.1f}%"
                        actual_growth_str = f"{actual_growth:>8.1f}%"
                        mape_str = f"{mape:>6.1f}%"

                        print(f"{period:<4} {target_quarter:<12} {pred_eps:>8.2f}  {actual_eps:>8.2f}  "
                              f"{pred_growth_str:<12} {actual_growth_str:<12} {direction_correct:<8} {mape_str:<8}")

                # 統計摘要
                stats = eps_results.get('statistics', {})
                print(f"\n📊 EPS統計摘要:")
                print(f"   平均MAPE: {stats.get('avg_eps_mape', 0):.1f}%")
                print(f"   方向準確度: {stats.get('direction_accuracy', 0):.1%}")
                print(f"   RMSE: {stats.get('rmse_growth', 0):.4f}")

            # 成功失敗判斷標準
            print(f"\n🎯 成功失敗判斷標準:")
            print(f"{'='*40}")
            print(f"📊 方向準確度:")
            print(f"   ✅ 優秀: ≥70%")
            print(f"   👍 良好: 60-69%")
            print(f"   👌 中等: 50-59%")
            print(f"   ⚠️  需改善: <50%")
            print(f"\n📈 MAPE (平均絕對百分比誤差):")
            print(f"   ✅ 優秀: ≤10%")
            print(f"   👍 良好: 11-15%")
            print(f"   👌 中等: 16-20%")
            print(f"   ⚠️  需改善: >20%")
            print(f"\n🏆 整體評級:")
            print(f"   A級: 方向準確度≥70% 且 MAPE≤10%")
            print(f"   B級: 方向準確度≥60% 且 MAPE≤15%")
            print(f"   C級: 方向準確度≥50% 且 MAPE≤20%")
            print(f"   D級: 其他情況")

            print(f"\n{'='*80}")

        except Exception as e:
            logger.error(f"Failed to display detailed backtest results: {e}")
            print(f"❌ 無法顯示詳細回測結果: {e}")
