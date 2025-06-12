# rag_initializer.py

## 概要
このモジュールはRAGシステムの初期化を一括で行うためのユーティリティです。ソースファイルのMarkdown化、データベースの初期化、ベクトルデータベースの更新、RAGデータベースの更新までの一連のプロセスを自動化します。環境変数のRESET系の設定を自動的にTrueに設定することで、簡単にシステム全体をリセットできる機能も提供します。

## 主な機能

1. **ソースファイルのMarkdown化** - `markdowns_maker.py`を使用して`data/source`ディレクトリのファイルをMarkdownに変換
2. **データベースの初期化** - `database_maker.py`を使用してPostgreSQLデータベースとテーブルを作成
3. **ベクトルデータベースの更新** - `vector_database.py`を使用してMarkdownファイルを処理し埋め込みベクトルを生成
4. **RAGデータベースの更新** - `rag_database.py`を使用してベクトルデータベースからデータを取り込み検索インデックスを作成
5. **自動リセット機能** - 環境変数の`RESET_TABLES`、`RESET_VECTOR_TABLE`、`RESET_RAG_TABLE`を自動的に`True`に設定

## 主なメソッド

### setup_db_config()
データベース接続設定を環境変数から取得します。

- **戻り値**:
  - データベース接続設定（辞書型）

### check_table_exists(db_config, table_name)
指定されたテーブルが存在するか確認します。

- **パラメータ**:
  - `db_config`: データベース接続設定
  - `table_name`: 確認するテーブル名
- **戻り値**:
  - テーブルが存在する場合はTrue、存在しない場合はFalse

### create_vector_database(db_config, markdown_dir, reset_table=True)
ベクトルデータベースを作成し、Markdownファイルを処理します。

- **パラメータ**:
  - `db_config`: データベース接続設定
  - `markdown_dir`: Markdownファイルのディレクトリパス
  - `reset_table`: テーブルをリセットするかどうか（デフォルト: True）
- **戻り値**:
  - 作成されたVectorDatabaseインスタンス

### create_rag_database(db_config, vector_db_config, reset_table=True)
RAGデータベースを作成し、ベクトルデータベースからデータを取り込みます。

- **パラメータ**:
  - `db_config`: RAGデータベース接続設定
  - `vector_db_config`: ベクトルデータベース接続設定
  - `reset_table`: テーブルをリセットするかどうか（デフォルト: True）
- **戻り値**:
  - 作成されたRAGDatabaseインスタンス

### initialize_rag_system()
RAGシステムの初期化を一括で行います。

1. ソースファイルをMarkdown化
2. データベースの初期化
3. ベクトルデータベースの更新
4. RAGデータベースの更新

このメソッドは環境変数の`RESET_TABLES`、`RESET_VECTOR_TABLE`、`RESET_RAG_TABLE`を自動的に`True`に設定します。

## 使用例

```python
# コマンドラインから実行
python src/rag_initializer.py

# モジュールとしてインポートして使用
from src.rag_initializer import initialize_rag_system

# RAGシステムを初期化
initialize_rag_system()
```

## 依存関係

- `markdowns_maker.py`: ソースファイルのMarkdown化
- `database_maker.py`: データベースの初期化
- `vector_database.py`: ベクトルデータベースの操作
- `rag_database.py`: RAGデータベースの操作
- 環境変数（`.env`ファイル）: 各種設定値

## 環境変数の設定

このモジュールは以下の環境変数を使用します：

- `SOURCE_DIR`: ソースディレクトリのパス（デフォルト: `./data/source`）
- `MD_DIR`: Markdownディレクトリのパス（デフォルト: `./data/markdowns`）
- `RAGDB_DIR`: RAGデータベースディレクトリのパス（デフォルト: `./db/rag_db`）
- `VECTORDB_DIR`: ベクトルデータベースディレクトリのパス（デフォルト: `./db/vector_db`）
- `EMBEDDING_MODEL`: 埋め込みモデル名（デフォルト: `intfloat/multilingual-e5-large`）
- `RAG_DB`: RAGデータベース名
- `VECTOR_DB`: ベクトルデータベース名
- `POSTGRES_USER`: PostgreSQLユーザー名
- `POSTGRES_PASSWORD`: PostgreSQLパスワード
- `POSTGRES_HOST`: PostgreSQLホスト（デフォルト: `localhost`）
- `POSTGRES_PORT`: PostgreSQLポート（デフォルト: `5432`）

## 注意事項

1. このモジュールは既存のデータベースとテーブルを完全にリセットします。重要なデータがある場合は事前にバックアップを取ってください。
2. 初期化プロセスはデータ量によっては時間がかかる場合があります。特に大量のソースファイルがある場合は注意してください。
3. 埋め込みモデルのダウンロードと読み込みには十分なメモリとディスク容量が必要です。
4. PostgreSQLサーバーが実行されていることを確認してください。
5. pgvector拡張機能がPostgreSQLにインストールされていることを確認してください。
