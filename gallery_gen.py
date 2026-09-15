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
        content = response.choices[0].message.content or ""
        alt_text = content.strip().replace('"', '').replace('「', '').replace('」', '')
        return alt_text if alt_text else f"画像 ({', '.join(labels[:2])})"
    except Exception as e:
        print(f"  [Error] Sakura LLM failed for {filename}: {e}")
        return f"画像 ({', '.join(labels[:2])})"

def generate_enemy_name_with_sakura_llm(filename, alt_text):
    if not sakura_client or not alt_text:
        return "ネームレス エリカ"
        
    system_prompt = (
        "あなたは中二病のネーミングセンスを持つ熟練のシステムエンジニアです。"
        "提供された画像の説明から、RPGのボスキャラクター風の名前を考案してください。\n"
        "【厳守する条件】\n"
        "1. 「終焉」「深淵」「漆黒」「幻影」などの大げさで中二病的な表現を使うこと。\n"
        "2. 「デッドロック」「カーネルパニック」「ゼロデイ」「オーバーフロー」などの『ITインフラ・ネットワーク・プログラミング用語』を必ず混ぜること。\n"
        "3. 名前の最後は必ず「 エリカ」で終わること。\n"
        "4. 挨拶や説明は一切不要です。生成した名前だけを1行で出力してください。"
    )
    user_prompt = f"画像の説明: {alt_text}\n出力例: 漆黒のデッドロック エリカ"

    try:
        response = sakura_client.chat.completions.create(
            model=SAKURA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8, 
            max_tokens=50
        )
        enemy_name = (response.choices[0].message.content or "").strip()
        enemy_name = enemy_name.replace('"', '').replace('「', '').replace('」', '').replace('\n', '')
        
        # 失敗時や空文字のときは「ネームレス エリカ」を返し、次回の再処理対象にする
        if not enemy_name or enemy_name == "エリカ":
            return "ネームレス エリカ"
            
        if not enemy_name.endswith("エリカ"):
            enemy_name += " エリカ"
            
        return enemy_name
    except Exception as e:
        print(f"  [Error] Enemy Name generation failed for {filename}: {e}")
        return "ネームレス エリカ"

def generate_gallery_json():
    gallery_data = []
    
    existing_data = {}
    if os.path.exists(GALLERY_OUTPUT):
        try:
            with open(GALLERY_OUTPUT, 'r', encoding='utf-8') as f:
                old_gallery = json.load(f)
                for category_data in old_gallery:
                    cat_name = category_data.get("name")
                    for img in category_data.get("images", []):
                        key = f"{cat_name}/{img['file']}"
                        existing_data[key] = {
                            "alt": img.get('alt', ''),
                            "enemy_name": img.get('enemy_name', '')
                        }
        except json.JSONDecodeError:
            pass
    
    alt_cache = {}
    if os.path.exists(ALT_CACHE_FILE):
        try:
            with open(ALT_CACHE_FILE, 'r', encoding='utf-8') as f:
                alt_cache = json.load(f)
        except json.JSONDecodeError:
            pass

    os.makedirs(GALLERY_DIR, exist_ok=True)
    dirs = [d for d in os.listdir(GALLERY_DIR) if os.path.isdir(os.path.join(GALLERY_DIR, d))]
    categories = sorted(dirs, reverse=True)
    
    for category in categories:
        cat_path = os.path.join(GALLERY_DIR, category)
        image_files = sorted([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        
        images_with_alt = []
        for img_file in image_files:
            file_path = os.path.join(cat_path, img_file)
            cache_key = f"{category}/{img_file}"
            
            alt_text = ""
            enemy_name = ""

            # ----------------------------------------------------
            # ① altテキストの独立チェック＆生成
            # ----------------------------------------------------
            if cache_key in existing_data and existing_data[cache_key].get('alt'):
                alt_text = existing_data[cache_key]['alt']
            elif cache_key in alt_cache and isinstance(alt_cache[cache_key], dict) and alt_cache[cache_key].get('alt'):
                alt_text = alt_cache[cache_key]['alt']
            elif cache_key in alt_cache and isinstance(alt_cache[cache_key], str):
                alt_text = alt_cache[cache_key] 
            else:
                print(f"[{cache_key}] altを生成中 (Vision API -> Sakura LLM)...")
                labels = get_image_labels_from_vision(file_path)
                alt_text = generate_alt_with_sakura_llm(img_file, labels) if labels else f"エリカの画像 ({img_file})"
                time.sleep(1)

            # ----------------------------------------------------
            # ② enemy_nameの独立チェック＆生成
            # ----------------------------------------------------
            exist_enemy = existing_data.get(cache_key, {}).get('enemy_name', '').strip()
            cached_enemy = alt_cache.get(cache_key, {}).get('enemy_name', '').strip() if isinstance(alt_cache.get(cache_key), dict) else ''

            # 再生成の対象となる「未完成」な名前のリスト
            invalid_names = ["", "エリカ", "ネームレス エリカ"]

            if exist_enemy and exist_enemy not in invalid_names:
                enemy_name = existing_data[cache_key]['enemy_name']
            elif cached_enemy and cached_enemy not in invalid_names:
                enemy_name = alt_cache[cache_key]['enemy_name']
            else:
                print(f"[{cache_key}] enemy_nameを(再)生成中 (Sakura LLM)...")
                enemy_name = generate_enemy_name_with_sakura_llm(img_file, alt_text)
                time.sleep(1)
            
            alt_cache[cache_key] = {"alt": alt_text, "enemy_name": enemy_name}
            
            images_with_alt.append({
                "file": img_file,
                "alt": alt_text,
                "enemy_name": enemy_name
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
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
        articles_data.append({"id": article_id, "title": title})
    os.makedirs(os.path.dirname(ARTICLES_OUTPUT), exist_ok=True)
    with open(ARTICLES_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, indent=4, ensure_ascii=False)
    print(f"Generated {ARTICLES_OUTPUT} with {len(articles_data)} articles.")

if __name__ == "__main__":
    generate_gallery_json()
    generate_articles_json()