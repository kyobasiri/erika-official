import os
import json
import time
from google.cloud import vision
from google.oauth2 import service_account
from openai import OpenAI

# ==========================================
# 設定項目
# ==========================================
SAKURA_API_KEY = os.environ.get("SAKURA_API_KEY")
SAKURA_API_BASE = "https://api.ai.sakura.ad.jp/v1"
SAKURA_MODEL = "gpt-oss-120b"
GCP_TOKEN_STR = os.environ.get("GCP_VISION_CREDENTIALS_TOKEN")

GALLERY_DIR = 'assets/images/gallery'
GALLERY_OUTPUT = 'assets/gallery.json'
ALT_CACHE_FILE = 'alt_cache.json'
ARTICLES_DIR = 'articles'
ARTICLES_OUTPUT = 'assets/articles.json'

# ==========================================
# クライアント初期化
# ==========================================
vision_client = None
if GCP_TOKEN_STR:
    try:
        creds_info = json.loads(GCP_TOKEN_STR)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    except Exception as e:
        print(f"Vision API 認証エラー: {e}")

sakura_client = None
if SAKURA_API_KEY:
    sakura_client = OpenAI(
        api_key=SAKURA_API_KEY,
        base_url=SAKURA_API_BASE
    )

# ==========================================
# 処理関数
# ==========================================
def get_image_labels_from_vision(image_path):
    if not vision_client:
        return []
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = vision_client.label_detection(image=image, max_results=5)
        return [label.description for label in response.label_annotations]
    except Exception as e:
        print(f"  [Error] Vision API failed for {image_path}: {e}")
        return []

def generate_alt_with_sakura_llm(filename, labels):
    if not sakura_client or not labels:
        return f"エリカのギャラリー画像 ({filename})"

    is_erika_art = "ComfyUI" in filename or "pixiv" in filename
    context = "これは「エリカ」という黒髪ミディアムヘアで黒縁メガネをかけ、泣きぼくろのある女性キャラクターの画像です。" if is_erika_art else "これはギャラリーの画像です。"
    
    system_prompt = (
        "あなたはWebアクセシビリティとSEOの専門家です。"
        "提供された画像の特徴を表すキーワード群から、HTMLのalt属性に最適な、"
        "簡潔で説明的な日本語のテキストを1文(50文字以内)で生成してください。"
    )
    user_prompt = f"{context}\n抽出されたキーワード: {', '.join(labels)}\n出力はalt属性のテキストのみとしてください。"

    try:
        response = sakura_client.chat.completions.create(
            model=SAKURA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        alt_text = response.choices[0].message.content.strip()
        return alt_text.replace('"', '').replace('「', '').replace('」', '')
    except Exception as e:
        print(f"  [Error] Sakura LLM failed for {filename}: {e}")
        return f"画像 ({', '.join(labels[:2])})"

def generate_gallery_json():
    gallery_data = []
    
    alt_cache = {}
    if os.path.exists(ALT_CACHE_FILE):
        try:
            with open(ALT_CACHE_FILE, 'r', encoding='utf-8') as f:
                alt_cache = json.load(f)
        except json.JSONDecodeError:
            print("Cache file is corrupted. Starting fresh.")
            alt_cache = {}

    if not os.path.exists(GALLERY_DIR):
        print(f"Directory {GALLERY_DIR} not found. Creating...")
        os.makedirs(GALLERY_DIR, exist_ok=True)

    dirs = [d for d in os.listdir(GALLERY_DIR) if os.path.isdir(os.path.join(GALLERY_DIR, d))]
    categories = sorted(dirs, reverse=True)
    
    for category in categories:
        cat_path = os.path.join(GALLERY_DIR, category)
        image_files = sorted([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        
        images_with_alt = []
        for img_file in image_files:
            file_path = os.path.join(cat_path, img_file)
            
            # 修正1: カテゴリ名を含めて一意のキーにする
            cache_key = f"{category}/{img_file}"
            
            if cache_key not in alt_cache:
                print(f"Processing alt text for {cache_key}...")
                labels = get_image_labels_from_vision(file_path)
                
                if labels:
                    alt_text = generate_alt_with_sakura_llm(img_file, labels)
                else:
                    alt_text = f"エリカの画像 ({img_file})"
                
                print(f"  -> Generated alt: {alt_text}")
                alt_cache[cache_key] = alt_text
                
                # 修正2: 取得するたびに逐次保存し、途中終了によるデータロスを防ぐ
                with open(ALT_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(alt_cache, f, indent=4, ensure_ascii=False)
                    
                time.sleep(1) # API制限対策
            
            images_with_alt.append({
                "file": img_file,
                "alt": alt_cache[cache_key] # 修正1に伴い参照キーを変更
            })
        
        if images_with_alt:
            gallery_data.append({
                "name": category,
                "images": images_with_alt
            })

    with open(ALT_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(alt_cache, f, indent=4, ensure_ascii=False)

    os.makedirs(os.path.dirname(GALLERY_OUTPUT), exist_ok=True)
    with open(GALLERY_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {GALLERY_OUTPUT} with {len(gallery_data)} categories.")

def generate_articles_json():
    articles_data = []
    
    if not os.path.exists(ARTICLES_DIR):
        os.makedirs(ARTICLES_DIR, exist_ok=True)

    files = [f for f in os.listdir(ARTICLES_DIR) if f.lower().endswith('.md')]
    files = sorted(files, reverse=True)
    
    for filename in files:
        file_path = os.path.join(ARTICLES_DIR, filename)
        article_id = os.path.splitext(filename)[0]
        title = article_id
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
        
        articles_data.append({
            "id": article_id,
            "title": title
        })

    os.makedirs(os.path.dirname(ARTICLES_OUTPUT), exist_ok=True)
    with open(ARTICLES_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {ARTICLES_OUTPUT} with {len(articles_data)} articles.")

if __name__ == "__main__":
    generate_gallery_json()
    generate_articles_json()