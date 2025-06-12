#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG初期化のテストモジュール

このモジュールは、src/rag/rag_initializer.pyの機能をテストするためのものです。
RAGシステムの初期化とセットアップをテストします。
"""

import os
import sys
import argparse
from pathlib import Path
import time
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# dotenvをインポート
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 自作モジュールのインポート
from src.rag.rag_initializer import (
    initialize_rag_system,
    create_vector_database,
    create_rag_database,
    setup_db_config
)
from src.rag.vector_database import VectorDatabase
from src.rag.rag_database import RAGDatabase
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)


def test_initialize_rag_system(reset: bool = False, source_dir: str = None, markdown_dir: str = None) -> None:
    """
    RAGシステムの初期化をテストする関数
    
    以下の検証を行います：
    1. RAGシステムが正常に初期化されること
    2. vector_dbにMarkdownファイルのデータが正しく蓄積されること
    3. rag_dbに最適化されたデータが正しく転送されること
    4. 検索インデックスが正しく作成されること
    
    Args:
        reset (bool): データベースをリセットするかどうか
        source_dir (str): ソースディレクトリ
        markdown_dir (str): Markdownディレクトリ
    """
    logger.info("RAGシステム初期化テストを実行します")
    
    try:
        start_time = time.time()
        
        # ディレクトリが指定されていない場合はデフォルトを使用
        if markdown_dir is None:
            markdown_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'markdowns')
        if source_dir is None:
            source_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'source')
        
        # RAGシステムの初期化
        initialize_rag_system()
        
        # データベース設定の取得
        vector_db_config = setup_db_config()
        vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
        
        rag_db_config = setup_db_config()
        rag_db_config['dbname'] = os.getenv('RAG_DB', 'rag_db')
        
        # データベース接続の確認
        try:
            vector_db = VectorDatabase(vector_db_config, markdown_dir)
            rag_db = RAGDatabase(rag_db_config, 1024, vector_db_config)
            
            # データが正しく蓄積されているか確認
            vector_count = vector_db.execute_query(f"SELECT COUNT(*) FROM {vector_db.table_name}")[0][0]
            assert vector_count > 0, "vector_dbにデータが蓄積されていません"
            logger.info(f"vector_dbのドキュメント数: {vector_count}")
            
            # データが正しく転送されているか確認
            rag_count = rag_db.execute_query(f"SELECT COUNT(*) FROM {rag_db.table_name}")[0][0]
            assert rag_count == vector_count, f"rag_dbのドキュメント数({rag_count})がvector_dbのドキュメント数({vector_count})と一致しません"
            logger.info(f"rag_dbのドキュメント数: {rag_count}")
            
            # 検索インデックスの確認
            index_exists = rag_db.execute_query(
                "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'rag_documents_embedding_idx')"
            )[0][0]
            assert index_exists, "検索インデックスが作成されていません"
            
        finally:
            # データベース接続のクリーンアップ
            if 'vector_db' in locals():
                vector_db.connection.close()
            if 'rag_db' in locals():
                rag_db.connection.close()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"RAGシステム初期化テストが完了しました。所要時間: {elapsed_time:.2f}秒")
        print(f"\nRAGシステム初期化テストが完了しました。所要時間: {elapsed_time:.2f}秒")
        
    except AssertionError as e:
        logger.error(f"検証に失敗しました: {e}")
        raise
    except Exception as e:
        logger.error(f"RAGシステム初期化テスト中にエラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {str(e)}")


def test_create_vector_database(reset: bool = False) -> None:
    """
    ベクトルデータベースの作成をテストする関数
    
    Args:
        reset (bool): データベースをリセットするかどうか
    """
    logger.info("ベクトルデータベース作成テストを実行します")
    
    try:
        start_time = time.time()
        
        # データベース設定の取得
        vector_db_config = setup_db_config()
        vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
        
        # Markdownディレクトリの設定
        markdown_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'markdowns')
        
        # ベクトルデータベースの作成
        create_vector_database(
            db_config=vector_db_config,
            markdown_dir=markdown_dir,
            reset_table=reset
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"ベクトルデータベース作成テストが完了しました。所要時間: {elapsed_time:.2f}秒")
        print(f"\nベクトルデータベース作成テストが完了しました。所要時間: {elapsed_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"ベクトルデータベース作成テスト中にエラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {str(e)}")


def test_create_rag_database(reset: bool = False) -> None:
    """
    RAGデータベースの作成をテストする関数
    
    Args:
        reset (bool): データベースをリセットするかどうか
    """
    logger.info("RAGデータベース作成テストを実行します")
    
    try:
        start_time = time.time()
        
        # データベース設定の取得
        rag_db_config = setup_db_config()
        rag_db_config['dbname'] = os.getenv('RAG_DB', 'rag_db')
        
        vector_db_config = setup_db_config()
        vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
        
        # RAGデータベースの作成
        create_rag_database(
            db_config=rag_db_config,
            vector_db_config=vector_db_config,
            reset_table=reset
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger.info(f"RAGデータベース作成テストが完了しました。所要時間: {elapsed_time:.2f}秒")
        print(f"\nRAGデータベース作成テストが完了しました。所要時間: {elapsed_time:.2f}秒")
        
    except Exception as e:
        logger.error(f"RAGデータベース作成テスト中にエラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {str(e)}")


def main():
    """
    メイン関数
    
    テストの実行順序：
    1. RAGシステム全体の初期化テスト（データフローの検証を含む）
    2. 個別のデータベーステスト（必要な場合のみ）
    """
    parser = argparse.ArgumentParser(description='RAG初期化テスト')
    parser.add_argument('--mode', type=str, choices=['all', 'vector', 'rag', 'initialize'], default='all',
                        help='テストモード (all: すべて, vector: ベクトルDBのみ, rag: RAG DBのみ, initialize: 初期化のみ)')
    parser.add_argument('--reset', action='store_true', help='データベースをリセットする')
    parser.add_argument('--source-dir', type=str, default=None, help='ソースディレクトリ')
    parser.add_argument('--markdown-dir', type=str, default=None, help='Markdownディレクトリ')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'all':
            print("\n" + "="*80)
            print("RAGシステム全体のテストを実行します")
            print("="*80)
            # 最初にRAGシステム全体の初期化テストを実行
            test_initialize_rag_system(reset=args.reset, source_dir=args.source_dir, markdown_dir=args.markdown_dir)
            
            # 必要に応じて個別のデータベーステストを実行
            print("\n" + "-"*80)
            print("個別のデータベーステストを実行します")
            print("-"*80)
            test_create_vector_database(reset=False)  # リセットしない
            test_create_rag_database(reset=False)    # リセットしない
            
        elif args.mode == 'vector':
            print("\n" + "="*80)
            print("ベクトルデータベース作成テストを実行します")
            print("="*80)
            test_create_vector_database(reset=args.reset)
            
        elif args.mode == 'rag':
            print("\n" + "="*80)
            print("RAGデータベース作成テストを実行します")
            print("="*80)
            test_create_rag_database(reset=args.reset)
            
        elif args.mode == 'initialize':
            print("\n" + "="*80)
            print("RAGシステム初期化テストを実行します")
            print("="*80)
            test_initialize_rag_system(reset=args.reset, source_dir=args.source_dir, markdown_dir=args.markdown_dir)
    
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}", exc_info=True)
        print(f"エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
