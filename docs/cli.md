# cli.py

## 概要
このモジュールはRAGシステムのコマンドラインインターフェース（CLI）を提供します。インデックスのクリアとインデックス化を行うためのコマンドラインツールです。

## 主な機能

### setup_logging()
ロギングの設定を行います。

- **戻り値**:
  - 設定されたロガーオブジェクト

### clear_index()
インデックスをクリアします。

処理内容:
- ファイルレジストリの削除
- インデックス内のすべてのドキュメントの削除

### index_documents(directory_path, chunk_size=500, chunk_overlap=100, incremental=False)
ドキュメントをインデックス化します。

- **パラメータ**:
  - `directory_path`: インデックス化するドキュメントが含まれるディレクトリのパス
  - `chunk_size`: チャンクサイズ（文字数）（デフォルト: 500）
  - `chunk_overlap`: チャンク間のオーバーラップ（文字数）（デフォルト: 100）
  - `incremental`: 差分のみをインデックス化するかどうか（デフォルト: False）

処理内容:
- 指定されたディレクトリ内のドキュメントを読み込み
- ドキュメントをチャンクに分割
- チャンクをインデックス化

### get_document_count()
インデックス内のドキュメント数を取得します。

### main()
メイン関数。コマンドライン引数を解析し、適切な処理を実行します。

サポートされるコマンド:
- `clear`: インデックスをクリアする
- `index`: ドキュメントをインデックス化する
  - `--directory`, `-d`: インデックス化するドキュメントが含まれるディレクトリのパス
  - `--chunk-size`, `-s`: チャンクサイズ（文字数）
  - `--chunk-overlap`, `-o`: チャンク間のオーバーラップ（文字数）
  - `--incremental`, `-i`: 差分のみをインデックス化する
- `count`: インデックス内のドキュメント数を取得する

## 依存関係
- sys
- os
- argparse
- logging
- pathlib.Path
- dotenv.load_dotenv
- .rag_tools.create_rag_service_from_env

## 使用例
```bash
# インデックスをクリア
python -m src.cli clear

# ドキュメントをインデックス化
python -m src.cli index --directory ./data/source --chunk-size 500 --chunk-overlap 100

# 差分のみをインデックス化
python -m src.cli index --directory ./data/source --incremental

# インデックス内のドキュメント数を取得
python -m src.cli count
```
