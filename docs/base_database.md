# base_database.py

## 概要
このモジュールはPostgreSQLデータベースの基本操作を提供する基底クラスを実装しています。他のデータベース関連クラス（VectorDatabase、RAGDatabaseなど）の基盤となるクラスです。

## クラス: BaseDatabase

### 初期化
```python
def __init__(self, db_config)
```

- **パラメータ**:
  - `db_config`: データベース接続設定（辞書型）。host, database, user, password, portなどの接続情報を含む

### 属性
- `db_config`: データベース接続設定
- `connection`: データベース接続オブジェクト
- `logger`: ロガーオブジェクト

### メソッド

#### connect()
データベースに接続します。

#### disconnect()
データベースから切断します。

#### get_connection()
コネクションのコンテキストマネージャを提供します。接続がない場合は自動的に接続を確立します。

使用例:
```python
with db.get_connection() as conn:
    # connを使用した処理
```

#### get_cursor()
カーソルのコンテキストマネージャを提供します。

使用例:
```python
with db.get_cursor() as cursor:
    # cursorを使用した処理
```

#### execute_query(query, params=None, fetch=True)
SQLクエリを実行します。

- **パラメータ**:
  - `query`: 実行するSQLクエリ
  - `params`: クエリパラメータ（タプル、辞書、またはNone）
  - `fetch`: 結果を取得するかどうか（デフォルト: True）
- **戻り値**:
  - クエリ結果のリスト（fetch=Trueの場合）

#### execute_many(query, params_list)
複数のパラメータセットでSQLクエリを実行します。

- **パラメータ**:
  - `query`: 実行するSQLクエリ
  - `params_list`: パラメータのリスト

#### commit()
トランザクションをコミットします。

#### rollback()
トランザクションをロールバックします。

#### table_exists(table_name)
テーブルが存在するかチェックします。

- **パラメータ**:
  - `table_name`: チェックするテーブル名
- **戻り値**:
  - テーブルが存在する場合はTrue、存在しない場合はFalse

## 依存関係
- psycopg2: PostgreSQLデータベース接続用のライブラリ
- logging: ログ出力用のライブラリ
- contextlib.contextmanager: コンテキストマネージャ作成用のデコレータ

## 使用例
```python
# データベース接続設定
db_config = {
    'host': 'localhost',
    'database': 'my_database',
    'user': 'postgres',
    'password': 'password',
    'port': '5432'
}

# BaseDatabase のインスタンス化
db = BaseDatabase(db_config)

# データベースに接続
db.connect()

# クエリの実行
results = db.execute_query("SELECT * FROM my_table WHERE id = %s", (1,))

# トランザクションのコミット
db.commit()

# データベースから切断
db.disconnect()
```
