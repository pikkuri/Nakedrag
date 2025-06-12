# Ollama設定ガイド

このドキュメントでは、NakedRAGプロジェクトにおけるOllamaの設定方法について説明します。

## 環境変数の設定

NakedRAGは`.env`ファイルを使用してOllamaの設定を管理します。以下の環境変数が利用可能です：

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `OLLAMA_MODEL` | 使用するOllamaモデル名 | `gemma3:12b` |
| `OLLAMA_HOST` | Ollamaサーバーのホスト | `localhost` |
| `OLLAMA_PORT` | Ollamaサーバーのポート | `11434` |
| `OLLAMA_BASE_URL` | Ollamaサーバーの完全なベースURL（設定した場合、HOST/PORTより優先） | なし |
| `LLM_TEMPERATURE` | LLMの温度パラメータ（0.0～1.0） | `0.1` |

## 設定例

### ローカルOllamaサーバーの使用

```
OLLAMA_MODEL=gemma3:12b
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_BASE_URL=
LLM_TEMPERATURE=0.1
```

### リモートOllamaサーバーの使用

```
OLLAMA_MODEL=gemma3:12b
OLLAMA_HOST=192.168.1.100
OLLAMA_PORT=11434
OLLAMA_BASE_URL=
LLM_TEMPERATURE=0.1
```

### 完全なURLを使用する場合

```
OLLAMA_MODEL=gemma3:12b
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_BASE_URL=http://my-ollama-server.example.com:11434
LLM_TEMPERATURE=0.1
```

この場合、`OLLAMA_BASE_URL`が設定されているため、`OLLAMA_HOST`と`OLLAMA_PORT`は無視されます。

## 異なるモデルの使用

Ollamaで利用可能な別のモデルを使用する場合は、`OLLAMA_MODEL`を変更します：

```
OLLAMA_MODEL=llama3:8b
```

## 温度パラメータの調整

生成される回答のランダム性を調整するには、`LLM_TEMPERATURE`を変更します：

- 低い値（0.0～0.3）：より決定論的で一貫性のある回答
- 中間の値（0.3～0.7）：バランスの取れた創造性
- 高い値（0.7～1.0）：より多様で創造的な回答

```
LLM_TEMPERATURE=0.5
```

## 影響を受けるファイル

以下のファイルがこれらの環境変数を使用するように更新されています：

- `src/rag_searcher.py`
- `src/chunk_processor.py`
- `test/rag_search_test.py`

## トラブルシューティング

### Ollamaサーバーに接続できない場合

1. Ollamaサーバーが実行されていることを確認します
2. `.env`ファイルの`OLLAMA_HOST`と`OLLAMA_PORT`が正しいことを確認します
3. ファイアウォールがポートをブロックしていないことを確認します
4. リモートサーバーを使用している場合は、ネットワーク接続を確認します

### モデルが見つからない場合

1. Ollamaサーバーに指定されたモデルがインストールされていることを確認します
2. `ollama list`コマンドを実行して利用可能なモデルを確認します
3. 必要に応じて`ollama pull モデル名`でモデルをインストールします
