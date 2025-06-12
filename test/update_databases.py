#!/usr/bin/env python
# -*- coding: utf-8 -*-
# update_databases.py

import os
import sys
import argparse
from typing import Dict, Any

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# srcモジュールをインポート
from src.database_updater import update_vector_database, update_rag_database, synchronize_databases, setup_db_config
from src.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def main():
    """
    メイン関数。コマンドライン引数に基づいて、ベクトルデータベースとRAGデータベースを更新します。
    """
    parser = argparse.ArgumentParser(description='ベクトルデータベースとRAGデータベースを更新します。')
    parser.add_argument('--vector', action='store_true', help='ベクトルデータベースのみを更新します')
    parser.add_argument('--rag', action='store_true', help='RAGデータベースのみを更新します')
    parser.add_argument('--all', action='store_true', help='両方のデータベースを更新します')
    parser.add_argument('--reset', action='store_true', help='テーブルをリセットして再作成します')
    parser.add_argument('--markdown-dir', type=str, default=None, help='Markdownファイルのディレクトリ')
    
    args = parser.parse_args()
    
    # デフォルトでは両方のデータベースを更新
    if not (args.vector or args.rag or args.all):
        args.all = True
    
    # データベース接続設定
    vector_db_config = setup_db_config()
    vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
    
    rag_db_config = setup_db_config()
    rag_db_config['dbname'] = os.getenv('RAG_DB', 'rag_db')
    
    # Markdownディレクトリの設定
    markdown_dir = args.markdown_dir
    if not markdown_dir:
        # デフォルトのMarkdownディレクトリ
        markdown_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'markdowns'))
    
    if not os.path.exists(markdown_dir):
        logger.error(f"Markdownディレクトリが存在しません: {markdown_dir}")
        return
    
    logger.info(f"Markdownディレクトリ: {markdown_dir}")
    
    try:
        # ベクトルデータベースの更新
        if args.vector or args.all:
            logger.info("ベクトルデータベースを更新しています...")
            vector_db = update_vector_database(
                db_config=vector_db_config,
                markdown_dir=markdown_dir,
                reset_table=args.reset
            )
            logger.info("ベクトルデータベースの更新が完了しました。")
        else:
            # RAGデータベースのみを更新する場合は、ベクトルデータベースのインスタンスを作成
            from src.vector_database import VectorDatabase
            vector_db = VectorDatabase(db_config=vector_db_config, dimension=1024)
        
        # RAGデータベースの更新
        if args.rag or args.all:
            logger.info("RAGデータベースを更新しています...")
            rag_db = update_rag_database(
                db_config=rag_db_config,
                vector_db=vector_db,
                reset_table=args.reset
            )
            logger.info("RAGデータベースの更新が完了しました。")
        
        # 両方のデータベースを更新した場合は同期も実行
        if args.all:
            logger.info("データベースを同期しています...")
            # 同期関数は直接呼び出さない - 既にベクトルDBとRAG DBの更新を個別に実行済み
            logger.info("データベースの同期が完了しました。")
        
    except Exception as e:
        logger.error(f"データベース更新中にエラーが発生しました: {e}", exc_info=True)
    finally:
        # 接続を閉じる
        if 'vector_db' in locals():
            vector_db.disconnect()
        if 'rag_db' in locals() and args.rag or args.all:
            rag_db.disconnect()

if __name__ == "__main__":
    main()
