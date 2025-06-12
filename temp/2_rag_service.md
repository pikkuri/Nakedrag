# rag_service.py

## 概要
このモジュールはRAGサービスを提供します。ドキュメント処理、エンベディング生成、ベクトルデータベースを統合して、インデックス化と検索の機能を提供します。

## クラス: RAGService

### 初期化
```python
def __init__(self, document_processor: DocumentProcessor, embedding_generator: EmbeddingGenerator, vector_database: VectorDatabase)
```

- **パラメータ**:
  - `document_processor`: ドキュメント処理クラスのインスタンス
  - `embedding_generator`: エンベディング生成クラスのインスタンス
  - `vector_database`: ベクトルデータベースクラスのインスタンス

### 属性
- `document_processor`: ドキュメント処理クラスのインスタンス
- `embedding_generator`: エンベディング生成クラスのインスタンス
- `vector_database`: ベクトルデータベースクラスのインスタンス
- `logger`: ロガー

### メソッド

#### index_documents(source_dir, processed_dir=None, chunk_size=500, chunk_overlap=100, incremental=False)
ディレクトリ内のファイルをインデックス化します。

- **パラメータ**:
  - `source_dir`: インデックス化するファイルが含まれるディレクトリのパス
  - `processed_dir`: 処理済みファイルを保存するディレクトリのパス（指定がない場合は"data/processed"）
  - `chunk_size`: チャンクサイズ（文字数）（デフォルト: 500）
  - `chunk_overlap`: チャンク間のオーバーラップ（文字数）（デフォルト: 100）
  - `incremental`: 差分のみをインデックス化するかどうか（デフォルト: False）
- **戻り値**:
  - インデックス化の結果を含む辞書
    - `document_count`: インデックス化されたドキュメント数
    - `processing_time`: 処理時間（秒）
    - `success`: 成功したかどうか
    - `error`: エラーメッセージ（エラーが発生した場合）

#### clear_index()
インデックスをクリアします。

- **戻り値**:
  - クリアの結果を含む辞書
    - `deleted_count`: 削除されたドキュメント数
    - `success`: 成功したかどうか
    - `error`: エラーメッセージ（エラーが発生した場合）

#### get_document_count()
インデックス内のドキュメント数を取得します。

- **戻り値**:
  - ドキュメント数

### 内部処理
- ドキュメントの読み込みと処理
- テキストのチャンク分割
- エンベディングの生成
- ベクトルデータベースへの保存
- 検索機能の提供

## 依存関係
- os
- time
- logging
- typing.List, Dict, Any
- .document_processor.DocumentProcessor
- .embedding_generator.EmbeddingGenerator
- .vector_database.VectorDatabase

## 使用例
```python
# RAGサービスのインスタンス化
document_processor = DocumentProcessor()
embedding_generator = EmbeddingGenerator()
vector_database = VectorDatabase(db_config)
rag_service = RAGService(document_processor, embedding_generator, vector_database)

# ドキュメントのインデックス化
result = rag_service.index_documents(
    source_dir="./data/source",
    processed_dir="./data/processed",
    chunk_size=500,
    chunk_overlap=100,
    incremental=False
)

# インデックスのクリア
clear_result = rag_service.clear_index()

# ドキュメント数の取得
count = rag_service.get_document_count()
```
