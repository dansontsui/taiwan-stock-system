# -*- coding: utf-8 -*-
from __future__ import annotations
import subprocess
import sys
from typing import Optional


def _safe_setup_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
    except Exception:
        pass


def _p(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            sys.stdout.write(msg.encode("utf-8", "ignore").decode("utf-8", "ignore") + "\n")
        except Exception:
            pass


def git_commit_and_push(
    commit_message: str,
    files_to_add: list[str] = None,
    dry_run: bool = False,
    working_dir: str = "."
) -> bool:
    """
    自動執行 git add, commit, push（支援 dry-run 模式）
    
    Args:
        commit_message: 中文 commit message
        files_to_add: 要添加的檔案列表，None 表示添加所有變更
        dry_run: True 為測試模式，僅顯示將執行的命令
        working_dir: git 工作目錄
    
    Returns:
        成功返回 True，失敗返回 False
    """
    _safe_setup_stdout()
    
    try:
        # 準備命令
        if files_to_add is None:
            add_cmd = ["git", "add", "."]
        else:
            add_cmd = ["git", "add"] + files_to_add
        
        commit_cmd = ["git", "commit", "-m", commit_message]
        push_cmd = ["git", "push", "origin", "main"]
        
        commands = [
            ("添加檔案", add_cmd),
            ("提交變更", commit_cmd),
            ("推送到遠端", push_cmd)
        ]
        
        if dry_run:
            _p("🧪 Dry-run 模式 - 將執行以下命令：")
            for desc, cmd in commands:
                _p(f"  {desc}：{' '.join(cmd)}")
            return True
        
        # 實際執行
        _p("🔄 開始執行 Git 自動化流程...")
        
        for desc, cmd in commands:
            _p(f"  執行：{desc}")
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                _p(f"❌ {desc}失敗：{result.stderr}")
                return False
            else:
                _p(f"✅ {desc}成功")
                if result.stdout.strip():
                    _p(f"   輸出：{result.stdout.strip()}")
        
        _p("🎉 Git 自動化流程完成！")
        return True
        
    except Exception as e:
        _p(f"❌ Git 自動化過程發生錯誤：{e}")
        return False


def check_git_status(working_dir: str = ".") -> dict:
    """
    檢查 git 狀態
    
    Returns:
        包含狀態資訊的字典
    """
    try:
        # 檢查是否有未提交的變更
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # 檢查當前分支
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # 檢查遠端狀態
        remote_result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        return {
            'has_changes': bool(status_result.stdout.strip()),
            'changes': status_result.stdout.strip().split('\n') if status_result.stdout.strip() else [],
            'current_branch': branch_result.stdout.strip(),
            'remote_info': remote_result.stdout.strip(),
            'is_git_repo': status_result.returncode == 0
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'is_git_repo': False
        }


def auto_commit_project_status(
    project_status_path: str,
    operation: str,
    metrics: dict,
    dry_run: bool = False
) -> bool:
    """
    自動提交 Project_status.md 與相關檔案
    
    Args:
        project_status_path: Project_status.md 檔案路徑
        operation: 操作類型
        metrics: 績效指標
        dry_run: 是否為測試模式
    
    Returns:
        成功返回 True
    """
    try:
        from .project_status import generate_commit_message
    except ImportError:
        from stock_price_investment_system.orchestrator.project_status import generate_commit_message
    
    # 生成中文 commit message
    commit_msg = generate_commit_message(operation, metrics)
    
    # 要提交的檔案
    files_to_add = [
        project_status_path,
        "stock_price_investment_system/",
        "outputs/",
        "reports/"
    ]
    
    return git_commit_and_push(
        commit_message=commit_msg,
        files_to_add=files_to_add,
        dry_run=dry_run
    )


# 測試與範例
if __name__ == "__main__":
    _safe_setup_stdout()
    
    # 測試 git 狀態檢查
    _p("🔍 檢查 Git 狀態...")
    status = check_git_status()
    _p(f"Git 倉庫：{'是' if status.get('is_git_repo') else '否'}")
    _p(f"當前分支：{status.get('current_branch', '未知')}")
    _p(f"有未提交變更：{'是' if status.get('has_changes') else '否'}")
    
    if status.get('has_changes'):
        _p("未提交的變更：")
        for change in status.get('changes', []):
            _p(f"  {change}")
    
    # 測試 dry-run 模式
    _p("\n🧪 測試 Dry-run 模式...")
    test_metrics = {
        'candidate_pool_size': 12,
        'annual_return': 8.5,
        'sharpe_ratio': 1.34,
        'max_drawdown': -8.9
    }
    
    success = auto_commit_project_status(
        project_status_path="stock_price_investment_system/Project_status.md",
        operation="月度更新",
        metrics=test_metrics,
        dry_run=True
    )
    
    _p(f"Dry-run 結果：{'成功' if success else '失敗'}")
