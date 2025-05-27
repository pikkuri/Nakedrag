# RAGのセットアップ方法

## 環境構築

- OS:Windows11
- 言語:Python3.10
- フレームワーク:LangChain, Ollama
- ベクトルDB:PostgreSQL, pgvector

## 初期セットアップ手順

1. Python 3.10をインストール

    以下の手続きはお任せ

    1.1 Python 3.10.11をダウンロード
    
    1.2 Python 3.10.11をインストール
    
    1.3 Python 3.10.11を有効化

2. 仮想環境を作成までの手続き

    - 参考：https://qiita.com/24Century/items/553086d840f2b67b569e


    - 2.1 環境管理ツールuvをインストール

    powershellを開いて以下のコマンドを実行

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    # もしくはpipを使用
    pip install uv
    ```

    - 2.2 uvのインストールチェック<br>

    環境が変わったことを反映させるためにpowershellを再起動してから以下のコマンドを実行

    ```powershell
    uv version

    PS > uv version
    warning: Failed to read project metadata (No `pyproject.toml` found in current directory or any parent directory). Running `uv self version` for compatibility. This fallback will be removed in the future; pass `--preview` to force an error.
    uv 0.7.8 (0ddcc1905 2025-05-23)
    ```

    このようになっていたらOK

    - 2.3 仮想環境を有効化<br>

    powershellでパッケージのメインディレクトリまで入ってから以下のコマンドを実行

    ```powershell
    cd NakedRAG

    uv venv

    .\.venv\Scripts\activate
    ```

    - 2.4 環境の反映同期<br>

    powershellで以下のコマンドを実行

    ```powershell
    uv sync
    ```

    requirements.txtが更新または追加されている場合は以下のコマンドでも可能

    ```powershell
    uv pip install -r requirements.txt
    ```

3. データベースのインストール

    PostgreSQLをインストールしてください。

    参考：https://www.postgresql.org/download/

    visualstudio 2022のインストールをしてください。

    参考：https://visualstudio.microsoft.com/ja/downloads/

    pgvectorの拡張機能をインストールしてください。

    参考：https://github.com/pgvector/pgvector  

    上から順番に手続きを進めていけば行けます。

    pgvectorのインストール後は、win + R で検索を開き、services.mscを入力して、PostgreSQLのサービスを再起動してください。

    pgvectorガチャンとインストールされているかの確認は以下の手続きで行えます。

    ```powershell
    # データベースに接続（デフォルトだとpostgresユーザーで接続）
    psql -U postgres

    # pgvectorがインストールされているか確認
    SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
    ```

    vectorが見つかっていればインストール完了。


## 以降のセットアップ手順

1. パッケージ内に移動

    ```powershell
    cd NakedRAG
    ```

2. 仮想環境の有効化

    ```powershell
    .\.venv\Scripts\activate
    ```

3. 仮想環境の終了方法

    ```powershell
    deactivate
    ```

## プログラムの実行方法

```powershell
uv run main.py
```



# メモ

# ベクトルデータベースのインスタンス化
vector_db = VectorDatabase(db_config)

# データベース接続とテーブル作成
vector_db.connect()
vector_db.create_table()

# Markdownディレクトリ内のファイルを処理
total_chunks = vector_db.process_markdown_directory()
print(f"{total_chunks}個のチャンクが処理されました")

# 定期的な更新（新規ファイルの処理と削除されたファイルのデータ削除）
new_chunks, updated_chunks, deleted_chunks = vector_db.update_markdown_directory()


# RAGデータベースのインスタンス化
rag_db = RAGDatabase(db_config)

# テーブルの作成（まだ存在しない場合）
rag_db.connect()
rag_db.create_table()

# vector_databaseからデータを取得してL2ノルム正規化し、ivfflatインデックスを作成
rag_db.build_from_vector_database()

# 高速な類似検索（ivfflatインデックスを使用）
results = rag_db.search_similar(query_embedding, limit=5, probes=10)

# より正確な検索が必要な場合（インデックスを使用しない）
exact_results = rag_db.search_similar_exact(query_embedding, limit=5)

