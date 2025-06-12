# database_updater.py

## 概要
このモジュールはベクトルデータベースとRAGデータベースを同期し、Markdownファイルからデータを取り込むための機能を提供します。新しいファイルの処理、既存データの更新、重複データの防止などを行います。

## 主な機能

### update_vector_database(db_config: Dict[str, Any], markdown_dir: str, reset_table: bool = False) -> VectorDatabase
ベクトルデータベースを更新し、新しいMarkdownファイルを処理します。

- **パラメータ**:
  - `db_config`: データベース接続設定（辞書型）
  - `markdown_dir`: Markdownファイルのディレクトリパス
  - `reset_table`: テーブルをリセットするかどうか（デフォルト: False）
- **戻り値**:
  - 更新されたベクトルデータベース

この関数は以下の処理を行います：
1. ベクトルデータベースの初期化と必要に応じたテーブルの作成
2. 既に処理済みのファイルの取得
3. 新しいMarkdownファイルの検出と処理
4. テキストのチャンク分割と埋め込みベクトルの生成
5. ベクトルデータベースへのデータ保存

### update_rag_database(db_config: Dict[str, Any], vector_db: VectorDatabase, reset_table: bool = False) -> RAGDatabase
RAGデータベースを更新し、ベクトルデータベースからデータを取り込みます。

- **パラメータ**:
  - `db_config`: データベース接続設定（辞書型）
  - `vector_db`: ベクトルデータベースのインスタンス
  - `reset_table`: テーブルをリセットするかどうか（デフォルト: False）
- **戻り値**:
  - 更新されたRAGデータベース

この関数は以下の処理を行います：
1. RAGデータベースの初期化と必要に応じたテーブルのリセット
2. ベクトルデータベースからのデータ取得
3. RAGデータベースへのデータ挿入
4. 検索インデックスの作成
5. データベース統計情報の表示

### synchronize_databases(db_config: Dict[str, Any], markdown_dir: str, reset_vector: bool = False, reset_rag: bool = False) -> Tuple[VectorDatabase, RAGDatabase]
ベクトルデータベースとRAGデータベースを同期します。

- **パラメータ**:
  - `db_config`: データベース接続設定（辞書型）
  - `markdown_dir`: Markdownファイルのディレクトリパス
  - `reset_vector`: ベクトルデータベースをリセットするかどうか（デフォルト: False）
  - `reset_rag`: RAGデータベースをリセットするかどうか（デフォルト: False）
- **戻り値**:
  - ベクトルデータベースとRAGデータベースのタプル

この関数は以下の処理を行います：
1. ベクトルデータベースの更新
2. RAGデータベースの更新
3. 両データベースの同期完了メッセージの表示

### setup_db_config() -> Dict[str, Any]
環境変数からデータベース接続設定を取得します。

- **戻り値**:
  - データベース接続設定（辞書型）

### main()
コマンドライン引数を解析し、データベース同期を実行します。

## コマンドラインオプション
- `--markdown-dir`: Markdownファイルのディレクトリパス（デフォルト: ./data/markdowns）
- `--reset-vector`: ベクトルデータベースのテーブルをリセット
- `--reset-rag`: RAGデータベースのテーブルをリセット
- `--reset-all`: すべてのデータベーステーブルをリセット

## 使用例
```bash
# 基本的な使用方法
python database_updater.py

# 特定のディレクトリのMarkdownファイルを処理
python database_updater.py --markdown-dir ./my_documents

# ベクトルデータベースをリセットして実行
python database_updater.py --reset-vector

# すべてのデータベースをリセットして実行
python database_updater.py --reset-all
```

## 依存関係
- os
- sys
- argparse
- logging
- typing.Dict, Any, Tuple, List, Optional
- dotenv.load_dotenv
- vector_database.VectorDatabase
- rag_database.RAGDatabase
- embedding_generator.EmbeddingGenerator
- chunk_processor.chunk_splitter
