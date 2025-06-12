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

### メインプログラム

```powershell
uv run app.py
```

#### app.pyのコマンドラインオプション

app.pyは以下のコマンドラインオプションをサポートしています：

```powershell
uv run app.py [オプション]
```

| オプション | 説明 |
| --- | --- |
| `--init` | 起動前にRAGシステムを初期化します |
| `--mcp` | MCPサーバーを有効にします（環境変数の設定より優先） |
| `--api` | APIサーバーを有効にします（環境変数の設定より優先） |
| `--line` | LINE Botサーバーを有効にします（環境変数の設定より優先） |
| `--web` | Webサーバーを有効にします（環境変数の設定より優先） |
| `--all` | 全てのサーバーを有効にします（環境変数の設定より優先） |
| `--help` | ヘルプメッセージを表示します |

例：

```powershell
# 全てのサーバーを起動
uv run app.py --all

# APIサーバーのみを起動
uv run app.py --api

# RAGシステムを初期化してからMCPサーバーを起動
uv run app.py --init --mcp
```

#### 環境変数による設定

app.pyは以下の環境変数を使用してサーバーの有効/無効を制御します：

| 環境変数 | 説明 | デフォルト値 |
| --- | --- | --- |
| `MCP_SERVER_ENABLED` | MCPサーバーを有効にするかどうか | `false` |
| `API_SERVER_ENABLED` | APIサーバーを有効にするかどうか | `false` |
| `LINE_BOT_ENABLED` | LINE Botサーバーを有効にするかどうか | `false` |
| `WEB_SERVER_ENABLED` | Webサーバーを有効にするかどうか | `false` |

環境変数は`.env`ファイルで設定できます。コマンドラインオプションが指定された場合は、環境変数の設定より優先されます。

#### 終了方法

app.pyを終了するには、コンソールで`Ctrl+C`を押してください。すべてのサーバーが適切に終了し、共有リソース（司書エージェントなど）がクリーンアップされます。

### APIサーバーの起動

FastAPIを使用したAPIサーバーを起動します：

```powershell
uv run .\src\server\fastapi_server.py
```

サーバーは`http://localhost:8000`でリッスンします。

### APIクライアントの実行

対話型のAPIクライアントを実行します：

```powershell
uv run .\src\server\fastapi_client.py
```

クライアントを起動すると、コマンドラインで質問を入力できます。質問に対する回答はRAGシステムによって生成され、関連する参考資料へのリンクも表示されます。

終了するには `exit` または `quit` と入力してください。

### 注意事項

- APIサーバーを起動する前に、Ollamaサーバーが実行されていることを確認してください。
- 環境変数`OLLAMA_MODEL`に設定されているモデル（デフォルト: `gemma3:12b`）がOllamaにインストールされている必要があります。
