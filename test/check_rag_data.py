#!/usr/bin/env python
# -*- coding: utf-8 -*-
# check_rag_data.py

import os
import sys
import argparse
import pathlib
from typing import Dict, Any, List, Tuple, Optional
from tabulate import tabulate
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

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

def check_column_existence(db_config: Dict[str, Any], table_name: str, column_name: str) -> bool:
    """
    指定されたテーブルに特定のカラムが存在するかを確認します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        table_name (str): テーブル名
        column_name (str): カラム名
        
    Returns:
        bool: カラムが存在する場合はTrue、それ以外はFalse
    """
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            );
            """, (table_name, column_name))
            result = cursor.fetchone()
            exists = result[0] if result else False
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"カラム '{column_name}' の存在確認中にエラーが発生しました: {e}")
        return False

def get_table_data(db_config: Dict[str, Any], table_name: str, limit: int = 100) -> List[Dict]:
    """
    テーブルからデータを取得します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        table_name (str): テーブル名
        limit (int): 取得する最大レコード数
        
    Returns:
        List[Dict]: テーブルデータのリスト
    """
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"テーブル '{table_name}' からのデータ取得中にエラーが発生しました: {e}")
        return []

def check_original_filepath_data(db_config: Dict[str, Any], table_name: str) -> None:
    """
    original_filepathカラムのデータを詳細に調査します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        table_name (str): テーブル名
    """
    logger.info(f"テーブル '{table_name}' のoriginal_filepathカラムを調査しています...")
    
    # カラムの存在確認
    if not check_column_existence(db_config, table_name, 'original_filepath'):
        logger.error(f"テーブル '{table_name}' にoriginal_filepathカラムが存在しません。")
        return
    
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cursor:
            # 総レコード数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            logger.info(f"総レコード数: {total_count}")
            
            # レコードが0件の場合は以降の処理をスキップ
            if total_count == 0:
                logger.warning("レコードが0件のため、詳細分析をスキップします。")
                return
            
            # original_filepathがNULLのレコード数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE original_filepath IS NULL")
            null_count = cursor.fetchone()[0]
            logger.info(f"original_filepathがNULLのレコード数: {null_count} ({null_count/total_count*100:.2f}%)")
            
            # original_filepathが空文字のレコード数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE original_filepath = ''")
            empty_count = cursor.fetchone()[0]
            logger.info(f"original_filepathが空文字のレコード数: {empty_count} ({empty_count/total_count*100:.2f}%)")
            
            # original_filepathの値がfilepathと同じレコード数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE original_filepath = filepath")
            same_as_filepath_count = cursor.fetchone()[0]
            logger.info(f"original_filepathがfilepathと同じレコード数: {same_as_filepath_count} ({same_as_filepath_count/total_count*100:.2f}%)")
            
            # original_filepathの値がfilepathと異なるレコード数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE original_filepath != filepath AND original_filepath IS NOT NULL")
            diff_from_filepath_count = cursor.fetchone()[0]
            logger.info(f"original_filepathがfilepathと異なるレコード数: {diff_from_filepath_count} ({diff_from_filepath_count/total_count*100:.2f}%)")
            
            # original_filepathの値の種類
            cursor.execute(f"SELECT DISTINCT original_filepath FROM {table_name} WHERE original_filepath IS NOT NULL LIMIT 20")
            distinct_values = cursor.fetchall()
            logger.info(f"original_filepathの異なる値の例 (最大20件):")
            for i, value in enumerate(distinct_values, 1):
                logger.info(f"  {i}. {value[0]}")
            
            # original_filepathとfilepathが異なるレコードの例
            cursor.execute(f"""
            SELECT id, filename, filepath, original_filepath 
            FROM {table_name} 
            WHERE original_filepath != filepath AND original_filepath IS NOT NULL 
            LIMIT 10
            """)
            diff_examples = cursor.fetchall()
            if diff_examples:
                logger.info(f"original_filepathとfilepathが異なるレコードの例:")
                headers = ["ID", "Filename", "Filepath", "Original Filepath"]
                print(tabulate(diff_examples, headers=headers, tablefmt="grid"))
            
        conn.close()
    except Exception as e:
        logger.error(f"original_filepathカラムの調査中にエラーが発生しました: {e}", exc_info=True)

def check_filepath_extensions(db_config: Dict[str, Any], table_name: str, column_name: str) -> None:
    """
    指定されたカラムのファイルパスの拡張子を集計します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
        table_name (str): テーブル名
        column_name (str): ファイルパスを含むカラム名
    """
    logger.info(f"テーブル '{table_name}' の {column_name} カラムの拡張子を集計しています...")
    
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cursor:
            # カラムの存在確認
            if not check_column_existence(db_config, table_name, column_name):
                logger.error(f"テーブル '{table_name}' に {column_name} カラムが存在しません。")
                return
            
            # 拡張子の抽出と集計
            cursor.execute(f"""
            SELECT 
                SUBSTRING({column_name} FROM '\\.[^.]*$') as extension,
                COUNT(*) as count
            FROM {table_name}
            WHERE {column_name} IS NOT NULL
            GROUP BY extension
            ORDER BY count DESC
            """)
            extensions = cursor.fetchall()
            
            if extensions:
                logger.info(f"{column_name} カラムの拡張子集計:")
                headers = ["拡張子", "件数"]
                print(tabulate(extensions, headers=headers, tablefmt="grid"))
            else:
                logger.info(f"{column_name} カラムに有効なファイルパスがありません。")
        
        conn.close()
    except Exception as e:
        logger.error(f"{column_name} カラムの拡張子集計中にエラーが発生しました: {e}", exc_info=True)

def check_rag_data(db_config: Dict[str, Any]) -> None:
    """
    RAGデータベースの中身を詳細に調査します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
    """
    logger.info("RAGデータベースを詳細に調査しています...")
    
    try:
        # RAGデータベースの初期化
        rag_db = RAGDatabase(db_config=db_config)
        
        # テーブル構造の取得
        logger.info("テーブル構造:")
        table_structure = rag_db.execute_query(f"""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = '{rag_db.table_name}'
        ORDER BY ordinal_position;
        """)
        
        if table_structure:
            headers = ["カラム名", "データ型", "最大長"]
            print(tabulate(table_structure, headers=headers, tablefmt="grid"))
            
            # カラム名を取得
            column_names = [col[0] for col in table_structure]
            logger.info(f"カラム一覧: {', '.join(column_names)}")
            
            # original_filepathカラムの詳細調査
            check_original_filepath_data(db_config, rag_db.table_name)
            
            # filepathとoriginal_filepathの拡張子集計
            check_filepath_extensions(db_config, rag_db.table_name, 'filepath')
            check_filepath_extensions(db_config, rag_db.table_name, 'original_filepath')
            
            # サンプルデータの取得と表示
            logger.info("サンプルデータ (最初の5件):")
            sample_data = rag_db.execute_query(f"""
            SELECT id, chunk_text, filename, filepath, original_filepath, chunk_index
            FROM {rag_db.table_name}
            LIMIT 5;
            """)
            
            if sample_data:
                headers = ["ID", "Chunk Text", "Filename", "Filepath", "Original Filepath", "Chunk Index"]
                # chunk_textを短く切り詰める
                formatted_data = []
                for row in sample_data:
                    row_list = list(row)
                    if row_list[1] and len(row_list[1]) > 50:
                        row_list[1] = row_list[1][:47] + "..."
                    formatted_data.append(row_list)
                print(tabulate(formatted_data, headers=headers, tablefmt="grid"))
            
            # ユニークなファイル名とパスの組み合わせ
            logger.info("ユニークなファイル名とパスの組み合わせ (最初の10件):")
            unique_files = rag_db.execute_query(f"""
            SELECT DISTINCT filename, filepath, original_filepath
            FROM {rag_db.table_name}
            LIMIT 10;
            """)
            
            if unique_files:
                headers = ["Filename", "Filepath", "Original Filepath"]
                print(tabulate(unique_files, headers=headers, tablefmt="grid"))
        else:
            logger.warning(f"テーブル '{rag_db.table_name}' が存在しないか、構造情報を取得できません。")
            return
        
    except Exception as e:
        logger.error(f"RAGデータベース調査中にエラーが発生しました: {e}", exc_info=True)
    finally:
        if 'rag_db' in locals():
            rag_db.disconnect()

def check_vector_data(db_config: Dict[str, Any]) -> None:
    """
    ベクトルデータベースの中身を詳細に調査します。
    
    Args:
        db_config (Dict[str, Any]): データベース接続設定
    """
    logger.info("ベクトルデータベースを詳細に調査しています...")
    
    try:
        # ベクトルデータベースの初期化
        vector_db = VectorDatabase(
            db_config=db_config,
            dimension=1024
        )
        
        # テーブル構造の取得
        logger.info("テーブル構造:")
        table_structure = vector_db.execute_query(f"""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = '{vector_db.table_name}'
        ORDER BY ordinal_position;
        """)
        
        if table_structure:
            headers = ["カラム名", "データ型", "最大長"]
            print(tabulate(table_structure, headers=headers, tablefmt="grid"))
            
            # カラム名を取得
            column_names = [col[0] for col in table_structure]
            logger.info(f"カラム一覧: {', '.join(column_names)}")
            
            # original_filepathカラムの詳細調査
            if 'original_filepath' in column_names:
                check_original_filepath_data(db_config, vector_db.table_name)
            
            # filepathとoriginal_filepathの拡張子集計
            check_filepath_extensions(db_config, vector_db.table_name, 'filepath')
            if 'original_filepath' in column_names:
                check_filepath_extensions(db_config, vector_db.table_name, 'original_filepath')
            
            # サンプルデータの取得と表示
            logger.info("サンプルデータ (最初の5件):")
            sample_query = f"SELECT id, chunk_text, filename, filepath"
            if 'original_filepath' in column_names:
                sample_query += ", original_filepath"
            if 'chunk_index' in column_names:
                sample_query += ", chunk_index"
            sample_query += f" FROM {vector_db.table_name} LIMIT 5;"
            
            sample_data = vector_db.execute_query(sample_query)
            
            if sample_data:
                headers = ["ID", "Chunk Text", "Filename", "Filepath"]
                if 'original_filepath' in column_names:
                    headers.append("Original Filepath")
                if 'chunk_index' in column_names:
                    headers.append("Chunk Index")
                
                # chunk_textを短く切り詰める
                formatted_data = []
                for row in sample_data:
                    row_list = list(row)
                    if row_list[1] and len(row_list[1]) > 50:
                        row_list[1] = row_list[1][:47] + "..."
                    formatted_data.append(row_list)
                print(tabulate(formatted_data, headers=headers, tablefmt="grid"))
            
            # ユニークなファイル名とパスの組み合わせ
            logger.info("ユニークなファイル名とパスの組み合わせ (最初の10件):")
            unique_query = f"SELECT DISTINCT filename, filepath"
            if 'original_filepath' in column_names:
                unique_query += ", original_filepath"
            unique_query += f" FROM {vector_db.table_name} LIMIT 10;"
            
            unique_files = vector_db.execute_query(unique_query)
            
            if unique_files:
                headers = ["Filename", "Filepath"]
                if 'original_filepath' in column_names:
                    headers.append("Original Filepath")
                print(tabulate(unique_files, headers=headers, tablefmt="grid"))
        else:
            logger.warning(f"テーブル '{vector_db.table_name}' が存在しないか、構造情報を取得できません。")
            return
        
    except Exception as e:
        logger.error(f"ベクトルデータベース調査中にエラーが発生しました: {e}", exc_info=True)
    finally:
        if 'vector_db' in locals():
            vector_db.disconnect()

def main():
    """
    メイン関数。コマンドライン引数に基づいて、ベクトルデータベースまたはRAGデータベース、
    あるいは両方のデータベースを詳細に調査します。
    """
    parser = argparse.ArgumentParser(description='ベクトルデータベースとRAGデータベースの中身を詳細に調査します。')
    parser.add_argument('--vector', action='store_true', help='ベクトルデータベースを調査します')
    parser.add_argument('--rag', action='store_true', help='RAGデータベースを調査します')
    parser.add_argument('--all', action='store_true', help='両方のデータベースを調査します')
    parser.add_argument('--limit', type=int, default=100, help='取得する最大レコード数 (デフォルト: 100)')
    
    args = parser.parse_args()
    
    # デフォルトでは両方のデータベースを調査
    if not (args.vector or args.rag or args.all):
        args.all = True
    
    # データベース接続設定
    vector_db_config = setup_db_config()
    vector_db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
    
    rag_db_config = setup_db_config()
    rag_db_config['dbname'] = os.getenv('RAG_DB', 'rag_db')
    
    try:
        # ベクトルデータベースの調査
        if args.vector or args.all:
            check_vector_data(vector_db_config)
            if args.rag or args.all:
                print("\n" + "="*80 + "\n")
        
        # RAGデータベースの調査
        if args.rag or args.all:
            check_rag_data(rag_db_config)
    
    except Exception as e:
        logger.error(f"データベース調査中にエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
