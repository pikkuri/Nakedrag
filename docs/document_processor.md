# document_processor.py

## 概要
このモジュールはマークダウン、テキスト、パワーポイント、PDFなどのファイルの読み込みと解析、チャンク分割を行うための機能を提供します。様々な形式のドキュメントを処理し、RAGシステムで使用できるチャンクに変換します。

## クラス: DocumentProcessor

### 初期化
```python
def __init__(self)
```

### クラス属性
- `SUPPORTED_EXTENSIONS`: サポートするファイル拡張子の辞書
  - "text": [".txt", ".md", ".markdown"]
  - "office": [".ppt", ".pptx", ".doc", ".docx"]
  - "pdf": [".pdf"]

### メソッド

#### read_file(file_path: str) -> str
ファイルを読み込みます。

- **パラメータ**:
  - `file_path`: ファイルのパス
- **戻り値**:
  - ファイルの内容
- **例外**:
  - `FileNotFoundError`: ファイルが見つからない場合
  - `IOError`: ファイルの読み込みに失敗した場合

処理内容:
- テキストファイル（.txt, .md, .markdown）はそのまま読み込み
- オフィスファイル（.ppt, .pptx, .doc, .docx）とPDFファイル（.pdf）はマークダウンに変換
- サポートしていない拡張子の場合は空文字列を返す

#### convert_to_markdown(file_path: str) -> str
パワーポイント、Word、PDFなどのファイルをマークダウンに変換します。

- **パラメータ**:
  - `file_path`: ファイルのパス
- **戻り値**:
  - マークダウンに変換された内容
- **例外**:
  - `Exception`: 変換に失敗した場合

#### split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]
テキストをチャンクに分割します。

- **パラメータ**:
  - `text`: 分割するテキスト
  - `chunk_size`: チャンクサイズ（文字数）（デフォルト: 500）
  - `overlap`: チャンク間のオーバーラップ（文字数）（デフォルト: 100）
- **戻り値**:
  - チャンクのリスト

#### calculate_file_hash(file_path: str) -> str
ファイルのハッシュ値を計算します。

- **パラメータ**:
  - `file_path`: ファイルのパス
- **戻り値**:
  - ファイルのSHA-256ハッシュ値

#### get_file_metadata(file_path: str) -> Dict[str, Any]
ファイルのメタデータを取得します。

- **パラメータ**:
  - `file_path`: ファイルのパス
- **戻り値**:
  - ファイルのメタデータ（ハッシュ値、最終更新日時、サイズなど）

#### load_file_registry(processed_dir: str) -> Dict[str, Dict[str, Any]]
処理済みファイルのレジストリを読み込みます。

- **パラメータ**:
  - `processed_dir`: 処理済みファイルを保存するディレクトリのパス
- **戻り値**:
  - 処理済みファイルのレジストリ（ファイルパスをキーとするメタデータの辞書）

#### save_file_registry(processed_dir: str, registry: Dict[str, Dict[str, Any]])
処理済みファイルのレジストリを保存します。

- **パラメータ**:
  - `processed_dir`: 処理済みファイルを保存するディレクトリのパス
  - `registry`: 処理済みファイルのレジストリ

#### process_file(file_path: str, processed_dir: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]
ファイルを処理します。

- **パラメータ**:
  - `file_path`: ファイルのパス
  - `processed_dir`: 処理済みファイルを保存するディレクトリのパス
  - `chunk_size`: チャンクサイズ（文字数）（デフォルト: 500）
  - `overlap`: チャンク間のオーバーラップ（文字数）（デフォルト: 100）
- **戻り値**:
  - 処理結果のリスト（各要素はチャンク情報を含む辞書）

#### process_directory(source_dir: str, processed_dir: str, chunk_size: int = 500, overlap: int = 100, incremental: bool = False) -> List[Dict[str, Any]]
ディレクトリ内のファイルを処理します。

- **パラメータ**:
  - `source_dir`: 原稿ファイルが含まれるディレクトリのパス
  - `processed_dir`: 処理済みファイルを保存するディレクトリのパス
  - `chunk_size`: チャンクサイズ（文字数）（デフォルト: 500）
  - `overlap`: チャンク間のオーバーラップ（文字数）（デフォルト: 100）
  - `incremental`: 差分のみを処理するかどうか（デフォルト: False）
- **戻り値**:
  - 処理結果のリスト（各要素はチャンク情報を含む辞書）

処理内容:
- ディレクトリ内のサポートされているファイルを検索
- 差分処理の場合は、変更されたファイルのみを処理
- 各ファイルを読み込み、チャンクに分割
- 処理結果とファイルレジストリを保存

## 依存関係
- logging
- os
- json
- pathlib.Path
- typing.List, Dict, Any
- hashlib
- time
- markitdown: オフィスファイルやPDFをマークダウンに変換するライブラリ
