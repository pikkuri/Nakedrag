#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ファイアウォール設定を管理するモジュール

このモジュールは、Windowsファイアウォールの設定を管理するための機能を提供します。
NakedRAGシステムで使用するポートを自動的に開放することができます。
"""

import os
import sys
import subprocess
import platform
from typing import List, Optional
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

class FirewallManager:
    """
    ファイアウォール設定を管理するクラス
    
    このクラスは以下の機能を提供します：
    1. ファイアウォールルールの追加
    2. ファイアウォールルールの削除
    3. ファイアウォールルールの存在確認
    """
    
    def __init__(self, rule_name: str = "NakedRAG_Server"):
        """
        FirewallManagerの初期化
        
        Args:
            rule_name (str): ファイアウォールルールの名前
        """
        self.rule_name = rule_name
        self.os_type = platform.system()
        
        # Windowsでない場合はエラーログを出力
        if self.os_type != "Windows":
            logger.warning(f"このモジュールはWindowsでのみ動作します。現在のOS: {self.os_type}")
    
    def add_firewall_rule(self, ports: List[int], protocol: str = "TCP", 
                          direction: str = "in", action: str = "allow", 
                          profile: str = "private") -> bool:
        """
        ファイアウォールルールを追加
        
        Args:
            ports (List[int]): 開放するポートのリスト
            protocol (str): プロトコル（TCP/UDP）
            direction (str): 方向（in/out）
            action (str): アクション（allow/block）
            profile (str): プロファイル（private/public/domain）
            
        Returns:
            bool: 成功したかどうか
        """
        if self.os_type != "Windows":
            logger.error("このメソッドはWindowsでのみ動作します")
            return False
        
        # ポートリストを文字列に変換
        ports_str = ",".join(map(str, ports))
        
        try:
            # 既に同名のルールが存在するか確認
            if self.rule_exists():
                logger.info(f"ファイアウォールルール '{self.rule_name}' は既に存在します")
                return True
            
            # netshコマンドを実行してファイアウォールルールを追加
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={self.rule_name}",
                f"dir={direction}",
                f"action={action}",
                f"protocol={protocol}",
                f"localport={ports_str}",
                f"profile={profile}"
            ]
            
            # 管理者権限が必要なため、runas経由で実行
            result = self._run_as_admin(cmd)
            
            if result:
                logger.info(f"ファイアウォールルール '{self.rule_name}' を追加しました（ポート: {ports_str}）")
                return True
            else:
                logger.error(f"ファイアウォールルールの追加に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"ファイアウォールルールの追加中にエラーが発生しました: {e}")
            return False
    
    def remove_firewall_rule(self) -> bool:
        """
        ファイアウォールルールを削除
        
        Returns:
            bool: 成功したかどうか
        """
        if self.os_type != "Windows":
            logger.error("このメソッドはWindowsでのみ動作します")
            return False
        
        try:
            # 既にルールが存在するか確認
            if not self.rule_exists():
                logger.info(f"ファイアウォールルール '{self.rule_name}' は存在しません")
                return True
            
            # netshコマンドを実行してファイアウォールルールを削除
            cmd = [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={self.rule_name}"
            ]
            
            # 管理者権限が必要なため、runas経由で実行
            result = self._run_as_admin(cmd)
            
            if result:
                logger.info(f"ファイアウォールルール '{self.rule_name}' を削除しました")
                return True
            else:
                logger.error(f"ファイアウォールルールの削除に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"ファイアウォールルールの削除中にエラーが発生しました: {e}")
            return False
    
    def rule_exists(self) -> bool:
        """
        ファイアウォールルールが存在するか確認
        
        Returns:
            bool: ルールが存在するかどうか
        """
        if self.os_type != "Windows":
            logger.error("このメソッドはWindowsでのみ動作します")
            return False
        
        try:
            # netshコマンドを実行してファイアウォールルールの存在を確認
            cmd = [
                "netsh", "advfirewall", "firewall", "show", "rule",
                f"name={self.rule_name}"
            ]
            
            # コマンドを実行
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            # 出力にルール名が含まれているか確認
            return self.rule_name in process.stdout
                
        except Exception as e:
            logger.error(f"ファイアウォールルールの確認中にエラーが発生しました: {e}")
            return False
    
    def _run_as_admin(self, cmd: List[str]) -> bool:
        """
        管理者権限でコマンドを実行
        
        Args:
            cmd (List[str]): 実行するコマンド
            
        Returns:
            bool: 成功したかどうか
        """
        try:
            # UAC（ユーザーアカウント制御）ダイアログを表示して管理者権限で実行
            process = subprocess.run(
                ["powershell", "Start-Process", "cmd", "-Verb", "RunAs", 
                 "-ArgumentList", f"/c {' '.join(cmd)}"],
                capture_output=True,
                text=True
            )
            
            # 終了コードが0なら成功
            return process.returncode == 0
                
        except Exception as e:
            logger.error(f"管理者権限でのコマンド実行中にエラーが発生しました: {e}")
            return False

def setup_firewall(web_port: int, mcp_port: int, network_type: str = "private") -> bool:
    """
    NakedRAGサーバー用のファイアウォール設定をセットアップ
    
    Args:
        web_port (int): Webサーバーのポート
        mcp_port (int): MCPサーバーのポート
        network_type (str): ネットワークタイプ ("private" または "public")
        
    Returns:
        bool: 成功したかどうか
    """
    # ファイアウォールマネージャーの初期化
    firewall = FirewallManager("NakedRAG_Server")
    
    # ネットワークタイプに基づいてプロファイルを設定
    if network_type.lower() == "public":
        # パブリックネットワークの場合、すべてのプロファイルで許可
        profile = "private,public,domain"
        logger.warning("パブリックネットワークでポートを開放します。セキュリティ上のリスクがあります。")
    else:
        # ローカルネットワークの場合、プライベートプロファイルのみ許可
        profile = "private"
        logger.info("プライベートネットワークのみでポートを開放します。")
    
    # ファイアウォールルールを追加
    return firewall.add_firewall_rule([web_port, mcp_port], profile=profile)

def cleanup_firewall() -> bool:
    """
    NakedRAGサーバー用のファイアウォール設定をクリーンアップ
    
    Returns:
        bool: 成功したかどうか
    """
    # ファイアウォールマネージャーの初期化
    firewall = FirewallManager("NakedRAG_Server")
    
    # ファイアウォールルールを削除
    return firewall.remove_firewall_rule()

def main():
    """
    メイン関数
    """
    import argparse
    from dotenv import load_dotenv
    
    # .envファイルの読み込み
    load_dotenv()
    
    # デフォルト値を.envから取得
    default_web_port = int(os.getenv('WEB_SERVER_PORT', '5000'))
    default_mcp_port = int(os.getenv('MCP_SERVER_PORT', '8080'))
    default_network_type = os.getenv('NETWORK_TYPE', 'private')
    
    parser = argparse.ArgumentParser(description='ファイアウォール設定マネージャー')
    parser.add_argument('--action', type=str, choices=['add', 'remove'], default='add',
                        help='実行するアクション（add/remove）')
    parser.add_argument('--web-port', type=int, default=default_web_port,
                        help=f'Webサーバーのポート (デフォルト: {default_web_port})')
    parser.add_argument('--mcp-port', type=int, default=default_mcp_port,
                        help=f'MCPサーバーのポート (デフォルト: {default_mcp_port})')
    parser.add_argument('--network-type', type=str, choices=['private', 'public'], default=default_network_type,
                        help=f'ネットワークタイプ (デフォルト: {default_network_type})')
    
    args = parser.parse_args()
    
    # OSがWindowsかどうか確認
    if platform.system() != "Windows":
        print("このスクリプトはWindowsでのみ動作します")
        sys.exit(1)
    
    if args.action == 'add':
        # ネットワークタイプに関する警告表示
        if args.network_type == 'public':
            print("\033[91m警告: パブリックネットワークでポートを開放します。セキュリティ上のリスクがあります。\033[0m")
            confirm = input("続行しますか？ (y/n): ")
            if confirm.lower() != 'y':
                print("キャンセルされました")
                sys.exit(0)
        
        print(f"ファイアウォールルールを追加します（ポート: {args.web_port}, {args.mcp_port}, ネットワークタイプ: {args.network_type}）...")
        if setup_firewall(args.web_port, args.mcp_port, args.network_type):
            print("ファイアウォールルールの追加に成功しました")
        else:
            print("ファイアウォールルールの追加に失敗しました")
            sys.exit(1)
    else:
        print("ファイアウォールルールを削除します...")
        if cleanup_firewall():
            print("ファイアウォールルールの削除に成功しました")
        else:
            print("ファイアウォールルールの削除に失敗しました")
            sys.exit(1)

if __name__ == "__main__":
    main()
