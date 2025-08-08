# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Backtest Engine
回測引擎 - 用於驗證和調整AI預測準確度
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.data.database_manager import DatabaseManager
from src.predictors.revenue_predictor import RevenuePredictor
from src.predictors.eps_predictor import EPSPredictor
from src.models.adjustment_model import AIAdjustmentModel
from src.utils.logger import get_logger, log_execution
from config.settings import PREDICTION_CONFIG

logger = get_logger('backtest_engine')

class BacktestEngine:
    """回測引擎

    用於驗證預測模型的歷史準確度並調整AI模型參數
    """

    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.revenue_predictor = RevenuePredictor(self.db_manager)
        self.eps_predictor = EPSPredictor(self.db_manager)
        self.ai_model = AIAdjustmentModel(self.db_manager)

        logger.info("BacktestEngine initialized")

    @log_execution
    def run_comprehensive_backtest(self, stock_id: str,
                                 backtest_periods: int = 12,
                                 prediction_types: List[str] = None) -> Dict:
        """
        執行全面回測

        Args:
            stock_id: 股票代碼
            backtest_periods: 回測期數 (月數)
            prediction_types: 預測類型 ['revenue', 'eps']

        Returns:
            回測結果字典
        """
        if prediction_types is None:
            prediction_types = ['revenue', 'eps']

        logger.info(f"Starting comprehensive backtest for {stock_id}")

        results = {
            'stock_id': stock_id,
            'backtest_periods': backtest_periods,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'results': {}
        }

        # 營收回測
        if 'revenue' in prediction_types:
            logger.info(f"Running revenue backtest for {stock_id}")
            revenue_results = self._run_revenue_backtest(stock_id, backtest_periods)
            results['results']['revenue'] = revenue_results

        # EPS回測
        if 'eps' in prediction_types:
            logger.info(f"Running EPS backtest for {stock_id}")
            eps_results = self._run_eps_backtest(stock_id, backtest_periods)
            results['results']['eps'] = eps_results

        # 計算整體統計
        overall_stats = self._calculate_overall_statistics(results['results'])
        results['overall_statistics'] = overall_stats

        # 生成改進建議
        improvement_suggestions = self._generate_improvement_suggestions(results)
        results['improvement_suggestions'] = improvement_suggestions

        results['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        logger.info(f"Comprehensive backtest completed for {stock_id}")
    @log_execution
    def run_comprehensive_backtest_by_range(self, stock_id: str,
                                            start_month: Optional[str] = None,
                                            end_month: Optional[str] = None,
                                            start_quarter: Optional[str] = None,
                                            end_quarter: Optional[str] = None,
                                            prediction_types: List[str] = None,
                                            retrain_ai_per_step: bool = False,
                                            optimize_after: bool = False) -> Dict:
        """以日期/季度區間執行滾動回測
        Args:
            stock_id: 股票代碼
            start_month: 起始月份 YYYY-MM (用於營收)
            end_month: 結束月份 YYYY-MM (用於營收)
            start_quarter: 起始季度 YYYY-Qn (用於EPS)
            end_quarter: 結束季度 YYYY-Qn (用於EPS)
            prediction_types: ['revenue','eps']
            retrain_ai_per_step: 是否在每一步回測前重訓AI調整模型
            optimize_after: 回測完是否基於結果呼叫一次整體優化
        """
        if prediction_types is None:
            prediction_types = ['revenue', 'eps']

        logger.info(f"Starting range backtest for {stock_id}")
        results = {
            'stock_id': stock_id,
            'mode': 'range',
            'range': {
                'start_month': start_month,
                'end_month': end_month,
                'start_quarter': start_quarter,
                'end_quarter': end_quarter
            },
            'results': {}
        }

        # revenue by month range
        if 'revenue' in prediction_types and start_month and end_month:
            monthly_data = self.db_manager.get_monthly_revenue_data(stock_id)
            if not monthly_data.empty:
                self.current_stock_id = stock_id
                backtest_results = []

                # iterate months from start to end-1 as backtest points, predict next month
                sm_y, sm_m = [int(x) for x in start_month.split('-')]
                em_y, em_m = [int(x) for x in end_month.split('-')]

                def month_iter(y0, m0, y1, m1):
                    y, m = y0, m0
                    while (y < y1) or (y == y1 and m < m1):
                        yield y, m
                        m += 1
                        if m > 12:
                            m = 1
                            y += 1

                for y, m in month_iter(sm_y, sm_m, em_y, em_m):
                    backtest_date = datetime(y, m, 1)
                    target_date = backtest_date + timedelta(days=30)
                    train_data = monthly_data[monthly_data['date'] <= backtest_date]
                    if len(train_data) < 6:
                        continue
                    if retrain_ai_per_step:
                        try:
                            self.ai_model.train_model(retrain=True)
                        except Exception:
                            pass
                    pred = self._simulate_revenue_prediction(stock_id, train_data, backtest_date)
                    actual = self._get_actual_revenue_result(monthly_data, target_date)
                    if pred and actual:
                        acc = self._calculate_revenue_accuracy(pred, actual)
                        backtest_results.append({
                            'backtest_date': backtest_date.strftime('%Y-%m-%d'),
                            'target_date': target_date.strftime('%Y-%m-%d'),
                            'target_month': target_date.strftime('%Y-%m'),
                            'prediction': pred,
                            'actual': actual,
                            'accuracy': acc
                        })
                results['results']['revenue'] = {
                    'success': True,
                    'periods_tested': len(backtest_results),
                    'backtest_results': backtest_results,
                    'statistics': self._calculate_revenue_statistics(backtest_results)
                }
            else:
                results['results']['revenue'] = {'success': False, 'error': 'no revenue data'}

        # eps by quarter range
        if 'eps' in prediction_types and start_quarter and end_quarter:
            q_data = self.db_manager.get_quarterly_financial_data(stock_id)
            if not q_data.empty:
                backtest_results = []

                def q_to_tuple(qs: str) -> Tuple[int, int]:
                    y, qn = qs.split('-Q')
                    return int(y), int(qn)

                def q_iter(y0, q0, y1, q1):
                    y, qn = y0, q0
                    while (y < y1) or (y == y1 and qn < q1):
                        yield y, qn
                        qn += 1
                        if qn > 4:
                            qn = 1
                            y += 1

                sy, sq = q_to_tuple(start_quarter)
                ey, eq = q_to_tuple(end_quarter)

                for y, qn in q_iter(sy, sq, ey, eq):
                    back_q = f"{y}-Q{qn}"
                    back_date = self.db_manager._quarter_to_date(back_q)
                    if back_date is None:
                        continue
                    train = q_data[q_data['date'] <= back_date]
                    if len(train) < 4:
                        continue
                    if retrain_ai_per_step:
                        try:
                            self.ai_model.train_model(retrain=True)
                        except Exception:
                            pass
                    pred = self._simulate_eps_prediction(stock_id, train, back_q)
                    tgt_q = self._get_next_quarter(back_q)
                    actual = self._get_actual_eps_result(q_data, tgt_q)
                    if pred and actual:
                        acc = self._calculate_eps_accuracy(pred, actual)
                        abnormal_info = self._detect_eps_abnormal_quarter(stock_id, tgt_q, q_data, pred, actual)
                        backtest_results.append({
                            'backtest_quarter': back_q,
                            'target_quarter': tgt_q,
                            'prediction': pred,
                            'actual': actual,
                            'accuracy': acc,
                            'abnormal': abnormal_info
                        })
                results['results']['eps'] = {
                    'success': True,
                    'periods_tested': len(backtest_results),
                    'backtest_results': backtest_results,
                    'statistics': self._calculate_eps_statistics(backtest_results)
                }
            else:
                results['results']['eps'] = {'success': False, 'error': 'no eps data'}

        # 整體統計與建議
        results['overall_statistics'] = self._calculate_overall_statistics(results['results'])
        if optimize_after:
            results['optimization'] = self.optimize_ai_model(stock_id, results)
        logger.info(f"Range backtest completed for {stock_id}")
        return results

    def _run_revenue_backtest(self, stock_id: str, periods: int) -> Dict:
        """執行營收回測"""
        logger.info(f"Running revenue backtest for {periods} periods")

        # 設置當前股票ID (供其他方法使用)
        self.current_stock_id = stock_id

        # 獲取歷史資料
        historical_data = self.db_manager.get_monthly_revenue_data(stock_id)

        if historical_data.empty or len(historical_data) < periods + 6:
            return {
                'success': False,
                'error': 'Insufficient historical data',
                'data_points': len(historical_data) if not historical_data.empty else 0
            }

        backtest_results = []

        # 🔧 修復: 實現真正的滾動窗口回測
        latest_date = historical_data['date'].max()

        for i in range(periods):
            # 🔧 修復: 正確的滾動窗口計算
            # 從最新資料往前推，每次滾動一個月
            backtest_date = latest_date - timedelta(days=30 * (periods - i))
            target_date = backtest_date + timedelta(days=30)

            # 🔧 滾動窗口: 固定使用12個月的訓練資料
            training_start_date = backtest_date - timedelta(days=365)  # 往前12個月

            # 分割資料：使用滾動窗口
            train_data = historical_data[
                (historical_data['date'] >= training_start_date) &
                (historical_data['date'] <= backtest_date)
            ]

            logger.info(f"[ROLLING_WINDOW] Period {i+1}/{periods} | "
                       f"backtest_date={backtest_date.strftime('%Y-%m-%d')} | "
                       f"target_month={target_date.strftime('%Y-%m')} | "
                       f"training_window={training_start_date.strftime('%Y-%m')}~{backtest_date.strftime('%Y-%m')} | "
                       f"training_samples={len(train_data)}")

            if len(train_data) < 6:  # 至少需要6個月資料
                logger.warning(f"Insufficient training data for period {i+1}: {len(train_data)} samples")
                continue

            # 執行預測 (模擬當時的預測)
            prediction_result = self._simulate_revenue_prediction(
                stock_id, train_data, backtest_date
            )

            # 獲取實際結果 (target_date已在上面計算)
            actual_result = self._get_actual_revenue_result(
                historical_data, target_date
            )

            if prediction_result and actual_result:
                # 計算準確度指標
                accuracy_metrics = self._calculate_revenue_accuracy(
                    prediction_result, actual_result
                )

                backtest_results.append({
                    'period': i + 1,
                    'backtest_date': backtest_date.strftime('%Y-%m-%d'),
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'target_month': target_date.strftime('%Y-%m'),  # 添加清楚的月份顯示
                    'prediction': prediction_result,
                    'actual': actual_result,
                    'accuracy': accuracy_metrics
                })

        # 計算統計指標
        statistics = self._calculate_revenue_statistics(backtest_results)

        return {
            'success': True,
            'periods_tested': len(backtest_results),
            'backtest_results': backtest_results,
            'statistics': statistics
        }

    def _run_eps_backtest(self, stock_id: str, periods: int) -> Dict:
        """執行EPS回測"""
        logger.info(f"Running EPS backtest for {periods//3} quarters")

        # EPS是季度資料，調整期數
        quarterly_periods = max(1, periods // 3)

        # 獲取歷史資料
        historical_data = self.db_manager.get_quarterly_financial_data(stock_id)

        if historical_data.empty or len(historical_data) < quarterly_periods + 4:
            return {
                'success': False,
                'error': 'Insufficient historical EPS data',
                'data_points': len(historical_data) if not historical_data.empty else 0
            }

        backtest_results = []

        # 逐季回測
        for i in range(quarterly_periods):
            # 計算回測時間點 (使用date欄位)
            if 'date' not in historical_data.columns:
                logger.error("No date column found in financial data")
                break

            latest_date = historical_data['date'].max()
            latest_quarter = self._date_to_quarter(latest_date)
            backtest_quarter = self._get_previous_quarter(latest_quarter, quarterly_periods - i)
            backtest_date = self.db_manager._quarter_to_date(backtest_quarter)

            if backtest_date is None:
                continue

            # 分割資料 (使用date欄位)
            train_data = historical_data[historical_data['date'] <= backtest_date]

            if len(train_data) < 4:  # 至少需要4季資料
                continue

            # 執行預測
            prediction_result = self._simulate_eps_prediction(
                stock_id, train_data, backtest_quarter
            )

            # 獲取實際結果
            target_quarter = self._get_next_quarter(backtest_quarter)
            actual_result = self._get_actual_eps_result(
                historical_data, target_quarter
            )

            if prediction_result and actual_result:
                # 計算準確度指標
                accuracy_metrics = self._calculate_eps_accuracy(
                    prediction_result, actual_result
                )

                # 標記異常季度（可能含非營業因素）
                abnormal_info = self._detect_eps_abnormal_quarter(
                    stock_id=stock_id,
                    target_quarter=target_quarter,
                    historical_data=historical_data,
                    prediction=prediction_result,
                    actual=actual_result
                )

                backtest_results.append({
                    'period': i + 1,
                    'backtest_quarter': backtest_quarter,
                    'target_quarter': target_quarter,
                    'prediction': prediction_result,
                    'actual': actual_result,
                    'accuracy': accuracy_metrics,
                    'abnormal': abnormal_info
                })

        # 計算統計指標
        statistics = self._calculate_eps_statistics(backtest_results)

        return {
            'success': True,
            'periods_tested': len(backtest_results),
            'backtest_results': backtest_results,
            'statistics': statistics
        }

    def _simulate_revenue_prediction(self, stock_id: str, train_data: pd.DataFrame,
                                   backtest_date: datetime) -> Optional[Dict]:
        """模擬營收預測 (基於歷史時間點)"""
        try:
            # 🔧 修復: 計算目標月份 (預測下個月)
            target_date = backtest_date + timedelta(days=30)
            target_month = target_date.strftime('%Y-%m')

            logger.info(f"[SIMULATION] Simulating prediction at {backtest_date.strftime('%Y-%m-%d')} | "
                       f"target_month={target_month} | training_samples={len(train_data)}")

            # 🔧 修復: 使用歷史時間點預測，限制資料範圍
            prediction = self.revenue_predictor.predict_monthly_growth_historical(
                stock_id, target_month, max_date=backtest_date
            )

            if prediction.get('success', True):
                return {
                    'growth_rate': prediction['growth_rate'],
                    'predicted_revenue': prediction['predicted_revenue'],
                    'confidence': prediction['confidence'],
                    'method_breakdown': prediction.get('method_breakdown', {}),
                    'ai_adjustment': prediction.get('ai_adjustment', {}),
                    'training_data_range': prediction.get('training_data_range', {}),
                    'model_retrained': prediction.get('model_retrained', False)
                }

            return None

        except Exception as e:
            logger.warning(f"Revenue prediction simulation failed: {e}")
            return None

    def _simulate_eps_prediction(self, stock_id: str, train_data: pd.DataFrame,
                               backtest_quarter: str) -> Optional[Dict]:
        """模擬EPS預測 (基於歷史時間點)"""
        try:
            # 計算目標季度
            target_quarter = self._get_next_quarter(backtest_quarter)

            # 轉換季度為日期限制
            backtest_date = self.db_manager._quarter_to_date(backtest_quarter)
            if backtest_date is None:
                return None

            # 🔧 修復: 使用歷史時間點預測，限制資料範圍
            prediction = self.eps_predictor.predict_quarterly_growth_historical(
                stock_id, target_quarter, max_date=backtest_date
            )

            if prediction.get('success', True):
                return {
                    'growth_rate': prediction['growth_rate'],
                    'predicted_eps': prediction['predicted_eps'],
                    'confidence': prediction['confidence'],
                    'method_breakdown': prediction.get('method_breakdown', {}),
                    'ai_adjustment': prediction.get('ai_adjustment', {}),
                    'training_data_range': prediction.get('training_data_range', {}),
                    'model_retrained': prediction.get('model_retrained', False)
                }

            return None

        except Exception as e:
            logger.warning(f"EPS prediction simulation failed: {e}")
            return None

    def _get_actual_revenue_result(self, historical_data: pd.DataFrame,
                                 target_date: datetime) -> Optional[Dict]:
        """
        獲取實際營收結果 (修復版)

        重要: 只使用回測時間點之前的資料，避免未來函數
        """
        try:
            target_month = target_date.strftime('%Y-%m')

            # 🔧 修復: 重新從資料庫查詢，確保資料的真實性和時間邏輯
            actual_data = self._get_actual_data_from_db(target_date)

            if not actual_data:
                logger.warning(f"No actual data available for {target_month} - cannot validate backtest")
                return {
                    'actual_revenue': None,
                    'actual_growth_rate': None,
                    'date': target_month,
                    'data_available': False,
                    'reason': f'No actual data for {target_month}'
                }

            actual_revenue = actual_data['revenue']
            actual_month = actual_data['actual_month']

            # 計算實際成長率 (與前一個月比較)
            prev_month_data = self._get_previous_month_data(target_date)

            if prev_month_data:
                prev_revenue = prev_month_data['revenue']
                actual_growth = (actual_revenue - prev_revenue) / prev_revenue
            else:
                actual_growth = 0.0

            return {
                'actual_revenue': actual_revenue,
                'actual_growth_rate': actual_growth,
                'date': target_month,
                'actual_month': actual_month,  # 實際資料的月份
                'data_available': True,
                'data_source': actual_data.get('source', 'database')
            }

        except Exception as e:
            logger.warning(f"Failed to get actual revenue result: {e}")
            return {
                'actual_revenue': None,
                'actual_growth_rate': None,
                'date': target_month,
                'actual_month': None,
                'data_available': False,
                'reason': f'Error: {str(e)}'
            }

    def _get_actual_data_from_db(self, target_date: datetime) -> Optional[Dict]:
        """
        從資料庫獲取實際資料，確保資料真實性

        Args:
            target_date: 目標日期

        Returns:
            實際資料字典或None
        """
        try:
            target_year = target_date.year
            target_month = target_date.month

            # 直接查詢資料庫
            query = """
            SELECT revenue_year, revenue_month, revenue
            FROM monthly_revenues
            WHERE stock_id = ? AND revenue_year = ? AND revenue_month = ?
            """

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (self.current_stock_id, target_year, target_month))
                result = cursor.fetchone()

                if result:
                    revenue_year, revenue_month, revenue = result
                    actual_month = f"{revenue_year}-{revenue_month:02d}"

                    logger.info(f"[ACTUAL_DATA] Found actual data for {target_date.strftime('%Y-%m')} | "
                               f"actual_month={actual_month} | revenue={revenue/1e8:.1f}億")

                    return {
                        'revenue': revenue,
                        'actual_month': actual_month,
                        'source': 'database_direct'
                    }
                else:
                    logger.warning(f"[ACTUAL_DATA] No actual data found for {target_date.strftime('%Y-%m')}")
                    return None

        except Exception as e:
            logger.error(f"Failed to get actual data from database: {e}")
            return None

    def _get_previous_month_data(self, target_date: datetime) -> Optional[Dict]:
        """獲取前一個月的資料"""
        try:
            # 計算前一個月
            if target_date.month == 1:
                prev_year = target_date.year - 1
                prev_month = 12
            else:
                prev_year = target_date.year
                prev_month = target_date.month - 1

            query = """
            SELECT revenue
            FROM monthly_revenues
            WHERE stock_id = ? AND revenue_year = ? AND revenue_month = ?
            """

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (self.current_stock_id, prev_year, prev_month))
                result = cursor.fetchone()

                if result:
                    return {'revenue': result[0]}
                else:
                    return None

        except Exception as e:
            logger.warning(f"Failed to get previous month data: {e}")
            return None

    def _get_actual_eps_result(self, historical_data: pd.DataFrame,
                             target_quarter: str) -> Optional[Dict]:
        """獲取實際EPS結果"""
        try:
            # 轉換季度為日期範圍
            target_date = self.db_manager._quarter_to_date(target_quarter)
            if target_date is None:
                return None

            # 找到對應日期的資料
            quarter_data = historical_data[
                historical_data['date'] == target_date
            ]

            if quarter_data.empty:
                # 嘗試找最接近的日期
                target_pd_date = pd.to_datetime(target_date)
                historical_data['date_diff'] = abs(pd.to_datetime(historical_data['date']) - target_pd_date)
                closest_data = historical_data.loc[historical_data['date_diff'].idxmin()]

                if closest_data['date_diff'].days > 90:  # 超過90天就認為沒有對應資料
                    return None

                actual_eps = closest_data['eps']
                actual_date = closest_data['date']
            else:
                actual_eps = quarter_data['eps'].iloc[0]
                actual_date = quarter_data['date'].iloc[0]

            # 計算實際成長率 (與去年同期比較)
            year, quarter_num = target_quarter.split('-Q')
            prev_year_quarter = f"{int(year)-1}-Q{quarter_num}"
            prev_year_date = self.db_manager._quarter_to_date(prev_year_quarter)

            if prev_year_date:
                prev_year_data = historical_data[
                    historical_data['date'] == prev_year_date
                ]

                if not prev_year_data.empty:
                    prev_eps = prev_year_data['eps'].iloc[0]
                    if prev_eps != 0:
                        actual_growth = (actual_eps - prev_eps) / abs(prev_eps)
                    else:
                        actual_growth = 0.0
                else:
                    actual_growth = 0.0
            else:
                actual_growth = 0.0

            return {
                'actual_eps': actual_eps,
                'actual_growth_rate': actual_growth,
                'quarter': target_quarter,
                'actual_date': str(actual_date)
            }

        except Exception as e:
            logger.warning(f"Failed to get actual EPS result: {e}")
            return None

    def _date_to_quarter(self, date_str: str) -> str:
        """將日期轉換為季度格式"""
        try:
            if isinstance(date_str, str):
                date_obj = pd.to_datetime(date_str)
            else:
                date_obj = date_str

            year = date_obj.year
            month = date_obj.month

            if month <= 3:
                quarter = 1
            elif month <= 6:
                quarter = 2
            elif month <= 9:
                quarter = 3
            else:
                quarter = 4

            return f"{year}-Q{quarter}"

        except Exception as e:
            logger.warning(f"Failed to convert date to quarter: {e}")
            return "2024-Q1"  # 預設值

    def _calculate_revenue_accuracy(self, prediction: Dict, actual: Dict) -> Dict:
        """計算營收預測準確度指標"""
        try:
            pred_growth = prediction['growth_rate']
            actual_growth = actual['actual_growth_rate']

            pred_revenue = prediction['predicted_revenue']
            actual_revenue = actual['actual_revenue']

            # 成長率誤差
            growth_error = abs(pred_growth - actual_growth)
            growth_mape = growth_error / (abs(actual_growth) + 1e-8) * 100

            # 營收金額誤差
            revenue_error = abs(pred_revenue - actual_revenue)
            revenue_mape = revenue_error / actual_revenue * 100

            # 方向準確性
            direction_correct = (pred_growth * actual_growth) >= 0

            return {
                'growth_rate_error': growth_error,
                'growth_rate_mape': growth_mape,
                'revenue_error': revenue_error,
                'revenue_mape': revenue_mape,
                'direction_correct': direction_correct,
                'confidence': prediction.get('confidence', 'Unknown')
            }

        except Exception as e:
            logger.warning(f"Failed to calculate revenue accuracy: {e}")
            return {}

    def _calculate_eps_accuracy(self, prediction: Dict, actual: Dict) -> Dict:
        """計算EPS預測準確度指標"""
        try:
            pred_growth = prediction['growth_rate']
            actual_growth = actual['actual_growth_rate']

            pred_eps = prediction['predicted_eps']
            actual_eps = actual['actual_eps']

            # 成長率誤差
            growth_error = abs(pred_growth - actual_growth)
            growth_mape = growth_error / (abs(actual_growth) + 1e-8) * 100

            # EPS金額誤差
            eps_error = abs(pred_eps - actual_eps)
            eps_mape = eps_error / abs(actual_eps) * 100

            # 方向準確性
            direction_correct = (pred_growth * actual_growth) >= 0

            return {
                'growth_rate_error': growth_error,
                'growth_rate_mape': growth_mape,
                'eps_error': eps_error,
                'eps_mape': eps_mape,
                'direction_correct': direction_correct,
                'confidence': prediction.get('confidence', 'Unknown')
            }

        except Exception as e:
            logger.warning(f"Failed to calculate EPS accuracy: {e}")
            return {}

    def _calculate_revenue_statistics(self, backtest_results: List[Dict]) -> Dict:
        """計算營收回測統計指標"""
        if not backtest_results:
            return {}

        try:
            # 提取準確度指標
            growth_errors = [r['accuracy']['growth_rate_error'] for r in backtest_results
                           if 'accuracy' in r and 'growth_rate_error' in r['accuracy']]
            growth_mapes = [r['accuracy']['growth_rate_mape'] for r in backtest_results
                          if 'accuracy' in r and 'growth_rate_mape' in r['accuracy']]
            revenue_mapes = [r['accuracy']['revenue_mape'] for r in backtest_results
                           if 'accuracy' in r and 'revenue_mape' in r['accuracy']]
            direction_correct = [r['accuracy']['direction_correct'] for r in backtest_results
                               if 'accuracy' in r and 'direction_correct' in r['accuracy']]

            # 計算統計指標
            stats = {
                'total_periods': len(backtest_results),
                'avg_growth_error': np.mean(growth_errors) if growth_errors else 0,
                'avg_growth_mape': np.mean(growth_mapes) if growth_mapes else 0,
                'avg_revenue_mape': np.mean(revenue_mapes) if revenue_mapes else 0,
                'direction_accuracy': np.mean(direction_correct) if direction_correct else 0,
                'rmse_growth': np.sqrt(np.mean([e**2 for e in growth_errors])) if growth_errors else 0
            }

            # 信心水準分析
            confidence_analysis = self._analyze_confidence_performance(backtest_results)
            stats['confidence_analysis'] = confidence_analysis

            return stats

        except Exception as e:
            logger.warning(f"Failed to calculate revenue statistics: {e}")
            return {}

    def _calculate_eps_statistics(self, backtest_results: List[Dict]) -> Dict:
        """計算EPS回測統計指標（新增：營業/總體分離與異常過濾）"""
        if not backtest_results:
            return {}

        try:
            # 分離正常季度與異常季度
            normal_results = [r for r in backtest_results if not r.get('abnormal', {}).get('is_abnormal', False)]
            abnormal_results = [r for r in backtest_results if r.get('abnormal', {}).get('is_abnormal', False)]

            def _stats(results: List[Dict]) -> Dict:
                if not results:
                    return {
                        'total_periods': 0,
                        'avg_growth_error': 0,
                        'avg_growth_mape': 0,
                        'avg_eps_mape': 0,
                        'direction_accuracy': 0,
                        'rmse_growth': 0
                    }
                growth_errors = [r['accuracy']['growth_rate_error'] for r in results
                                 if 'accuracy' in r and 'growth_rate_error' in r['accuracy']]
                growth_mapes = [r['accuracy']['growth_rate_mape'] for r in results
                                if 'accuracy' in r and 'growth_rate_mape' in r['accuracy']]
                eps_mapes = [r['accuracy']['eps_mape'] for r in results
                             if 'accuracy' in r and 'eps_mape' in r['accuracy']]
                direction_correct = [r['accuracy']['direction_correct'] for r in results
                                     if 'accuracy' in r and 'direction_correct' in r['accuracy']]
                return {
                    'total_periods': len(results),
                    'avg_growth_error': np.mean(growth_errors) if growth_errors else 0,
                    'avg_growth_mape': np.mean(growth_mapes) if growth_mapes else 0,
                    'avg_eps_mape': np.mean(eps_mapes) if eps_mapes else 0,
                    'direction_accuracy': np.mean(direction_correct) if direction_correct else 0,
                    'rmse_growth': np.sqrt(np.mean([e**2 for e in growth_errors])) if growth_errors else 0
                }

            # 原統計（總體）
            overall_stats = _stats(backtest_results)
            # 營業統計（排除異常季度）
            operating_stats = _stats(normal_results)
            # 異常統計（僅異常季度）
            abnormal_stats = _stats(abnormal_results)

            # 信心水準分析（用總體）
            confidence_analysis = self._analyze_confidence_performance(backtest_results)

            return {
                'overall': overall_stats,
                'operating_only': operating_stats,
                'abnormal_only': abnormal_stats,
                'confidence_analysis': confidence_analysis,
                'abnormal_quarters': [r.get('abnormal') for r in abnormal_results]
            }

        except Exception as e:
            logger.warning(f"Failed to calculate EPS statistics: {e}")
            return {}

    def _analyze_confidence_performance(self, backtest_results: List[Dict]) -> Dict:
        """分析不同信心水準的表現"""
        try:
            confidence_groups = {'High': [], 'Medium': [], 'Low': []}

            for result in backtest_results:
                confidence = result.get('accuracy', {}).get('confidence', 'Unknown')
                if confidence in confidence_groups:
                    confidence_groups[confidence].append(result['accuracy'])

            analysis = {}
            for conf_level, results in confidence_groups.items():
                if results:
                    growth_errors = [r.get('growth_rate_error', 0) for r in results]
                    direction_correct = [r.get('direction_correct', False) for r in results]

                    analysis[conf_level] = {
                        'count': len(results),
                        'avg_error': np.mean(growth_errors),
                        'direction_accuracy': np.mean(direction_correct)
                    }

            return analysis

        except Exception as e:
            logger.warning(f"Failed to analyze confidence performance: {e}")
            return {}

    def _calculate_overall_statistics(self, results: Dict) -> Dict:
        """計算整體統計指標（新增：EPS營業/總體分離）"""
        try:
            overall_stats = {
                'revenue': results.get('revenue', {}).get('statistics', {}),
                'eps': results.get('eps', {}).get('statistics', {}),
                'combined_performance': {}
            }

            # 計算綜合表現
            revenue_stats = overall_stats['revenue']
            eps_stats = overall_stats['eps']

            if revenue_stats and eps_stats:
                # 兼容舊/新統計格式
                eps_direction = 0
                eps_total = 0
                if 'direction_accuracy' in eps_stats:
                    eps_direction = eps_stats.get('direction_accuracy', 0)
                    eps_total = eps_stats.get('total_periods', 0)
                elif 'operating_only' in eps_stats:
                    eps_direction = eps_stats['operating_only'].get('direction_accuracy', 0)
                    eps_total = eps_stats['operating_only'].get('total_periods', 0)

                combined = {
                    'avg_direction_accuracy': (
                        revenue_stats.get('direction_accuracy', 0) + eps_direction
                    ) / 2,
                    'total_predictions': (
                        revenue_stats.get('total_periods', 0) + eps_total
                    )
                }
                overall_stats['combined_performance'] = combined

            return overall_stats

        except Exception as e:
            logger.warning(f"Failed to calculate overall statistics: {e}")
            return {}

    def _generate_improvement_suggestions(self, backtest_results: Dict) -> List[str]:
        """生成改進建議"""
        suggestions = []

        try:
            revenue_stats = backtest_results.get('results', {}).get('revenue', {}).get('statistics', {})
            eps_stats = backtest_results.get('results', {}).get('eps', {}).get('statistics', {})

            # 營收預測改進建議
            if revenue_stats:
                revenue_mape = revenue_stats.get('avg_revenue_mape', 0)
                direction_acc = revenue_stats.get('direction_accuracy', 0)

                if revenue_mape > 15:
                    suggestions.append("營收預測誤差較大，建議調整財務公式權重或增加更多歷史資料")

                if direction_acc < 0.6:
                    suggestions.append("營收趨勢方向預測準確度偏低，建議強化趨勢分析模型")

            # EPS預測改進建議
            if eps_stats:
                eps_mape = eps_stats.get('avg_eps_mape', 0)
                direction_acc = eps_stats.get('direction_accuracy', 0)

                if eps_mape > 20:
                    suggestions.append("EPS預測誤差較大，建議調整利潤率分析方法")

                if direction_acc < 0.6:
                    suggestions.append("EPS趨勢方向預測準確度偏低，建議加強營收與EPS關聯性分析")

            # AI模型改進建議
            overall_stats = backtest_results.get('overall_statistics', {})
            combined_perf = overall_stats.get('combined_performance', {})

            if combined_perf.get('avg_direction_accuracy', 0) < 0.65:
                suggestions.append("整體預測方向準確度偏低，建議重新訓練AI調整模型")

            # 信心水準分析建議
            revenue_conf = revenue_stats.get('confidence_analysis', {})
            eps_conf = eps_stats.get('confidence_analysis', {})

            if revenue_conf.get('High', {}).get('count', 0) < 3:
                suggestions.append("高信心營收預測數量不足，建議增加資料品質檢查機制")

            if eps_conf.get('High', {}).get('count', 0) < 2:
                suggestions.append("高信心EPS預測數量不足，建議優化EPS預測模型")

            if not suggestions:
                suggestions.append("預測模型表現良好，建議持續監控並定期更新模型")

            return suggestions

        except Exception as e:
            logger.warning(f"Failed to generate improvement suggestions: {e}")
            return ["無法生成改進建議，請檢查回測結果"]

    def _get_previous_quarter(self, quarter: str, periods_back: int) -> str:
        """獲取前N個季度"""
        try:
            year, q = quarter.split('-Q')
            year = int(year)
            q = int(q)

            total_quarters_back = periods_back
            years_back = total_quarters_back // 4
            quarters_back = total_quarters_back % 4

            new_year = year - years_back
            new_quarter = q - quarters_back

            if new_quarter <= 0:
                new_year -= 1
                new_quarter += 4

            return f"{new_year}-Q{new_quarter}"

        except Exception as e:
            logger.warning(f"Failed to calculate previous quarter: {e}")
            return quarter

    def _get_next_quarter(self, quarter: str) -> str:
        """獲取下一個季度"""
        try:
            year, q = quarter.split('-Q')
            year = int(year)
            q = int(q)

            if q == 4:
                return f"{year + 1}-Q1"
            else:
                return f"{year}-Q{q + 1}"

        except Exception as e:
            logger.warning(f"Failed to calculate next quarter: {e}")
            return quarter

    def _detect_eps_abnormal_quarter(self, stock_id: str, target_quarter: str,
                                     historical_data: pd.DataFrame, prediction: Dict, actual: Dict) -> Dict:
        """檢測EPS異常季度（非營業因素）
        規則：
        - 淨利率QoQ變化 > 5 個百分點
        - EPS QoQ變化 > 100% 且 營收季度變化 < 20%
        返回：{'is_abnormal': bool, 'reason': str, 'net_margin': float, 'prev_net_margin': float}
        """
        try:
            # 取得財務比率（含淨利率）
            ratios = self.db_manager.get_financial_ratios(stock_id)
            net_margin = None
            prev_net_margin = None
            reason_parts = []
            is_abnormal = False

            # 解析季度
            year, q = target_quarter.split('-Q')
            year = int(year)
            q = int(q)

            def quarter_to_date(y: int, qq: int) -> str:
                month = {1: '03', 2: '06', 3: '09', 4: '12'}[qq]
                day = '30' if month in ['06', '09'] else '31'
                return f"{y}-{month}-{day}"

            target_date = quarter_to_date(year, q)
            prev_q = 4 if q == 1 else q - 1
            prev_y = year - 1 if q == 1 else year
            prev_date = quarter_to_date(prev_y, prev_q)

            if not ratios.empty:
                r_t = ratios[ratios['date'] == target_date]
                r_p = ratios[ratios['date'] == prev_date]
                if not r_t.empty and not r_p.empty:
                    net_margin = float(r_t.iloc[0].get('net_margin') or 0)
                    prev_net_margin = float(r_p.iloc[0].get('net_margin') or 0)
                    if prev_net_margin is not None and abs(net_margin - prev_net_margin) > 5:
                        is_abnormal = True
                        reason_parts.append(f"淨利率QoQ變化{net_margin - prev_net_margin:+.1f}pp")

            # EPS QoQ vs 營收季變化
            eps_qoq = None
            rev_q_change = None
            try:
                # EPS QoQ
                prev_eps_row = historical_data[historical_data['date'] == prev_date]
                if not prev_eps_row.empty:
                    prev_eps = float(prev_eps_row['eps'].iloc[0])
                    if prev_eps != 0:
                        eps_qoq = (actual['actual_eps'] - prev_eps) / abs(prev_eps) * 100
                        if eps_qoq > 100:
                            # 計算營收季度變化
                            monthly = self.db_manager.get_monthly_revenue(stock_id)
                            if not monthly.empty:
                                def quarter_months(y, qq):
                                    if qq == 1:
                                        return [f"{y}-01", f"{y}-02", f"{y}-03"]
                                    if qq == 2:
                                        return [f"{y}-04", f"{y}-05", f"{y}-06"]
                                    if qq == 3:
                                        return [f"{y}-07", f"{y}-08", f"{y}-09"]
                                    return [f"{y}-10", f"{y}-11", f"{y}-12"]
                                curr_months = quarter_months(year, q)
                                prev_months = quarter_months(prev_y, prev_q)
                                rev_curr = monthly[monthly['date'].isin(curr_months)]['revenue'].sum()
                                rev_prev = monthly[monthly['date'].isin(prev_months)]['revenue'].sum()
                                if rev_prev > 0:
                                    rev_q_change = (rev_curr - rev_prev) / rev_prev * 100
                                    if eps_qoq > 100 and abs(rev_q_change) < 20:
                                        is_abnormal = True
                                        reason_parts.append(f"EPS QoQ {eps_qoq:.1f}% vs 營收{rev_q_change:+.1f}%")
            except Exception:
                pass

            return {
                'is_abnormal': is_abnormal,
                'reason': '; '.join(reason_parts) if reason_parts else None,
                'net_margin': net_margin,
                'prev_net_margin': prev_net_margin,
                'eps_qoq_pct': eps_qoq,
                'revenue_quarter_change_pct': rev_q_change
            }
        except Exception as e:
            logger.warning(f"Failed to detect abnormal quarter: {e}")
            return {'is_abnormal': False}

    @log_execution
    def optimize_ai_model(self, stock_id: str, backtest_results: Dict) -> Dict:
        """基於回測結果優化AI模型"""
        logger.info(f"Optimizing AI model based on backtest results for {stock_id}")

        try:
            # 分析回測結果
            revenue_stats = backtest_results.get('results', {}).get('revenue', {}).get('statistics', {})
            eps_stats = backtest_results.get('results', {}).get('eps', {}).get('statistics', {})

            optimization_result = {
                'stock_id': stock_id,
                'optimization_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'improvements': []
            }

            # 檢查是否需要重新訓練AI模型
            revenue_direction_acc = revenue_stats.get('direction_accuracy', 0)
            eps_direction_acc = eps_stats.get('direction_accuracy', 0)

            if revenue_direction_acc < 0.6 or eps_direction_acc < 0.6:
                logger.info("Direction accuracy below threshold, retraining AI model")

                # 重新訓練通用AI模型
                retrain_result = self.ai_model.train_model(retrain=True)
                optimization_result['improvements'].append({
                    'type': 'ai_model_retrain',
                    'result': retrain_result,
                    'reason': 'Low direction accuracy'
                })

            # 檢查是否需要訓練股票專用模型
            overall_mape = (revenue_stats.get('avg_revenue_mape', 0) +
                          eps_stats.get('avg_eps_mape', 0)) / 2

            if overall_mape > 18:
                logger.info("High prediction error, suggesting stock-specific model")
                optimization_result['improvements'].append({
                    'type': 'stock_specific_model_suggestion',
                    'reason': f'High overall MAPE: {overall_mape:.2f}%',
                    'recommendation': f'建議為股票 {stock_id} 訓練專用AI模型'
                })

            return optimization_result

        except Exception as e:
            logger.error(f"AI model optimization failed: {e}")
            return {
                'stock_id': stock_id,
                'error': str(e),
                'optimization_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
