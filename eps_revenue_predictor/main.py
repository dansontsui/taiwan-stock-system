#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPS Revenue Predictor - Main Entry Point
EPS與營收成長預測系統主程式
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 設定編碼以支援中文輸出
if sys.platform.startswith('win'):
    # 設定控制台編碼
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        # Python 3.6 以下版本的備用方案
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 導入模組
from config.settings import PREDICTION_CONFIG, ensure_directories
from src.data.database_manager import DatabaseManager
from src.predictors.revenue_predictor import RevenuePredictor
from src.predictors.eps_predictor import EPSPredictor
from src.models.adjustment_model import AIAdjustmentModel
from src.utils.logger import get_logger

# 確保目錄存在
ensure_directories()

# 設置日誌
logger = get_logger('main')

class EPSRevenuePredictor:
    """EPS營收預測系統主類別"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.revenue_predictor = RevenuePredictor(self.db_manager)
        self.eps_predictor = EPSPredictor(self.db_manager)
        self.ai_model = AIAdjustmentModel(self.db_manager)
        self.config = PREDICTION_CONFIG

        logger.info("EPS與營收預測系統已初始化")
    
    def predict_stock(self, stock_id: str, prediction_type: str = 'revenue') -> dict:
        """
        預測單一股票
        
        Args:
            stock_id: 股票代碼
            prediction_type: 預測類型 ('revenue' 或 'eps')
            
        Returns:
            預測結果字典
        """
        logger.info(f"Starting prediction for stock {stock_id}, type: {prediction_type}")
        
        try:
            if prediction_type == 'revenue':
                return self._predict_revenue_with_ai(stock_id)
            elif prediction_type == 'eps':
                return self._predict_eps_with_ai(stock_id)
            else:
                raise ValueError(f"Unsupported prediction type: {prediction_type}")
                
        except Exception as e:
            logger.error(f"Prediction failed for {stock_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'stock_id': stock_id,
                'prediction_type': prediction_type
            }
    
    def _predict_revenue_with_ai(self, stock_id: str) -> dict:
        """營收預測 (財務公式 + AI調整)"""
        
        # 步驟1: 財務公式預測
        formula_result = self.revenue_predictor.predict_monthly_growth(stock_id)
        
        if not formula_result.get('success', True):
            return formula_result
        
        # 步驟2: AI調整
        base_prediction = formula_result['growth_rate']
        
        # 確保AI模型可用
        if not self.ai_model.is_trained:
            train_result = self.ai_model.train_model(retrain=False)
            if train_result['status'] not in ['success', 'loaded_existing']:
                logger.warning("AI model not available, using formula-only prediction")
                ai_adjustment = {
                    'adjustment_factor': 0.0,
                    'adjusted_prediction': base_prediction,
                    'confidence': 'N/A',
                    'reason': 'ai_model_unavailable'
                }
            else:
                ai_adjustment = self.ai_model.predict_adjustment_factor(
                    stock_id, base_prediction, 'revenue'
                )
        else:
            ai_adjustment = self.ai_model.predict_adjustment_factor(
                stock_id, base_prediction, 'revenue'
            )
        
        # 步驟3: 整合預測
        formula_weight = self.config['formula_weight']
        ai_weight = self.config['ai_adjustment_weight']
        
        if ai_adjustment['adjustment_factor'] != 0.0:
            final_prediction = (base_prediction * formula_weight + 
                              ai_adjustment['adjusted_prediction'] * ai_weight)
        else:
            final_prediction = base_prediction
        
        # 計算最終營收金額
        latest_revenue = formula_result['latest_revenue']
        final_revenue = latest_revenue * (1 + final_prediction)
        
        # 整合結果
        result = {
            'success': True,
            'stock_id': stock_id,
            'prediction_type': 'revenue',
            'final_prediction': {
                'growth_rate': final_prediction,
                'predicted_revenue': final_revenue,
                'confidence': self._calculate_overall_confidence(
                    formula_result['confidence'], ai_adjustment['confidence']
                )
            },
            'formula_prediction': {
                'growth_rate': base_prediction,
                'predicted_revenue': formula_result['predicted_revenue'],
                'confidence': formula_result['confidence'],
                'weight': formula_weight
            },
            'ai_adjustment': {
                'adjustment_factor': ai_adjustment['adjustment_factor'],
                'adjusted_prediction': ai_adjustment['adjusted_prediction'],
                'confidence': ai_adjustment['confidence'],
                'weight': ai_weight
            },
            'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'target_month': formula_result.get('target_month'),
            'risk_factors': formula_result.get('risk_factors', [])
        }
        
        logger.info(f"營收預測完成 {stock_id}: {final_prediction:.2%}")
        
        return result
    
    def _predict_eps_with_ai(self, stock_id: str) -> dict:
        """EPS預測 (財務公式 + AI調整)"""
        try:
            # 使用EPS預測器進行預測
            eps_result = self.eps_predictor.predict_quarterly_growth(stock_id)

            if not eps_result.get('success', True):
                return eps_result

            # 格式化結果
            final_prediction = eps_result['growth_rate']
            predicted_eps = eps_result['predicted_eps']

            result = {
                'success': True,
                'predicted_eps': predicted_eps,
                'growth_rate': final_prediction,
                'confidence': eps_result['confidence'],
                'formula_prediction': eps_result.get('formula_prediction', {}),
                'ai_adjustment': eps_result.get('ai_adjustment', {}),
                'integration_weights': eps_result.get('integration_weights', {}),
                'stock_id': stock_id,
                'prediction_type': 'eps',
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'target_quarter': eps_result.get('target_quarter'),
                'risk_factors': eps_result.get('risk_factors', [])
            }

            logger.info(f"EPS預測完成 {stock_id}: {final_prediction:.2%}")

            return result

        except Exception as e:
            logger.error(f"EPS預測失敗 {stock_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'stock_id': stock_id,
                'prediction_type': 'eps'
            }
    
    def _calculate_overall_confidence(self, formula_confidence: str, ai_confidence: str) -> str:
        """計算整體信心水準"""
        confidence_scores = {'High': 3, 'Medium': 2, 'Low': 1, 'N/A': 1}
        
        formula_score = confidence_scores.get(formula_confidence, 1)
        ai_score = confidence_scores.get(ai_confidence, 1)
        
        # 加權平均
        overall_score = (formula_score * self.config['formula_weight'] + 
                        ai_score * self.config['ai_adjustment_weight'])
        
        if overall_score >= 2.5:
            return 'High'
        elif overall_score >= 1.8:
            return 'Medium'
        else:
            return 'Low'
    
    def batch_predict(self, stock_list: list, prediction_type: str = 'revenue') -> dict:
        """批量預測"""
        logger.info(f"Starting batch prediction for {len(stock_list)} stocks")
        
        results = []
        successful_predictions = 0
        
        for stock_id in stock_list:
            try:
                result = self.predict_stock(stock_id, prediction_type)
                results.append(result)
                
                if result.get('success', False):
                    successful_predictions += 1
                    
            except Exception as e:
                logger.error(f"Batch prediction failed for {stock_id}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'stock_id': stock_id,
                    'prediction_type': prediction_type
                })
        
        batch_result = {
            'total_stocks': len(stock_list),
            'successful_predictions': successful_predictions,
            'success_rate': successful_predictions / len(stock_list),
            'results': results,
            'batch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"Batch prediction completed: {successful_predictions}/{len(stock_list)} successful")
        
        return batch_result

def create_argument_parser():
    """創建命令列參數解析器"""
    parser = argparse.ArgumentParser(description='EPS與營收成長預測系統')

    parser.add_argument('--stock', '-s', type=str,
                       help='要預測的股票代碼 (例如: 2385)')

    parser.add_argument('--type', '-t', type=str, choices=['revenue', 'eps'],
                       default='revenue', help='預測類型 (revenue=營收, eps=每股盈餘)')

    parser.add_argument('--batch', '-b', type=str,
                       help='批量預測股票清單檔案')

    parser.add_argument('--test', action='store_true',
                       help='執行2385群光電子完整測試 (營收+EPS)')

    parser.add_argument('--train-ai', action='store_true',
                       help='訓練AI調整模型')

    return parser

def main():
    """主函數"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("🚀 EPS與營收成長預測系統")
    print("=" * 60)

    # 初始化系統
    try:
        predictor = EPSRevenuePredictor()
        print("✅ 系統初始化成功")
    except Exception as e:
        print(f"❌ 系統初始化失敗: {e}")
        return 1
    
    # 執行相應操作
    try:
        if args.train_ai:
            print("\n🤖 正在訓練AI調整模型...")
            result = predictor.ai_model.train_model(retrain=True)
            print(f"訓練結果: {result['status']}")

        elif args.test:
            print(f"\n🧪 執行2385群光電子完整測試...")

            # 測試營收預測
            print(f"\n📊 測試營收預測...")
            revenue_result = predictor.predict_stock('2385', 'revenue')

            if revenue_result['success']:
                print("✅ 營收預測成功")
                final = revenue_result['final_prediction']
                print(f"📈 預測成長率: {final['growth_rate']:.2%}")
                print(f"💰 預測營收: {final['predicted_revenue']:,.0f} 千元新台幣")
                print(f"🎯 信心水準: {final['confidence']}")
            else:
                print(f"❌ 營收預測失敗: {revenue_result['error']}")

            # 測試EPS預測
            print(f"\n📊 測試EPS預測...")
            eps_result = predictor.predict_stock('2385', 'eps')

            if eps_result['success']:
                print("✅ EPS預測成功")
                print(f"📈 預測EPS成長率: {eps_result['growth_rate']:.2%}")
                print(f"💰 預測EPS: {eps_result['predicted_eps']:.3f} 元")
                print(f"🎯 信心水準: {eps_result['confidence']}")
            else:
                print(f"❌ EPS預測失敗: {eps_result['error']}")

            # 測試總結
            revenue_success = revenue_result['success']
            eps_success = eps_result['success']

            print(f"\n📋 測試總結:")
            print(f"營收預測: {'✅ 成功' if revenue_success else '❌ 失敗'}")
            print(f"EPS預測: {'✅ 成功' if eps_success else '❌ 失敗'}")

            if revenue_success and eps_success:
                print("🎉 所有測試通過！系統運作正常。")
            else:
                print("⚠️  部分測試失敗，請檢查系統狀態。")
                
        elif args.stock:
            print(f"\n📊 正在預測股票 {args.stock}...")
            result = predictor.predict_stock(args.stock, args.type)

            if result['success']:
                print("✅ 預測成功")

                if args.type == 'revenue':
                    final = result['final_prediction']
                    print(f"📈 預測成長率: {final['growth_rate']:.2%}")
                    print(f"💰 預測營收: {final['predicted_revenue']:,.0f} 千元新台幣")
                    print(f"🎯 信心水準: {final['confidence']}")
                elif args.type == 'eps':
                    print(f"📈 預測EPS成長率: {result['growth_rate']:.2%}")
                    print(f"💰 預測EPS: {result['predicted_eps']:.3f} 元")
                    print(f"🎯 信心水準: {result['confidence']}")
            else:
                print(f"❌ 預測失敗: {result['error']}")
                
        elif args.batch:
            print(f"\n📦 從檔案批量預測: {args.batch}")
            # TODO: 實作批量預測檔案讀取
            print("❌ 批量預測功能尚未實作")

        else:
            # 互動模式
            print("\n🎯 互動模式")
            print("可用指令:")
            print("  predict <股票代碼> - 預測單一股票")
            print("  test - 執行2385測試")
            print("  train - 訓練AI模型")
            print("  quit - 離開")
            
            while True:
                try:
                    command = input("\n> ").strip().lower()
                    
                    if command == 'quit':
                        print("👋 再見！")
                        break
                    elif command == 'test':
                        print("🧪 執行測試...")
                        result = predictor.predict_stock('2385', 'revenue')
                        if result['success']:
                            final = result['final_prediction']
                            print(f"📈 成長率: {final['growth_rate']:.2%}, 🎯 信心水準: {final['confidence']}")
                        else:
                            print(f"❌ 失敗: {result['error']}")
                    elif command == 'train':
                        print("🤖 訓練AI模型...")
                        result = predictor.ai_model.train_model(retrain=True)
                        print(f"訓練結果: {result['status']}")
                    elif command.startswith('predict '):
                        stock_id = command.split()[1]
                        print(f"📊 預測股票 {stock_id}...")
                        result = predictor.predict_stock(stock_id, 'revenue')
                        if result['success']:
                            final = result['final_prediction']
                            print(f"📈 成長率: {final['growth_rate']:.2%}, 🎯 信心水準: {final['confidence']}")
                        else:
                            print(f"❌ 失敗: {result['error']}")
                    else:
                        print("❓ 未知指令。輸入 'quit' 離開。")
                        
                except KeyboardInterrupt:
                    print("\n👋 再見！")
                    break
                except Exception as e:
                    print(f"❌ 錯誤: {e}")

        print("\n✅ 程式執行完成")
        return 0

    except Exception as e:
        print(f"\n❌ 程式執行失敗: {e}")
        logger.error(f"Main program error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
