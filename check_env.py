import os
import dotenv

# .envファイルを読み込む
dotenv.load_dotenv()

# Ollama関連の環境変数を表示
print(f"OLLAMA_HOST={os.getenv('OLLAMA_HOST', 'not set')}")
print(f"OLLAMA_PORT={os.getenv('OLLAMA_PORT', 'not set')}")
print(f"OLLAMA_BASE_URL={os.getenv('OLLAMA_BASE_URL', 'not set')}")

# システム環境変数も確認
print("\nシステム環境変数:")
for key in os.environ:
    if key.startswith('OLLAMA'):
        print(f"{key}={os.environ[key]}")
