import os
import requests
import datetime
import base64
# Google GenAI SDK
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# ==========================================
# Cloudflare 認証設定（テスト用）
# ==========================================
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

MODEL = "@cf/black-forest-labs/flux-2-klein-9b"

# 共通のディレクトリ設定
ASSETS_DIR = "assets"

def generate_eyecatch(date_str, news_text):
    """今日のニュースからプロンプトを作り、Cloudflare Workers AIで画像を生成する"""
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("エラー: Cloudflareの認証情報が設定されていません。")
        return None
    if not GEMINI_API_KEY:
        print("エラー: GEMINI_API_KEYが設定されていません。")
        return None

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 1. ニュースから英語プロンプトを生成
    prompt_maker = f"""
    以下の今日のニュースをもとに、画像生成AI用の英語プロンプトを1つ作成してください。
    【条件】
    - 背景は今日のニュースのテーマ（AI、インフラ、サイバーセキュリティ、経済、国内一般ニュース、世界ニュース・国際情勢など）を象徴する近未来的なサイバー空間やニューススタジオ。
    - アニメ調で非常に美しく細部まで詳細に書き込まれた「黒髪ミディアムボブで黒縁メガネをかけた知的な女性」を配置すること。この女性が画像の中央に来るようにすること。この女性が魅力的であることがこの画像の必須条件。
    - 出力は英語のプロンプト（50〜100文字程度）のみ。
    【ニュース】\n{news_text[:1000]}
    """
    
    print("画像生成用のプロンプトをGeminiで作成中...")
    try:
        res_prompt = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt_maker
        )
        image_prompt = res_prompt.text.strip()
        print(f"作成されたプロンプト: {image_prompt}")
    except Exception as e:
        print(f"プロンプト生成エラー: {e}")
        return None

    # 2. Cloudflare APIで画像生成
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    multipart_data = {
        "prompt": (None, image_prompt),
        "num_steps": (None, "20")
    }

    print(f"Cloudflare Workers AI ({MODEL}) で画像を生成中...")
    response = requests.post(url, headers=headers, files=multipart_data)

    if response.status_code == 200:
        image_dir = os.path.join(ASSETS_DIR, "images")
        os.makedirs(image_dir, exist_ok=True)
        image_filename = f"{date_str}-eyecatch.jpg"
        image_filepath = os.path.join(image_dir, image_filename)
        
        if "application/json" in response.headers.get("Content-Type", ""):
            res_json = response.json()
            image_bytes = base64.b64decode(res_json["result"]["image"])
        else:
            image_bytes = response.content
            
        with open(image_filepath, "wb") as f:
            f.write(image_bytes)
        print(f"画像を正常に保存しました: {image_filepath}")
        return image_filename
    else:
        print(f"Cloudflare APIエラー: {response.status_code} - {response.text}")
        return None

# ==========================================
# 単独テスト用の実行ブロック
# ==========================================
if __name__ == "__main__":
    print("Cloudflare画像生成の単独テストを開始します...")
    
    test_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # 英語のプロンプトを直接指定してテスト
    test_prompt = "Anime style futuristic news studio, holographic AI data streams, glowing security network grids. Intelligent woman with black medium bob hair, black-rimmed glasses, and a mole under her right eye. Cinematic lighting, cybersecurity theme, sleek infrastructure, high quality, no text, no logos, vibrant digital atmosphere."
    
    generate_eyecatch(test_date, test_prompt)
