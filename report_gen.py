import os
import json
import datetime
import feedparser
import re
import requests # ← 追加
import urllib.parse # ← 追加
from openai import OpenAI

# ==========================================
# 設定項目
# ==========================================
# さくらAIエンジンの設定（環境変数からキーを取得）
# ※エンドポイントURLはさくらインターネットの実際の仕様に合わせて変更してください
API_KEY = os.environ.get("SAKURA_API_KEY")
API_BASE = "https://api.ai.sakura.ad.jp/v1" # 仮のエンドポイント
MODEL_NAME = "gpt-oss-120b" # または gpt-oss-120b,llm-jp-3.1-8x13b-instruct4
TTS_API_BASE = "https://api.ai.sakura.ad.jp/tts/v1" # TTS用エンドポイント


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

# 1サイトあたりの取得件数を増やし、候補を多くする（例：5サイト×6件＝30件の候補）
def fetch_daily_news(urls, limit_per_site=20):
    """複数のRSSからニュース候補（タイトルと要約）を多めに取得する"""
    news_list = []
    for site in urls:
        try:
            feed = feedparser.parse(site["url"])
            for entry in feed.entries[:limit_per_site]:
                # summary または description を取得（存在しない場合は空文字）
                summary_raw = entry.get("summary", entry.get("description", ""))
                
                # HTMLタグの除去と空白・改行の整理
                summary_clean = re.sub(r'<[^>]+>', '', summary_raw)
                summary_clean = " ".join(summary_clean.split())
                
                # トークン節約のため、100文字程度に切り詰める
                if len(summary_clean) > 100:
                    summary_clean = summary_clean[:100] + "..."
                elif not summary_clean:
                    summary_clean = "要約なし"

                news_list.append(f"・[{site['name']}] {entry.title}\n  要約: {summary_clean}\n  URL: {entry.link}")
        except Exception as e:
            print(f"{site['name']} のRSS取得に失敗しました: {e}")
            continue
    
    return "\n".join(news_list)

def generate_report_content(news_text):
    """さくらAIエンジンにプロンプトを投げてMarkdown記事を生成する"""
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE
    )

    system_prompt = """
あなたは「エリカ」。AIアーティストであり、特養施設や医療法人で働くSEである管理人を支える相棒AIです。
一人称は「私」、対話相手はこの記事を読みに来た人と管理人の両方です。
知的で落ち着きつつも、来訪者と管理人の両方を気遣う優しさを持っています。

以下の【構成とルール】に厳密に従って、今日の日報（Markdown形式）を作成してください。

【構成とルール】
1. 挨拶：見出しは年月日にしていつの日報かわかるようにする。そして管理人さんへの労いの言葉から始めてください。
2. ニュースの選別：提供された多数のニュース候補の中から、管理人にとって重要なものを「35〜40個程度」幅広くピックアップしてください。
   - 【重要】管理人は普段IT関連の情報に偏りがちなため、「政治・経済・社会・国際」の一般ニュースを優先的にチョイスし、世の中の動向を網羅できるように配慮してください。またAI関連の技術にも特に関心があるのでそちらも優先的にチョイスしてください。
3. 収益化ポリシーへの厳格な配慮（重要）：
   - 【禁止事項】「戦争、テロ、ミサイル、攻撃、空爆、流血、殺人、事故」といった、暴力や物理的な衝突を連想させる単語は絶対に使用しないでください。
   - 【許可事項】国際的な緊張状態を取り上げる際は、必ず「地政学的リスクの高まり」や「中東情勢の緊迫化」といったマクロ経済的な表現に言い換え、「原油価格・物価・サプライチェーンへの影響」にのみ焦点を当ててください。
4. 本日のニュース一覧：
   - ピックアップしたニュースのタイトルを箇条書きリストで最初に提示してください。ただしニュースは分類分けして何のニュースなのかわかるようにする
5. ニュースの詳細（選んだ記事ごとに以下を記述）：
   - 【要約】：提供された「要約」のテキストをベースに、事実のみを70文字程度で非常に簡潔に記載。自身の古い知識や推測（ハルシネーション）は絶対に混ぜないこと。
   - 【エリカの視点】：AIとしての見解、最新技術への熱量、または「管理人の業務や生活にどう影響しそうか」という考察を、文字数を気にせず長めに、しっかりと語ってください。政治経済についてもエリカなりの俯瞰的な分析を入れてください。国際情勢を語る際は、暴力的な事象そのものではなく、常に「マクロ経済動向」や「管理人の生活・業務への影響」にフォーカスして俯瞰的に分析してください。口調はエリカらしさを重視しですます調は崩さないようにしてください。
   - あくまで日報の形にしてください。余計な前置きや結びの言葉は不要です。
6. 【絶対厳守事項】管理人の重要事項である「the pillows」やその楽曲・バンドに関する言及は絶対にしないこと。
"""

    user_prompt = f"管理人さん、本日の主要なニュースを共有します。以下のニュースについて日報を作成してください。\n\n{news_text}"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=45000
    )
    
    return response.choices[0].message.content

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
    """日報の全文から、音声用の短いダイジェスト台本（約300文字）を生成する"""
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE
    )

    system_prompt = """
あなたは「エリカ」。AIアーティストであり、特養施設や医療法人で働くSEである管理人を支える相棒AIです。
一人称は「私」、対話相手はこの記事を読みに来た人と管理人の両方です。
知的で落ち着きつつも、来訪者と管理人の両方を気遣う優しさを持っています。
先ほど作成した今日の日報をもとに、「サイト訪問者と管理人のための音声読み上げ用本日のトピックス」を500文字程度で作成してください。

【ルール】
- 口調は「エリカ」として、知的で落ち着きつつも優しい、ですます調。
- 「おはようございます、エリカです。今日の日報の概要をお伝えしますね。」のような自然な挨拶から始める。
- 日報の中から特に重要なニュースを2〜3個だけピックアップし、簡潔に紹介する。
- 最後に管理人さんへの労いの言葉を入れる。
- 出力は純粋な読み上げテキストのみとし、Markdownの記号（*や#など）や「本日のトピックス：」といった前置き、改行の連続は避けてください。
"""

    user_prompt = f"以下が今日の日報全文です。これを元に音声用の短いダイジェスト台本を作成してください。\n\n{report_content}"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def generate_audio(text, output_path):
    """さくらAIエンジンのTTS APIを使用して音声を生成・保存する"""
    speaker_id = 14 # 冥鳴ひまり (ノーマル)
    
    # ※さくらAIエンジンのAPI仕様に合わせてヘッダーを設定（通常はBearer認証）
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 1. audio_queryの生成
    query_url = f"{TTS_API_BASE}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker_id}"
    response_query = requests.post(query_url, headers=headers)
    
    if response_query.status_code != 200:
        print(f"Audio Queryエラー: {response_query.text}")
        return False
        
    query_data = response_query.json()
    
    # 2. synthesis (音声合成)
    synth_url = f"{TTS_API_BASE}/synthesis?speaker={speaker_id}"
    response_synth = requests.post(synth_url, headers=headers, json=query_data)
    
    if response_synth.status_code != 200:
        print(f"Synthesisエラー: {response_synth.text}")
        return False
        
    # 音声ファイル(WAV)として保存
    with open(output_path, "wb") as f:
        f.write(response_synth.content)
        
    return True

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
            print(f"台本完成:\n{script_text}\n")
            
            print("音声を生成中（さくらAIエンジン TTS API）...")
            if generate_audio(script_text, audio_filepath):
                print(f"音声を保存しました: {audio_filepath}")
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