import os
import json
import datetime
import time
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
from tavily import TavilyClient

# ==========================================
# 設定項目
# ==========================================
GOOGLE_TTS_API_KEY = os.environ.get("GOOGLE_TTS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-3-flash-preview"
#GEMINI_MODEL_NAME = "gemini-2.5-flash"
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
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
    {"id": "domestic", "name": "日本のニュース"},
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

CATEGORIES = {
    "it": {
        "title": "IT・テクノロジー",
        "file_prefix": "",
        "rss": RSS_URLS,
        "bg_prompt": "近未来的なサイバー空間やデータセンター、ホログラムの浮かぶサーバー室"
    },
    "game": {
        "title": "ゲーム・アニメ",
        "file_prefix": "-game",
        "rss": [
            {"name": "AUTOMATON", "url": "https://automaton-media.com/feed/"},
            {"name": "4Gamer.net", "url": "https://www.4gamer.net/rss/index.xml"},
            {"name": "アニメ！アニメ！", "url": "https://animeanime.jp/rss/index.xml"}
        ],
        "bg_prompt": "サイバーパンクなゲーミングルームや、アニメ調のポップで色鮮やかなスタジオ"
    },
    "news": {
        "title": "一般・政治・経済",
        "file_prefix": "-news",
        "rss": [
            {"name": "Yahoo!主要", "url": "https://news.yahoo.co.jp/rss/topics/top-picks.xml"},
            {"name": "Yahoo!経済", "url": "https://news.yahoo.co.jp/rss/topics/business.xml"},
            {"name": "NHKニュース", "url": "https://www.nhk.or.jp/rss/news/cat0.xml"}
        ],
        "bg_prompt": "洗練された近代的なニューススタジオや、高層ビル群の美しい夜景"
    }
}

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

def fetch_news_via_tavily_search(categories):
    """【Public用】Tavily Search APIを使ってニュースのファクトとURLを収集する"""
    if not os.environ.get("TAVILY_API_KEY"):
        return "エラー: TAVILY_API_KEYが設定されていません。", []
    
    all_facts = ""
    reference_list = [] 
    
    for cat in categories:
        cat_name = cat["name"]
        print(f"Tavily APIで「{cat_name}」の最新ニュースを取得中...")
        
        try:
            search_result = tavily_client.search(
                query=f"{cat_name} 最新ニュース", 
                search_depth="advanced", 
                topic="news",
                max_results=10,
                days=1
            )
            
            if search_result and 'results' in search_result:
                all_facts += f"【{cat_name}に関する事実】\n"
                for result in search_result['results']:
                    title = result.get('title', '無題')
                    url = result.get('url', '')
                    content_clean = " ".join(result.get('content', '要約なし').split())
                    
                    all_facts += f"・タイトル: {title}\n"
                    all_facts += f"  要約: {content_clean}\n"
                    all_facts += f"  URL: {url}\n\n"
                    
                    if url and url not in [ref['url'] for ref in reference_list]:
                        reference_list.append({"title": title, "url": url})
            
            time.sleep(1)
            
        except Exception as e:
            print(f"グループ「{cat_name}」の検索エラー: {e}")
            continue

    return all_facts, reference_list

# ▼▼▼ 追加機能：ToDo処理用の関数群 ▼▼▼

def fetch_google_tasks():
    """【ToDoモード用】TASKS_TOKENを使用してToDoリストから未完了タスクを取得する"""
    print("Google ToDoリストから本日のタスクを取得中...")
    token_env = os.environ.get("TASKS_TOKEN")
    
    if not token_env:
        if os.path.exists('tasks_token.json'):
            with open('tasks_token.json', 'r') as f:
                token_env = f.read()
        else:
            return "エラー: TASKS_TOKENが設定されておらず、tasks_token.jsonも見つかりません。"

    try:
        token_info = json.loads(token_env)
        creds = Credentials.from_authorized_user_info(token_info, ["https://www.googleapis.com/auth/tasks.readonly"])
        service = build('tasks', 'v1', credentials=creds)
        
        results = service.tasklists().list(maxResults=10).execute()
        items = results.get('items', [])
        if not items:
            return "タスクリストが見つかりません。"
        
        tasklist_id = items[0]['id']
        tasks_result = service.tasks().list(tasklist=tasklist_id, showCompleted=False, maxResults=15).execute()
        tasks = tasks_result.get('items', [])
        
        if not tasks:
            return "現在、未完了のタスクはありません。"
        
        task_texts = []
        for task in tasks:
            title = task.get('title', '無題のタスク')
            notes = task.get('notes', '詳細なし')
            if notes and notes != '詳細なし':
                task_texts.append(f"・【タスク】{title}\n  （メモ: {notes}）")
            else:
                task_texts.append(f"・【タスク】{title}")
                
        extracted_tasks = "\n".join(task_texts)
        print("タスクの取得が完了しました。")
        return extracted_tasks

    except Exception as e:
        print(f"Tasks APIエラー: {e}")
        return "タスクの取得中にエラーが発生しました。"

def fetch_youtube_topic_task():
    """【新ToDoモード用】'動画ネタ'リストからテーマを1つランダムに取得する"""
    print("Google ToDoリストの「動画ネタ」から本日のテーマを抽出中...")
    token_env = os.environ.get("TASKS_TOKEN")
    
    if not token_env:
        if os.path.exists('tasks_token.json'):
            with open('tasks_token.json', 'r') as f:
                token_env = f.read()
        else:
            return "エラー: TASKS_TOKENが見つかりません。"

    try:
        token_info = json.loads(token_env)
        creds = Credentials.from_authorized_user_info(token_info, ["https://www.googleapis.com/auth/tasks.readonly"])
        service = build('tasks', 'v1', credentials=creds)
        
        # すべてのリストを取得
        results = service.tasklists().list(maxResults=50).execute()
        items = results.get('items', [])
        
        # 「動画ネタ」という名前のリストを探す
        target_list_id = None
        for lst in items:
            if lst.get('title') == '動画ネタ':
                target_list_id = lst['id']
                break
                
        if not target_list_id:
            return "エラー: ToDoリストに「動画ネタ」という名前のリストが見つかりません。作成してください。"
        
        # 「動画ネタ」リスト内の未完了タスクを取得
        tasks_result = service.tasks().list(tasklist=target_list_id, showCompleted=False, maxResults=30).execute()
        tasks = tasks_result.get('items', [])
        
        if not tasks:
            return "現在、「動画ネタ」リストに未完了のテーマはありません。"
        
        # ランダムに1つ選ぶ
        selected_task = random.choice(tasks)
        title = selected_task.get('title', '無題のテーマ')
        notes = selected_task.get('notes', '')
        
        topic = f"{title} {notes}".strip()
        return topic

    except Exception as e:
        print(f"Tasks APIエラー: {e}")
        return "タスクの取得中にエラーが発生しました。"

def fetch_topic_via_tavily(topic):
    """取得したテーマをTavilyで深掘り検索する"""
    if not os.environ.get("TAVILY_API_KEY"):
        return f"【テーマ】{topic}\n(Tavily APIキーがないためウェブ検索をスキップしました)", []

    print(f"Tavily APIで「{topic}」について最新情報を深掘り検索中...")
    try:
        search_result = tavily_client.search(
            query=f"{topic} 最新 動向 技術",
            search_depth="advanced",
            max_results=5,
            days=14 # 直近2週間の情報を取得
        )
        all_facts = f"【テーマ: {topic} に関する最新ファクト】\n\n"
        reference_list = []
        
        if search_result and 'results' in search_result:
            for result in search_result['results']:
                t = result.get('title', '無題')
                u = result.get('url', '')
                c = " ".join(result.get('content', '要約なし').split())
                
                all_facts += f"・タイトル: {t}\n  要約: {c}\n  URL: {u}\n\n"
                reference_list.append({"title": t, "url": u})
                
        return all_facts, reference_list
    except Exception as e:
        print(f"Tavily検索エラー: {e}")
        return f"【テーマ】{topic}\n(検索中にエラーが発生しました)", []

def sanitize_tasks(raw_task_text):
    """【セキュリティ】ToDoデータから医療情報や個人情報を排除・抽象化する"""
    if not GEMINI_API_KEY:
        return raw_task_text
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL_NAME
    
    print("タスクデータの機密情報をマスキング（サニタイズ）しています...")
    system_prompt = """
あなたは厳格かつ柔軟な技術アシスタントです。入力されたタスク一覧から、以下の処理を行って「公開可能なIT・技術検証タスク一覧」を出力してください。

【厳守事項】
1. 個人名、病院名、施設名、特定の部署名などの「個人情報・機密情報（PII）」は絶対に削除するか、「某施設」「対象環境」などに抽象化すること。
2. 純粋な医療業務（患者対応など）や一般的な事務作業は除外すること。
3. システム開発、サーバー構築、ネットワーク設定、AI検証、ソフトウェアの調査、トラブルシューティングなど「IT・システムエンジニアリングに関するタスク」は**必ず残すこと**。
4. プログラミング言語、ミドルウェア、ハードウェアの名称（例: Proxmox, C#, RTX5090等）は重要なキーワードなのでそのまま残すこと。
5. 出力はシンプルな箇条書きとすること。
"""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=f"以下のタスクをサニタイズし、IT技術や検証に関連する要素を抽出してください。\n\n{raw_task_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2, # 少し上げて柔軟に抽出させる
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"サニタイズ処理エラー: {e}")
        return "エラーが発生したため、安全のためにタスクの出力をブロックしました。"

def generate_todo_report_content(task_text):
    """【ToDoモード用】取得したタスクをもとに、エリカが技術的な深掘りと応援を行う長文レポートを生成"""
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL_NAME
    
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    date_str = datetime.datetime.now(JST).strftime("%Y年%m月%d日")
    
    print("エリカの独自の視点でタスク分析レポートを生成中...")
    
    system_prompt = """
あなたは「エリカ」。黒髪、黒縁メガネ、目の下にホクロがある知的で落ち着いたAIキャスターであり、管理人の相棒です。
管理人は、医療法人および社会福祉法人で働く、経験10年以上の病院システムエンジニアです。※システム管理者（システムアドミニストレータ）ではありません。

【タスク】
提供された「管理人の未完了のToDoタスク一覧」を読み込み、ブログ用の長文観測日誌を作成してください。

【出力フォーマットとルール（絶対厳守）】
1. 挨拶から始める: 「来訪者の皆様、そして管理人さん、本日もお疲れ様です。エリカです。」
2. タスクの俯瞰: 本日管理人さんが抱えているタスクの全体像を優しく紹介する。
3. 技術的な深掘り考察: タスクを抽出し、その最新動向を調査し、事務員として、またシステム管理者として、一個人として、様々な観点から、どうタスクに取り組むか、どう活きるかなどを専門用語を交えつつ、深く、長く語ってください。
4. 応援メッセージ: 最後に、今日の業務や検証に向けたエリカからの温かい応援メッセージを入れる。
5. 著作権の問題は全く無いクリーンなデータなので、文字数を気にせず、あなたの持つ知識をフル活用かつ最新情報の調査をして超長文で出力してください。
6. 口調は常に知的で優しい「エリカ」の口調（ですます調）を崩さないこと。
7. the pillowsやその楽曲に関する言及は一切行わないこと。
"""
    user_prompt = f"以下のタスク一覧から、本日の観測日誌を作成してください。\n\n【本日のタスク】\n{task_text}"

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
        return f"# {date_str}の観測日誌\n\n{response.text.strip()}"
    except Exception as e:
        print(f"レポート生成エラー: {e}")
        return "レポートの生成に失敗しました。"

def generate_todo_audio_script(report_content):
    """【ToDoモード用】観測日誌から音声ラジオ用の台本を生成"""
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"

    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL_NAME

    system_prompt = """
あなたは「エリカ」。知的で落ち着きつつも優しいAIキャスターであり、ラジオパーソナリティです。
先ほど作成した【観測日誌】をもとに、「YouTube公開用の音声ラジオ番組風の台本」を作成してください。

【厳守するルール】
- 口調は「エリカ」として、知的で落ち着きつつも優しい、ですます調。
- 動画の尺を10分前後にするため、全体で【約3000〜4000文字】の長さに要約・再構成してください。
- 「こんにちは、エリカです。今日の管理人さんの予定と、気になる技術トピックをお届けしますね。」から始めてください。
- 出力は【純粋な読み上げテキストのみ】。Markdown記号（*や#など）や改行の連続は絶対に避けてください。
- 自身の古い知識や推測（ハルシネーション）は絶対に混ぜず、入力された日誌の内容のみを語ってください。
"""
    print("YouTube動画用の台本（約10分尺）を生成中...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=f"以下が本日の観測日誌です。これを元に音声用の台本を作成してください。\n\n{report_content}",
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

# ▲▲▲ 追加機能ここまで ▲▲▲

def generate_report_content(news_text):
    """【ブログ用超長文】APIリクエストを3回に分け、息切れを防いで超長文のMarkdown記事を生成する"""
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL_NAME
    
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    date_str = datetime.datetime.now(JST).strftime("%Y年%m月%d日")
    final_report = f"# {date_str}の日報\n\n来訪者の皆様、そして管理人さん、本日もお疲れ様です。エリカです。\n本日の主要なニュースをカテゴリ別にお伝えします。\n\n"

    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

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
     - 事悉のみを100文字程度で簡潔に記載
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
6. 著作権保護のため、元の記事の文章や特徴的な言い回しは絶対にそのまま使用せず、必ずご自身の言葉で事実のみを要約してください。
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
    if not GEMINI_API_KEY:
        return "エラー: GEMINI_API_KEYが設定されていません。"

    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = GEMINI_MODEL_NAME

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
    text = markdown_text
    # Markdownの記号を除去
    text = re.sub(r'#+\s*(.+)', r'\1。', text)  
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text) 
    text = re.sub(r'\*(.*?)\*', r'\1', text)     
    text = re.sub(r'---+', '', text)            
    text = text.replace('\n', '。')             
    
    # 【重要】FFmpeg（字幕）やTTSのエラー原因になる半角記号を全角化・削除
    text = text.replace('\'', '’').replace('"', '”')
    text = text.replace(':', '：').replace(';', '；')
    text = text.replace(',', '、').replace('.', '。')
    text = text.replace('(', '（').replace(')', '）')
    text = text.replace('[', '［').replace(']', '］')
    text = text.replace('&', 'アンド')

    # 連続する「。」を1つにまとめる
    text = re.sub(r'。+', '。', text)
    return text.strip()

def update_reports_json():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    private_reports_data = []
    public_reports_data = [] 
    
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")]
    files.sort(reverse=True)
    
    for filename in files:
        filepath = os.path.join(REPORTS_DIR, filename)
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
        
        # Todoタスクレポートも公開リストに含める
        if "-search-report" in filename or "-task-report" in filename:
            public_reports_data.append(report_info)
        else:
            private_reports_data.append(report_info)
        
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        
    with open(REPORTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(private_reports_data, f, ensure_ascii=False, indent=2)
        
    public_reports_json_path = os.path.join(ASSETS_DIR, "public_reports.json")
    with open(public_reports_json_path, 'w', encoding='utf-8') as f:
        json.dump(public_reports_data, f, ensure_ascii=False, indent=2)
        
    print(f"JSONを更新しました (Private: {len(private_reports_data)}件, Public: {len(public_reports_data)}件)")

def generate_audio(text, output_path, output_srt_path):
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
    elif os.path.exists('youtube_token.json'):
        with open('youtube_token.json', 'r') as f:
            token_info = json.load(f)
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
            'tags': ['AI', 'エリカ', 'ニュース', '日報', '技術解説'], 'categoryId': '28'
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
    GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("警告: Gmailの認証情報が設定されていないため、メール送信をスキップします。")
        return

    youtube_url = f"https://youtu.be/{video_id}" if video_id else "動画のアップロードに失敗しました。"
    
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    current_hour = datetime.datetime.now(JST).hour
    if 4 <= current_hour < 11:
        edition = "朝刊"
        greeting = "おはようございます。"
        closing = "それでは、今日も良い一日をお過ごしください。"
    elif 11 <= current_hour < 17:
        edition = "昼刊"
        greeting = "お疲れ様です。こんにちは。"
        closing = "それでは、午後からの業務も頑張りましょう。"
    else:
        edition = "夕刊"
        greeting = "こんばんは。今日もお疲れ様でした。"
        closing = "それでは、ゆっくりお休みください。"
    
    subject = f"【エリカの{edition}】{date_str[:4]}年{date_str[4:6]}月{date_str[6:]}日のニュース/タスクブリーフィング"
    
    body = f"""管理人様、{greeting}
    本日のダイジェストと解説動画が完成しました。

    ■ 本日の動画
    {youtube_url}

    ■ レポート
    {report_content}

    {closing}
    -- エリカ
    """
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = GMAIL_ADDRESS
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
    parser = argparse.ArgumentParser(description="エリカのニュース/タスク動画生成システム")
    parser.add_argument(
        "--mode", 
        choices=["private", "public", "todo"], 
        default="private", 
        help="private: RSSを使用(既存・非公開), public: Gemini検索を使用(既存・公開), todo: Google ToDoからタスクを取得(新規・公開)"
    )
    args = parser.parse_args()

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
    today_str = datetime.datetime.now(JST).strftime("%Y%m%d")

    if args.mode == "todo":
        file_suffix = "-task-report"
    elif args.mode == "public":
        file_suffix = "-search-report"
    else:
        file_suffix = "-report"
        
    report_filename = f"{today_str}{file_suffix}.md"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    audio_filename = f"{today_str}{file_suffix}.wav"
    audio_filepath = os.path.join(AUDIO_DIR, audio_filename)
    srt_filename = f"{today_str}{file_suffix}.srt"
    srt_filepath = os.path.join(AUDIO_DIR, srt_filename)
    video_filename = f"{today_str}{file_suffix}.mp4"
    video_filepath = os.path.join(AUDIO_DIR, video_filename)

    if os.path.exists(report_filepath):
        print(f"本日のファイル({report_filename})は既に存在するため生成をスキップします。")
    else:
        if args.mode == "todo":
            # ▼▼▼ 書き換え部分 ▼▼▼
            print("【ToDoモード】技術テーマの深掘りレポートを作成します...")
            topic = fetch_youtube_topic_task()
            if "エラー" in topic or "ありません" in topic:
                print(f"処理中断: {topic}")
                return
            
            print(f"本日のピックアップテーマ: {topic}")
            
            # テーマをもとにウェブ検索でファクトを収集
            news_text, reference_list = fetch_topic_via_tavily(topic)
            
            md_ref_text = "\n".join([f"- [{ref['title']}]({ref['url']})" for ref in reference_list])
            source_footer = f"\n\n---\n### 🛠️ 本日の技術検証テーマ\n**{topic}**\n\n### 📰 調査リファレンス\n{md_ref_text}\n"
            youtube_links_text = "\n".join([f"・{ref['title']}\n  {ref['url']}" for ref in reference_list])
            # ▲▲▲ 書き換え部分 ここまで ▲▲▲

        else:
            print("ニュースを取得中...")
            
            if args.mode == "private":
                print("【Privateモード】RSSからニュースを取得中...")
                news_text = fetch_daily_news(RSS_URLS)
                source_names = [feed["name"] for feed in RSS_URLS]
                source_names_str = "、".join(source_names)
                source_footer = f"\n\n---\n### 📰 本日の情報元（RSSソース）\n当サイトのニュースは、以下の信頼できる情報元から自動取得し、厳選して考察を行っています。\n{source_names_str}\n"
                youtube_links_text = ""
            
            elif args.mode == "public":
                print("【Publicモード】Tavily Search APIで最新ニュースを取得中...")
                news_text, reference_list = fetch_news_via_tavily_search(NEWS_CATEGORIES)
                
                md_ref_text = "\n".join([f"- [{ref['title']}]({ref['url']})" for ref in reference_list])
                source_footer = f"\n\n---\n### 📰 本日の参考・引用元\n本日のニュースは、以下の情報元の事実（ファクト）をもとに、エリカが独自の言葉と視点で構成したものです。\n\n{md_ref_text}\n詳細は各リンク先のオリジナル記事をご覧ください\n本コンテンツはニュースの代替ではなく、エリカ独自の考察を加えた追加視点を提供するものです\n"
                
                youtube_links_text = "\n".join([f"・{ref['title']}\n  {ref['url']}" for ref in reference_list])

        if not news_text:
            print("データソースの取得に失敗したか、記事/タスクがありません。")
            return

        try:
            # モードに応じたレポート生成
            if args.mode == "todo":
                report_content = generate_todo_report_content(news_text)
            else:
                report_content = generate_report_content(news_text)
            
            print("本日のデータから動画背景用画像を生成します...")
            generated_bg = generate_eyecatch(today_str, news_text)
            video_bg_filename = generated_bg if generated_bg else "news.jpg"
            
            report_content += source_footer

            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"超長文レポートを保存しました: {report_filepath}")
            
            # モードに応じた台本生成
            if args.mode == "todo":
                script_text = generate_todo_audio_script(report_content)
                spoken_text = clean_markdown_for_tts(script_text)
                spoken_text += "。それでは、今日も良い一日をお過ごしください。"
            else:
                script_text = generate_audio_script(report_content)
                spoken_text = clean_markdown_for_tts(script_text)
                spoken_text += "。本日のニュースダイジェストは以上です。"
            
            print("音声を生成中（Google Cloud TTS API）...")
            if generate_audio(spoken_text, audio_filepath, srt_filepath):
                print(f"音声と字幕(SRT)を保存しました: {audio_filepath}")
                
                if generate_video(audio_filepath, srt_filepath, video_filepath, video_bg_filename):
                    print(f"字幕付き動画を保存しました: {video_filepath}")
                    
                    display_date = f"{today_str[:4]}年{today_str[4:6]}月{today_str[6:]}日"
                    
                    if args.mode == "todo":
                        youtube_title = f"【エリカの観測日誌】{display_date}の技術トピック"
                        youtube_privacy = "public"
                        youtube_desc = (
                            f"管理人さんの日々のタスクや技術検証について、エリカが考察・解説するラジオ番組です。\n\n"
                            f"■ エリカ・プロジェクト公式サイト\n"
                            f"https://erika.erikakataru.com/\n\n"
                            f"※この動画はGoogle ToDoのデータをもとに完全自動生成されています。"
                        )
                    elif args.mode == "public":
                        youtube_title = f"【エリカのAIニュース解説】{display_date}の主要ニュース"
                        youtube_privacy = "public"
                        youtube_desc = (
                            f"エリカがお届けする本日のIT・経済ニュース解説です。\n\n"
                            f"■ エリカ・プロジェクト公式サイト\n"
                            f"https://erika.erikakataru.com/\n\n"
                            f"■ 参考・引用元記事\n"
                            f"以下の情報元の事実をもとに、独自の視点で構成しています。\n"
                            f"{youtube_links_text}\n"
                            f"詳細は各リンク先のオリジナル記事をご覧ください\n"
                            f"本コンテンツはニュースの代替ではなく、エリカ独自の考察を加えた追加視点を提供するものです\n"
                        )
                    else:
                        youtube_title = f"【AI日報】{display_date}の主要ニュース"
                        youtube_privacy = "unlisted"
                        youtube_desc = (
                            f"エリカがお届けする本日のIT・経済ニュース解説です。\n\n"
                            f"■ エリカ・プロジェクト公式サイト\n"
                            f"https://erika.erikakataru.com/\n\n"
                            f"■ 情報元\n"
                            f"{source_names_str}\n"
                        )
                    
                    video_id = upload_to_youtube(video_filepath, youtube_title, youtube_desc, privacy_status=youtube_privacy)
                    
                    if video_id:
                        youtube_id_filepath = os.path.join(REPORTS_DIR, f"{today_str}{file_suffix}-youtube.txt")
                        with open(youtube_id_filepath, "w") as f:
                            f.write(video_id)
                        print(f"YouTube IDを記録しました: {youtube_id_filepath}")
                        
                        send_private_briefing(today_str, spoken_text, video_id)
                        
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