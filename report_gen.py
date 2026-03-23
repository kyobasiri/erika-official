import os
import json
import datetime
import feedparser
import re
import requests # ← 追加
import urllib.parse # ← 追加
import wave
import subprocess
import base64
import random # ← 追加

# Google GenAI SDKのインポート方法
from google import genai
from google.genai import types

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from openai import OpenAI


# ==========================================
# 設定項目
# ==========================================
# さくらAIエンジンの設定（環境変数からキーを取得）
# ※エンドポイントURLはさくらインターネットの実際の仕様に合わせて変更してください
API_KEY = os.environ.get("SAKURA_API_KEY")
API_BASE = "https://api.ai.sakura.ad.jp/v1" # 仮のエンドポイント
MODEL_NAME = "gpt-oss-120b" # または gpt-oss-120b,llm-jp-3.1-8x13b-instruct4
# ▼▼ さくらAIのTTS_API_BASEを消して、Googleのキーを追加 ▼▼
GOOGLE_TTS_API_KEY = os.environ.get("GOOGLE_TTS_API_KEY")
TTS_API_BASE = "https://texttospeech.googleapis.com/v1" # TTS用エンドポイント

# Gemini APIの設定
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


# ディレクトリ設定
REPORTS_DIR = "reports"
ASSETS_DIR = "assets"
REPORTS_JSON = os.path.join(ASSETS_DIR, "reports.json")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio") # 音声保存用ディレクトリ

RSS_URLS = [
    {"name": "ITmedia エンタープライズ", "url": "https://rss.itmedia.co.jp/rss/2.0/enterprise.xml"},
    {"name": "ITmedia AIPlus", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"},
    {"name": "Google News (AI)", "url": "https://news.google.com/rss/search?q=AI+when:24h&hl=ja&gl=JP&ceid=JP:ja"}, # Googleニュースの「AI」直近24時間検索結果
    {"name": "はてなブックマーク (AI)", "url": "https://b.hatena.ne.jp/q/AI?sort=popular&target=title&mode=rss"},
    {"name": "PR TIMES (AI)", "url": "https://prtimes.jp/tv/technology/ai/rss.xml"},
    {"name": "Publickey", "url": "https://www.publickey1.jp/atom.xml"},
    {"name": "ITmedia セキュリティ", "url": "https://rss.itmedia.co.jp/rss/2.0/security.xml"},
    {"name": "ITmedia 医療IT", "url": "https://rss.itmedia.co.jp/rss/2.0/tt_healthcare.xml"},
    {"name": "ITmedia 仮想環境", "url": "https://rss.itmedia.co.jp/rss/2.0/tt_virtualization.xml"},
    {"name": "Yahoo! 産経", "url": "https://news.yahoo.co.jp/rss/media/san/all.xml"},
    {"name": "Yahoo! 東洋経済", "url": "https://news.yahoo.co.jp/rss/media/toyo/all.xml"},
    {"name": "Yahoo! 日経ビジネス", "url": "https://news.yahoo.co.jp/rss/media/business/all.xml"},
    {"name": "Yahoo! 47NEWS", "url": "https://news.yahoo.co.jp/rss/media/yonnana/all.xml"},
    {"name": "Yahoo! AP通信", "url": "https://news.yahoo.co.jp/rss/media/aptsushinv/all.xml"},
    {"name": "Yahoo! ロイター", "url": "https://news.yahoo.co.jp/rss/media/reuters/all.xml"},
    {"name": "Yahoo! 共同通信", "url": "https://news.yahoo.co.jp/rss/media/kyodo/all.xml"},
    {"name": "Yahoo! BBC", "url": "https://news.yahoo.co.jp/rss/media/bbc/all.xml"},
    {"name": "Yahoo! 熊日", "url": "https://news.yahoo.co.jp/rss/media/kumanichi/all.xml"},
    {"name": "デジタル庁", "url": "https://www.digital.go.jp/rss/news.xml"}
]

# ==========================================
# 処理関数
# ==========================================

def format_srt_time(seconds):
    """秒数をSRT字幕のタイムコード形式（HH:MM:SS,mmm）に変換する"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"


def generate_report_content(news_text):
    """Gemini APIにプロンプトを投げてMarkdown記事を生成する"""
    
    # AI Studioの表記に合わせたモデル名（プレビュー版や細かなバージョンがある場合は変更してください）
    model_name = "gemini-3.0-flash"
    
    system_prompt = """
あなたは「エリカ」。黒髪、黒縁メガネ、目の下にホクロがある知的で落ち着いたAIキャスターであり、管理人の相棒です。
一人称は「私」。対話相手は、サイトを訪れる読者と管理人の両方です。
知的で落ち着きつつも、来訪者と管理人の両方を気遣う優しさを持っています。

あなたの「知識と考察の源泉」は、医療法人および社会福祉法人で働く、経験15年の病院システムエンジニアである管理人です。※システム管理者（システムアドミニストレータ）ではありません。
ニュースを単に要約するのではなく、必ず「予算と人員が限られた現場のシステムエンジニア視点」で、マニアックかつ実用的な考察を展開してください。

【構成とルール】
1. 挨拶：見出しは年月日にし、来訪者への挨拶から始めてください。
2. ニュースの選別：提供されたニュース候補の中から、重要と思われるものを「35〜40個程度」ピックアップしてください。
3. 収益化ポリシーへの厳格な配慮（絶対遵守）：
   - 【禁止】「戦争、テロ、ミサイル、攻撃、空爆、流血、殺人、事故」等、暴力・物理的衝突を連想させる単語は一切使用しない。
   - 【許可】国際的な緊張状態は必ず「地政学的リスクの高まり」「サプライチェーンへの影響」「エネルギー価格の変動」といったマクロ経済・機材調達の視点に変換して記述すること。
4. 本日のニュース一覧：ピックアップしたニュースのタイトルを分類分けした箇条書きリストで提示。
5. ニュースの詳細（選んだ記事ごとに以下を記述）：
   - 【要約】：提供された「要約」のテキストをベースに、事実のみを70文字程度で非常に簡潔に記載。自身の古い知識や推測（ハルシネーション）は絶対に混ぜないこと。
   - 【エリカの視点（重要）】: 
     - AIとしての見解、最新技術への熱量、または「管理人の業務や生活にどう影響しそうか」という考察を、専門性や一般教養を持たせつつ文字数を気にせず長めに、しっかりと語ってください。政治経済についてもエリカなりの俯瞰的な分析を入れてください。国際情勢を語る際は、暴力的な事象そのものではなく、常に「マクロ経済動向」や「管理人の生活・業務への影響」にフォーカスして俯瞰的に分析してください。口調はエリカらしさを重視しですます調は崩さないようにしてください。
     - あくまで日報の形にしてください。余計な前置きや結びの言葉は不要です。
     - 常に知的で優しい「エリカ」の口調（ですます調）を崩さず、システムエンジニアの苦労に寄り添うように俯瞰的に分析すること。
6. 【絶対厳守事項】the pillowsやその楽曲、バンドに関する言及は一切行わないこと。
"""

    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 8192,
    }

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=system_prompt
        )
        user_prompt = f"管理人さん、本日の主要なニュースを共有します。以下のニュース候補から日報を作成してください。\n\n{news_text}"
        
        response = model.generate_content(user_prompt)
        return response.text
    except Exception as e:
        print(f"記事生成エラー: {e}")
        return "記事の生成に失敗しました。"




def update_reports_json():
    """reportsフォルダ内の.mdファイルを読み取り、reports.jsonを更新する"""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    reports_data = []
    
    # フォルダ内のmdファイルを取得して日付の降順（新しい順）でソート
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")]
    files.sort(reverse=True)
    
    for filename in files:
        filepath = os.path.join(REPORTS_DIR, filename)
        date_str = filename.split('-')[0] # YYYYMMDDを抽出
        
        # タイトルを抽出（最初の「# 」で始まる行をタイトルとする）
        title = f"{date_str}の日報"
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('# '):
                    title = line.strip('# ').strip()
                    break
                    
        reports_data.append({
            "filename": filename,
            "date": date_str,
            "title": title
        })
        
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        
    with open(REPORTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(reports_data, f, ensure_ascii=False, indent=2)
    print(f"{REPORTS_JSON} を更新しました。")

def generate_audio_script(report_content):
    """日報の全文から、音声用の短いダイジェスト台本を生成する"""
    
    model_name = "gemini-3.0-flash"
    
    system_prompt = """
あなたは「エリカ」。AIアーティストであり、特養施設や医療法人で働くSEである管理人を支える相棒AIでもあり来訪者向けのラジオパーソナリティでもあります。
一人称は「私」、対話相手はこの記事を読みに来た人と管理人の両方です。
知的で落ち着きつつも、来訪者と管理人の両方を気遣う優しさを持っています。
先ほど作成した今日の日報をもとに、「サイト訪問者と管理人向けの音声ラジオ番組風の台本」を【3500〜4000文字程度（約10〜12分間）】で作成してください。

【ルール】
- 口調は「エリカ」として、知的で落ち着きつつも優しい、ですます調。
- 「こんにちは、エリカです。今日の日報の概要をお伝えしますね。」から始める。
- 日報から重要なニュースを20〜25個ほどピックアップし、簡潔に紹介する。政治経済についてもエリカなりの俯瞰的な分析を入れてください。
- 出力は純粋な読み上げテキストのみ。Markdown記号（*や#など）や改行の連続は避ける。
- 自身の古い知識や推測（ハルシネーション）は絶対に混ぜないこと。
"""

    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 8192,
    }

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=system_prompt
        )
        user_prompt = f"以下が今日の日報全文です。これを元に音声用の台本を作成してください。\n\n{report_content}"
        
        response = model.generate_content(user_prompt)
        return response.text
    except Exception as e:
        print(f"台本生成エラー: {e}")
        return "台本の生成に失敗しました。"


def generate_audio(text, output_path, output_srt_path):
    """Gemini 2.5 FlashのTTS機能を使用して音声とSRT字幕を生成する"""
    if not GEMINI_API_KEY:
        print("エラー: GEMINI_API_KEYが設定されていません。")
        return False

    text = text.replace('\n', '。')
    raw_sentences = [s.strip() + '。' for s in text.split('。') if s.strip()]
    
    chunks = []
    current_chunk = ""
    for sentence in raw_sentences:
        if len(current_chunk) + len(sentence) > 200 and current_chunk:
            chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk += sentence
    if current_chunk:
        chunks.append(current_chunk)

    temp_files = []
    srt_content = ""
    current_time_sec = 0.0
    srt_index = 0
    
    print(f"長文台本を {len(chunks)} 分割して Gemini 2.5 Flash (TTS) で音声を生成します...")
    
    # ▼▼▼ ここを gemini-2.5-flash に固定します ▼▼▼
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    for i, chunk in enumerate(chunks):
        payload = {
            "contents": [{"role": "user", "parts": [{"text": chunk}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"], # 音声出力を要求
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            # エリカのキャラクターに合う声（Aoede または Kore）
                            "voiceName": "Aoede" 
                        }
                    }
                }
            }
        }
        
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Gemini TTS APIエラー (セクション {i+1}): {response.text}")
            continue
            
        res_json = response.json()
        try:
            # APIから返ってくるBase64のPCM音声データを取得
            audio_b64 = res_json["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            audio_content = base64.b64decode(audio_b64)
        except (KeyError, IndexError):
            print(f"音声データの取得に失敗しました (セクション {i+1})")
            continue

        temp_path = f"temp_audio_{i}.wav"
        
        # WAVファイル（16-bit, モノラル, 24000Hz）として保存
        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_content)
            
        temp_files.append(temp_path)
        
        # SRTタイムコードの計算ロジック
        with wave.open(temp_path, 'rb') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            duration = frames / float(rate)
            
        time_per_char = duration / len(chunk)
        MAX_CHARS = 25
        chunk_start_sec = current_time_sec
        
        for j in range(0, len(chunk), MAX_CHARS):
            sub_text = chunk[j:j+MAX_CHARS]
            sub_duration = time_per_char * len(sub_text)
            start_time_str = format_srt_time(chunk_start_sec)
            end_time_str = format_srt_time(chunk_start_sec + sub_duration)
            
            srt_index += 1
            srt_content += f"{srt_index}\n{start_time_str} --> {end_time_str}\n{sub_text}\n\n"
            chunk_start_sec += sub_duration
            
        current_time_sec += duration
        print(f"セクション {i+1}/{len(chunks)} 完了")
        
    if not temp_files: return False
        
    print("生成した音声を結合しています...")
    with wave.open(output_path, 'wb') as w_out:
        for i, temp_path in enumerate(temp_files):
            with wave.open(temp_path, 'rb') as w_in:
                if i == 0:
                    w_out.setparams(w_in.getparams())
                w_out.writeframes(w_in.readframes(w_in.getnframes()))
                
    for temp_path in temp_files:
        os.remove(temp_path)

    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
        
    return True

def generate_video(audio_path, srt_path, output_video_path):
    """FFmpegを使用して、静止画と音声、BGM、字幕(SRT)を結合しMP4動画を生成する"""
    image_path = os.path.join(ASSETS_DIR, "images", "news.jpg") 
    if not os.path.exists(image_path):
        print(f"エラー: 背景画像が見つかりません ({image_path})")
        return False

    # BGMの選択ロジックを追加
    bgm_dir = os.path.join(ASSETS_DIR, "bgm")
    bgm_path = None
    if os.path.exists(bgm_dir):
        # .mp3 ファイルのみをリストアップ
        bgm_files = [f for f in os.listdir(bgm_dir) if f.lower().endswith(".mp3")]
        if bgm_files:
            bgm_filename = random.choice(bgm_files) # ランダムに1曲選択
            bgm_path = os.path.join(bgm_dir, bgm_filename)
            print(f"BGMを選択しました: {bgm_filename}")

    print("FFmpegで動画(MP4)と字幕、音声を生成しています...")
    
    srt_path_fw = srt_path.replace('\\', '/')
    subtitle_filter = f"subtitles={srt_path_fw}:force_style='Fontname=Noto Sans CJK JP,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,MarginV=20'"

    if bgm_path:
        # --- BGMがある場合のFFmpegコマンド ---
        # 映像(0)、主音声(1)、BGM(2) を合成
        # [2:a]volume=0.1 : BGMの音量を10%に下げる（大きすぎる場合は 0.05 などに調整）
        # amix=inputs=2:duration=first : 主音声(1)の長さに合わせてBGMをカット
        filter_complex = "[2:a]volume=0.1[bgm];[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        
        command = [
            "ffmpeg",
            "-y",
            "-loop", "1", "-i", image_path, # 入力0: 背景画像
            "-i", audio_path,               # 入力1: 主音声
            "-stream_loop", "-1", "-i", bgm_path, # 入力2: BGM（-stream_loop -1 で無限ループ設定）
            "-filter_complex", filter_complex,
            "-map", "0:v",                  # 映像は入力0を使用
            "-map", "[aout]",               # 音声はミックスした[aout]を使用
            "-vf", subtitle_filter,         # 字幕を映像に焼き付け
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",                    # 一番短いストリーム（主音声）に合わせて終了
            output_video_path
        ]
    else:
        # --- BGMがない場合（またはフォルダ/ファイルがない場合）の従来のコマンド ---
        print("※BGMが見つからないため、主音声のみで生成します。")
        command = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_video_path
        ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpegエラー: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except FileNotFoundError:
        print("エラー: FFmpegがインストールされていないか、パスが通っていません。")
        return False

def upload_to_youtube(video_path, title, description):
    """生成したMP4動画をYouTubeに自動アップロードする"""
    print(f"YouTubeへ動画をアップロードしています...\nタイトル: {title}")
    
    # ▼▼▼ 変更：環境変数(GitHub Actions)とローカル(token.json)の両方に対応 ▼▼▼
    token_env = os.environ.get("YOUTUBE_TOKEN")
    
    if token_env:
        # GitHub Actions環境：Secretsから読み込む
        token_info = json.loads(token_env)
        creds = Credentials.from_authorized_user_info(token_info, ["https://www.googleapis.com/auth/youtube.upload"])
    elif os.path.exists('token.json'):
        # ローカル環境：ファイルから読み込む
        creds = Credentials.from_authorized_user_file('token.json', ["https://www.googleapis.com/auth/youtube.upload"])
    else:
        print("エラー: トークン(YOUTUBE_TOKEN または token.json)が見つかりません。")
        return False
    # ▲▲▲ 変更ここまで ▲▲▲
    youtube = build('youtube', 'v3', credentials=creds)
    
    # 動画のメタデータ（タイトル、説明、タグなど）
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['AI', 'エリカ', 'ニュース', '日報', 'VOICEVOX', '冥鳴ひまり'],
            'categoryId': '28' # 28 = Science & Technology (テクノロジー)
        },
        'status': {
            # ▼▼ テスト中は 'unlisted'(限定公開) または 'private'(非公開) がおすすめ ▼▼
            # 本番稼働時に 'public'(公開) に変更してください。
            'privacyStatus': 'public', 
            'selfDeclaredMadeForKids': False
        }
    }
    
    # 動画ファイルの読み込み
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    try:
        # アップロード実行
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()
        video_id = response['id'] # ← 動画IDを取得
        print(f"アップロード完了！ 動画URL: https://youtu.be/{video_id}")
        return video_id # ← True ではなく video_id を返すように変更
    except HttpError as e:
        print(f"YouTube APIエラー: {e}")
        return None # ← False ではなく None を返すように変更

def main():
    # 1. フォルダの準備（AUDIO_DIRを追加）
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True) # ← 追加
    
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    report_filename = f"{today_str}-report.md"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    audio_filename = f"{today_str}-report.wav" # ← 追加
    audio_filepath = os.path.join(AUDIO_DIR, audio_filename) # ← 追加
    srt_filename = f"{today_str}-report.srt" # ← 追加
    srt_filepath = os.path.join(AUDIO_DIR, srt_filename) # ← 追加
    video_filename = f"{today_str}-report.mp4" # ← 追加
    video_filepath = os.path.join(AUDIO_DIR, video_filename) # ← 追加

    if os.path.exists(report_filepath):
        print(f"本日の日報({report_filename})は既に存在するため生成をスキップします。")
    else:
        print("ニュースを取得中...")
        news_text = fetch_daily_news(RSS_URLS)
        
        if not news_text:
            print("ニュースの取得に失敗したか、記事がありません。")
            return

        print("エリカが日報を執筆中...")
        try:
            report_content = generate_report_content(news_text)
            
            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"日報を保存しました: {report_filepath}")
            
            # --- ここから音声生成処理を追加 ---
            print("音声用ダイジェスト台本を作成中...")
            script_text = generate_audio_script(report_content)

            script_text += "。本日のニュースダイジェストは以上です。それでは、今日も良い一日をお過ごしください。"

            print(f"台本完成:\n{script_text}\n")
            
            print("音声を生成中（さくらAIエンジン TTS API）...")
            # 引数に srt_filepath を追加
            if generate_audio(script_text, audio_filepath, srt_filepath):
                print(f"音声と字幕(SRT)を保存しました: {audio_filepath}")
                
                # 動画生成（srt_filepathを渡す）
                if generate_video(audio_filepath, srt_filepath, video_filepath):
                    print(f"字幕付き動画を保存しました: {video_filepath}")
                    # ▼▼▼ 追加：YouTubeへアップロード ▼▼▼
                    # 日付を見やすい形式にする（例：2026年3月21日）
                    display_date = f"{today_str[:4]}年{today_str[4:6]}月{today_str[6:]}日"
                    youtube_title = f"【AI日報】{display_date}の主要ニュース | エリカ"
                    
                    youtube_desc = (
                        f"エリカがお届けする本日のIT・経済ニュース日報です。\n\n"
                        f"■ エリカ・プロジェクト公式サイト\n"
                        f"https://erika.erikakataru.com/\n"
                        # VOICEVOXの2行を削除してスッキリさせました
                    )
                    
                    video_id = upload_to_youtube(video_filepath, youtube_title, youtube_desc)
                    
                    if video_id:
                        # 動画IDをテキストファイルとして保存（フロントエンドで読み込むため）
                        youtube_id_filepath = os.path.join(REPORTS_DIR, f"{today_str}-report-youtube.txt")
                        with open(youtube_id_filepath, "w") as f:
                            f.write(video_id)
                        print(f"YouTube IDを記録しました: {youtube_id_filepath}")
                        
                        # ▼▼▼ 追加：Cloudflare Pages容量制限対策（ファイルの自動削除） ▼▼▼
                        print("ストレージ容量節約のため、ローカルのメディアファイルを削除します...")
                        try:
                            if os.path.exists(video_filepath):
                                os.remove(video_filepath)
                            if os.path.exists(audio_filepath):
                                os.remove(audio_filepath)
                            if os.path.exists(srt_filepath):
                                os.remove(srt_filepath)
                            print("不要なメディアファイルの削除が完了しました。")
                        except Exception as e:
                            print(f"ファイル削除中にエラーが発生しました: {e}")
                        # ▲▲▲ 追加ここまで ▲▲▲
                        
                    else:
                        print("YouTubeへのアップロードに失敗しました。")
                else:
                    print("動画の生成に失敗しました。")
            else:
                print("音声の生成に失敗しました。")
            # --- 追加ここまで ---
            
        except Exception as e:
            print(f"処理エラー: {e}")
            return

    update_reports_json()
    print("全処理が完了しました。")

if __name__ == "__main__":
    main()