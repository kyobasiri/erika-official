import os
import json
import time
import base64
import re
from openai import OpenAI

# ==========================================
# 設定項目
# ==========================================
SAKURA_API_KEY = os.environ.get("SAKURA_API_KEY")
SAKURA_API_BASE = "https://api.ai.sakura.ad.jp/v1"
SAKURA_MODEL = "preview/gemma-4-31B-it"

GALLERY_DIR = 'public/assets/images/gallery'
# 崩れていた既存の説明文を作り直す件数の上限（1回の実行あたり）。
# 一度に全部やるとデプロイが長く止まるので、push のたびに少しずつ直す。新しい画像はこの上限に含めない。
MAX_REGENERATE_PER_RUN = int(os.environ.get('GALLERY_MAX_REGENERATE', '100'))
GALLERY_OUTPUT = 'public/assets/gallery.json'
ALT_CACHE_FILE = 'alt_cache.json' # これはそのままでもOK
ARTICLES_DIR = 'public/articles'
ARTICLES_OUTPUT = 'public/assets/articles.json'
# トップページで流す「目玉の画像」の一覧。ファイル名が数字だけの画像（1.webp, 20.webp など）を集める。
# 0 は歌詞付きの画像なので入れない。数字以外の名前（ComfyUI_... など）は作っただけの画像として入れない。
FEATURED_OUTPUT = 'public/assets/featured.json'
_FEATURED_FILE = re.compile(r'^(?!0+\.)\d+\.(?:webp|png|jpe?g)$', re.IGNORECASE)

# ==========================================
# クライアント初期化
# ==========================================
sakura_client = None
if SAKURA_API_KEY:
    sakura_client = OpenAI(
        api_key=SAKURA_API_KEY,
        base_url=SAKURA_API_BASE
    )

# モデルの出力の後始末
#  - 制御用の文字（<tool_call|>、<|im_end|>、<end_of_turn> など）を取り除く
#  - 説明文の代わりに <img ... alt=...> を書いてきた場合は、alt の中身を取り出す
_CONTROL_TOKEN = re.compile(r'<\|?/?[A-Za-z_][\w-]*\|?>')
_ALT_ATTR = re.compile(r'alt\s*[=:]\s*["\']?([^"\'>\n`}]+)')
# 説明文の先頭にくっつく不要な文字（}、{、記号、英字のかけら など）。日本語が始まるところまで落とす
_LEADING_JUNK = re.compile(r'^[^぀-ヿ㐀-鿿０-ｚ「『（]+')

def clean_model_text(text):
    text = _CONTROL_TOKEN.sub('', text or '')
    m = _ALT_ATTR.search(text)
    if m:
        text = m.group(1)
    text = text.replace('```html', '').replace('```', '').replace('`', '').replace('**', '')
    text = text.replace('\r', '').replace('\n', '')
    text = _LEADING_JUNK.sub('', text.strip())
    # 「い。白い狐の…」のような、前の文の切れ端を落とす
    text = re.sub(r'^.{1,3}。(?=.{8,})', '', text)
    return text.strip().rstrip('}').strip()

# 説明文として使えない出力か（思考の過程・断り文句・指示文の写し・長すぎる・HTMLの残りなど）
_BROKEN_WORDS = ('記述してください', '思考', '提供されていない', '添付されていない', 'できません', '申し訳',
                 'アップロード', '提案', 'alt属性', 'キャプション', '画像の分析', '以下の')

def looks_broken(text):
    if not text or len(text) < 8 or len(text) > 90:
        return True
    if any(w in text for w in _BROKEN_WORDS):
        return True
    if '<' in text or '>' in text or '[' in text or '*' in text:
        return True
    if re.search(r'https?://|\.jp\b|\.com\b', text):
        return True
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    return ascii_letters > len(text) * 0.3

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

    alt_text = ""
    for attempt in range(2):  # 壊れた出力のときは1回だけ作り直す
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
            alt_text = clean_model_text(alt_response.choices[0].message.content).replace('"', '').replace('「', '').replace('」', '')
        except Exception as e:
            print(f"  [Error] Sakura LLM (alt) failed for {filename}: {e}")
            alt_text = ""
        if not looks_broken(alt_text):
            break
        print(f"  [Retry] alt の出力が崩れていたので作り直します: {alt_text[:40]!r}")
        alt_text = ""
        time.sleep(1)

    # それでも作れなかったときは空にしておく（次回の実行でまた作り直される）
    if looks_broken(alt_text):
        alt_text = ""

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
        enemy_name = clean_model_text(enemy_response.choices[0].message.content)
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
    existing_data = {}
    
    # すでに存在する gallery.json を読み込んでキャッシュ代わりにする
    if os.path.exists(GALLERY_OUTPUT):
        try:
            with open(GALLERY_OUTPUT, 'r', encoding='utf-8') as f:
                old_gallery = json.load(f)
                for cat in old_gallery:
                    for img in cat.get("images", []):
                        key = f"{cat['name']}/{img['file']}"
                        # 以前の出力に残っている制御用の文字も、ここで掃除する
                        alt = clean_model_text(img.get("alt", ""))
                        existing_data[key] = {
                            # 使えない説明文は空にして、下で作り直させる
                            "alt": "" if looks_broken(alt) else alt,
                            "enemy_name": clean_model_text(img.get("enemy_name", ""))
                        }
        except json.JSONDecodeError:
            pass

    os.makedirs(GALLERY_DIR, exist_ok=True)
    dirs = [d for d in os.listdir(GALLERY_DIR) if os.path.isdir(os.path.join(GALLERY_DIR, d))]
    categories = sorted(dirs, reverse=True)
    
    regenerated = 0
    for category in categories:
        cat_path = os.path.join(GALLERY_DIR, category)
        image_files = sorted([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        
        images_with_alt = []
        for img_file in image_files:
            file_path = os.path.join(cat_path, img_file)
            cache_key = f"{category}/{img_file}"
            
            # gallery.json に有効なデータが存在していればAPI呼び出しをスキップ
            cached = existing_data.get(cache_key)
            if isinstance(cached, dict) and cached.get('alt') and cached.get('enemy_name') and cached.get('enemy_name') != "ネームレス エリカ":
                alt_text = cached['alt']
                enemy_name = cached['enemy_name']
            elif isinstance(cached, dict) and regenerated >= MAX_REGENERATE_PER_RUN:
                # 既存の画像の作り直しは、上限に達したら次回へ回す
                alt_text = cached.get('alt', '')
                enemy_name = cached.get('enemy_name') or "ネームレス エリカ"
            else:
                if isinstance(cached, dict):
                    regenerated += 1
                print(f"[{cache_key}] 画像を解析して alt と enemy_name を生成中...")
                alt_text, enemy_name = generate_alt_and_enemy_name(file_path, img_file)
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

    # gallery.jsonの保存
    os.makedirs(os.path.dirname(GALLERY_OUTPUT), exist_ok=True)
    with open(GALLERY_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {GALLERY_OUTPUT} with {len(gallery_data)} categories.")

    generate_featured_json(gallery_data)

def generate_featured_json(gallery_data):
    # { "20261009": ["1.webp", "2.webp", ...], ... } の形で、小さく保存する（トップページで読むため）
    featured = {}
    for category in gallery_data:
        files = [img['file'] for img in category['images'] if _FEATURED_FILE.match(img['file'])]
        if files:
            featured[category['name']] = sorted(files, key=lambda f: int(f.split('.')[0]))
    with open(FEATURED_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(featured, f, ensure_ascii=False, separators=(',', ':'))
    total = sum(len(v) for v in featured.values())
    print(f"Generated {FEATURED_OUTPUT} with {total} images.")

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