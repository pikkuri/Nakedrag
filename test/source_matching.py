#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ソースファイルマッチングテスト

このスクリプトは、data/markdownsディレクトリ内のファイルに対応するソースファイルを
data/sourceディレクトリ内から検索するテストプログラムです。
"""

import os
import sys
from pathlib import Path
import logging

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def find_source_files(markdown_dir: str, source_dir: str, debug: bool = False) -> None:
    """
    Markdownファイルに対応するソースファイルを検索します。
    
    Args:
        markdown_dir (str): Markdownファイルのディレクトリパス
        source_dir (str): ソースファイルのディレクトリパス
        debug (bool): デバッグモードを有効にするかどうか
    """
    # Markdownディレクトリ内のファイルを取得
    markdown_files = []
    for root, _, files in os.walk(markdown_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                markdown_files.append(file_path)
    
    logger.info(f"Markdownファイル数: {len(markdown_files)}")
    
    # 各Markdownファイルに対応するソースファイルを検索
    for markdown_file in markdown_files:
        file_basename = os.path.basename(markdown_file)
        base_filename_without_ext = os.path.splitext(file_basename)[0]
        
        logger.info(f"検索中: {file_basename} (ベース名: {base_filename_without_ext})")
        
        # ソースファイルを検索
        found = False
        
        # 方法1: 完全一致で検索
        markdown_source_dir = os.path.join(source_dir, "markdown")
        if os.path.exists(markdown_source_dir):
            source_file = os.path.join(markdown_source_dir, file_basename)
            if os.path.exists(source_file):
                relative_path = os.path.relpath(source_file, os.path.dirname(os.path.dirname(markdown_dir)))
                logger.info(f"完全一致で見つかりました: original_filepath={relative_path}")
                found = True
                continue
        
        # 方法2: ベース名で検索
        if not found and os.path.exists(markdown_source_dir):
            try:
                files_in_markdown_dir = [f for f in os.listdir(markdown_source_dir) if os.path.isfile(os.path.join(markdown_source_dir, f))]
                if debug:
                    logger.debug(f"markdownディレクトリ内のファイル: {files_in_markdown_dir}")
                
                for source_file_name in files_in_markdown_dir:
                    source_base_name = os.path.splitext(source_file_name)[0]
                    if debug:
                        logger.debug(f"比較: {source_base_name} vs {base_filename_without_ext}")
                    
                    if source_base_name == base_filename_without_ext:
                        source_file = os.path.join(markdown_source_dir, source_file_name)
                        relative_path = os.path.relpath(source_file, os.path.dirname(os.path.dirname(markdown_dir)))
                        logger.info(f"ベース名一致で見つかりました: original_filepath={relative_path}")
                        found = True
                        break
            except Exception as e:
                logger.error(f"markdownディレクトリの読み取り中にエラーが発生しました: {e}")
        
        # 方法3: 全サブディレクトリを検索
        if not found:
            for root, dirs, files in os.walk(source_dir):
                if found:
                    break
                
                for file in files:
                    source_base_name = os.path.splitext(file)[0]
                    if source_base_name == base_filename_without_ext:
                        source_file = os.path.join(root, file)
                        relative_path = os.path.relpath(source_file, os.path.dirname(os.path.dirname(markdown_dir)))
                        logger.info(f"サブディレクトリ内で見つかりました: original_filepath={relative_path}")
                        found = True
                        break
        
        if not found:
            logger.warning(f"ファイル '{file_basename}' に対応するソースファイルが見つかりませんでした。")

def main():
    """
    メイン関数
    """
    # プロジェクトルートからの相対パス
    markdown_dir = "./data/markdowns"
    source_dir = "./data/source"
    
    # 絶対パスに変換
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    markdown_dir = os.path.join(current_dir, markdown_dir.lstrip("./"))
    source_dir = os.path.join(current_dir, source_dir.lstrip("./"))
    
    logger.info(f"Markdownディレクトリ: {markdown_dir}")
    logger.info(f"ソースディレクトリ: {source_dir}")
    
    # ディレクトリの存在確認
    if not os.path.exists(markdown_dir):
        logger.error(f"Markdownディレクトリ '{markdown_dir}' が存在しません。")
        return
    
    if not os.path.exists(source_dir):
        logger.error(f"ソースディレクトリ '{source_dir}' が存在しません。")
        return
    
    # ソースファイル検索
    find_source_files(markdown_dir, source_dir, debug=True)

if __name__ == "__main__":
    main()
