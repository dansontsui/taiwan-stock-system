# -*- coding: utf-8 -*-
"""
股價預測與投資建議系統 - 主程式入口
Stock Price Investment System - Main Entry Point
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# 添加專案路徑（確保可用套件匯入）
project_root = Path(__file__).parent
repo_root = project_root.parent
# 先放入 repo 根目錄，確保以 stock_price_investment_system.* 方式匯入
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from stock_price_investment_system.config.settings import get_config
from stock_price_investment_system.data.data_manager import DataManager
from stock_price_investment_system.price_models.feature_engineering import FeatureEngineer
from stock_price_investment_system.price_models.stock_price_predictor import StockPricePredictor
from stock_price_investment_system.price_models.walk_forward_validator import WalkForwardValidator
from stock_price_investment_system.selector.candidate_pool_generator import CandidatePoolGenerator
from stock_price_investment_system.utils.operation_history import get_operation_history

# 設定日誌
def setup_logging():
    """設定日誌系統（每次執行重新開始新log檔案）"""
    cfg = get_config('output')
    log_dir = cfg['paths']['logs']
    log_dir.mkdir(parents=True, exist_ok=True)

    # 每次執行都用新的時間戳，並刪除舊檔案
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"current_session_{timestamp}.log"

    # 清理舊的 log 檔案（保留最近3個）
    try:
        existing_logs = sorted(log_dir.glob("current_session_*.log"))
        if len(existing_logs) > 2:  # 保留最近2個，加上新的這個共3個
            for old_log in existing_logs[:-2]:
                old_log.unlink()
                _p(f"🗑️  已刪除舊日誌: {old_log.name}")
    except Exception as e:
        pass  # 刪除失敗不影響程式執行

    # 取得根 logger 並清空舊 handler
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    root_logger.setLevel(logging.DEBUG)

    # 檔案handler（DEBUG級別，重新開始寫入）
    file_handler = logging.FileHandler(log_file, mode='w', encoding=cfg['logging']['file_encoding'])
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(cfg['logging']['format']))

    # 終端handler（INFO級別）
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(cfg['logging']['format']))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    _p(f"📝 新日誌檔案: {log_file.name}")
    root_logger.info(f"=== 新執行階段開始 ===")
    root_logger.info(f"日誌檔案: {log_file}")

def _safe_setup_stdout():
    """安全設定標準輸出編碼"""
    try:
        # 避免 Windows cp950 編碼問題
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass

def _p(msg: str):
    """安全列印中文訊息"""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.write(msg.encode("utf-8", "ignore").decode("utf-8", "ignore") + "\n")
        except Exception:
            pass

def display_menu():
    """顯示主選單"""
    _p("\n" + "="*60)
    _p("🏦 股價預測與投資建議系統 - 功能選單")
    _p("="*60)
    _p("  1) 執行月度流程（營收→股價→選股→建議→報告）")
    _p("  2) 只跑股價預測")
    _p("  3) 執行內層 walk-forward（訓練期：2015–2022）")
    _p("  4) 生成 candidate pool（由內層結果套門檻）")
    _p("  5) 執行外層回測（2023–2024）")
    _p("  6) 顯示/編輯 config 檔案")
    _p("  7) 匯出報表（HTML / CSV）")
    _p("  8) 模型管理（列出 / 匯出 / 刪除）")
    _p("  9) 超參數調優（單檔/批量股票網格搜尋）")
    _p("  10) 系統狀態檢查")
    _p("  11) 日誌檔案管理（清理/壓縮/查看）")
    _p("  12) 查看操作歷史")
    _p("  q) 離開系統")
    _p("-"*60)
    _p("💡 建議執行順序：")
    _p("   首次建置：3→4→5")
    _p("   每月更新：2→4→5（若績效下降則從3開始）")
    _p("-"*60)

def get_user_input(prompt: str, default: str = None) -> str:
    """獲取使用者輸入"""
    if default:
        full_prompt = f"{prompt} [預設: {default}]: "
    else:
        full_prompt = f"{prompt}: "

    user_input = input(full_prompt).strip()
    return user_input if user_input else default

def confirm_action(message: str) -> bool:
    """確認動作"""
    response = input(f"{message} (y/N): ").strip().lower()
    return response in ['y', 'yes', '是']

def show_operation_history(menu_id: str) -> None:
    """顯示指定選單的操作歷史"""
    history = get_operation_history()
    records = history.get_operations_by_menu(menu_id, limit=5)

    if not records:
        _p(f"📝 選單 {menu_id} 沒有操作歷史")
        return

    _p(f"\n📋 選單 {menu_id} 最近操作歷史:")
    _p("-" * 60)

    for i, record in enumerate(reversed(records), 1):
        timestamp = record.get('timestamp', '')
        if timestamp:
            # 格式化時間顯示
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%m-%d %H:%M')
            except:
                time_str = timestamp[:16]
        else:
            time_str = "未知時間"

        operation_name = record.get('operation_name', '未知操作')
        parameters = record.get('parameters', {})
        param_str = history.format_parameters(parameters)

        _p(f"  {i}. {time_str} - {operation_name}")
        _p(f"     參數: {param_str}")

    _p("-" * 60)

def get_date_range_input(prompt: str, default_start: str, default_end: str, menu_id: str = "") -> tuple:
    """獲取日期區間輸入，支援歷史記錄"""
    _p(f"\n📅 {prompt}")

    # 從歷史記錄獲取上次設定
    history = get_operation_history()
    last_record = history.get_last_operation(menu_id) if menu_id else None

    if last_record and 'parameters' in last_record:
        last_start = last_record['parameters'].get('date_start', default_start)
        last_end = last_record['parameters'].get('date_end', default_end)
        _p(f"上次設定: {last_start} ~ {last_end}")
    else:
        last_start, last_end = default_start, default_end

    # 詢問是否使用預設或自訂
    use_custom = get_user_input("使用自訂日期區間？ (y/N)", "N").lower() == 'y'

    if use_custom:
        start_date = get_user_input(f"開始日期 (YYYY-MM格式)", last_start)
        end_date = get_user_input(f"結束日期 (YYYY-MM格式)", last_end)

        # 驗證日期格式
        try:
            from datetime import datetime
            datetime.strptime(start_date + '-01', '%Y-%m-%d')
            datetime.strptime(end_date + '-01', '%Y-%m-%d')
            _p(f"✅ 設定日期區間: {start_date} ~ {end_date}")
            return start_date, end_date
        except ValueError:
            _p("❌ 日期格式錯誤，使用預設值")
            return default_start, default_end
    else:
        _p(f"✅ 使用預設區間: {default_start} ~ {default_end}")
        return default_start, default_end

def get_user_input_with_history(prompt: str, default: str = None, menu_id: str = "", param_name: str = "") -> str:
    """獲取用戶輸入，支援歷史記錄"""
    # 嘗試從歷史記錄中獲取上次的值
    history_default = default
    if menu_id and param_name:
        history = get_operation_history()
        last_record = history.get_last_operation(menu_id)
        if last_record and 'parameters' in last_record:
            last_value = last_record['parameters'].get(param_name)
            if last_value is not None:
                history_default = str(last_value)

    # 構建提示字串
    if history_default and history_default != str(default):
        full_prompt = f"{prompt} [上次: {history_default}, 預設: {default or '無'}]: "
    elif history_default:
        full_prompt = f"{prompt} [預設: {history_default}]: "
    else:
        full_prompt = f"{prompt}: "

    user_input = input(full_prompt).strip()
    return user_input if user_input else history_default

def save_operation_to_history(menu_id: str, operation_name: str, parameters: dict) -> None:
    """保存操作到歷史記錄"""
    try:
        history = get_operation_history()
        history.save_operation(menu_id, operation_name, parameters)
    except Exception as e:
        # 歷史記錄失敗不應影響主要功能
        import logging
        logging.warning(f"保存操作歷史失敗: {e}")

def run_walk_forward_validation():
    """執行Walk-forward驗證"""
    _p("\n🔄 執行內層 walk-forward 驗證")
    _p("="*50)

    try:
        # 獲取參數
        config = get_config('walkforward')

        _p("📋 當前配置：")
        _p(f"   訓練視窗: {config['train_window_months']} 個月")
        _p(f"   測試視窗: {config['test_window_months']} 個月")
        _p(f"   步長: {config['stride_months']} 個月")
        _p(f"   訓練期間: {config['training_start']} 到 {config['training_end']}")

        # 詢問是否使用預設參數
        use_default = confirm_action("使用預設參數？")

        if not use_default:
            train_window = int(get_user_input("訓練視窗（月）", str(config['train_window_months'])))
            test_window = int(get_user_input("測試視窗（月）", str(config['test_window_months'])))
            stride = int(get_user_input("步長（月）", str(config['stride_months'])))
        else:
            train_window = config['train_window_months']
            test_window = config['test_window_months']
            stride = config['stride_months']

        # 獲取股票清單
        _p("\n📊 準備資料...")
        data_manager = DataManager()
        # 正確處理月底日期
        from calendar import monthrange
        year, month = map(int, config['training_end'].split('-'))
        last_day = monthrange(year, month)[1]
        end_date = f"{config['training_end']}-{last_day:02d}"

        stock_ids = data_manager.get_available_stocks(
            start_date=config['training_start'] + '-01',
            end_date=end_date,
            min_history_months=config['min_stock_history_months']
        )

        _p(f"找到 {len(stock_ids)} 檔符合條件的股票")

        if not stock_ids:
            _p("❌ 沒有找到符合條件的股票")
            return

        # 選擇股票範圍
        stock_choice = get_user_input("選擇股票範圍: 1=已調優股票, 2=全部股票(限制數量)", "1")

        if stock_choice == '1':
            # 只使用已調優的股票
            from stock_price_investment_system.price_models.hyperparameter_tuner import HyperparameterTuner
            tuned_df = HyperparameterTuner.get_tuned_stocks_info()

            if tuned_df.empty:
                _p("❌ 找不到任何已調優股票")
                _p("💡 請先執行選項 9 進行超參數調優")
                return

            # 獲取成功調優的股票清單
            successful_tuned = tuned_df[tuned_df['是否成功'] == '成功']
            tuned_stock_ids = successful_tuned['股票代碼'].unique().tolist()

            # 轉換為字串格式進行比較
            tuned_stock_ids_str = [str(sid) for sid in tuned_stock_ids]
            available_stock_ids_str = [str(sid) for sid in stock_ids]

            # 過濾出在可用股票中的已調優股票
            filtered_stock_ids = [sid for sid in tuned_stock_ids_str if sid in available_stock_ids_str]

            _p(f"📊 找到 {len(tuned_stock_ids)} 檔已調優股票: {tuned_stock_ids_str}")
            _p(f"📈 其中 {len(filtered_stock_ids)} 檔在可用股票清單中")
            _p(f"前10檔: {filtered_stock_ids[:10]}")

            if not filtered_stock_ids:
                _p("❌ 沒有可用的已調優股票")
                _p(f"💡 已調優股票: {tuned_stock_ids_str}")
                _p(f"💡 可用股票前10檔: {available_stock_ids_str[:10]}")
                return

            # 使用過濾後的股票清單
            stock_ids = filtered_stock_ids

        else:
            # 限制股票數量（測試用）
            max_stocks = int(get_user_input("最大股票數量（測試用）", "10"))
            if len(stock_ids) > max_stocks:
                stock_ids = stock_ids[:max_stocks]
                _p(f"限制為前 {max_stocks} 檔股票進行測試")

        # 執行驗證
        _p(f"\n🚀 開始執行 walk-forward 驗證...")
        _p(f"股票數量: {len(stock_ids)}")
        _p(f"參數: 訓練{train_window}月, 測試{test_window}月, 步長{stride}月")

        if not confirm_action("確認執行？"):
            _p("❌ 取消執行")
            return

        # 日期區間設定
        config = get_config()
        wf_config = config['walkforward']

        training_start, training_end = get_date_range_input(
            "訓練期間設定",
            wf_config['training_start'],
            wf_config['training_end'],
            "3"
        )

        # 日誌級別設定
        log_level_choice = get_user_input_with_history("日誌級別? 1=精簡(預設), 2=詳細", "2", "3", "log_level")
        verbose_logging = log_level_choice == "2"

        # 日誌輸出設定
        log_output_choice = get_user_input_with_history("日誌輸出? 1=CLI+檔案(預設), 2=只輸出CLI", "2", "3", "log_output")
        cli_only_logging = log_output_choice == "2"

        # 設定全域日誌模式
        if cli_only_logging:
            from stock_price_investment_system.utils.log_manager import set_cli_only_mode, suppress_verbose_logging, suppress_repetitive_warnings, suppress_data_missing_warnings
            set_cli_only_mode(True)
            suppress_verbose_logging()
            suppress_repetitive_warnings()
            suppress_data_missing_warnings()  # 完全抑制資料缺失警告
            _p("🔇 已啟用CLI專用模式，不會記錄日誌檔案")
            _p("🔇 已抑制重複警告和資料缺失警告")

        # 初始化驗證器（在變數定義之後）
        feature_engineer = FeatureEngineer()
        validator = WalkForwardValidator(feature_engineer, verbose_logging=verbose_logging, cli_only_logging=cli_only_logging)

        # 是否使用最佳參數與多模型
        use_best = get_user_input("是否使用最佳參數? (y/N)", "n").lower() in ["y","yes","是"]
        models_choice = get_user_input("使用哪些模型? 1=全三種, 2=主模型, 3=自選(逗號分隔), 4=自動選擇最佳模型", "2")

        models_to_use = None
        use_auto_best_model = False

        if models_choice == '1':
            models_to_use = ['xgboost','lightgbm','random_forest']
            _p("🔧 將使用三種模型: XGBoost, LightGBM, RandomForest")
        elif models_choice == '2':
            models_to_use = None  # 使用 primary_model
            config = get_config()
            primary_model = config['model']['primary_model']
            _p(f"🔧 將使用主模型: {primary_model}")
        elif models_choice == '4':
            use_auto_best_model = True
            models_to_use = ['auto_best']  # 特殊標記
            _p("🔧 將自動選擇每檔股票的最佳模型和參數")
            if not use_best:
                _p("⚠️  自動選擇最佳模型需要使用最佳參數，已自動啟用")
                use_best = True
        else:
            custom = get_user_input("輸入模型清單(例如: xgboost,random_forest)", "random_forest")
            models_to_use = [m.strip() for m in custom.split(',') if m.strip()]
            _p(f"🔧 將使用自選模型: {models_to_use}")

        # 確保 models_to_use 不為空
        if models_to_use is None:
            config = get_config()
            models_to_use = [config['model']['primary_model']]
            _p(f"🔧 使用預設主模型: {models_to_use}")

        _p(f"📋 訓練期間: {training_start} ~ {training_end}")
        _p(f"📋 模型設定: {models_to_use}")
        _p(f"📋 使用最佳參數: {'是' if use_best else '否'}")
        _p(f"📋 自動選擇最佳模型: {'是' if use_auto_best_model else '否'}")
        _p(f"📋 日誌級別: {'詳細' if verbose_logging else '精簡'}")

        # 保存操作到歷史記錄
        parameters = {
            'date_start': training_start,
            'date_end': training_end,
            'use_best_params': use_best,
            'models_choice': models_choice,
            'models_to_use': str(models_to_use),
            'use_auto_best_model': use_auto_best_model,
            'log_level': log_level_choice,
            'log_output': log_output_choice,
            'cli_only_logging': cli_only_logging
        }
        save_operation_to_history('3', '內層Walk-Forward驗證', parameters)

        # 記錄參數到日誌檔案（強制記錄，即使在CLI專用模式下）
        from stock_price_investment_system.utils.log_manager import log_menu_parameters
        log_menu_parameters('3', '內層Walk-Forward驗證', parameters, force_log=True)

        override_models = None
        if use_best:
            # 檢查已調優股票註冊表
            from stock_price_investment_system.price_models.hyperparameter_tuner import HyperparameterTuner
            tuned_df = HyperparameterTuner.get_tuned_stocks_info()

            if not tuned_df.empty:
                successful_tuned = tuned_df[tuned_df['是否成功'] == '成功']

                if not successful_tuned.empty:
                    _p(f"\n🧠 已調優股票統計:")
                    model_counts = successful_tuned['模型類型'].value_counts()
                    for model, count in model_counts.items():
                        _p(f"  {model}: {count} 檔股票")

                    _p(f"\n💡 每檔股票將使用專屬的最佳參數")
                    _p(f"   未調優的股票將使用預設參數")

                    # 建立通用備用參數（給沒有專屬參數的股票用）
                    override_models = {}
                    for model in model_counts.index:
                        # 取該模型類型中分數最高的參數作為通用備用
                        model_records = successful_tuned[successful_tuned['模型類型'] == model]
                        best_record = model_records.loc[model_records['最佳分數'].idxmax()]
                        try:
                            import ast
                            override_models[model] = ast.literal_eval(best_record['最佳參數'])
                        except:
                            pass
                else:
                    _p("⚠️ 沒有成功的調優結果，將使用預設參數")
            else:
                _p("⚠️ 找不到調優註冊表，將使用預設參數")

        # 正確處理月底日期
        from calendar import monthrange

        # 開始日期：月初
        start_date = training_start + '-01'

        # 結束日期：該月的最後一天
        year, month = map(int, training_end.split('-'))
        last_day = monthrange(year, month)[1]
        end_date = f"{training_end}-{last_day:02d}"

        _p(f"📅 實際訓練期間: {start_date} ~ {end_date}")

        # 記錄開始時間
        import time
        start_time = time.time()

        # 執行驗證（使用自訂日期）
        results = validator.run_validation(
            stock_ids=stock_ids,
            start_date=start_date,
            end_date=end_date,
            train_window_months=train_window,
            test_window_months=test_window,
            stride_months=stride,
            models_to_use=models_to_use,
            override_models=override_models
        )

        # 儲存結果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"walk_forward_results_{timestamp}.json"
        validator.save_results(results_file)

        # 計算執行時間
        duration = time.time() - start_time

        _p(f"\n✅ Walk-forward 驗證完成！")
        _p(f"📁 結果已儲存至: {results_file}")
        _p(f"📊 總共執行了 {results['fold_count']} 個 fold")
        _p(f"📈 涵蓋 {results['stock_count']} 檔股票")
        _p(f"💼 總交易次數: {results['total_trades']}")

        # 記錄執行摘要
        from stock_price_investment_system.utils.log_manager import log_execution_summary
        result_summary = f"處理 {results['stock_count']} 檔股票，{results['fold_count']} 個fold，{results['total_trades']} 筆交易"
        log_execution_summary('3', '內層Walk-Forward驗證', True, duration, result_summary)

    except Exception as e:
        _p(f"❌ Walk-forward 驗證失敗: {e}")

        # 記錄錯誤摘要
        from stock_price_investment_system.utils.log_manager import log_execution_summary
        log_execution_summary('3', '內層Walk-Forward驗證', False, None, f"執行錯誤: {str(e)}")

        logging.error(f"Walk-forward validation failed: {e}")

def generate_candidate_pool():
    """生成候選池"""
    _p("\n🎯 生成候選股票池")
    _p("="*50)

    try:
        # 日誌級別設定
        log_level_choice = get_user_input_with_history("日誌級別? 1=精簡(預設), 2=詳細", "1", "4", "log_level")
        verbose_logging = log_level_choice == "2"

        # 日誌輸出設定
        log_output_choice = get_user_input_with_history("日誌輸出? 1=CLI+檔案(預設), 2=只輸出CLI", "1", "4", "log_output")
        cli_only_logging = log_output_choice == "2"

        # 設定全域日誌模式
        if cli_only_logging:
            from stock_price_investment_system.utils.log_manager import set_cli_only_mode, suppress_verbose_logging, suppress_repetitive_warnings, suppress_data_missing_warnings
            set_cli_only_mode(True)
            suppress_verbose_logging()
            suppress_repetitive_warnings()
            suppress_data_missing_warnings()  # 完全抑制資料缺失警告
            _p("🔇 已啟用CLI專用模式，不會記錄日誌檔案")
            _p("🔇 已抑制重複警告和資料缺失警告")

        # 尋找最新的walk-forward結果
        import glob
        from stock_price_investment_system.config.settings import get_config as _get
        out_dir = _get('output')['paths']['walk_forward_results']
        result_files = glob.glob(str(out_dir / "walk_forward_results_*.json"))

        if not result_files:
            _p("❌ 找不到 walk-forward 驗證結果檔案")
            _p("💡 請先執行選項 3 進行 walk-forward 驗證")
            return

        # 使用最新的結果檔案
        latest_file = max(result_files, key=os.path.getctime)
        _p(f"📁 使用結果檔案: {latest_file}")

        # 載入結果
        import json
        try:
            with open(latest_file, 'r', encoding='utf-8-sig') as f:
                walk_forward_results = json.load(f)
        except Exception as e:
            logging.error(f"讀取walk-forward結果失敗，將嘗試以utf-8重試: {e}")
            with open(latest_file, 'r', encoding='utf-8') as f:
                walk_forward_results = json.load(f)

        # 顯示門檻設定
        config = get_config('selection')
        thresholds = config['candidate_pool_thresholds']

        _p("\n📋 當前門檻設定：")
        _p(f"   最小勝率: {thresholds['min_win_rate']:.1%}")
        _p(f"   最小盈虧比: {thresholds['min_profit_loss_ratio']:.2f}")
        _p(f"   最小交易次數: {thresholds['min_trade_count']}")
        _p(f"   最小fold數: {thresholds['min_folds_with_trades']}")
        _p(f"   最大回撤門檻: {thresholds['max_drawdown_threshold']:.1%}")

        # 詢問是否調整門檻
        adjust_thresholds = confirm_action("是否調整門檻設定？")

        if adjust_thresholds:
            custom_thresholds = {}
            custom_thresholds['min_win_rate'] = float(get_user_input("最小勝率 (0-1)", str(thresholds['min_win_rate'])))
            custom_thresholds['min_profit_loss_ratio'] = float(get_user_input("最小盈虧比", str(thresholds['min_profit_loss_ratio'])))
            custom_thresholds['min_trade_count'] = int(get_user_input("最小交易次數", str(thresholds['min_trade_count'])))
            custom_thresholds['min_folds_with_trades'] = int(get_user_input("最小fold數", str(thresholds['min_folds_with_trades'])))
            custom_thresholds['max_drawdown_threshold'] = float(get_user_input("最大回撤門檻 (0-1)", str(thresholds['max_drawdown_threshold'])))
        else:
            custom_thresholds = None

        # 記錄參數到日誌檔案
        parameters = {
            'walk_forward_file': latest_file,
            'use_custom_thresholds': adjust_thresholds,
            'thresholds': custom_thresholds or thresholds,
            'log_level': log_level_choice,
            'log_output': log_output_choice,
            'cli_only_logging': cli_only_logging
        }

        from stock_price_investment_system.utils.log_manager import log_menu_parameters
        log_menu_parameters('4', '候選池生成', parameters, force_log=True)

        # 保存操作到歷史記錄
        save_operation_to_history('4', '候選池生成', parameters)

        # 生成候選池
        _p("\n🚀 開始生成候選池...")

        # 記錄開始時間
        import time
        start_time = time.time()

        generator = CandidatePoolGenerator()
        pool_result = generator.generate_candidate_pool(walk_forward_results, custom_thresholds)

        # 計算執行時間
        duration = time.time() - start_time

        if pool_result['success']:
            # 儲存結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"candidate_pool_{timestamp}.json"
            csv_file = f"candidate_pool_{timestamp}.csv"

            generator.save_candidate_pool(pool_result, json_file)
            generator.export_candidate_pool_csv(pool_result, csv_file)

            _p(f"\n✅ 候選池生成完成！")
            _p(f"📊 評估股票數: {pool_result['total_evaluated']}")
            _p(f"🎯 合格股票數: {pool_result['pool_size']}")
            _p(f"📈 合格率: {pool_result['qualification_rate']:.1%}")
            _p(f"📁 JSON結果: {json_file}")
            _p(f"📁 CSV結果: {csv_file}")

            # 顯示前5名候選股票
            if pool_result['candidate_pool']:
                _p("\n🏆 前5名候選股票：")
                for i, stock in enumerate(pool_result['candidate_pool'][:5], 1):
                    stats = stock['statistics']
                    _p(f"   {i}. {stock['stock_id']} - 分數: {stock['stock_score']:.1f}")
                    _p(f"      勝率: {stats.get('win_rate', 0):.1%}, 盈虧比: {stats.get('profit_loss_ratio', 0):.2f}")

            # 記錄成功摘要
            from stock_price_investment_system.utils.log_manager import log_execution_summary
            result_summary = f"評估 {pool_result['total_evaluated']} 檔股票，合格 {pool_result['pool_size']} 檔，合格率 {pool_result['qualification_rate']:.1%}"
            log_execution_summary('4', '候選池生成', True, duration, result_summary)
        else:
            _p(f"❌ 候選池生成失敗: {pool_result.get('error', 'Unknown error')}")

            # 記錄失敗摘要
            from stock_price_investment_system.utils.log_manager import log_execution_summary
            log_execution_summary('4', '候選池生成', False, duration, f"生成失敗: {pool_result.get('error', 'Unknown error')}")

    except Exception as e:
        _p(f"❌ 候選池生成失敗: {e}")

        # 記錄錯誤摘要
        from stock_price_investment_system.utils.log_manager import log_execution_summary
        log_execution_summary('4', '候選池生成', False, None, f"執行錯誤: {str(e)}")

        logging.error(f"Candidate pool generation failed: {e}")

def run_hyperparameter_tuning():
    """執行超參數調優"""
    _p("\n🔧 超參數調優")
    _p("="*50)

    try:
        # 獲取可用股票
        data_manager = DataManager()
        config = get_config('walkforward')

        # 正確處理月底日期
        from calendar import monthrange
        year, month = map(int, config['training_end'].split('-'))
        last_day = monthrange(year, month)[1]
        end_date = f"{config['training_end']}-{last_day:02d}"

        available_stocks = data_manager.get_available_stocks(
            start_date=config['training_start'] + '-01',
            end_date=end_date,
            min_history_months=config['min_stock_history_months']
        )

        if not available_stocks:
            _p("❌ 找不到可用股票")
            return

        _p(f"📊 找到 {len(available_stocks)} 檔可用股票")
        _p(f"前10檔: {available_stocks[:10]}")

        # 選擇調優模式
        _p("\n📋 調優模式：")
        _p("  1) 單檔股票調優")
        _p("  2) 自動掃描所有股票（批量調優）")

        tuning_mode = get_user_input("選擇調優模式 (1-2)", "1")

        if tuning_mode == '2':
            # 批量調優所有股票
            run_batch_hyperparameter_tuning(available_stocks)
            return

        # 單檔股票調優（原有邏輯）
        _p("\n🔧 單檔股票網格搜尋")
        _p("-" * 30)

        # 顯示操作歷史
        show_operation_history('9')

        # 讓使用者選擇股票（支援歷史記錄）
        stock_id = get_user_input_with_history("請輸入要調優的股票代碼", available_stocks[0], "9", "stock_id")

        if stock_id not in available_stocks:
            _p(f"⚠️  股票 {stock_id} 不在可用清單中，但仍會嘗試執行")

        # 選擇測試模式
        _p("\n📋 測試模式：")
        _p("  1) 測試所有模型 (XGBoost + LightGBM + RandomForest)")
        _p("  2) 測試單一模型")

        mode_choice = get_user_input_with_history("選擇測試模式 (1-2)", "1", "9", "mode_choice")

        # 設定參數組合數量
        max_combinations = int(get_user_input_with_history("每個模型最大參數組合數量", "20", "9", "max_combinations"))

        if not confirm_action("確認執行？"):
            _p("❌ 取消執行")
            return

        # 執行調優
        from stock_price_investment_system.price_models.hyperparameter_tuner import HyperparameterTuner
        tuner = HyperparameterTuner()

        if mode_choice == '1':
            # 測試所有模型
            _p(f"\n🚀 開始對股票 {stock_id} 進行全模型調優...")
            _p(f"將測試 XGBoost、LightGBM、RandomForest 三個模型")
            _p(f"每個模型最多 {max_combinations} 個參數組合")

            all_results = tuner.tune_all_models(
                stock_id=stock_id,
                max_combinations=max_combinations
            )

            _p(f"\n✅ 全模型調優完成！")
            _p(f"📊 股票: {all_results['stock_id']}")

            # 顯示每個模型的結果
            for model_type, result in all_results['all_models'].items():
                _p(f"\n🔧 {model_type.upper()}:")
                if result['success']:
                    _p(f"   🎯 最佳分數: {result['best_score']:.4f}")
                    _p(f"   📈 成功組合: {result['successful_combinations']}/{result['total_combinations']}")
                    if result['failed_combinations'] > 0:
                        _p(f"   ❌ 失敗組合: {result['failed_combinations']}")
                        _p(f"   🔍 失敗原因: {result['failure_analysis']}")
                else:
                    _p(f"   ❌ 全部失敗 ({result['total_combinations']} 個組合)")
                    _p(f"   🔍 失敗原因: {result['failure_analysis']}")

            # 顯示最佳整體結果
            best = all_results['best_overall']
            if best['model']:
                _p(f"\n🏆 最佳整體結果:")
                _p(f"   模型: {best['model'].upper()}")
                _p(f"   分數: {best['score']:.4f}")
                _p(f"   參數: {best['params']}")
            else:
                _p(f"\n❌ 所有模型都失敗")

        else:
            # 測試單一模型
            _p("\n📋 選擇模型類型：")
            _p("  1) xgboost")
            _p("  2) lightgbm")
            _p("  3) random_forest")

            model_choice = get_user_input("選擇模型類型 (1-3)", "1")
            model_map = {'1': 'xgboost', '2': 'lightgbm', '3': 'random_forest'}
            model_type = model_map.get(model_choice, 'xgboost')

            _p(f"\n🚀 開始對股票 {stock_id} 進行 {model_type} 模型調優...")

            result = tuner.tune_single_stock(
                stock_id=stock_id,
                model_type=model_type,
                max_combinations=max_combinations
            )

            _p(f"\n✅ 超參數調優完成！")
            _p(f"📊 股票: {result['stock_id']}")

            if result['success']:
                _p(f"🎯 最佳分數: {result['best_score']:.4f} (方向準確率)")
                _p(f"   📊 分數說明: 預測漲跌方向的準確度，1.0=100%準確")
                _p(f"🔧 最佳參數: {result['best_params']}")
                _p(f"📈 成功組合: {result['successful_combinations']}/{result['total_combinations']}")

                if result['failed_combinations'] > 0:
                    _p(f"❌ 失敗組合: {result['failed_combinations']}")
                    _p(f"🔍 失敗原因: {result['failure_analysis']}")

                summary = result['results_summary']
                _p(f"📊 分數統計: 平均={summary['mean_score']:.4f}, 標準差={summary['std_score']:.4f}")
                _p(f"🏆 前5名分數: {[f'{s:.4f}' for s in summary['top_5_scores']]}")

                _p(f"\n💡 CSV欄位說明:")
                _p(f"   - test_direction_accuracy: 測試集方向準確率 (主要指標)")
                _p(f"   - test_r2: 測試集R²決定係數")
                _p(f"   - train_r2: 訓練集R²決定係數")
                _p(f"   - param_*: 各種模型參數")
            else:
                _p(f"❌ 所有參數組合都失敗 ({result['total_combinations']} 個)")
                _p(f"🔍 失敗原因: {result['failure_analysis']}")

        _p(f"\n📁 詳細結果已儲存至:")
        _p(f"   stock_price_investment_system/models/hyperparameter_tuning/")
        _p(f"   - JSON: 完整結果與失敗原因")
        _p(f"   - CSV:  所有參數組合與指標（中文欄位，包含失敗記錄）")

        # 提示最佳參數應用
        if mode_choice == '1':
            best = all_results['best_overall']
            if best['model']:
                _p(f"\n🔧 建議將最佳參數應用到系統:")
                _p(f"   1. 編輯 stock_price_investment_system/config/settings.py")
                _p(f"   2. 更新 {best['model']}_params 區段:")
                for param, value in best['params'].items():
                    _p(f"      '{param}': {value},")
                _p(f"   3. 重新執行選單3,4,5 使用最佳參數")
        else:
            if result['success']:
                _p(f"\n🔧 建議將最佳參數應用到系統:")
                _p(f"   1. 編輯 stock_price_investment_system/config/settings.py")
                _p(f"   2. 更新 {model_type}_params 區段:")
                for param, value in result['best_params'].items():
                    _p(f"      '{param}': {value},")
                _p(f"   3. 重新執行選單3,4,5 使用最佳參數")

        # 保存操作到歷史記錄
        parameters = {
            'stock_id': stock_id,
            'mode_choice': mode_choice,
            'max_combinations': max_combinations
        }
        if mode_choice == '2':
            parameters['model_type'] = model_type

        save_operation_to_history('9', '超參數調優', parameters)

    except Exception as e:
        _p(f"❌ 超參數調優執行失敗: {e}")
        logging.error(f"Hyperparameter tuning failed: {e}")


def run_batch_hyperparameter_tuning(available_stocks):
    """批量執行所有股票的超參數調優"""
    _p("\n🚀 自動掃描所有股票最佳參數")
    _p("="*50)

    try:
        from stock_price_investment_system.price_models.hyperparameter_tuner import HyperparameterTuner
        from stock_price_investment_system.utils.log_manager import BatchLogManager, clean_old_logs

        # 顯示當前已調優股票狀態
        tuned_df = HyperparameterTuner.get_tuned_stocks_info()
        if not tuned_df.empty:
            successful_count = len(tuned_df[tuned_df['是否成功'] == '成功'])
            _p(f"📊 當前已調優股票: {len(tuned_df)} 檔 (成功: {successful_count} 檔)")

            # 詢問是否跳過已調優股票
            skip_existing = confirm_action("是否跳過已成功調優的股票？")
            if skip_existing:
                successful_stocks = tuned_df[tuned_df['是否成功'] == '成功']['股票代碼'].astype(str).tolist()
                available_stocks = [s for s in available_stocks if str(s) not in successful_stocks]
                _p(f"📈 跳過已調優股票，剩餘 {len(available_stocks)} 檔待調優")

        if not available_stocks:
            _p("✅ 所有股票都已調優完成！")
            return

        # 設定批量調優參數
        _p(f"\n📋 批量調優設定:")
        _p(f"   待調優股票數: {len(available_stocks)}")
        _p(f"   前10檔: {available_stocks[:10]}")

        # 選擇調優範圍
        max_stocks = int(get_user_input("最大調優股票數（0=全部）", "50"))
        if max_stocks > 0 and len(available_stocks) > max_stocks:
            available_stocks = available_stocks[:max_stocks]
            _p(f"📊 限制為前 {max_stocks} 檔股票")

        # 選擇模型類型
        _p("\n📋 模型選擇：")
        _p("  1) 只測試最佳模型 (RandomForest)")
        _p("  2) 測試所有模型 (XGBoost + LightGBM + RandomForest)")

        model_choice = get_user_input("選擇模型範圍 (1-2)", "1")
        test_all_models = (model_choice == '2')

        # 設定參數組合數量
        max_combinations = int(get_user_input("每個模型最大參數組合數", "10"))

        # 日誌模式選擇
        _p(f"\n📝 日誌設定：")
        _p(f"  1) 標準模式（詳細日誌，適合小量股票）")
        _p(f"  2) 簡化模式（僅關鍵訊息，適合大量股票）")
        _p(f"  3) 靜默模式（最少日誌，僅結果摘要）")

        log_mode = get_user_input("選擇日誌模式 (1-3)", "2")

        # 確認執行
        _p(f"\n🎯 即將開始批量調優:")
        _p(f"   股票數量: {len(available_stocks)}")
        _p(f"   模型類型: {'全部模型' if test_all_models else '最佳模型(RandomForest)'}")
        _p(f"   每模型組合數: {max_combinations}")
        _p(f"   日誌模式: {['標準', '簡化', '靜默'][int(log_mode)-1]}")
        _p(f"   預估時間: {len(available_stocks) * (3 if test_all_models else 1) * 2} 分鐘")

        if not confirm_action("確認執行批量調優？"):
            _p("❌ 取消執行")
            return

        # 清理舊日誌檔案
        _p("🧹 清理舊日誌檔案...")
        clean_old_logs()

        # 初始化日誌管理器
        log_manager = BatchLogManager(log_mode=log_mode, max_log_size_mb=100)
        log_manager.start_batch_logging("batch_hyperparameter_tuning")

        # 執行批量調優
        tuner = HyperparameterTuner()
        successful_count = 0
        failed_count = 0

        _p(f"\n🚀 開始批量調優...")
        if log_mode != '3':
            _p(f"進度追蹤: 0/{len(available_stocks)}")

        for i, stock_id in enumerate(available_stocks, 1):
            try:
                if test_all_models:
                    # 測試所有模型
                    result = tuner.tune_all_models(
                        stock_id=stock_id,
                        max_combinations=max_combinations
                    )

                    if result['best_overall']['model']:
                        successful_count += 1
                        best = result['best_overall']
                        result_msg = f"✅ 成功 - 最佳: {best['model']} (分數: {best['score']:.4f})"
                    else:
                        failed_count += 1
                        result_msg = "❌ 失敗 - 所有模型都無法訓練"

                else:
                    # 只測試最佳模型
                    result = tuner.tune_single_stock(
                        stock_id=stock_id,
                        model_type='random_forest',
                        max_combinations=max_combinations
                    )

                    if result['success']:
                        successful_count += 1
                        result_msg = f"✅ 成功 - RandomForest (分數: {result['best_score']:.4f})"
                    else:
                        failed_count += 1
                        result_msg = "❌ 失敗 - 無法找到有效參數"

            except Exception as e:
                failed_count += 1
                result_msg = f"❌ 錯誤 - {str(e)[:50]}..."
                # 錯誤仍然記錄到日誌
                logging.error(f"Stock {stock_id} tuning failed: {e}")

            # 使用日誌管理器記錄進度
            log_manager.log_progress(i, len(available_stocks), successful_count, failed_count, stock_id, result_msg)
            log_manager.log_summary(i, len(available_stocks), successful_count, failed_count)

        # 停止批量日誌記錄
        log_manager.stop_batch_logging()

        # 最終結果摘要
        _p(f"\n🎉 批量調優完成！")
        _p(f"📊 總結果:")
        _p(f"   成功調優: {successful_count} 檔")
        _p(f"   調優失敗: {failed_count} 檔")
        _p(f"   成功率: {successful_count/(successful_count+failed_count)*100:.1f}%")

        # 顯示調優後的統計
        updated_tuned_df = HyperparameterTuner.get_tuned_stocks_info()
        if not updated_tuned_df.empty:
            successful_total = len(updated_tuned_df[updated_tuned_df['是否成功'] == '成功'])
            model_counts = updated_tuned_df[updated_tuned_df['是否成功'] == '成功']['模型類型'].value_counts()

            _p(f"\n📈 系統調優總覽:")
            _p(f"   總成功股票: {successful_total} 檔")
            _p(f"   模型分佈:")
            for model, count in model_counts.items():
                _p(f"     {model}: {count} 檔")

        _p(f"\n💡 下一步建議:")
        _p(f"   1. 執行選項3 (walk-forward驗證) - 使用已調優參數")
        _p(f"   2. 執行選項4 (生成候選池) - 篩選獲利股票")
        _p(f"   3. 執行選項5 (外層回測) - 驗證最終績效")

    except Exception as e:
        _p(f"❌ 批量調優執行失敗: {e}")
        logging.error(f"Batch hyperparameter tuning failed: {e}")


def _display_backtest_results(res: dict):
    """顯示回測結果的詳細摘要"""
    _p("\n" + "="*60)
    _p("🏆 投資組合回測結果摘要")
    _p("="*60)

    # 基本資訊
    m = res['metrics']
    _p(f"📅 回測期間: {res.get('start', 'N/A')} ~ {res.get('end', 'N/A')}")
    _p(f"📊 候選股票數: {res.get('stock_count', 0)} 檔")
    _p(f"💼 總交易次數: {m.get('trade_count', 0)} 筆")

    # 績效指標
    _p(f"\n📈 績效指標:")
    _p(f"   💰 總報酬率: {m.get('total_return', 0):.2%}")
    _p(f"   📊 平均報酬率: {m.get('avg_return', 0):.2%}")
    _p(f"   🎯 勝率: {m.get('win_rate', 0):.1%}")

    # 年化指標計算
    if res.get('start') and res.get('end'):
        try:
            from datetime import datetime
            start_date = datetime.strptime(res['start'], '%Y-%m-%d')
            end_date = datetime.strptime(res['end'], '%Y-%m-%d')
            years = (end_date - start_date).days / 365.25
            if years > 0:
                total_return = m.get('total_return', 0)
                annualized_return = (1 + total_return) ** (1/years) - 1
                _p(f"   📅 年化報酬率: {annualized_return:.2%}")
        except:
            pass

    # 風險指標
    if m.get('trade_count', 0) > 0:
        _p(f"\n⚠️  風險指標:")
        if 'max_drawdown' in m:
            _p(f"   📉 最大回撤: {m['max_drawdown']:.2%}")
        if 'volatility' in m:
            _p(f"   📊 波動率: {m['volatility']:.2%}")
        if 'sharpe_ratio' in m:
            _p(f"   📈 夏普比率: {m['sharpe_ratio']:.2f}")

    # 檔案輸出資訊
    _p(f"\n📁 輸出檔案:")
    if 'charts' in res and res['charts']:
        _p(f"   📈 圖表檔案: {len(res['charts'])} 個")
        for chart_name, chart_path in res['charts'].items():
            _p(f"      - {chart_name}: {chart_path}")

    # 交易分析
    if m.get('trade_count', 0) > 0:
        _p(f"\n💡 交易分析:")
        win_count = int(m.get('win_rate', 0) * m.get('trade_count', 0))
        lose_count = m.get('trade_count', 0) - win_count
        _p(f"   ✅ 獲利交易: {win_count} 筆")
        _p(f"   ❌ 虧損交易: {lose_count} 筆")

        if win_count > 0 and lose_count > 0:
            avg_win = m.get('avg_return', 0) * m.get('trade_count', 0) / win_count if win_count > 0 else 0
            avg_loss = m.get('avg_return', 0) * m.get('trade_count', 0) / lose_count if lose_count > 0 else 0
            if avg_loss != 0:
                profit_loss_ratio = abs(avg_win / avg_loss)
                _p(f"   📊 盈虧比: {profit_loss_ratio:.2f}")

    _p("\n" + "="*60)


def _save_holdout_results(results: dict, start_date: str, end_date: str):
    """保存外層回測結果到檔案"""
    try:
        import json
        from datetime import datetime
        from pathlib import Path
        from stock_price_investment_system.config.settings import get_config

        # 獲取holdout結果目錄
        config = get_config()
        holdout_dir = Path(config['output']['paths']['holdout_results'])
        holdout_dir.mkdir(parents=True, exist_ok=True)

        # 生成檔案名稱
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = holdout_dir / f"holdout_backtest_{timestamp}.json"

        # 準備保存的資料
        save_data = {
            'backtest_info': {
                'type': 'holdout_backtest',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'success': results.get('success'),
                'stock_count': results.get('stock_count'),
                'trade_count': results.get('trade_count'),
                'total_return': results.get('total_return'),
                'metrics': results.get('metrics', {}),
                'params': results.get('params', {})
            },
            'monthly_results': results.get('monthly_results', []),
            'detailed_trades': results.get('detailed_trades', [])
        }

        # 保存到檔案
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)

        _p(f"💾 完整回測結果已保存至: {filename}")
        _p(f"   📊 包含 {len(results.get('monthly_results', []))} 個月的詳細結果")
        _p(f"   📋 包含 {len(results.get('detailed_trades', []))} 筆交易記錄")

    except Exception as e:
        _p(f"⚠️  保存回測結果失敗: {e}")


def run_stock_prediction():
    """執行股價預測（選單2）- 使用與選單5完全相同的邏輯確保一致性"""
    _p("\n📈 股價預測")
    _p("="*50)

    try:
        # 顯示操作歷史
        show_operation_history('2')

        # 日期設定
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')

        prediction_date = get_user_input_with_history(
            "數據月份 (YYYY-MM格式) 預測月底購買",
            current_month,
            "2",
            "prediction_date"
        )

        # 回測參數設定（與選單5保持一致）
        _p("\n⚙️  預測參數設定（與選單5回測邏輯保持一致）：")
        min_pred = float(get_user_input_with_history("最小預測報酬門檻(例如0.02=2%)", "0.02", "2", "min_predicted_return"))
        top_k = int(get_user_input_with_history("每月最多持股數 TopK (0=不限制)", "10", "2", "top_k"))
        use_filter_input = get_user_input_with_history("啟用市場濾網(50MA>200MA)？ (Y/n)", "y", "2", "use_market_filter")
        use_filter = use_filter_input.strip().lower() == 'y'

        # 保存操作歷史
        parameters = {
            'prediction_date': prediction_date,
            'min_predicted_return': min_pred,
            'top_k': top_k,
            'use_market_filter': use_filter
        }
        save_operation_to_history('2', '股價預測', parameters)

        _p(f"\n🎯 預測設定:")
        _p(f"   預測月份: {prediction_date}")
        _p(f"   最小報酬門檻: {min_pred:.2%}")
        _p(f"   TopK限制: {top_k}")
        _p(f"   市場濾網: {'啟用' if use_filter else '關閉'}")

        # 🔑 關鍵：直接使用 HoldoutBacktester 的邏輯確保一致性
        _p("\n🚀 使用與選單5相同的回測邏輯進行預測...")

        from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester

        # 日誌設定 - 與選單5保持一致
        verbose_logging = False  # 選單2預設使用簡潔模式
        cli_only_logging = True  # 選單2預設只輸出到CLI

        # 抑制警告 - 與選單5保持一致
        from stock_price_investment_system.utils.log_manager import suppress_repetitive_warnings, suppress_data_missing_warnings
        suppress_repetitive_warnings()
        suppress_data_missing_warnings()

        # 額外抑制選單2的初始化日誌
        import logging
        logging.getLogger('stock_price_investment_system.data.data_manager').setLevel(logging.ERROR)
        logging.getLogger('stock_price_investment_system.data.price_data').setLevel(logging.ERROR)
        logging.getLogger('stock_price_investment_system.data.revenue_integration').setLevel(logging.ERROR)
        logging.getLogger('stock_price_investment_system.price_models.feature_engineering').setLevel(logging.ERROR)

        # 創建回測器 - 使用與選單5相同的日誌設定
        hb = HoldoutBacktester(verbose_logging=verbose_logging, cli_only_logging=cli_only_logging)

        # 載入候選池
        pool = hb._load_candidate_pool(None)
        stocks = [s['stock_id'] for s in pool.get('candidate_pool', [])]

        if not stocks:
            _p("❌ 候選池為空，無法執行預測")
            return

        _p(f"📊 候選池股票數: {len(stocks)}")

        # 🔑 使用與選單5完全相同的邏輯
        # 為每檔股票建立使用最佳參數的預測器
        stock_predictors = hb._create_stock_predictors(stocks)

        # 設定預測日期（實際月底）- 與選單5保持一致
        from calendar import monthrange
        year, month = map(int, prediction_date.split('-'))
        last_day = monthrange(year, month)[1]
        as_of = f"{prediction_date}-{last_day:02d}"

        # 市場濾網檢查
        if use_filter and (not hb._is_market_ok(as_of)):
            _p(f"⚠️  市場濾網觸發，建議暫停交易: {prediction_date}")
            _p("📊 大盤技術面不佳 (50MA < 200MA)")
            return

        # 為每檔股票訓練模型（使用截至預測日期之前的資料）
        _p(f"🔄 訓練模型，共 {len(stocks)} 檔股票需要處理...")
        fe = FeatureEngineer()

        for stock_idx, stock_id in enumerate(stocks, 1):
            if stock_id in stock_predictors:
                # 顯示訓練進度
                progress_percent = (stock_idx / len(stocks)) * 100
                progress_bar = hb._create_progress_bar(stock_idx, len(stocks))
                _p(f"   📊 [{stock_idx:2d}/{len(stocks)}] {progress_bar} {progress_percent:5.1f}% - 訓練 {stock_id}")

                try:
                    # 生成訓練資料，使用截至預測日期之前的資料
                    features_df, targets_df = fe.generate_training_dataset(
                        stock_ids=[stock_id],
                        start_date='2015-01-01',
                        end_date=as_of
                    )

                    if features_df.empty:
                        continue

                    # 訓練模型
                    train_result = stock_predictors[stock_id].train(
                        feature_df=features_df,
                        target_df=targets_df
                    )

                    if not train_result['success']:
                        _p(f"⚠️  模型訓練失敗 {stock_id}: {train_result.get('error', '未知錯誤')}")

                except Exception as e:
                    _p(f"⚠️  訓練資料生成失敗 {stock_id}: {e}")
                    continue

        # 使用個股專屬預測器進行預測
        _p(f"🔮 執行預測，共 {len(stocks)} 檔股票需要處理...")
        predictions = []
        for stock_idx, stock_id in enumerate(stocks, 1):
            if stock_id in stock_predictors:
                # 顯示預測進度
                progress_percent = (stock_idx / len(stocks)) * 100
                progress_bar = hb._create_progress_bar(stock_idx, len(stocks))
                _p(f"   🔮 [{stock_idx:2d}/{len(stocks)}] {progress_bar} {progress_percent:5.1f}% - 預測 {stock_id}")

                pred_result = stock_predictors[stock_id].predict(stock_id, as_of)
                if pred_result['success']:
                    predictions.append({
                        'stock_id': stock_id,
                        'predicted_return': float(pred_result['predicted_return']),
                        'model_type': getattr(stock_predictors[stock_id], 'model_type', 'unknown')
                    })

        _p(f"✅ 預測完成: {len(predictions)} 檔成功")

        if predictions:
            # 🔑 使用與選單5完全相同的篩選邏輯
            filtered = hb._filter_predictions(predictions, min_pred, top_k)

            _p(f"\n🏆 {prediction_date} 推薦股票")
            _p("="*60)
            _p(f"📊 總預測數: {len(predictions)}")
            _p(f"📊 符合門檻: {len([p for p in predictions if p['predicted_return'] >= min_pred])}")
            _p(f"📊 最終推薦: {len(filtered)}")

            if filtered:
                _p(f"\n{'排名':>4} {'股票代碼':>8} {'預測報酬率':>12} {'使用模型':>12}")
                _p("-"*60)

                for i, pred in enumerate(filtered, 1):
                    _p(f"{i:>4} {pred['stock_id']:>8} {pred['predicted_return']:>11.2%} {pred['model_type']:>12}")

                _p("="*60)
                _p(f"💡 平均預測報酬: {sum(p['predicted_return'] for p in filtered)/len(filtered):.2%}")

                # 重要提示
                _p(f"\n🔍 一致性驗證:")
                _p(f"   此結果應與選單5回測{prediction_date}的結果完全一致")
                _p(f"   如有差異，請檢查參數設定是否相同")
            else:
                _p("❌ 沒有符合條件的推薦股票")
        else:
            _p("❌ 預測失敗，沒有成功的預測結果")

    except Exception as e:
        _p(f"❌ 股價預測失敗: {e}")
        import logging
        logging.error(f"Stock prediction failed: {e}")
        import traceback
        traceback.print_exc()

def run_operation_history_viewer():
    """查看操作歷史"""
    _p("\n📋 操作歷史查看")
    _p("="*50)

    try:
        history = get_operation_history()

        _p("\n📋 選擇查看方式：")
        _p("  1) 查看最近操作 (所有選單)")
        _p("  2) 查看指定選單歷史")
        _p("  3) 清空操作歷史")

        choice = get_user_input("請選擇 (1-3)", "1")

        if choice == '1':
            # 查看最近操作
            records = history.get_recent_operations(limit=15)
            if not records:
                _p("📝 沒有操作歷史記錄")
                return

            _p(f"\n📋 最近 {len(records)} 次操作:")
            _p("-" * 80)

            for i, record in enumerate(reversed(records), 1):
                timestamp = record.get('timestamp', '')
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = timestamp[:16]
                else:
                    time_str = "未知時間"

                menu_id = record.get('menu_id', '?')
                operation_name = record.get('operation_name', '未知操作')
                parameters = record.get('parameters', {})
                param_str = history.format_parameters(parameters)

                _p(f"  {i:2d}. [{time_str}] 選單{menu_id} - {operation_name}")
                _p(f"      參數: {param_str}")

            _p("-" * 80)

        elif choice == '2':
            # 查看指定選單歷史
            menu_id = get_user_input("請輸入選單編號 (如: 5, 9)", "5")
            show_operation_history(menu_id)

        elif choice == '3':
            # 清空歷史
            if confirm_action("確認要清空所有操作歷史嗎？"):
                if history.clear_history():
                    _p("✅ 操作歷史已清空")
                else:
                    _p("❌ 清空操作歷史失敗")
            else:
                _p("❌ 取消清空操作")
        else:
            _p("❌ 無效選項")

    except Exception as e:
        _p(f"❌ 查看操作歷史失敗: {e}")
        import logging
        logging.error(f"Operation history viewer failed: {e}")

def run_log_management():
    """日誌檔案管理"""
    _p("\n🗂️  日誌檔案管理")
    _p("="*50)

    try:
        from stock_price_investment_system.utils.log_manager import clean_old_logs
        from pathlib import Path
        import os

        log_dir = Path("stock_price_investment_system/logs")

        # 檢查日誌目錄
        if not log_dir.exists():
            _p("📁 日誌目錄不存在，將自動建立")
            log_dir.mkdir(parents=True, exist_ok=True)
            return

        # 統計日誌檔案
        log_files = list(log_dir.glob("*.log"))
        gz_files = list(log_dir.glob("*.log.gz"))

        total_size = sum(f.stat().st_size for f in log_files + gz_files)
        total_size_mb = total_size / (1024 * 1024)

        _p(f"📊 日誌檔案統計:")
        _p(f"   未壓縮日誌: {len(log_files)} 個")
        _p(f"   壓縮日誌: {len(gz_files)} 個")
        _p(f"   總大小: {total_size_mb:.1f} MB")

        if log_files:
            _p(f"\n📄 最近的日誌檔案:")
            for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                _p(f"   {log_file.name} ({size_mb:.1f} MB, {mtime})")

        # 管理選項
        _p(f"\n📋 管理選項:")
        _p(f"  1) 清理舊日誌檔案（保留7天）")
        _p(f"  2) 壓縮大日誌檔案（>10MB）")
        _p(f"  3) 查看最新日誌檔案")
        _p(f"  4) 自訂清理設定")
        _p(f"  q) 返回主選單")

        choice = get_user_input("選擇操作 (1-4, q)", "q")

        if choice == '1':
            # 清理舊日誌
            _p("\n🧹 清理舊日誌檔案...")
            clean_old_logs(keep_days=7, compress_days=1)
            _p("✅ 清理完成")

        elif choice == '2':
            # 壓縮大檔案
            _p("\n📦 壓縮大日誌檔案...")
            compressed_count = 0

            for log_file in log_files:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                if size_mb > 10:  # 大於10MB
                    try:
                        import gzip
                        compressed_file = log_file.with_suffix('.log.gz')

                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                f_out.writelines(f_in)

                        log_file.unlink()
                        compressed_count += 1
                        _p(f"   ✅ 壓縮: {log_file.name}")

                    except Exception as e:
                        _p(f"   ❌ 壓縮失敗 {log_file.name}: {e}")

            _p(f"📦 壓縮完成，共處理 {compressed_count} 個檔案")

        elif choice == '3':
            # 查看最新日誌
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                _p(f"\n📄 最新日誌檔案: {latest_log.name}")

                try:
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    _p(f"📊 檔案資訊:")
                    _p(f"   行數: {len(lines)}")
                    _p(f"   大小: {latest_log.stat().st_size / (1024 * 1024):.1f} MB")

                    # 顯示最後20行
                    _p(f"\n📝 最後20行內容:")
                    _p("-" * 50)
                    for line in lines[-20:]:
                        _p(line.rstrip())
                    _p("-" * 50)

                except Exception as e:
                    _p(f"❌ 讀取日誌檔案失敗: {e}")
            else:
                _p("📄 沒有找到日誌檔案")

        elif choice == '4':
            # 自訂清理設定
            _p(f"\n⚙️  自訂清理設定:")

            keep_days = int(get_user_input("保留天數", "7"))
            compress_days = int(get_user_input("壓縮天數（超過此天數的檔案將被壓縮）", "1"))

            _p(f"\n🧹 執行自訂清理...")
            _p(f"   保留天數: {keep_days}")
            _p(f"   壓縮天數: {compress_days}")

            clean_old_logs(keep_days=keep_days, compress_days=compress_days)
            _p("✅ 自訂清理完成")

    except Exception as e:
        _p(f"❌ 日誌管理執行失敗: {e}")
        logging.error(f"Log management failed: {e}")


def main():
    _safe_setup_stdout()
    setup_logging()

    while True:
        display_menu()

        # 顯示當前日誌檔案
        log_dir = get_config('output')['paths']['logs']
        current_logs = sorted(log_dir.glob("current_session_*.log"))
        if current_logs:
            latest_log = current_logs[-1]
            _p(f"📝 當前日誌: {latest_log.name}")

        sel = input("🎯 請選擇功能 (1-12, q): ").strip().lower()

        if sel == '1':
            _p('⚙️  執行月度流程（尚未實作，將在下一個里程碑補上）')
        elif sel == '2':
            run_stock_prediction()
        elif sel == '3':
            run_walk_forward_validation()
        elif sel == '4':
            generate_candidate_pool()
        elif sel == '5':
            try:
                from stock_price_investment_system.price_models.holdout_backtester import HoldoutBacktester
                from stock_price_investment_system.price_models.hyperparameter_tuner import HyperparameterTuner

                _p('🏆 開始執行外層 holdout 回測...')

                # 檢查已調優股票
                tuned_df = HyperparameterTuner.get_tuned_stocks_info()
                if not tuned_df.empty:
                    successful_tuned = tuned_df[tuned_df['是否成功'] == '成功']
                    if not successful_tuned.empty:
                        model_counts = successful_tuned['模型類型'].value_counts()
                        _p(f"🧠 將使用個股最佳參數:")
                        for model, count in model_counts.items():
                            _p(f"   {model}: {count} 檔股票")
                        _p(f"   未調優股票將使用預設參數")
                    else:
                        _p("⚠️ 沒有成功調優的股票，將使用預設參數")
                else:
                    _p("⚠️ 沒有調優記錄，將使用預設參數")

                # 顯示操作歷史
                show_operation_history('5')

                # 日誌級別設定
                log_level_choice = get_user_input_with_history("日誌級別? 1=精簡(預設), 2=詳細", "1", "5", "log_level")
                verbose_logging = log_level_choice == "2"

                # 日誌輸出設定
                log_output_choice = get_user_input_with_history("日誌輸出? 1=CLI+檔案(預設), 2=只輸出CLI", "1", "5", "log_output")
                cli_only_logging = log_output_choice == "2"

                # 設定全域日誌模式
                if cli_only_logging:
                    from stock_price_investment_system.utils.log_manager import set_cli_only_mode, suppress_verbose_logging, suppress_repetitive_warnings, suppress_data_missing_warnings
                    set_cli_only_mode(True)
                    suppress_verbose_logging()
                    suppress_repetitive_warnings()
                    suppress_data_missing_warnings()  # 完全抑制資料缺失警告
                    _p("🔇 已啟用CLI專用模式，不會記錄日誌檔案")
                    _p("🔇 已抑制重複警告和資料缺失警告")

                hb = HoldoutBacktester(verbose_logging=verbose_logging, cli_only_logging=cli_only_logging)

                # 日期區間設定
                config = get_config()
                wf_config = config['walkforward']

                holdout_start, holdout_end = get_date_range_input(
                    "外層回測期間設定",
                    wf_config['holdout_start'],
                    wf_config['holdout_end'],
                    "5"
                )

                # 互動式參數（支援歷史記錄）
                _p("\n⚙️  回測參數設定：")
                min_pred = float(get_user_input_with_history("最小預測報酬門檻(例如0.02=2%)", "0.02", "5", "min_predicted_return"))
                top_k = int(get_user_input_with_history("每月最多持股數 TopK (0=不限制)", "10", "5", "top_k"))
                use_filter_input = get_user_input_with_history("啟用市場濾網(50MA>200MA)？ (Y/n)", "y", "5", "use_market_filter")
                if use_filter_input == True :
                    use_filter_input = 'y'
                use_filter = use_filter_input.strip().lower() == 'y'

                # 保存參數到歷史記錄
                parameters = {
                    'holdout_start': holdout_start,
                    'holdout_end': holdout_end,
                    'min_predicted_return': min_pred,
                    'top_k': top_k,
                    'use_market_filter': use_filter,
                    'log_level': log_level_choice,
                    'log_output': log_output_choice,
                    'cli_only_logging': cli_only_logging
                }
                save_operation_to_history('5', '外層回測', parameters)

                # 記錄參數到日誌檔案（強制記錄，即使在CLI專用模式下）
                from stock_price_investment_system.utils.log_manager import log_menu_parameters
                log_menu_parameters('5', '外層回測', parameters, force_log=True)

                # 正確處理月底日期
                from datetime import datetime
                from calendar import monthrange

                # 開始日期：月初
                start_date = holdout_start + '-01'

                # 結束日期：該月的最後一天
                year, month = map(int, holdout_end.split('-'))
                last_day = monthrange(year, month)[1]  # 獲取該月的最後一天
                end_date = f"{holdout_end}-{last_day:02d}"

                _p(f"📅 實際回測期間: {start_date} ~ {end_date}")

                # 記錄開始時間
                import time
                start_time = time.time()

                res = hb.run(
                    holdout_start=start_date,
                    holdout_end=end_date,
                    min_predicted_return=min_pred,
                    top_k=top_k,
                    use_market_filter=use_filter
                )

                # 計算執行時間
                duration = time.time() - start_time

                if res.get('success'):
                    _display_backtest_results(res)

                    # 保存完整的回測結果（包含月度結果）
                    _save_holdout_results(res, start_date, end_date)

                    # 記錄成功摘要
                    from stock_price_investment_system.utils.log_manager import log_execution_summary
                    result_summary = f"回測期間: {start_date}~{end_date}, 總報酬: {res.get('total_return', 'N/A')}"
                    log_execution_summary('5', '外層回測', True, duration, result_summary)
                else:
                    _p(f"❌ 外層回測失敗: {res.get('error','未知錯誤')}")

                    # 記錄失敗摘要
                    from stock_price_investment_system.utils.log_manager import log_execution_summary
                    log_execution_summary('5', '外層回測', False, duration, f"回測失敗: {res.get('error','未知錯誤')}")

            except Exception as e:
                _p(f"❌ 外層回測執行失敗: {e}")

                # 記錄錯誤摘要
                from stock_price_investment_system.utils.log_manager import log_execution_summary
                log_execution_summary('5', '外層回測', False, None, f"執行錯誤: {str(e)}")
        elif sel == '6':
            _p('⚙️  顯示/編輯 config 檔案（尚未實作）')
        elif sel == '7':
            _p('📋 報表輸出（尚未實作）')
        elif sel == '8':
            _p('🗂️  模型管理（尚未實作）')
        elif sel == '9':
            run_hyperparameter_tuning()
        elif sel == '10':
            _p('🩺 系統狀態檢查（尚未實作）')
        elif sel == '11':
            run_log_management()
        elif sel == '12':
            run_operation_history_viewer()
        elif sel in {'q', 'quit', 'exit'}:
            _p("👋 再見！")
            return 0
        else:
            _p("❌ 無效選項，請重試。")


if __name__ == "__main__":
    sys.exit(main())


