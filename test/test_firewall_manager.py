#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
firewall_manager.pyのテストモジュール

このモジュールは、Windowsファイアウォール設定を管理する機能をテストします。
実際のファイアウォール操作を行わず、モックを使用してテストします。
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import platform
import subprocess

# 親ディレクトリをパスに追加して、srcモジュールをインポートできるようにする
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
from src.firewall_manager import FirewallManager, setup_firewall, cleanup_firewall


class TestFirewallManager(unittest.TestCase):
    """FirewallManagerクラスのテスト"""

    def setUp(self):
        """テストの前準備"""
        # プラットフォームのモックはテストメソッド内で行うため、ここではモックしない
        self.firewall = FirewallManager("TestRule")

    @patch('platform.system')
    def test_init_windows(self, mock_platform):
        """Windowsでの初期化テスト"""
        mock_platform.return_value = "Windows"
        firewall = FirewallManager("TestRule")
        self.assertEqual(firewall.rule_name, "TestRule")
        self.assertEqual(firewall.os_type, "Windows")

    @patch('platform.system')
    def test_init_non_windows(self, mock_platform):
        """Windows以外での初期化テスト"""
        mock_platform.return_value = "Linux"
        firewall = FirewallManager("TestRule")
        self.assertEqual(firewall.os_type, "Linux")

    @patch('platform.system')
    @patch.object(FirewallManager, '_run_as_admin')
    @patch.object(FirewallManager, 'rule_exists')
    def test_add_firewall_rule_success(self, mock_rule_exists, mock_run_as_admin, mock_platform):
        """ファイアウォールルール追加成功のテスト"""
        mock_platform.return_value = "Windows"
        mock_rule_exists.return_value = False
        mock_run_as_admin.return_value = True

        result = self.firewall.add_firewall_rule([8080, 5000])
        self.assertTrue(result)
        
        # _run_as_adminが正しい引数で呼ばれたか確認
        mock_run_as_admin.assert_called_once()
        cmd_args = mock_run_as_admin.call_args[0][0]
        self.assertIn("localport=8080,5000", " ".join(cmd_args))

    @patch('platform.system')
    @patch.object(FirewallManager, 'rule_exists')
    def test_add_firewall_rule_already_exists(self, mock_rule_exists, mock_platform):
        """既存ルールがある場合のテスト"""
        mock_platform.return_value = "Windows"
        mock_rule_exists.return_value = True

        result = self.firewall.add_firewall_rule([8080])
        self.assertTrue(result)
        # rule_existsが呼ばれたことを確認
        mock_rule_exists.assert_called_once()

    @patch('platform.system')
    def test_add_firewall_rule_non_windows(self, mock_platform):
        """Windows以外での追加テスト"""
        mock_platform.return_value = "Linux"
        result = self.firewall.add_firewall_rule([8080])
        self.assertFalse(result)

    @patch('platform.system')
    @patch.object(FirewallManager, '_run_as_admin')
    @patch.object(FirewallManager, 'rule_exists')
    def test_remove_firewall_rule_success(self, mock_rule_exists, mock_run_as_admin, mock_platform):
        """ファイアウォールルール削除成功のテスト"""
        mock_platform.return_value = "Windows"
        mock_rule_exists.return_value = True
        mock_run_as_admin.return_value = True

        result = self.firewall.remove_firewall_rule()
        self.assertTrue(result)
        
        # _run_as_adminが正しい引数で呼ばれたか確認
        mock_run_as_admin.assert_called_once()
        cmd_args = mock_run_as_admin.call_args[0][0]
        self.assertIn("delete", " ".join(cmd_args))
        self.assertIn(f"name={self.firewall.rule_name}", " ".join(cmd_args))

    @patch('platform.system')
    @patch.object(FirewallManager, 'rule_exists')
    def test_remove_firewall_rule_not_exists(self, mock_rule_exists, mock_platform):
        """存在しないルールの削除テスト"""
        mock_platform.return_value = "Windows"
        mock_rule_exists.return_value = False

        result = self.firewall.remove_firewall_rule()
        self.assertTrue(result)
        # rule_existsが呼ばれたことを確認
        mock_rule_exists.assert_called_once()

    @patch('platform.system')
    def test_remove_firewall_rule_non_windows(self, mock_platform):
        """Windows以外での削除テスト"""
        mock_platform.return_value = "Linux"
        # FirewallManagerインスタンスを再作成して正しいOS情報を反映
        self.firewall = FirewallManager("TestRule")
        result = self.firewall.remove_firewall_rule()
        self.assertFalse(result)

    @patch('platform.system')
    @patch('subprocess.run')
    def test_rule_exists_true(self, mock_subprocess, mock_platform):
        """ルールが存在する場合のテスト"""
        mock_platform.return_value = "Windows"
        # サブプロセスの戻り値を設定
        process_mock = MagicMock()
        process_mock.returncode = 0
        # stdout属性をバイト列として設定し、デコードの問題を回避
        process_mock.stdout = f"ルール名:                     {self.firewall.rule_name}\n方向:                       受信"
        mock_subprocess.return_value = process_mock

        # rule_existsメソッド内のsubprocess.runの呼び出しをモック
        result = self.firewall.rule_exists()
        self.assertTrue(result)
        mock_subprocess.assert_called_once()

    @patch('platform.system')
    @patch('subprocess.run')
    def test_rule_exists_false(self, mock_subprocess, mock_platform):
        """ルールが存在しない場合のテスト"""
        mock_platform.return_value = "Windows"
        # サブプロセスの戻り値を設定
        process_mock = MagicMock()
        process_mock.returncode = 0
        # stdout属性をバイト列として設定し、デコードの問題を回避
        process_mock.stdout = "指定されたルールが見つかりません。"
        mock_subprocess.return_value = process_mock

        result = self.firewall.rule_exists()
        self.assertFalse(result)
        mock_subprocess.assert_called_once()

    @patch('platform.system')
    def test_rule_exists_non_windows(self, mock_platform):
        """Windows以外でのルール確認テスト"""
        mock_platform.return_value = "Linux"
        result = self.firewall.rule_exists()
        self.assertFalse(result)


class TestFirewallFunctions(unittest.TestCase):
    """setup_firewallとcleanup_firewall関数のテスト"""

    @patch('platform.system')
    @patch.object(FirewallManager, 'add_firewall_rule')
    def test_setup_firewall_private(self, mock_add_rule, mock_platform):
        """プライベートネットワークでのセットアップテスト"""
        mock_platform.return_value = "Windows"
        mock_add_rule.return_value = True

        result = setup_firewall(5000, 8080, "private")
        self.assertTrue(result)
        
        # add_firewall_ruleが正しい引数で呼ばれたか確認
        mock_add_rule.assert_called_once()
        args, kwargs = mock_add_rule.call_args
        self.assertEqual(args[0], [5000, 8080])
        self.assertEqual(kwargs['profile'], "private")

    @patch('platform.system')
    @patch.object(FirewallManager, 'add_firewall_rule')
    def test_setup_firewall_public(self, mock_add_rule, mock_platform):
        """パブリックネットワークでのセットアップテスト"""
        mock_platform.return_value = "Windows"
        mock_add_rule.return_value = True

        result = setup_firewall(5000, 8080, "public")
        self.assertTrue(result)
        
        # add_firewall_ruleが正しい引数で呼ばれたか確認
        mock_add_rule.assert_called_once()
        args, kwargs = mock_add_rule.call_args
        self.assertEqual(args[0], [5000, 8080])
        self.assertEqual(kwargs['profile'], "private,public,domain")

    @patch('platform.system')
    @patch.object(FirewallManager, 'remove_firewall_rule')
    def test_cleanup_firewall(self, mock_remove_rule, mock_platform):
        """ファイアウォールクリーンアップのテスト"""
        mock_platform.return_value = "Windows"
        mock_remove_rule.return_value = True

        result = cleanup_firewall()
        self.assertTrue(result)
        
        # remove_firewall_ruleが呼ばれたことを確認
        mock_remove_rule.assert_called_once()


if __name__ == '__main__':
    unittest.main()
