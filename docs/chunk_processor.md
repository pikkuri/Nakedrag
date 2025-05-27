# chunk_processor.py

## 概要
このモジュールはテキストの前処理とチャンク分割を行うための機能を提供します。HTMLタグの除去、マークダウン記法の削除、テキストのクリーニング、そしてLLMを使用したテキストの整形とチャンク分割を行います。

## 主な機能

### clean_text(text: str) -> str
テキストから不要なタグや記号を除去し、クリーンなテキストを返します。

- **パラメータ**:
  - `text`: 処理する元のテキスト
- **戻り値**:
  - クリーニングされたテキスト

処理内容:
- HTMLタグの除去（script, style, commentsを含む）
- マークダウン記法の除去
- URLとメールアドレスの除去
- 特殊文字や記号の除去
- 全角英数字を半角に変換
- 余分な空白や改行の削除

### organize_text_with_llm(text: str, model: str = "gemma3:12b", temperature: float = 0.0, num_ctx: int = 2048, num_predict: int = 1024) -> str
テキストをLLMで整形し、意味のある単位でチャンク分割されたテキストを返します。

- **パラメータ**:
  - `text`: 整形する元のテキスト
  - `model`: 使用するLLMモデル（デフォルト: "gemma3:12b"）
  - `temperature`: 生成の多様性を制御するパラメータ（デフォルト: 0.0）
  - `num_ctx`: コンテキストウィンドウのサイズ（デフォルト: 2048）
  - `num_predict`: 予測するトークンの最大数（デフォルト: 1024）
- **戻り値**:
  - LLMによって整形されたテキスト

### chunk_splitter(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]
テキストを指定されたサイズのチャンクに分割します。

- **パラメータ**:
  - `text`: 分割する元のテキスト
  - `chunk_size`: 各チャンクの最大サイズ（デフォルト: 500）
  - `chunk_overlap`: チャンク間のオーバーラップサイズ（デフォルト: 100）
- **戻り値**:
  - 分割されたテキストチャンクのリスト

## 依存関係
- re
- unicodedata
- BeautifulSoup (bs4)
- langchain_community.llms.Ollama
- langchain.chains.LLMChain
- langchain.prompts.PromptTemplate
- langchain.text_splitter.RecursiveCharacterTextSplitter
