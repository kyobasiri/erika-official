import os
import json
import time
import base64
from openai import OpenAI

# ==========================================
# 設定項目
# ==========================================
SAKURA_API_KEY = os.environ.get("SAKURA_API_KEY")
SAKURA_API_BASE = "https://api.ai.sakura.ad.jp/v1"
SAKURA_MODEL = "preview/gemma-4-31B-it"

GALLERY_DIR = 'assets/images/gallery'
GALLERY_OUTPUT = 'assets/gallery.json'
ALT_CACHE_FILE = 'alt_cache.json'
ARTICLES_DIR = 'articles'
ARTICLES_OUTPUT = 'assets/articles.json'

# ==========================================
# クライアント初期化
# ==========================================
sakura_client = None
if SAKURA_API_KEY:
    sakura_client = OpenAI(
        api_key=SAKURA_API_KEY,
        base_url=SAKURA_API_BASE
    )

def encode_image(image_path):
    """画像をBase64形式にエンコードする"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_alt_and_enemy_name(image_path, filename):
    """画像をAIに視認させ、alt属性と敵キャラ名を同時に生成する"""
    if not sakura_client:
        return f"エリカの画像 ({filename})", "ネームレス エリカ"

    is_erika_art = "ComfyUI" in filename or "pixiv" in filename
    context = "これは「エリカ」という黒髪ミディアムヘアで黒縁メガネをかけ、泣きぼくろのある女性キャラクターの画像です。" if is_erika_art else "これはギャラリーの画像です。"
    
    base64_image = encode_image(image_path)
    
    # ----------------------------------------------------
    # ① 画像を視認して alt テキストを生成
    # ----------------------------------------------------
    alt_system_prompt = (
        "あなたはWebアクセシビリティとSEOの専門家です。"
        "提供された画像の特徴を読み取り、簡潔で説明的な日本語のテキストを1文(50文字以内)で生成してください。"
        "出力はalt属性のテキストのみとしてください。"
    )
    alt_user_prompt = f"{context}\nこの画像の特徴を50文字以内で説明してください。"

    try:
        alt_response = sakura_client.chat.completions.create(
            model=SAKURA_MODEL,
            messages=[
                {"role": "system", "content": alt_system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": alt_user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=100
        )
        alt_text = (alt_response.choices[0].message.content or "").strip().replace('"', '').replace('「', '').replace('」', '')
        if not alt_text:
            alt_text = f"エリカの画像 ({filename})"
    except Exception as e:
        print(f"  [Error] Sakura LLM (alt) failed for {filename}: {e}")
        alt_text = f"エリカの画像 ({filename})"

    time.sleep(1) # APIの連続リクエスト制限対策

    # ----------------------------------------------------
    # ② 生成した alt テキストを元に中二病の敵キャラ名を生成
    # ----------------------------------------------------
    enemy_system_prompt = (
        "あなたは中二病のネーミングセンスを持つ熟練のシステムエンジニアです。"
        "提供された画像の説明から、RPGの敵キャラクター風の名前を考案してください。\n"
        "【厳守する条件】\n"
        "1. 過剰な装飾の中二病用語を混ぜて、大袈裟でカッコつけるような言葉を使うこと。\n"
        "2. ITインフラ・ネットワーク・プログラミング用語のような言葉を少しだけ混ぜて、ちょっとしたアクセントにすること。\n"
        "3. 名前の最後は必ず「 エリカ」で終わること。\n"
        "4. 挨拶や説明は一切不要です。生成した名前だけを1行で出力してください。"
    )
    enemy_user_prompt = f"画像の説明: {alt_text}\n出力例: 漆黒のデッドロック エリカ"

    try:
        enemy_response = sakura_client.chat.completions.create(
            model=SAKURA_MODEL,
            messages=[
                {"role": "system", "content": enemy_system_prompt},
                {"role": "user", "content": enemy_user_prompt}
            ],
            temperature=0.8, 
            max_tokens=100        )
        enemy_name = (enemy_response.choices[0].message.content or "").strip()
        enemy_name = enemy_name.replace('"', '').replace('「', '').replace('」', '').replace('\n', '')
        
        if not enemy_name or enemy_name == "エリカ" or "ネームレス" in enemy_name:
            enemy_name = "ネームレス エリカ"
        elif not enemy_name.endswith("エリカ"):
            enemy_name += " エリカ"
            
    except Exception as e:
        print(f"  [Error] Enemy Name generation failed for {filename}: {e}")
        enemy_name = "ネームレス エリカ"

    return alt_text, enemy_name

def generate_gallery_json():
    gallery_data = []
    alt_cache = {}
    
    # 既存のキャッシュファイルがあれば読み込む（今回は全再生成のため無視することも可能ですが、後々のために残します）
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
            
            # キャッシュに存在し、有効なデータが入っていればスキップ
            cached_data = alt_cache.get(cache_key)
            if isinstance(cached_data, dict) and cached_data.get('alt') and cached_data.get('enemy_name') and cached_data.get('enemy_name') != "ネームレス エリカ":
                alt_text = cached_data['alt']
                enemy_name = cached_data['enemy_name']
            else:
                print(f"[{cache_key}] 画像を解析して alt と enemy_name を生成中...")
                alt_text, enemy_name = generate_alt_and_enemy_name(file_path, img_file)
                # キャッシュに保存
                alt_cache[cache_key] = {"alt": alt_text, "enemy_name": enemy_name}
                time.sleep(1) # API制限対策
            
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

    # キャッシュファイルの保存
    with open(ALT_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(alt_cache, f, indent=4, ensure_ascii=False)

    # gallery.jsonの保存
    os.makedirs(os.path.dirname(GALLERY_OUTPUT), exist_ok=True)
    with open(GALLERY_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {GALLERY_OUTPUT} with {len(gallery_data)} categories.")

def generate_articles_json():
    # 記事一覧の生成（既存のまま）
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