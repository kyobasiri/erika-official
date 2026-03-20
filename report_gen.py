import os
import json
import datetime
import feedparser
import re
from openai import OpenAI

# ==========================================
# 設定項目
# ==========================================
# さくらAIエンジンの設定（環境変数からキーを取得）
# ※エンドポイントURLはさくらインターネットの実際の仕様に合わせて変更してください
API_KEY = os.environ.get("SAKURA_API_KEY")
API_BASE = "https://api.ai.sakura.ad.jp/v1" # 仮のエンドポイント
MODEL_NAME = "gpt-oss-120b" # または gpt-oss-120b,llm-jp-3.1-8x13b-instruct4

# ディレクトリ設定
REPORTS_DIR = "reports"
ASSETS_DIR = "assets"
REPORTS_JSON = os.path.join(ASSETS_DIR, "reports.json")

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

def main():
    # 1. フォルダの準備
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # 2. 今日の日付でファイル名を決定
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    report_filename = f"{today_str}-report.md"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    
    # すでに今日の日報が存在する場合はスキップ（重複実行防止）
    if os.path.exists(report_filepath):
        print(f"本日の日報({report_filename})は既に存在するため生成をスキップします。")
    else:
        # 3. ニュースの取得
        print("ニュースを取得中...")
        news_text = fetch_daily_news(RSS_URLS)
        
        if not news_text:
            print("ニュースの取得に失敗したか、記事がありません。")
            return

        # 4. AIによる日報生成
        print("エリカが日報を執筆中...")
        try:
            report_content = generate_report_content(news_text)
            
            # 5. Markdownとして保存
            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"日報を保存しました: {report_filepath}")
            
        except Exception as e:
            print(f"AIAPI呼び出しエラー: {e}")
            return

    # 6. JSONインデックスの更新（既存のものも含めて再構築）
    update_reports_json()
    print("全処理が完了しました。")

if __name__ == "__main__":
    main()