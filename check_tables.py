#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def check_database_tables():
    """データベースのテーブル一覧を取得して表示します"""
    # 接続設定
    db_config = {
        'dbname': os.getenv('RAG_DB', 'rag_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    try:
        # RAGデータベースに接続
        print("RAGデータベースのテーブル一覧:")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = [r[0] for r in cur.fetchall()]
        print(tables)
        
        # テーブル構造を確認
        for table in tables:
            print(f"\n{table}テーブルの構造:")
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';")
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        
        conn.close()
        
        # ベクトルデータベースに接続
        db_config['dbname'] = os.getenv('VECTOR_DB', 'vector_db')
        print("\n\nベクトルデータベースのテーブル一覧:")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = [r[0] for r in cur.fetchall()]
        print(tables)
        
        # テーブル構造を確認
        for table in tables:
            print(f"\n{table}テーブルの構造:")
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';")
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    check_database_tables()
