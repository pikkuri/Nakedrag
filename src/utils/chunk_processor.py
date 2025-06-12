# -*- coding: utf-8 -*-
import re
import os
import unicodedata
from bs4 import BeautifulSoup, Comment
from typing import List

# dotenvをインポート
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 最新のlangchainの推奨インポート方法に更新
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.utils.logger_util import setup_logger

# ロガーの設定
logger = setup_logger(__name__)

def clean_text(text: str) -> str:
    """
    テキストから不要なタグや記号を除去し、クリーンなテキストを返します。
    """
    # HTMLタグの除去（script, style, comments含む）
    soup = BeautifulSoup(text, "html.parser")
    for element in soup(["script", "style"]):
        element.decompose()
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    text = soup.get_text(separator=" ")

    # マークダウン記法の除去
    markdown_patterns = [
        r'!\[.*?\]\(.*?\)',  # 画像リンク
        r'\[.*?\]\(.*?\)',   # ハイパーリンク
        r'`{1,3}.*?`{1,3}',  # インラインコード
        r'\*\*(.*?)\*\*',    # 太字
        r'\*(.*?)\*',        # イタリック
        r'~~(.*?)~~',        # 取り消し線
        r'^>.*$',            # 引用
        r'^#+\s.*$',         # 見出し
        r'---',              # 水平線
    ]
    for pattern in markdown_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)

    # URLとメールアドレスの除去
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)

    # 特殊文字や記号の除去（英数字、漢字、ひらがな、カタカナ以外を除去）
    text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', '', text)

    # 全角英数字を半角に変換
    text = unicodedata.normalize('NFKC', text)

    # 余分な空白や改行の削除
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def organize_text_with_llm(
    text: str,
    model: str = None,
    temperature: float = None,
    num_ctx: int = 2048,
    num_predict: int = 1024,
) -> str:
    """
    テキストをLLMで整形し、チャンク分割されたテキストのリストを返します。
    """
    # 環境変数から設定を取得
    if model is None:
        model = os.getenv('OLLAMA_MODEL', 'gemma3:12b')
    
    if temperature is None:
        temperature = float(os.getenv('LLM_TEMPERATURE', '0.0'))
    
    # Ollamaサーバーの設定を取得
    ollama_base_url = os.getenv('OLLAMA_BASE_URL')
    ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
    ollama_port = os.getenv('OLLAMA_PORT', '11434')
    
    # クライアント接続用にホスト名を調整
    # 0.0.0.0はサーバー側のリッスン設定であり、クライアントからの接続には使用できない
    if ollama_host == '0.0.0.0':
        client_host = 'localhost'
    else:
        client_host = ollama_host
    
    # base_urlが設定されている場合はそれを使用、そうでなければhost/portから構築
    if ollama_base_url:
        base_url = ollama_base_url
    else:
        # ホスト名にポート番号が含まれていないか確認
        if ':' in client_host:
            # ホスト部分にすでにポートが含まれている場合は、そのまま使用
            base_url = f"http://{client_host}"
        else:
            # 通常のホスト名とポートの組み合わせ
            base_url = f"http://{client_host}:{ollama_port}"
    
    # Ollamaで指定されたモデルを使用するLLMを初期化
    llm = Ollama(
        model=model,
        temperature=temperature,
        num_ctx=num_ctx,
        num_predict=num_predict,
        base_url=base_url
    )

    # プロンプトテンプレートを定義
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=(
            "以下のテキストを読み、内容を改ざんせずに、意味のある単位でチャンクに分割してください。"
            "各チャンクは、文脈的に一貫性があり、情報の損失がないようにしてください。\n\n"
            "テキスト:\n{text}\n\n"
            "チャンク:"
        )
    )

    # LLMChainを作成
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # テキストを整形
    organized_text = chain.run(text)

    return organized_text


def chunk_splitter(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
    """
    テキストをチャンクに分割します。
    """

    # チャンク分割器を初期化
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "．", ".", " ", ""],
        length_function=len,
        is_separator_regex=False
    )

    # テキストをチャンク分割
    chunks = text_splitter.split_text(text)

    return chunks