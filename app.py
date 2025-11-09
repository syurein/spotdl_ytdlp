import gradio as gr
import subprocess
import os
import sys

# 実行環境のチェック（オプションですが親切）
try:
    subprocess.run(["yt-dlp", "--version"], check=True, capture_output=True, text=True)
    subprocess.run(["spotdl", "--version"], check=True, capture_output=True, text=True)
    subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, text=True)
    print("✅ yt-dlp, spotdl, ffmpeg が見つかりました。")
except Exception as e:
    print(f"⚠️ 警告: yt-dlp, spotdl, または ffmpeg が見つからないか、実行できません。 {e}")
    # Gradioアプリ内でも警告を出すことができます
    # gr.Warning("yt-dlp, spotdl, または ffmpeg がインストールされていません。")


def download_media(url: str, output_folder: str, progress=gr.Progress(track_tqdm=True)):
    """
    URLを受け取り、spotdlかyt-dlpを使ってメディアをダウンロードする関数
    """
    # 出力先ディレクトリが指定されていない場合はデフォルト値を使う
    if not output_folder:
        output_folder = "downloads"
        
    os.makedirs(output_folder, exist_ok=True)
    
    # 出力ログを格納するリスト
    logs = []
    
    try:
        if "spotify.com" in url:
            # --- spotdl (Spotify) の処理 ---
            progress(0.1, desc="[spotdl] Spotify URLを検出しました。ダウンロード準備中...")
            
            # spotdlコマンドを構築
            command = [
                "spotdl", 
                url, 
                # 保存先とファイル名形式を指定
                "--output", os.path.join(output_folder, "{title} - {artist}.{output-ext}")
            ]
            
            logs.append(f"🏃‍♂️ 実行コマンド: {' '.join(command)}\n")
            progress(0.3, desc="[spotdl] ダウンロードを実行します...")

            # サブプロセスを実行
            # encodingとerrorsを指定して、文字化けやUnicodeDecodeErrorを防ぐ
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace' 
            )
            
            progress(1.0, desc="[spotdl] 処理が完了しました。")

            # 実行結果をログに追加
            if result.stdout:
                logs.append(f"--- 標準出力 ---\n{result.stdout}\n")
            if result.stderr:
                logs.append(f"--- エラー出力 ---\n{result.stderr}\n")

            if result.returncode == 0:
                logs.insert(0, f"✅ [spotdl] ダウンロードが完了しました。\n'{output_folder}' フォルダを確認してください。\n")
            else:
                logs.insert(0, f"❌ [spotdl] ダウンロードに失敗しました。\n")

        else:
            # --- yt-dlp (YouTubeなど) の処理 ---
            progress(0.1, desc="[yt-dlp] URLを検出しました。ダウンロード準備中...")
            
            # yt-dlpコマンドを構築（音声MP3でダウンロード）
            command = [
                "yt-dlp",
                "-x",  # 音声を抽出
                "--audio-format", "mp3", # MP3形式に変換
                # 保存先とファイル名形式を指定
                "-o", os.path.join(output_folder, "%(title)s.%(ext)s"),
                url
            ]
            
            logs.append(f"🏃‍♂️ 実行コマンド: {' '.join(command)}\n")
            progress(0.3, desc="[yt-dlp] ダウンロードを実行します...")

            # サブプロセスを実行
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace'
            )
            
            progress(1.0, desc="[yt-dlp] 処理が完了しました。")

            # 実行結果をログに追加
            if result.stdout:
                logs.append(f"--- 標準出力 ---\n{result.stdout}\n")
            if result.stderr:
                logs.append(f"--- エラー出力 ---\n{result.stderr}\n")

            if result.returncode == 0:
                logs.insert(0, f"✅ [yt-dlp] ダウンロードが完了しました。\n'{output_folder}' フォルダを確認してください。\n")
            else:
                logs.insert(0, f"❌ [yt-dlp] ダウンロードに失敗しました。\n")

    except Exception as e:
        progress(1.0, desc="エラー発生")
        logs.insert(0, f"❌ 予期せぬエラーが発生しました: {str(e)}\n")
    
    # 結合したログを返す
    return "".join(logs)

# --- Gradioインターフェースの構築 ---
with gr.Blocks(title="Media Downloader", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🎵 メディアダウンローダー (spotdl & yt-dlp)
        
        Spotifyのトラック・アルバム・プレイリスト、またはYouTubeなどのURLを入力してください。
        指定したフォルダに音声ファイル（MP3）として保存されます。
        """
    )
    
    with gr.Row():
        url_input = gr.Textbox(
            label="URL", 
            placeholder="ここにSpotifyまたはYouTubeのURLを貼り付け...",
            scale=4
        )
    
    with gr.Row():
        output_folder_input = gr.Textbox(
            label="保存先フォルダ名",
            placeholder="例: downloads (未入力の場合は 'downloads' になります)",
            scale=4
        )
        download_button = gr.Button("ダウンロード実行", variant="primary", scale=1)
    
    output_log = gr.Textbox(
        label="実行結果ログ", 
        lines=20, 
        interactive=False,
        placeholder="ここにダウンロード結果が表示されます..."
    )
    
    # ボタンクリック時の動作
    download_button.click(
        fn=download_media,
        inputs=[url_input, output_folder_input],
        outputs=output_log
    )
    
    gr.Markdown(
        """
        ---
        ### ⚠️ 注意事項
        * このプログラムを実行する環境には、`gradio`, `spotdl`, `yt-dlp`, `ffmpeg` がインストールされている必要があります。
        * ダウンロード（特にプレイリスト）には時間がかかる場合があります。
        * 著作権法を遵守し、ダウンロードしたメディアは私的利用の範囲内で使用してください。
        """
    )

# --- アプリの起動 ---
if __name__ == "__main__":
    # queue() を使うことで、複数のリクエストや長時間の処理に対応できます
    demo.queue().launch(debug=True, share=True)