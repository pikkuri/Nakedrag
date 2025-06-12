@echo off
setlocal enabledelayedexpansion

:: Ollamaの環境変数設定バッチファイル
echo Ollama環境変数設定ツール
echo ============================
echo.

:: 管理者権限チェック
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 管理者権限が必要です。右クリックして「管理者として実行」を選択してください。
    echo 処理を中止します。
    pause
    exit /b 1
)

:: Pythonが利用可能か確認
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Pythonが見つかりません。Pythonがインストールされていることを確認してください。
    echo 処理を中止します。
    pause
    exit /b 1
)

:: .envファイルが存在するか確認
if not exist ".env" (
    echo .envファイルが見つかりません。
    echo NakedRAGのルートディレクトリで実行してください。
    pause
    exit /b 1
)

:: .envファイルからOLLAMA_PORTを読み込む
set OLLAMA_PORT=11434
for /f "tokens=1,* delims==" %%a in ('type .env ^| findstr /i "OLLAMA_PORT"') do (
    set OLLAMA_PORT=%%b
)

:: GPUの数を検出
set GPU_NUM=1
for /f "tokens=*" %%i in ('nvidia-smi --query-gpu^=name --format^=csv,noheader 2^>nul') do (
    set /a GPU_NUM+=1
)
set /a GPU_NUM-=1
if %GPU_NUM% lss 1 set GPU_NUM=1
echo 検出されたGPU数: %GPU_NUM%

:: 環境変数を設定
echo Ollama環境変数を設定しています...
setx OLLAMA_CUDA 1 /M
setx OLLAMA_FLASH_ATTENTION 1 /M
setx OLLAMA_HOST 0.0.0.0 /M
setx OLLAMA_PORT %OLLAMA_PORT% /M
setx OLLAMA_KEEP_ALIVE 0 /M
setx OLLAMA_NUM_GPU %GPU_NUM% /M

echo.
echo 環境変数の設定が完了しました。

:: Ollamaサービスの再起動を確認
echo.
set /p RESTART=Ollamaサービスを再起動しますか？ (y/n): 
if /i "%RESTART%"=="y" (
    echo.
    echo Ollamaサービスを再起動しています...
    net stop ollama
    net start ollama
    echo Ollamaサービスの再起動が完了しました。
) else (
    echo.
    echo 環境変数を反映させるには、Ollamaサービスの再起動が必要です。
    echo 後で手動で再起動してください。
)

echo.
echo 設定完了しました。
echo Ollamaモデルのダウンロードと設定後、serve コマンドを実行してください。
echo.
pause
