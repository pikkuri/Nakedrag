# vector_database.py

## 概要
このモジュールはMarkdownファイルをベクトル化して格納するデータベース機能を提供します。`./data/markdowns`内のmdファイルを全てRAGで使用するベクトルの形に変換し、データを蓄積します。

## クラス: VectorDatabase

`BaseDatabase`を継承し、Markdownファイルの処理とベクトル化を行うためのクラスです。

### 初期化
```python
def __init__(self, db_config: Dict[str, Any], dimension: int = 1024, markdown_dir: str = "./data/markdowns", 
             model_name: str = "intfloat/multilingual-e5-large", chunk_size: int = 500, chunk_overlap: int = 100)
```

- **パラメータ**:
  - `db_config`: データベース接続設定（辞書型）
  - `dimension`: ベクトルの次元数（デフォルト: 1024）
  - `markdown_dir`: Markdownファイルが格納されているディレクトリ（デフォルト: "./data/markdowns"）
  - `model_name`: 埋め込みベクトル生成に使用するモデル名（デフォルト: "intfloat/multilingual-e5-large"）
  - `chunk_size`: チャンクのサイズ（デフォルト: 500）
  - `chunk_overlap`: チャンクの重複サイズ（デフォルト: 100）

### 主なメソッド

#### create_table() -> None
Markdownファイルのテキストとベクトルを格納するテーブルを作成します。

#### store_markdown_chunk(chunk_text: str, embedding: List[float], filename: str, filepath: str, chunk_index: int) -> Optional[int]
Markdownのチャンクとそのベクトル埋め込みを保存します。

- **パラメータ**:
  - `chunk_text`: Markdownテキストのチャンク
  - `embedding`: ベクトル埋め込み
  - `filename`: ファイル名
  - `filepath`: ファイルパス
  - `chunk_index`: チャンクのインデックス
- **戻り値**:
  - 挿入されたチャンクのID、エラー時はNone

#### store_markdown_chunks(chunks: List[Dict[str, Any]]) -> List[int]
複数のMarkdownチャンクを一括して保存します。バッチ処理を使用して効率的に保存します。

- **パラメータ**:
  - `chunks`: 保存するチャンクのリスト。各チャンクは `{'chunk_text': str, 'embedding': list, 'filename': str, 'filepath': str, 'chunk_index': int}` の形式
- **戻り値**:
  - 挿入されたチャンクのIDリスト

#### get_all_vectors() -> List[Tuple]
データベースから全てのベクトルを取得します。RAGデータベースの構築に使用されます。

- **戻り値**:
  - 全てのベクトルデータ

#### get_file_vectors(filepath: str) -> List[Tuple]
特定のファイルに関連するベクトルを取得します。

- **パラメータ**:
  - `filepath`: ファイルパス
- **戻り値**:
  - ファイルに関連するベクトルデータ

#### get_processed_files() -> List[str]
すでに処理されたファイルのリストを取得します。

- **戻り値**:
  - 処理済みファイルのパスリスト

#### delete_file_vectors(filepath: str) -> int
特定のファイルに関連するベクトルを削除します。エラーハンドリングが強化されています。

- **パラメータ**:
  - `filepath`: 削除するファイルのパス
- **戻り値**:
  - 削除されたベクトルの数

#### clear_table() -> bool
テーブルの全データを削除します。エラーハンドリングが強化されています。

- **戻り値**:
  - 成功した場合はTrue、失敗した場合はFalse

#### process_markdown_directory() -> int
Markdownディレクトリ内の全ての.mdファイルを処理します。

- **戻り値**:
  - 処理されたチャンクの総数

#### update_markdown_directory() -> Tuple[int, int, int]
Markdownディレクトリ内のファイルを更新します。新しいファイルを処理し、削除されたファイルのデータを削除します。

- **戻り値**:
  - `Tuple[int, int, int]`: (新規チャンク数, 更新チャンク数, 削除チャンク数)

### 内部メソッド

#### _init_embedding_generator() -> None
埋め込みベクトル生成器を初期化します。

#### _read_markdown_file(file_path: str) -> str
Markdownファイルを読み込みます。エラーハンドリングが強化されています。

- **パラメータ**:
  - `file_path`: ファイルパス
- **戻り値**:
  - ファイルの内容

#### _process_markdown_file(file_path: str) -> List[Dict[str, Any]]
Markdownファイルを処理し、チャンク化して埋め込みベクトルを生成します。

- **パラメータ**:
  - `file_path`: ファイルパス
- **戻り値**:
  - チャンクと埋め込みベクトルのリスト

## 依存関係
- base_database.BaseDatabase
- logging
- os
- glob
- json
- pathlib
- typing.List, Dict, Any, Tuple, Optional
- psycopg2.extras.execute_batch
- chunk_processor.clean_text, chunk_splitter
- embedding_generator.EmbeddingGenerator
