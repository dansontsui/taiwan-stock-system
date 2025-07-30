#!/usr/bin/env python3
"""
潛力股預測系統主程式

提供命令列介面來執行各種功能：
- 特徵生成
- 模型訓練
- 預測執行
- 結果分析

使用方法:
    python main.py --help
    python main.py generate-features --stock-ids 2330,2317 --date 2024-06-30
    python main.py train-models --features-file features.csv --targets-file targets.csv
    python main.py predict --stock-ids 2330,2317 --model lightgbm
    python main.py ranking --top-k 50
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 添加專案路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from src.features.feature_engineering import FeatureEngineer
    from src.features.target_generator import TargetGenerator
    from src.models.model_trainer import ModelTrainer
    from src.models.predictor import Predictor
    from src.utils.database import DatabaseManager
    from src.utils.logger import setup_logger
    from config.config import ensure_directories, get_date_ranges
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    print("請確保在 potential_stock_predictor 目錄下執行此程式")
    sys.exit(1)

# 設置日誌
logger = setup_logger('potential_stock_predictor')

def setup_argparse():
    """設置命令列參數解析"""
    parser = argparse.ArgumentParser(
        description='潛力股預測系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 生成特徵
  python main.py generate-features --date 2024-06-30
  
  # 訓練模型
  python main.py train-models
  
  # 執行預測
  python main.py predict --model lightgbm
  
  # 生成排行榜
  python main.py ranking --top-k 50
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 生成特徵命令
    features_parser = subparsers.add_parser('generate-features', help='生成特徵')
    features_parser.add_argument('--stock-ids', type=str, help='股票代碼列表（逗號分隔）')
    features_parser.add_argument('--date', type=str, help='特徵計算日期 (YYYY-MM-DD)')
    features_parser.add_argument('--output', type=str, help='輸出檔案路徑')
    
    # 生成目標變數命令
    targets_parser = subparsers.add_parser('generate-targets', help='生成目標變數')
    targets_parser.add_argument('--stock-ids', type=str, help='股票代碼列表（逗號分隔）')
    targets_parser.add_argument('--start-date', type=str, help='開始日期 (YYYY-MM-DD)')
    targets_parser.add_argument('--end-date', type=str, help='結束日期 (YYYY-MM-DD)')
    targets_parser.add_argument('--frequency', type=str, choices=['monthly', 'quarterly'], 
                               default='quarterly', help='頻率')
    targets_parser.add_argument('--output', type=str, help='輸出檔案路徑')
    
    # 訓練模型命令
    train_parser = subparsers.add_parser('train-models', help='訓練模型')
    train_parser.add_argument('--features-file', type=str, help='特徵檔案路徑')
    train_parser.add_argument('--targets-file', type=str, help='目標變數檔案路徑')
    train_parser.add_argument('--models', type=str, help='模型類型列表（逗號分隔）')
    
    # 預測命令
    predict_parser = subparsers.add_parser('predict', help='執行預測')
    predict_parser.add_argument('--stock-ids', type=str, help='股票代碼列表（逗號分隔）')
    predict_parser.add_argument('--date', type=str, help='預測日期 (YYYY-MM-DD)')
    predict_parser.add_argument('--model', type=str, default='lightgbm', help='模型類型')
    predict_parser.add_argument('--output', type=str, help='輸出檔案路徑')
    
    # 排行榜命令
    ranking_parser = subparsers.add_parser('ranking', help='生成潛力股排行榜')
    ranking_parser.add_argument('--date', type=str, help='預測日期 (YYYY-MM-DD)')
    ranking_parser.add_argument('--model', type=str, default='lightgbm', help='模型類型')
    ranking_parser.add_argument('--top-k', type=int, default=50, help='返回前K個股票')
    ranking_parser.add_argument('--output', type=str, help='輸出檔案路徑')
    
    # 測試命令
    test_parser = subparsers.add_parser('test', help='執行系統測試')
    test_parser.add_argument('--module', type=str, help='測試模組名稱')
    
    return parser

def generate_features_command(args):
    """執行特徵生成命令"""
    logger.info("開始生成特徵...")
    
    # 初始化
    db_manager = DatabaseManager()
    feature_engineer = FeatureEngineer(db_manager)
    
    # 處理參數
    if args.stock_ids:
        stock_ids = args.stock_ids.split(',')
    else:
        stock_list = db_manager.get_stock_list(exclude_patterns=['00'])
        stock_ids = stock_list['stock_id'].tolist()
    
    date = args.date or datetime.now().strftime('%Y-%m-%d')
    
    # 生成特徵
    features_df = feature_engineer.generate_batch_features(stock_ids, date)
    
    if features_df.empty:
        logger.error("沒有生成任何特徵")
        return
    
    # 儲存結果
    output_path = args.output or f"data/features/features_{date}.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)
    
    logger.info(f"特徵生成完成，儲存到: {output_path}")
    logger.info(f"生成 {len(features_df)} 個樣本，{len(features_df.columns)-2} 個特徵")

def generate_targets_command(args):
    """執行目標變數生成命令"""
    logger.info("開始生成目標變數...")
    
    # 初始化
    db_manager = DatabaseManager()
    target_generator = TargetGenerator(db_manager)
    
    # 處理參數
    if args.stock_ids:
        stock_ids = args.stock_ids.split(',')
    else:
        stock_list = db_manager.get_stock_list(exclude_patterns=['00'])
        stock_ids = stock_list['stock_id'].tolist()
    
    start_date = args.start_date or '2022-01-01'
    end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')
    frequency = args.frequency
    
    # 生成目標變數
    targets_df = target_generator.create_time_series_targets(
        stock_ids, start_date, end_date, frequency
    )
    
    if targets_df.empty:
        logger.error("沒有生成任何目標變數")
        return
    
    # 儲存結果
    output_path = args.output or f"data/targets/targets_{frequency}_{end_date}.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    targets_df.to_csv(output_path, index=False)
    
    # 分析目標變數分布
    analysis = target_generator.analyze_target_distribution(targets_df)
    logger.info(f"目標變數生成完成，儲存到: {output_path}")
    logger.info(f"生成 {len(targets_df)} 個樣本，正樣本比例: {analysis.get('positive_ratio', 0):.2%}")

def train_models_command(args):
    """執行模型訓練命令"""
    logger.info("開始訓練模型...")
    
    # 載入資料
    if args.features_file and args.targets_file:
        features_df = pd.read_csv(args.features_file)
        targets_df = pd.read_csv(args.targets_file)
    else:
        logger.error("請提供特徵檔案和目標變數檔案路徑")
        return
    
    # 初始化訓練器
    trainer = ModelTrainer()
    
    # 訓練模型
    results = trainer.train_all_models(features_df, targets_df)
    
    if results:
        logger.info("模型訓練完成")
        for model_type, result in results.items():
            metrics = result['metrics']
            logger.info(f"{model_type}: AUC={metrics['roc_auc']:.4f}, F1={metrics['f1_score']:.4f}")
    else:
        logger.error("模型訓練失敗")

def predict_command(args):
    """執行預測命令"""
    logger.info("開始執行預測...")
    
    # 初始化預測器
    predictor = Predictor()
    
    # 處理參數
    stock_ids = args.stock_ids.split(',') if args.stock_ids else None
    date = args.date or datetime.now().strftime('%Y-%m-%d')
    model_type = args.model
    
    # 執行預測
    predictions_df = predictor.predict_batch(stock_ids, date, model_type)
    
    if predictions_df.empty:
        logger.error("沒有預測結果")
        return
    
    # 儲存結果
    output_path = args.output or f"data/predictions/predictions_{model_type}_{date}.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    predictions_df.to_csv(output_path, index=False)
    
    # 統計結果
    success_count = (predictions_df['status'] == 'success').sum()
    positive_count = (predictions_df['prediction'] == 1).sum()
    
    logger.info(f"預測完成，儲存到: {output_path}")
    logger.info(f"成功預測 {success_count} 個股票，潛力股 {positive_count} 個")

def ranking_command(args):
    """執行排行榜生成命令"""
    logger.info("開始生成潛力股排行榜...")
    
    # 初始化預測器
    predictor = Predictor()
    
    # 處理參數
    date = args.date or datetime.now().strftime('%Y-%m-%d')
    model_type = args.model
    top_k = args.top_k
    
    # 生成排行榜
    ranking_df = predictor.generate_potential_stock_ranking(date, model_type, top_k)
    
    if ranking_df.empty:
        logger.error("沒有生成排行榜")
        return
    
    # 儲存結果
    output_path = args.output or f"data/rankings/ranking_{model_type}_{date}.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ranking_df.to_csv(output_path, index=False)
    
    logger.info(f"潛力股排行榜生成完成，儲存到: {output_path}")
    logger.info(f"排行榜包含 {len(ranking_df)} 個股票")
    
    # 顯示前10名
    print("\n🏆 潛力股排行榜 (前10名):")
    print("=" * 80)
    for _, row in ranking_df.head(10).iterrows():
        print(f"{row['rank']:2d}. {row['stock_id']} {row.get('stock_name', '')} - "
              f"機率: {row['probability']:.3f}")

def test_command(args):
    """執行測試命令"""
    logger.info("開始執行系統測試...")
    
    import unittest
    
    if args.module:
        # 執行特定模組測試
        module_name = f"tests.{args.module}"
        suite = unittest.TestLoader().loadTestsFromName(module_name)
    else:
        # 執行所有測試
        suite = unittest.TestLoader().discover('tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        logger.info("所有測試通過")
    else:
        logger.error(f"測試失敗: {len(result.failures)} 個失敗, {len(result.errors)} 個錯誤")

def main():
    """主程式"""
    # 確保目錄存在
    ensure_directories()
    
    # 解析命令列參數
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # 執行對應命令
        if args.command == 'generate-features':
            generate_features_command(args)
        elif args.command == 'generate-targets':
            generate_targets_command(args)
        elif args.command == 'train-models':
            train_models_command(args)
        elif args.command == 'predict':
            predict_command(args)
        elif args.command == 'ranking':
            ranking_command(args)
        elif args.command == 'test':
            test_command(args)
        else:
            logger.error(f"未知命令: {args.command}")
            parser.print_help()
    
    except Exception as e:
        logger.error(f"執行命令失敗: {e}")
        raise

if __name__ == "__main__":
    main()
