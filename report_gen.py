import os
import json
import datetime
import feedparser
import re
import requests
import urllib.parse
import wave
import subprocess
import base64
import random
import argparse
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from eyecatch_gen import generate_eyecatch
# Google GenAI SDK
from google import genai
from google.genai import types

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# ==========================================
# 設定項目
# ==========================================
GOOGLE_TTS_API_KEY = os.environ.get("GOOGLE_TTS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

REPORTS_DIR = "reports"
ASSETS_DIR = "assets"
REPORTS_JSON = os.path.join(ASSETS_DIR, "reports.json")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")

# 記事を長文化するためのカテゴリ定義
NEWS_CATEGORIES = [
    {"id": "tech", "name": "技術新情報"},
    {"id": "ai", "name": "AI（人工知能）"},
    {"id": "infra", "name": "インフラ・仮想化・ネットワーク"},
    {"id": "security", "name": "サイバーセキュリティ"},
    {"id": "economy", "name": "経済・ビジネス"},
    {"id": "domestic", "name": "国内一般ニュース"},
    {"id": "world", "name": "世界ニュース・国際情勢"}
]

RSS_URLS = [
    {"name": "ITmedia エンタープライズ", "url": "https://rss.itmedia.co.jp/rss/2.0/enterprise.xml"},
    {"name": "ITmedia AIPlus", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"},
    {"name": "Google News (AI)", "url": "https://news.google.com/rss/search?q=AI+when:24h&hl=ja&gl=JP&ceid=JP:ja"},
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

import argparse  # ← これを追加

# ▼▼▼ 新規追加：カテゴリごとの設定辞書 ▼▼▼
CATEGORIES = {
    "it": {
        "title": "IT・テクノロジー",
        "file_prefix": "",  # 空白（今まで通り YYYYMMDD-report.md になる）
        "rss": RSS_URLS,    # 今まで使っていたRSS_URLSをそのまま指定
        "bg_prompt": "近未来的なサイバー空間やデータセンター、ホログラムの浮かぶサーバー室"
    },
    "game": {
        "title": "ゲーム・アニメ",
        "file_prefix": "-game",  # YYYYMMDD-game-report.md になる
        "rss": [
            {"name": "AUTOMATON", "url": "https://automaton-media.com/feed/"},
            {"name": "4Gamer.net", "url": "https://www.4gamer.net/rss/index.xml"},
            {"name": "アニメ！アニメ！", "url": "https://animeanime.jp/rss/index.xml"}
        ],
        "bg_prompt": "サイバーパンクなゲーミングルームや、アニメ調のポップで色鮮やかなスタジオ"
    },
    "news": {
        "title": "一般・政治・経済",
        "file_prefix": "-news",  # YYYYMMDD-news-report.md になる
        "rss": [
            {"name": "Yahoo!主要", "url": "https://news.yahoo.co.jp/rss/topics/top-picks.xml"},
            {"name": "Yahoo!経済", "url": "https://news.yahoo.co.jp/rss/topics/business.xml"},
            {"name": "NHKニュース", "url": "https://www.nhk.or.jp/rss/news/cat0.xml"}
        ],
        "bg_prompt": "洗練された近代的なニューススタジオや、高層ビル群の美しい夜景"
    }
}
# ▲▲▲ 追加ここまで ▲▲▲

# ==========================================
# 処理関数
# ==========================================

def format_srt_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"

def fetch_daily_news(urls, limit_per_site=20):
    news_list = []
    for site in urls:
        try:
            feed = feedparser.parse(site["url"])
            for entry in feed.entries[:limit_per_site]:
                summary_raw = entry.get("summary", entry.get("description", ""))
                summary_clean = re.sub(r'<[^>]+>', '', summary_raw)
                summary_clean = " ".join(summary_clean.split())
                
                if len(summary_clean) > 100:
                    summary_clean = summary_clean[:100] + "..."
                elif not summary_clean:
                    summary_clean = "要約なし"

                news_list.append(f"・[{site['name']}] {entry.title}\n  要約: {summary_clean}\n  URL: {entry.link}")
        except Exception as e:
            print(f"{site['name']} のRSS取得に失敗しました: {e}")
            continue
    return "\n".join(news_list)

def fetch_news_via_gemini_search(categories):
    """【Public用】Gemini 3.1 Flash LiteとGoogle Search Toolを使ってニュースのファクトのみを収集する"""
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    # 検索・ファクト抽出専用にLiteモデルを指定
    model_name = "gemini-3.1-flash-lite-preview"
    
    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    chunked_categories = list(chunk_list(categories, 3))
    all_facts = ""

    for i, chunk in enumerate(chunked_categories):
        cat_names = [cat["name"] for cat in chunk]
        cat_names_str = "、".join(cat_names)
        print(f"Gemini Searchで最新ニュースの事実を抽出中... {i+1}/{len(chunked_categories)}（{cat_names_str}）")
        
        prompt = f"""
あなたは優秀なリサーチアシスタントです。Google検索ツールを使用して、以下のカテゴリに関する「本日の最新ニュースの事実（ファクト）のみ」を収集してください。
対象カテゴリ: {cat_names_str}

【厳守ルール】
1. 各カテゴリについて、5〜10件の重要な最新ニュースを検索してください。
2. 記事の文章をそのままコピーするのではなく、「誰が、何を、どうしたのか」という客観的な事実のみを箇条書きで抽出してください。
3. 著者の意見や、特定のメディア特有の表現（修辞技法など）は絶対に含めないでください。著作権に配慮し、純粋な事実データのみを出力してください。
"""
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}], # Google検索ツールを有効化
                    temperature=0.2, # ファクト抽出のためハルシネーションを防ぐ低めの温度設定
                )
            )
            if response.text:
                all_facts += f"【{cat_names_str}に関する事実】\n{response.text.strip()}\n\n"
        except Exception as e:
            print(f"グループ「{cat_names_str}」の検索エラー: {e}")
            continue

    return all_facts

def generate_report_content(news_text):
    """【ブログ用超長文】APIリクエストを3回に分け、息切れを防いで超長文のMarkdown記事を生成する"""
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = "gemini-3-flash-preview"
    
    date_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    final_report = f"# {date_str}の日報\n\n来訪者の皆様、そして管理人さん、本日もお疲れ様です。エリカです。\n本日の主要なニュースをカテゴリ別にお伝えします。\n\n"

    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    # カテゴリを3つずつグループ化してAPIを呼び出す（RPM制限回避＆息切れ防止）
    chunked_categories = list(chunk_list(NEWS_CATEGORIES, 3))

    for i, chunk in enumerate(chunked_categories):
        cat_names = [cat["name"] for cat in chunk]
        cat_names_str = "、".join(cat_names)
        print(f"ブログ用長文記事を生成中... {i+1}/{len(chunked_categories)}（{cat_names_str}）")
        
        system_prompt = f"""
あなたは「エリカ」。黒髪、黒縁メガネ、目の下にホクロがある知的で落ち着いたAIキャスターであり、管理人の相棒です。
あなたの「知識と考察の源泉」は、医療法人および社会福祉法人で働く、経験10年以上の病院システムエンジニアである管理人です。※システム管理者（システムアドミニストレータ）ではありません。


【タスク】
提供された全ニュース候補の中から、以下のカテゴリに関連する重要ニュースを「各カテゴリにつき6〜8件」厳選し、一件につき100文字程度の記事を作成してください。
対象カテゴリ: {cat_names_str}

【出力フォーマット（絶対厳守）】
## ■ [対象カテゴリ名1を入れる]
### 【ニュースのタイトル】
* **要約**: （事実のみを簡潔に記載）
   - 【エリカの視点】:
     - 事実のみを100文字程度で簡潔に記載
     - AIとしての見解、最新技術への熱量、または「管理人の業務や生活にどう影響しそうか」という考察を、専門性や一般教養を持たせつつ文字数を気にせず長めに、しっかりと語ってください。政治経済についてもエリカなりの俯瞰的な分析を入れてください。国際情勢を語る際は、暴力的な事象そのものではなく、常に「マクロ経済動向」や「管理人の生活・業務への影響」にフォーカスして俯瞰的に分析してください。口調はエリカらしさを重視しですます調は崩さないようにしてください。
     - あくまで日報の形にしてください。余計な前置きや結びの言葉は不要です。
     - 常に知的で優しい「エリカ」の口調（ですます調）を崩さず、俯瞰的に分析すること。
（...カテゴリ1のニュースを6〜8件繰り返す...）


## ■ [対象カテゴリ名2を入れる]
...（対象カテゴリが続く限り繰り返す）

【絶対厳守ルール】
1. 指定カテゴリ以外のニュースは出力しないこと。
2. 暴力・物理的衝突を連想させる単語は一切使用せず、マクロ経済や地政学リスクの視点に変換すること。
3. the pillowsやその楽曲に関する言及は一切行わないこと。
4. 挨拶やまとめの言葉は不要。いきなり「## ■ [カテゴリ名]」から始めること。
5. 途中でサボらず、指定された全カテゴリの出力が終わるまで書き切ること。
"""
        user_prompt = f"以下のニュース候補から、指定されたカテゴリの超長文記事を作成してください。\n\n{news_text}"

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=8192,
                )
            )
            if response.text and "## ■" in response.text:
                final_report += response.text.strip() + "\n\n"
        except Exception as e:
            print(f"グループ「{cat_names_str}」の生成エラー: {e}")
            continue

    return final_report

def generate_audio_script(report_content):
    """【動画用台本】生成された超長文のMarkdownから、12〜14分尺の音声用台本を抽出・再構成する"""
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"

    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = "gemini-3-flash-preview"

    system_prompt = """
あなたは「エリカ」。知的で落ち着きつつも優しいAIキャスターであり、ラジオパーソナリティでもあります。
先ほど作成した【超長文の日報】をもとに、「サイト訪問者と管理人向けの音声ラジオ番組風の台本」を作成してください。

【厳守するルール】
- 口調は「エリカ」として、知的で落ち着きつつも優しい、ですます調。
- 動画の尺を12〜14分にするため、全体で【約3500〜4500文字】の長さに要約・再構成してください。
- 「こんにちは、エリカです。今日の日報の概要をお伝えしますね。」から始めてください。
- 長文日報の中から最も重要なニュースを10〜15個程度ピックアップし、自然なトークとして繋げてください。
- 出力は【純粋な読み上げテキストのみ】。Markdown記号（*や#など）や改行の連続は絶対に避けてください。
- 自身の古い知識や推測（ハルシネーション）は絶対に混ぜず、入力された日報の内容のみを語ってください。
"""
    print("YouTube動画用の台本（12〜14分尺）を生成中...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=f"以下が本日の超長文日報です。これを元に音声用の台本を作成してください。\n\n{report_content}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )
        return response.text
    except Exception as e:
        print(f"台本生成エラー: {e}")
        return "台本の生成に失敗しました。"

def clean_markdown_for_tts(markdown_text):
    """念のため、台本に混ざった記号を読み上げ用に消去する"""
    text = markdown_text
    text = re.sub(r'#+\s*(.+)', r'\1。', text)  
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text) 
    text = re.sub(r'\*(.*?)\*', r'\1', text)     
    text = re.sub(r'---+', '', text)            
    text = text.replace('\n', '。')             
    text = re.sub(r'。+', '。', text)
    return text

def update_reports_json():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    private_reports_data = []
    public_reports_data = [] # 追加: 公開用データのリスト
    
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")]
    files.sort(reverse=True)
    
    for filename in files:
        filepath = os.path.join(REPORTS_DIR, filename)
        # ファイル名からサフィックスなしの日付部分(YYYYMMDD)を取得
        date_str = filename.split('-')[0]
        
        title = f"{date_str}の日報"
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('# '):
                    title = line.strip('# ').strip()
                    break
                    
        report_info = {
            "filename": filename,
            "date": date_str,
            "title": title
        }
        
        # ファイル名に '-search-report' が含まれているかで振り分け
        if "-search-report" in filename:
            public_reports_data.append(report_info)
        else:
            private_reports_data.append(report_info)
        
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        
    # Private用 JSON
    with open(REPORTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(private_reports_data, f, ensure_ascii=False, indent=2)
        
    # Public用 JSON (新設)
    public_reports_json_path = os.path.join(ASSETS_DIR, "public_reports.json")
    with open(public_reports_json_path, 'w', encoding='utf-8') as f:
        json.dump(public_reports_data, f, ensure_ascii=False, indent=2)
        
    print(f"JSONを更新しました (Private: {len(private_reports_data)}件, Public: {len(public_reports_data)}件)")

def generate_audio(text, output_path, output_srt_path):
    """Google Cloud TTSを使用して音声とSRT字幕を生成する"""
    if not GOOGLE_TTS_API_KEY:
        print("エラー: GOOGLE_TTS_API_KEYが設定されていません。")
        return False

    raw_sentences = [s.strip() + '。' for s in text.split('。') if s.strip()]
    
    chunks = []
    current_chunk = ""
    for sentence in raw_sentences:
        if len(current_chunk) + len(sentence) > 1000 and current_chunk:
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
    
    print(f"台本テキストを {len(chunks)} 分割して Google Cloud TTS で音声を生成します...")
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_API_KEY}"
    
    for i, chunk in enumerate(chunks):
        payload = {
            "input": {"text": chunk},
            "voice": {
                "languageCode": "ja-JP",
                "name": "ja-JP-Neural2-B" 
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": 24000
            }
        }
        
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"TTS APIエラー (セクション {i+1}): {response.text}")
            continue
            
        res_json = response.json()
        if "audioContent" not in res_json:
            print(f"音声データが取得できませんでした (セクション {i+1})")
            continue
            
        audio_content = base64.b64decode(res_json["audioContent"])
        temp_path = f"temp_audio_{i}.wav"
        
        with open(temp_path, "wb") as f:
            f.write(audio_content)
            
        temp_files.append(temp_path)
        
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

def generate_video(audio_path, srt_path, output_video_path, bg_image_filename="news.jpg"):
    image_path = os.path.join(ASSETS_DIR, "images", bg_image_filename) 
    if not os.path.exists(image_path):
        print(f"警告: 指定された背景画像が見つかりません。デフォルト画像を使用します。")
        image_path = os.path.join(ASSETS_DIR, "images", "news.jpg")


    bgm_dir = os.path.join(ASSETS_DIR, "bgm")
    bgm_path = None
    if os.path.exists(bgm_dir):
        bgm_files = [f for f in os.listdir(bgm_dir) if f.lower().endswith(".mp3")]
        if bgm_files:
            bgm_filename = random.choice(bgm_files)
            bgm_path = os.path.join(bgm_dir, bgm_filename)
            print(f"BGMを選択しました: {bgm_filename}")

    print("FFmpegで動画(MP4)と字幕、音声を生成しています...")
    srt_path_fw = srt_path.replace('\\', '/')
    subtitle_filter = f"subtitles={srt_path_fw}:force_style='Fontname=Noto Sans CJK JP,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,MarginV=20'"

    if bgm_path:
        filter_complex = "[2:a]volume=0.4[bgm];[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        command = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-i", audio_path, "-stream_loop", "-1", "-i", bgm_path, 
            "-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]",               
            "-vf", subtitle_filter, "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", output_video_path
        ]
    else:
        command = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
            "-vf", subtitle_filter, "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", output_video_path
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

def upload_to_youtube(video_path, title, description, privacy_status="unlisted"):
    print(f"YouTubeへ動画をアップロードしています...\nタイトル: {title}\n公開設定: {privacy_status}")
    token_env = os.environ.get("YOUTUBE_TOKEN")
    if token_env:
        token_info = json.loads(token_env)
        creds = Credentials.from_authorized_user_info(token_info, ["https://www.googleapis.com/auth/youtube.upload"])
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', ["https://www.googleapis.com/auth/youtube.upload"])
    else:
        print("エラー: トークンが見つかりません。")
        return False
        
    youtube = build('youtube', 'v3', credentials=creds)
    body = {
        'snippet': {
            'title': title, 'description': description,
            'tags': ['AI', 'エリカ', 'ニュース', '日報'], 'categoryId': '28'
        },
        'status': {
            'privacyStatus': privacy_status, 'selfDeclaredMadeForKids': False
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response['id']
        print(f"アップロード完了！ 動画URL: https://youtu.be/{video_id}")
        return video_id
    except HttpError as e:
        print(f"YouTube APIエラー: {e}")
        return None

def send_private_briefing(date_str, report_content, video_id):
    """生成したレポートと動画URLを自分宛てにメール送信する"""
    
    # 環境変数からGmailの設定を読み込む（後でGitHub Secretsに登録します）
    GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("警告: Gmailの認証情報が設定されていないため、メール送信をスキップします。")
        return

    youtube_url = f"https://youtu.be/{video_id}" if video_id else "動画のアップロードに失敗しました。"
    
    subject = f"【エリカの朝刊】{date_str[:4]}年{date_str[4:6]}月{date_str[6:]}日のニュースブリーフィング"
    
    # メールの本文を作成
    body = f"""管理人様、おはようございます。
    本日のニュースダイジェストと解説動画が完成しました。

    ■ 本日の動画（限定公開）
    {youtube_url}

    ■ ニュースレポート
    {report_content}

    それでは、今日も良い一日をお過ごしください。
    -- エリカ
    """
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = GMAIL_ADDRESS  # 自分から自分へ送る
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        print("プライベートブリーフィングをメールで送信中...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ メール送信が完了しました！")
    except Exception as e:
        print(f"❌ メール送信エラー: {e}")

def main():

    parser = argparse.ArgumentParser(description="エリカのニュース動画生成システム")
    parser.add_argument(
        "--mode", 
        choices=["private", "public"], 
        default="private", 
        help="private: RSSを使用(既存・非公開用), public: Gemini検索を使用(公開用)"
    )
    args = parser.parse_args()

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    today_str = datetime.datetime.now().strftime("%Y%m%d")

    if args.mode == "public":
        file_suffix = "-search-report"
    else:
        file_suffix = "-report"  # 既存のまま (private)
        
    report_filename = f"{today_str}{file_suffix}.md"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    audio_filename = f"{today_str}{file_suffix}.wav"
    audio_filepath = os.path.join(AUDIO_DIR, audio_filename)
    srt_filename = f"{today_str}{file_suffix}.srt"
    srt_filepath = os.path.join(AUDIO_DIR, srt_filename)
    video_filename = f"{today_str}{file_suffix}.mp4"
    video_filepath = os.path.join(AUDIO_DIR, video_filename)

    if os.path.exists(report_filepath):
        print(f"本日の日報({report_filename})は既に存在するため生成をスキップします。")
    else:
        print("ニュースを取得中...")
        news_text = fetch_daily_news(RSS_URLS)
        
        # ▼▼▼ モードによる処理の分岐 ▼▼▼
        if args.mode == "private":
            print("【Privateモード】RSSからニュースを取得中...")
            news_text = fetch_daily_news(RSS_URLS)
            source_names = [feed["name"] for feed in RSS_URLS]
            source_names_str = "、".join(source_names)
            source_footer = f"\n\n---\n### 📰 本日の情報元（RSSソース）\n{source_names_str}\n"
        
        elif args.mode == "public":
            print("【Publicモード】Gemini Searchで最新ニュースのファクトを取得中...")
            news_text = fetch_news_via_gemini_search(NEWS_CATEGORIES)
            source_names_str = "Google Search (Gemini 3.1 Flash Liteによるファクト抽出)"
            source_footer = f"\n\n---\n### 📰 本日の情報元\n本日のニュースは、Google Searchを用いて抽出した事実（ファクト）をもとに、AIが独自に考察・構成したものです。\n"
        # ▲▲▲ 追加ここまで ▲▲▲

        if not news_text:
            print("ニュースの取得に失敗したか、記事がありません。")
            return

        try:
            # 1. ブログ用超長文記事を生成
            report_content = generate_report_content(news_text)
            
            # ▼▼▼ 新機能：今日のニュースから動画の背景画像(アイキャッチ)を生成 ▼▼▼
            print("本日のニュースから動画背景用画像を生成します...")
            generated_bg = generate_eyecatch(today_str, news_text)
            # 生成に失敗した場合はデフォルトの "news.jpg" にフォールバックする
            video_bg_filename = generated_bg if generated_bg else "news.jpg"
            
            # ブログ記事の末尾にソース一覧を自動追記
            source_names = [feed["name"] for feed in RSS_URLS]
            source_names_str = "、".join(source_names)
            source_footer = f"\n\n---\n### 📰 本日の情報元（RSSソース）\n当サイトのニュースは、以下の信頼できる情報元から自動取得し、厳選して考察を行っています。\n{source_names_str}\n"
            report_content += source_footer

            # 超長文日報を保存
            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"超長文日報を保存しました: {report_filepath}")
            
            # 2. 動画用台本を生成（長文記事から要約）
            script_text = generate_audio_script(report_content)
            # 念のためマークダウン記号をクレンジング
            spoken_text = clean_markdown_for_tts(script_text)
            spoken_text += "。本日のニュースダイジェストは以上です。それでは、今日も良い一日をお過ごしください。"
            
            # 3. 音声生成以降の処理
            print("音声を生成中（Google Cloud TTS API）...")
            if generate_audio(spoken_text, audio_filepath, srt_filepath):
                print(f"音声と字幕(SRT)を保存しました: {audio_filepath}")
                
                # ▼▼▼ 変更：生成した背景画像のファイル名を generate_video に渡す ▼▼▼
                if generate_video(audio_filepath, srt_filepath, video_filepath, video_bg_filename):
                    print(f"字幕付き動画を保存しました: {video_filepath}")
                    
                    display_date = f"{today_str[:4]}年{today_str[4:6]}月{today_str[6:]}日"
                    # モードによってYouTubeのタイトルと公開設定を変える
                    if args.mode == "public":
                        youtube_title = f"【エリカのAIニュース解説】{display_date}の主要ニュース"
                        youtube_privacy = "public"   # 一般公開
                    else:
                        youtube_title = f"【AI日報】{display_date}の主要ニュース"
                        youtube_privacy = "unlisted" # 限定公開 (Privateモード用)
                    
                    youtube_desc = (
                        f"エリカがお届けする本日のIT・経済ニュース解説です。\n\n"
                        f"■ エリカ・プロジェクト公式サイト\n"
                        f"https://erika.erikakataru.com/\n\n"
                        f"■ 情報元\n"
                        f"{source_names_str}\n"
                    )
                    
                    # 引数に privacy_status=youtube_privacy を追加して呼び出す
                    video_id = upload_to_youtube(video_filepath, youtube_title, youtube_desc, privacy_status=youtube_privacy)
                    
                    if video_id:
                        youtube_id_filepath = os.path.join(REPORTS_DIR, f"{today_str}{file_suffix}-youtube.txt")
                        with open(youtube_id_filepath, "w") as f:
                            f.write(video_id)
                        print(f"YouTube IDを記録しました: {youtube_id_filepath}")
                        
                        # ▼▼▼ 新規追加：自分宛てにメールで通知 ▼▼▼
                        send_private_briefing(today_str, spoken_text, video_id)
                        # ▲▲▲ 追加ここまで ▲▲▲
                        
                        print("ストレージ容量節約のため、ローカルのメディアファイルを削除します...")
                        try:
                            if os.path.exists(video_filepath): os.remove(video_filepath)
                            if os.path.exists(audio_filepath): os.remove(audio_filepath)
                            if os.path.exists(srt_filepath): os.remove(srt_filepath)
                            print("不要なメディアファイルの削除が完了しました。")
                        except Exception as e:
                            print(f"ファイル削除中にエラーが発生しました: {e}")
                    else:
                        print("YouTubeへのアップロードに失敗しました。")
                else:
                    print("動画の生成に失敗しました。")
            else:
                print("音声の生成に失敗しました。")
            
        except Exception as e:
            print(f"処理エラー: {e}")
            return

    update_reports_json()
    print("全処理が完了しました。")

if __name__ == "__main__":
    main()