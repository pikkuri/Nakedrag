# rag_database.py

## 概要
このモジュールはRAG（Retrieval-Augmented Generation）用のデータベース操作を提供します。`BaseDatabase`を継承し、RAG特有の機能を追加しています。実際にRAGが参照するデータベースとして機能し、vector_database.pyからデータを取得して埋め込みベクトルをL2ノルム正規化した上で格納します。

## クラス: RAGDatabase

### 主な改善点

1. **埋め込みベクトルの正規化の改善** - ゼロベクトルや非常に小さいノルムのベクトルに対する適切な処理と警告ログの追加
2. **動的なprobes設定** - pgvectorのドキュメントで推奨されているsqrt(lists)を使用するように変更
3. **PostgreSQLクエリの最適化** - search_similar_exactがPostgreSQLのクエリプランナー設定を適切に管理するように改善
4. **型ヒント** - コードの可読性と静的解析のためのPythonの型ヒントの追加
5. **エラーハンドリング** - finallyブロックでの適切なリソースのクリーンアップによるエラーハンドリングの強化

### 初期化
```python
def __init__(self, db_config: Dict[str, str], dimension: int = 1024, vector_db_config: Optional[Dict[str, str]] = None)
```

- **パラメータ**:
  - `db_config`: データベース接続設定（辞書型）
  - `dimension`: ベクトルの次元数（デフォルト: 1024）
  - `vector_db_config`: ベクトルデータベースの接続設定（デフォルト: None）。Noneの場合は環境変数から取得

### 主なメソッド

#### create_table()
RAG用のドキュメントテーブルを作成します。pgvectorエクステンションを使用します。エラーハンドリングが強化されています。

**注意**: インデックスはデータ挿入後に作成するため、ここでは作成しません。

#### reset_table()
テーブルをリセットします（全データを削除し、テーブルを再作成します）。エラーハンドリングが強化されています。

#### _normalize_embedding(embedding: List[float]) -> List[float]
埋め込みベクトルをL2ノルムで正規化します。ゼロベクトルや非常に小さいノルムのベクトルに対する処理が改善されています。

- **パラメータ**:
  - `embedding`: 正規化する埋め込みベクトル
- **戻り値**:
  - 正規化された埋め込みベクトル

#### build_from_vector_database()
ベクトルデータベースから直接データを取得し、L2ノルム正規化して格納します。vector_database.pyで作成されるデータベースのデータを取得し、バッチ処理を使用して効率的にデータを格納します。

- **戻り値**:
  - 格納されたドキュメントの数

#### create_search_index()
検索用のIVFFLATインデックスを作成します。データ量に応じてクラスタ数(lists)を動的に設定します。

- 少量データ（1000件未満）: 10クラスタ
- 中量データ: sqrt(n)を目安
- 大量データ（100万件以上）: 1000クラスタ

#### insert_document(text, embedding, filename, filepath, chunk_index=None)
ドキュメントをRAGテーブルに挿入します。埋め込みベクトルを自動的に正規化します。

- **パラメータ**:
  - `text`: テキストチャンク
  - `embedding`: ベクトル埋め込み
  - `filename`: ファイル名
  - `filepath`: ファイルパス
  - `chunk_index`: チャンクのインデックス（デフォルト: None）
- **戻り値**:
  - 挿入されたドキュメントのID、エラー時はNone

#### search_similar(query_embedding: List[float], limit: int = 5, probes: Optional[int] = None, similarity_threshold: float = 0.0) -> List[Tuple]
ivfflatインデックスを使用して類似ドキュメントを高速に検索します。probesパラメータが自動設定されるように改善されています。

- **パラメータ**:
  - `query_embedding`: 検索クエリのベクトル埋め込み
  - `limit`: 返す結果の最大数（デフォルト: 5）
  - `probes`: 検索時に調査するクラスタ数（Noneの場合は自動設定）
  - `similarity_threshold`: 類似度の最小閾値（0～1の間、デフォルト: 0.0）
- **戻り値**:
  - 類似度順に並べられたドキュメントのリスト

#### search_similar_exact(query_embedding: List[float], limit: int = 5, similarity_threshold: float = 0.0) -> List[Tuple]
インデックスを使用せずに正確な類似ドキュメント検索を行います。PostgreSQLのクエリプランナー設定を適切に管理するように改善されています。

- **パラメータ**:
  - `query_embedding`: 検索クエリのベクトル埋め込み
  - `limit`: 返す結果の最大数（デフォルト: 5）
  - `similarity_threshold`: 類似度の最小閾値（0～1の間、デフォルト: 0.0）
- **戻り値**:
  - 類似度順に並べられたドキュメントのリスト

#### get_document_by_id(doc_id)
IDによりドキュメントを取得します。エラーハンドリングが強化されています。

- **パラメータ**:
  - `doc_id`: ドキュメントID
- **戻り値**:
  - ドキュメント情報、見つからない場合はNone

#### get_document_count()
ドキュメントの総数を取得します。

- **戻り値**:
  - ドキュメントの総数

#### get_unique_sources()
ユニークなファイルのリストを取得します。エラーハンドリングが強化されています。

- **戻り値**:
  - ファイルのリスト（ファイル名とパス）

#### delete_document(doc_id)
ドキュメントを削除します。エラーハンドリングが強化されています。

- **パラメータ**:
  - `doc_id`: 削除するドキュメントのID
- **戻り値**:
  - 削除が成功した場合はTrue、失敗した場合はFalse

### データベーススキーマの変更

データベーススキーマが一貫性を持つように列名が変更されました：
- `original_text` → `chunk_text`
- `source_filename` → `filename`
- `source_filepath` → `filepath`

## 依存関係
- base_database.BaseDatabase
- logging
- numpy
- psycopg2
- psycopg2.extras.execute_batch
- os
- typing.Dict, List, Tuple, Any, Optional, Union
