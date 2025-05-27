# -*- coding: utf-8 -*-
import os
import psycopg2
import pathlib
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

"""
一番最初のデータベース構築処理のみ
"""


# .envファイルから環境変数を読み込む
load_dotenv()

def ensure_directory_exists(directory_path):
    """指定されたディレクトリが存在することを確認し、存在しない場合は作成する"""
    path = pathlib.Path(directory_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"ディレクトリを作成しました: {directory_path}")
    return str(path.absolute())

def create_database(db_name=None, user=None, password=None, host=None, port=None):
    """指定された名前のデータベースを作成する"""
    db_name = db_name or os.getenv('POSTGRES_DB')
    user = user or os.getenv('POSTGRES_USER')
    password = password or os.getenv('POSTGRES_PASSWORD')
    host = host or os.getenv('POSTGRES_HOST', 'localhost')
    port = port or os.getenv('POSTGRES_PORT', '5432')

    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {db_name};")
        cur.close()
        conn.close()
        print(f"データベース '{db_name}' を作成しました。")
    except psycopg2.errors.DuplicateDatabase:
        print(f"データベース '{db_name}' は既に存在します。")
    except Exception as e:
        print(f"データベース作成中にエラーが発生しました: {e}")
        raise

def enable_pgvector_extension(db_name=None, user=None, password=None, host=None, port=None):
    """指定されたデータベースでpgvector拡張機能を有効にする"""
    db_name = db_name or os.getenv('POSTGRES_DB')
    user = user or os.getenv('POSTGRES_USER')
    password = password or os.getenv('POSTGRES_PASSWORD')
    host = host or os.getenv('POSTGRES_HOST', 'localhost')
    port = port or os.getenv('POSTGRES_PORT', '5432')

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        cur.close()
        conn.close()
        print(f"データベース '{db_name}' でpgvector拡張機能を有効にしました。")
    except Exception as e:
        print(f"pgvector拡張機能の有効化中にエラーが発生しました: {e}")
        raise

def create_rag_table(db_name=None, user=None, password=None, host=None, port=None):
    """rag_documentsテーブルを作成する"""
    db_name = db_name or os.getenv('RAG_DB')
    user = user or os.getenv('POSTGRES_USER')
    password = password or os.getenv('POSTGRES_PASSWORD')
    host = host or os.getenv('POSTGRES_HOST', 'localhost')
    port = port or os.getenv('POSTGRES_PORT', '5432')

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS rag_documents (
            id SERIAL PRIMARY KEY,
            original_text TEXT NOT NULL,
            embedding VECTOR(1024) NOT NULL,
            source_filename TEXT NOT NULL,
            source_filepath TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        cur.execute(create_table_query)
        conn.commit()
        cur.close()
        conn.close()
        print("rag_documentsテーブルを作成しました。")
    except Exception as e:
        print(f"rag_documentsテーブルの作成中にエラーが発生しました: {e}")
        raise

def create_vector_table(db_name=None, user=None, password=None, host=None, port=None):
    """vector_embeddingsテーブルを作成する"""
    db_name = db_name or os.getenv('VECTOR_DB')
    user = user or os.getenv('POSTGRES_USER')
    password = password or os.getenv('POSTGRES_PASSWORD')
    host = host or os.getenv('POSTGRES_HOST', 'localhost')
    port = port or os.getenv('POSTGRES_PORT', '5432')

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS vector_embeddings (
            id SERIAL PRIMARY KEY,
            chunk_text TEXT NOT NULL,
            embedding VECTOR(1024) NOT NULL,
            source_filename TEXT NOT NULL,
            source_filepath TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        cur.execute(create_table_query)
        conn.commit()
        cur.close()
        conn.close()
        print("vector_embeddingsテーブルを作成しました。")
    except Exception as e:
        print(f"vector_embeddingsテーブルの作成中にエラーが発生しました: {e}")
        raise


def main():
    """データベースとテーブルの作成を行うメイン関数"""
    try:
        # ディレクトリの作成
        rag_db_dir = ensure_directory_exists(os.getenv('RAGDB_DIR', './db/rag_db'))
        vector_db_dir = ensure_directory_exists(os.getenv('VECTORDB_DIR', './db/vector_db'))
        print(f"RAGデータベースディレクトリ: {rag_db_dir}")
        print(f"ベクトルデータベースディレクトリ: {vector_db_dir}")

        # データベースの作成
        print("PostgreSQLデータベースを作成しています...")
        create_database(db_name=os.getenv('RAG_DB'))
        create_database(db_name=os.getenv('VECTOR_DB'))

        # pgvector拡張機能の有効化
        print("pgvector拡張機能を有効にしています...")
        enable_pgvector_extension(db_name=os.getenv('RAG_DB'))
        enable_pgvector_extension(db_name=os.getenv('VECTOR_DB'))

        # テーブルの作成
        print("RAGテーブルを作成しています...")
        create_rag_table(db_name=os.getenv('RAG_DB'))

        print("ベクトルテーブルを作成しています...")
        create_vector_table(db_name=os.getenv('VECTOR_DB'))

        print("データベースとテーブルの作成が完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
