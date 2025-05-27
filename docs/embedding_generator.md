# embedding_generator.py

## 概要
このモジュールはテキストからエンベディング（埋め込みベクトル）を生成する機能を提供します。SentenceTransformerライブラリを使用して、テキストを固定長のベクトル表現に変換します。

## クラス: EmbeddingGenerator

### 初期化
```python
def __init__(self, model_name: str = "intfloat/multilingual-e5-large")
```

- **パラメータ**:
  - `model_name`: 使用するモデル名（デフォルト: "intfloat/multilingual-e5-large"）

### 属性
- `model`: SentenceTransformerモデル
- `logger`: ロガー

### メソッド

#### generate_embedding(text: str) -> List[float]
テキストからエンベディングを生成します。

- **パラメータ**:
  - `text`: エンベディングを生成するテキスト
- **戻り値**:
  - エンベディング（浮動小数点数のリスト）

処理内容:
- テキストに "query: " プレフィックスを追加（multilingual-e5-largeモデルの場合）
- モデルを使用してエンベディングを生成
- numpy配列をリストに変換して返す

#### generate_embeddings(texts: List[str]) -> List[List[float]]
複数のテキストからエンベディングを生成します。バッチ処理を行うため、多数のテキストを処理する場合に効率的です。

- **パラメータ**:
  - `texts`: エンベディングを生成するテキストのリスト
- **戻り値**:
  - エンベディングのリスト

処理内容:
- 各テキストに "query: " プレフィックスを追加（必要な場合）
- バッチ処理でエンベディングを生成
- numpy配列をリストに変換して返す

#### generate_search_embedding(query: str) -> List[float]
検索クエリからエンベディングを生成します。検索用のクエリに特化した処理を行います。

- **パラメータ**:
  - `query`: 検索クエリ
- **戻り値**:
  - エンベディング（浮動小数点数のリスト）

処理内容:
- クエリに "query: " プレフィックスを追加（必要な場合）
- モデルを使用してエンベディングを生成
- numpy配列をリストに変換して返す

## 依存関係
- logging
- typing.List
- sentence_transformers.SentenceTransformer

## 使用例
```python
# エンベディング生成器のインスタンス化
embedding_generator = EmbeddingGenerator()

# 単一テキストからエンベディングを生成
text = "これはサンプルテキストです。"
embedding = embedding_generator.generate_embedding(text)

# 複数テキストからエンベディングを生成
texts = ["テキスト1", "テキスト2", "テキスト3"]
embeddings = embedding_generator.generate_embeddings(texts)

# 検索クエリからエンベディングを生成
query = "検索キーワード"
query_embedding = embedding_generator.generate_search_embedding(query)
```
