# データベーススキーマの変更手順

このドキュメントでは、NakedRAGシステムのデータベーススキーマを変更する際の手順を説明します。データベーススキーマの変更は、新しいカラムの追加や既存のカラム名の変更など、データベース構造を変更する必要がある場合に行います。

## 目次

1. [概要](#概要)
2. [変更手順](#変更手順)
3. [影響範囲の確認](#影響範囲の確認)
4. [テストの実行](#テストの実行)
5. [トラブルシューティング](#トラブルシューティング)
6. [変更例](#変更例)

## 概要

NakedRAGシステムでは、以下の2つのデータベーステーブルを使用しています：

1. **vector_embeddings**: ベクトルデータベース内のテーブルで、チャンクテキストと埋め込みベクトルを保存
2. **rag_documents**: RAGデータベース内のテーブルで、検索用のデータを保存

これらのテーブルのスキーマを変更する場合、複数のファイルを修正し、テーブルを再作成する必要があります。

## 変更手順

データベーススキーマを変更する際の基本的な手順は以下の通りです：

### 1. 関連ファイルの修正

以下のファイルを修正して、新しいスキーマに対応させます：

- **src/database_maker.py**: テーブル作成時のSQL定義を修正
  - `create_vector_table`関数のCREATE TABLE文を更新
  - `create_rag_table`関数のCREATE TABLE文を更新

- **src/vector_database.py**: ベクトルデータベースの操作関数を修正
  - `create_table`メソッドのテーブル定義を更新
  - `store_markdown_chunk`メソッドのINSERT文を更新
  - `process_markdown_file`メソッドを必要に応じて修正

- **src/rag_database.py**: RAGデータベースの操作関数を修正
  - `create_table`メソッドのテーブル定義を更新
  - `search_similar`メソッドのSELECT文を更新
  - `search_similar_exact`メソッドのSELECT文を更新

- **src/rag_class.py**: 検索結果の処理を修正
  - `search`メソッドの結果処理部分を更新
  - `search_exact`メソッドの結果処理部分を更新

- **test/rag_search_test.py**: 検索結果の利用方法を修正
  - `search_documents`メソッドを更新

### 2. テーブルリセット設定の有効化

`.env`ファイルの`RESET_TABLES`設定を`True`に変更して、テーブルを強制的に再作成するようにします：

```
# データベース設定
# RESET_TABLES: True（テーブルを強制的に再作成）または False（既存のテーブルを使用）
RESET_TABLES=True
```

### 3. テストの実行

テストを実行して、変更が正しく適用されていることを確認します：

```
uv run .\test\test_rag_pipeline.py
```

### 4. 設定の元に戻す

テストが成功したら、`.env`ファイルの`RESET_TABLES`設定を`False`に戻します：

```
RESET_TABLES=False
```

## 影響範囲の確認

データベーススキーマを変更する際は、以下の点に注意して影響範囲を確認してください：

1. **テーブル定義の整合性**: 全てのファイルで同じテーブル定義が使用されていることを確認
2. **SQL文の更新**: INSERT文やSELECT文など、SQLを使用している箇所を全て更新
3. **結果処理の更新**: 検索結果の処理方法を新しいスキーマに合わせて更新
4. **後方互換性**: 可能であれば、古いスキーマとの互換性を維持する処理を追加

## テストの実行

スキーマ変更後は、以下のテストを実行して動作を確認してください：

1. **テーブル作成テスト**: テーブルが正しく作成されることを確認
2. **データ挿入テスト**: 新しいスキーマでデータが正しく挿入されることを確認
3. **検索テスト**: 検索機能が正しく動作することを確認
4. **エンドツーエンドテスト**: システム全体が正しく動作することを確認

## トラブルシューティング

スキーマ変更時によくある問題と解決策：

1. **カラム不一致エラー**: SQLエラーが発生した場合、テーブル定義とSQL文が一致しているか確認
2. **テーブルリセットの失敗**: `RESET_TABLES`設定が正しく反映されているか確認
3. **検索結果の不整合**: 検索結果の処理方法が新しいスキーマに対応しているか確認

## 変更例

### original_filepathカラムの追加例

以下は、`original_filepath`カラムを追加した例です：

#### database_maker.pyの修正

```python
# vector_embeddingsテーブルの定義を修正
create_table_query = '''
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    original_filepath TEXT,  # 追加
    chunk_index INTEGER,     # 追加
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

# rag_documentsテーブルの定義も同様に修正
```

#### vector_database.pyの修正

```python
def store_markdown_chunk(self, chunk_text, embedding, filename, filepath, chunk_index, original_filepath=None):
    query = f'''
    INSERT INTO {self.table_name} (chunk_text, embedding, filename, filepath, chunk_index, original_filepath)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;
    '''
    # ...
```

#### rag_class.pyの修正

```python
# 検索結果の処理を修正
for result in results:
    # 結果のカラム数に応じて処理を分ける
    if len(result) == 7:  # original_filepathが含まれている場合
        doc_id, text, filename, filepath, original_filepath, chunk_index, similarity = result
    else:  # 従来の形式
        doc_id, text, filename, filepath, chunk_index, similarity = result
        original_filepath = None
    
    formatted_results.append({
        'id': doc_id,
        'text': text,
        'filename': filename,
        'filepath': filepath,
        'original_filepath': original_filepath,
        'chunk_index': chunk_index,
        'similarity': similarity
    })
```

このような手順でデータベーススキーマを変更することで、システム全体の整合性を保ちながら新しい機能を追加できます。
