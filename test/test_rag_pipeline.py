#!/usr/bin/env python
# -*- coding: utf-8 -*-
# test_rag_pipeline.py

import os
import sys
import pathlib
import psycopg2
from typing import Dict, Any
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# srcモジュールをインポート
from src.vector_database import VectorDatabase
from src.rag_database import RAGDatabase
from src.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def setup_db_config() -> Dict[str, Any]:
    """
    データベース接続設定を返します。
    環境変数から設定を取得するか、デフォルト値を使用します。
    
    Returns:
        Dict[str, Any]: データベース接続設定
    """
    return {
        'dbname': os.getenv('POSTGRES_DB', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432'))
    }

def check_table_exists(db_config, table_name):
    """
    テーブルが存在するか確認します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        table_name (str): 確認するテーブル名
        
    Returns:
        bool: テーブルが存在する場合はTrue
    """
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
            """, (table_name,))
            result = cursor.fetchone()
            exists = result[0] if result else False
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"テーブル '{table_name}' の存在確認中にエラーが発生しました: {e}")
        return False

def create_vector_database(db_config: Dict[str, Any], markdown_dir: str, reset_table: bool = False) -> VectorDatabase:
    """
    ベクトルデータベースを作成し、Markdownファイルを処理します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        markdown_dir (str): Markdownファイルのディレクトリパス
        reset_table (bool): テーブルをリセットするかどうか
        
    Returns:
        VectorDatabase: 作成されたベクトルデータベース
    """
    logger.info("ベクトルデータベースを初期化しています...")
    logger.info(f"テーブルリセット設定: {reset_table}")
    
    # ベクトルデータベースの初期化
    vector_db = VectorDatabase(
        db_config=db_config,
        dimension=1024,
        markdown_dir=markdown_dir,
        model_name="intfloat/multilingual-e5-large",
        chunk_size=500,
        chunk_overlap=100
    )
    
    # テーブルが存在するか確認
    table_exists = check_table_exists(db_config, "vector_embeddings")
    logger.info(f"テーブル存在確認結果: {table_exists}")
    
    # reset_tableがTrueの場合は必ずテーブルを再作成する
    logger.info(f"ベクトルテーブルリセット設定: {reset_table}")
    if reset_table:
        logger.info("テーブルリセットモードが有効なため、ベクトルデータベーステーブルを再作成します...")
        
        try:
            # テーブルを削除
            query = "DROP TABLE IF EXISTS vector_embeddings CASCADE;"
            vector_db.execute_query(query, fetch=False)
            vector_db.commit()
            logger.info("ベクトルデータベーステーブルを削除しました。")
            
            # テーブルを再作成
            logger.info("ベクトルデータベーステーブルを作成しています...")
            vector_db.create_table()
            
            # テーブルが作成されたことを確認
            table_exists = check_table_exists(db_config, "vector_embeddings")
            logger.info(f"テーブル作成確認結果: {table_exists}")
            
            # Markdownディレクトリの処理
            logger.info(f"Markdownディレクトリ '{markdown_dir}' を処理しています...")
            total_chunks = vector_db.process_markdown_directory(force_reprocess=True)
            logger.info(f"合計 {total_chunks} 個のチャンクを処理しました。")
            
            return vector_db
        except Exception as e:
            logger.error(f"テーブル操作中にエラーが発生しました: {e}", exc_info=True)
    
    # リセットしない場合の処理
    if not table_exists:
        logger.info("ベクトルデータベーステーブルを作成しています...")
        vector_db.create_table()
    else:
        logger.info("既存のベクトルデータベーステーブルを使用します。")
    
    # Markdownディレクトリの処理
    logger.info(f"Markdownディレクトリ '{markdown_dir}' を処理しています...")
    # テーブルがリセットされた場合は強制的に再処理する
    chunk_count = vector_db.process_markdown_directory(force_reprocess=reset_table)
    logger.info(f"合計 {chunk_count} 個のチャンクを処理しました。")
    
    return vector_db

def create_rag_database(db_config: Dict[str, Any], vector_db_config: Dict[str, Any], reset_table: bool = False) -> RAGDatabase:
    """
    RAGデータベースを作成し、ベクトルデータベースからデータを取り込みます。
    
    Args:
        db_config (Dict[str, Any]): RAGデータベース接続設定
        vector_db_config (Dict[str, Any]): ベクトルデータベース接続設定
        reset_table (bool): テーブルをリセットするかどうか
        
    Returns:
        RAGDatabase: 作成されたRAGデータベース
    """
    logger.info("RAGデータベースを初期化しています...")
    
    # RAGデータベースの初期化
    rag_db = RAGDatabase(
        db_config=db_config,
        dimension=1024,
        vector_db_config=vector_db_config
    )
    
    # テーブルの作成（または既存のテーブルを使用）
    table_exists = check_table_exists(db_config, "rag_documents")
    
    # reset_tableがTrueの場合は必ずテーブルを再作成する
    if reset_table:
        logger.info("テーブルリセットモードが有効なため、RAGデータベーステーブルを再作成します...")
        # テーブルをリセット
        try:
            rag_db.reset_table()
            logger.info("RAGデータベーステーブルをリセットしました。")
            table_exists = False
        except Exception as e:
            logger.error(f"テーブルリセット中にエラーが発生しました: {e}")
    
    if not table_exists:
        logger.info("RAGデータベーステーブルを作成しています...")
        rag_db.create_table()
    else:
        logger.info("既存のRAGデータベーステーブルを使用します。")
    
    # ベクトルデータベースからデータを取り込む
    logger.info("ベクトルデータベースからデータを取り込んでいます...")
    document_count = rag_db.build_from_vector_database()
    logger.info(f"合計 {document_count} 個のドキュメントを取り込みました。")
    
    # 検索インデックスの作成
    logger.info("検索インデックスを作成しています...")
    rag_db.create_search_index()
    
    return rag_db

def main():
    """
    メイン関数。ベクトルデータベースとRAGデータベースを作成し、
    ./data/markdownsディレクトリのMarkdownファイルを処理します。
    """
    # .envファイルを明示的に読み込む
    load_dotenv(override=True)
    
    logger.info("RAGパイプラインテストを開始します...")
    
    # プロジェクトのルートディレクトリを取得
    root_dir = pathlib.Path(__file__).parent.parent.absolute()
    
    # Markdownディレクトリのパス
    markdown_dir = os.path.join(root_dir, "data", "markdowns")
    logger.info(f"Markdownディレクトリ: {markdown_dir}")
    
    # データベース接続設定
    vector_db_config = setup_db_config()
    vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
    
    rag_db_config = setup_db_config()
    rag_db_config['dbname'] = os.getenv('RAG_DB', 'rag_db')
    
    # テーブルをリセットするかどうかの設定を取得
    reset_tables = os.getenv('RESET_TABLES', 'False').lower() in ('true', '1', 't')
    reset_vector_table = os.getenv('RESET_VECTOR_TABLE', 'False').lower() in ('true', '1', 't')
    reset_rag_table = os.getenv('RESET_RAG_TABLE', 'False').lower() in ('true', '1', 't')
    
    # 環境変数の値をログに出力
    logger.info(f"環境変数の設定値: RESET_TABLES={reset_tables}, RESET_VECTOR_TABLE={reset_vector_table}, RESET_RAG_TABLE={reset_rag_table}")
    
    # RESET_TABLESが有効な場合は、両方のテーブルをリセット
    if reset_tables:
        logger.info("全テーブルをリセットモードで実行します。")
        reset_vector_table = True
        reset_rag_table = True
    else:
        if reset_vector_table:
            logger.info("ベクトルデータベーステーブルのみリセットモードで実行します。")
        if reset_rag_table:
            logger.info("RAGデータベーステーブルのみリセットモードで実行します。")
    
    try:
        # ベクトルデータベースの作成
        vector_db = create_vector_database(vector_db_config, markdown_dir, reset_vector_table)
        logger.info("ベクトルデータベースの作成が完了しました。")
        
        # RAGデータベースの作成
        rag_db = create_rag_database(rag_db_config, vector_db_config, reset_rag_table)
        logger.info("RAGデータベースの作成が完了しました。")
        
        # ドキュメント数の確認
        doc_count = rag_db.get_document_count()
        logger.info(f"RAGデータベース内のドキュメント数: {doc_count}")
        
        # ユニークなソースの取得
        sources = rag_db.get_unique_sources()
        logger.info(f"RAGデータベース内のユニークなソース数: {len(sources)}")
        for i, (filename, filepath) in enumerate(sources[:5], 1):
            logger.info(f"ソース {i}: {filename} ({filepath})")
        
        if len(sources) > 5:
            logger.info(f"...他 {len(sources) - 5} 件のソース")
        
        logger.info("RAGパイプラインテストが正常に完了しました。")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
    finally:
        # 接続のクリーンアップ
        if 'vector_db' in locals():
            vector_db.disconnect()
        if 'rag_db' in locals():
            rag_db.disconnect()

if __name__ == "__main__":
    main()
