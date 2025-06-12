#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ollamaの環境変数設定を自動化するモジュール

このモジュールは、Ollamaの実行に必要なシステム環境変数を
Windowsシステムに自動的に設定します。
"""

import os
import sys
import subprocess
import platform
import winreg
import ctypes
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple
from src.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class OllamaInitializer:
    """
    Ollamaの環境変数を設定するクラス
    
    このクラスは以下の機能を提供します：
    1. Ollamaの環境変数を.envファイルから読み込む
    2. Windowsのシステム環境変数として設定する
    3. 必要に応じてOllamaサービスを再起動する
    """
    
    def __init__(self):
        """
        OllamaInitializerの初期化
        """
        # OSがWindowsかどうか確認
        if platform.system() != "Windows":
            logger.error("このモジュールはWindowsでのみ動作します")
            raise OSError("このモジュールはWindowsでのみ動作します")
        
        # .envファイルの読み込み
        load_dotenv()
        
        # 管理者権限があるか確認
        self.is_admin = self._is_admin()
        if not self.is_admin:
            logger.warning("管理者権限がありません。環境変数の設定には管理者権限が必要です。")
    
    def _is_admin(self) -> bool:
        """
        現在のプロセスが管理者権限で実行されているかを確認
        
        Returns:
            bool: 管理者権限があるかどうか
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _run_as_admin(self, cmd: list) -> bool:
        """
        管理者権限でコマンドを実行
        
        Args:
            cmd (list): 実行するコマンド
            
        Returns:
            bool: 成功したかどうか
        """
        if self.is_admin:
            # 既に管理者権限がある場合は直接実行
            try:
                subprocess.run(cmd, check=True)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"コマンド実行エラー: {e}")
                return False
        else:
            # 管理者権限がない場合は昇格して実行
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", cmd[0], " ".join(cmd[1:]), None, 1
                )
                return True
            except Exception as e:
                logger.error(f"管理者権限での実行に失敗しました: {e}")
                return False
    
    def _set_system_env_var(self, name: str, value: str) -> bool:
        """
        システム環境変数を設定
        
        Args:
            name (str): 環境変数名
            value (str): 環境変数の値
            
        Returns:
            bool: 成功したかどうか
        """
        try:
            # システム環境変数のレジストリキーを開く
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                0, winreg.KEY_ALL_ACCESS
            )
            
            # 環境変数を設定
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            
            # 環境変数の変更を通知
            subprocess.run(["setx", name, value, "/M"], check=True, capture_output=True)
            
            logger.info(f"システム環境変数 {name}={value} を設定しました")
            return True
        except Exception as e:
            logger.error(f"システム環境変数の設定に失敗しました: {e}")
            return False
    
    def _get_gpu_count(self) -> int:
        """
        利用可能なNVIDIA GPUの数を取得
        
        Returns:
            int: GPUの数（検出できない場合は1）
        """
        try:
            # nvidia-smiコマンドを実行してGPU情報を取得
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                check=True, capture_output=True, text=True
            )
            
            # 出力行数をカウント（各行が1つのGPUに対応）
            gpu_count = len(result.stdout.strip().split('\n'))
            logger.info(f"検出されたGPU数: {gpu_count}")
            return max(1, gpu_count)  # 最低1を返す
        except Exception as e:
            logger.warning(f"GPUの検出に失敗しました: {e}")
            logger.info("GPUが検出できないため、デフォルト値の1を使用します")
            return 1
    
    def setup_ollama_env_vars(self) -> bool:
        """
        Ollama用の環境変数をシステムに設定
        
        Returns:
            bool: すべての環境変数の設定に成功したかどうか
        """
        if not self.is_admin:
            logger.error("管理者権限がないため、環境変数を設定できません")
            return False
        
        # .envファイルから設定を読み込む
        ollama_port = os.getenv("OLLAMA_PORT", "11434")
        ollama_host = os.getenv("OLLAMA_HOST", "localhost")
        
        # GPUの数を取得
        gpu_num = self._get_gpu_count()
        
        # 設定する環境変数
        env_vars = {
            "OLLAMA_CUDA": "1",
            "OLLAMA_FLASH_ATTENTION": "1",
            "OLLAMA_HOST": "0.0.0.0",
            "OLLAMA_PORT": ollama_port,
            "OLLAMA_KEEP_ALIVE": "0",
            "OLLAMA_NUM_GPU": str(gpu_num)
        }
        
        # 環境変数を設定
        success = True
        for name, value in env_vars.items():
            if not self._set_system_env_var(name, value):
                success = False
        
        if success:
            logger.info("すべてのOllama環境変数の設定に成功しました")
        else:
            logger.warning("一部のOllama環境変数の設定に失敗しました")
        
        return success
    
    def restart_ollama_service(self) -> bool:
        """
        Ollamaサービスを再起動
        
        Returns:
            bool: 再起動に成功したかどうか
        """
        try:
            # Ollamaサービスを停止
            logger.info("Ollamaサービスを停止しています...")
            subprocess.run(["net", "stop", "ollama"], check=False)
            
            # Ollamaサービスを開始
            logger.info("Ollamaサービスを開始しています...")
            subprocess.run(["net", "start", "ollama"], check=True)
            
            logger.info("Ollamaサービスの再起動に成功しました")
            return True
        except Exception as e:
            logger.error(f"Ollamaサービスの再起動に失敗しました: {e}")
            return False


def main():
    """
    メイン関数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Ollama環境変数設定ツール')
    parser.add_argument('--restart', action='store_true',
                        help='環境変数設定後にOllamaサービスを再起動する')
    
    args = parser.parse_args()
    
    # OSがWindowsかどうか確認
    if platform.system() != "Windows":
        print("このスクリプトはWindowsでのみ動作します")
        sys.exit(1)
    
    # 管理者権限があるか確認
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("このスクリプトは管理者権限で実行する必要があります")
        print("スクリプトを管理者として再実行してください")
        sys.exit(1)
    
    try:
        # Ollama初期化クラスのインスタンス化
        initializer = OllamaInitializer()
        
        # 環境変数の設定
        print("Ollama環境変数を設定しています...")
        if initializer.setup_ollama_env_vars():
            print("Ollama環境変数の設定に成功しました")
        else:
            print("Ollama環境変数の設定に失敗しました")
            sys.exit(1)
        
        # 必要に応じてサービスを再起動
        if args.restart:
            print("Ollamaサービスを再起動しています...")
            if initializer.restart_ollama_service():
                print("Ollamaサービスの再起動に成功しました")
            else:
                print("Ollamaサービスの再起動に失敗しました")
                sys.exit(1)
        
        print("\nOllama環境変数の設定が完了しました")
        print("新しい環境変数を反映させるには、Ollamaサービスの再起動が必要です")
        print("--restart オプションを使用するか、手動でサービスを再起動してください")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
