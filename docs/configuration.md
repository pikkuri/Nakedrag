# 設定ファイルの説明

## agent_settings.json

このファイルはNakedRAGシステムの主要な設定を管理します。

### ファイル構成

```json
{
  "agents": {
    "エージェント名": {
      "role": "エージェントの役割",
      "model": "使用するモデル名",
      "temperature": 生成時の温度（0-1の値）,
      "system_message": {
        "description": "システムメッセージの説明",
        "content": [
          "システムメッセージの内容（配列の各要素は改行で結合）"
        ]
      },
      "rag_database_introduction": {
        "description": "RAGデータベースの説明",
        "content": [
          "RAGデータベースの説明文（配列の各要素は改行で結合）"
        ]
      },
      "templates": {
        "search_query": "検索クエリのテンプレート",
        "in_scope_response": "範囲内応答のテンプレート",
        "out_of_scope_response": "範囲外応答のテンプレート",
        "no_results": "検索結果なしの応答テンプレート"
      }
    }
  },
  "rag_database": {
    "chunk_size": チャンクサイズ（文字数）,
    "overlap_size": オーバーラップサイズ（文字数）,
    "similarity_threshold": 類似度閾値（0-1の値）,
    "max_results": 最大検索結果数
  },
  "embedding": {
    "model_name": "埋め込みモデルの名前",
    "cache_dir": "モデルのキャッシュディレクトリ"
  }
}
```

### 設定項目の説明

#### agents セクション

各エージェントの設定を定義します。複数のエージェントを定義できます。

- **role**: エージェントの役割を示す識別子
- **model**: 使用するLLMモデル（例：gemma:7b）
- **temperature**: 生成時の多様性（0=決定的、1=創造的）
- **system_message**: エージェントの基本的な振る舞いを定義
  - description: システムメッセージの説明
  - content: システムメッセージの本文（配列）
- **rag_database_introduction**: RAGシステムの説明
  - description: 説明文の概要
  - content: 説明文の本文（配列）
- **templates**: 各種応答テンプレート
  - search_query: 検索クエリ生成用
  - in_scope_response: 範囲内の質問への応答
  - out_of_scope_response: 範囲外の質問への応答
  - no_results: 検索結果がない場合の応答

#### rag_database セクション

RAGシステムの動作パラメータを設定します。

- **chunk_size**: 文書を分割する際のチャンクサイズ
- **overlap_size**: チャンク間のオーバーラップサイズ
- **similarity_threshold**: 検索時の類似度閾値
- **max_results**: 返す検索結果の最大数

#### embedding セクション

埋め込みモデルの設定を行います。

- **model_name**: 使用する埋め込みモデルの名前
- **cache_dir**: モデルファイルを保存するディレクトリ

### 使用例

1. 新しいエージェントの追加:
```json
{
  "agents": {
    "research_assistant": {
      "role": "research_assistant",
      "model": "gemma:7b",
      "temperature": 0.5,
      "system_message": {
        "description": "研究アシスタントの役割定義",
        "content": ["研究支援の指示を記述"]
      }
    }
  }
}
```

2. テンプレートの変数:
- `{user_query}`: ユーザーの質問
- `{scope_description}`: エージェントの対応範囲の説明

### 注意事項

- JSONファイルにコメントを含めることはできません
- 設定変更後は、アプリケーションの再起動が必要な場合があります
- テンプレート内の変数は `{変数名}` の形式で指定します
