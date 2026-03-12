import os
import json

# --- ギャラリー用の設定 ---
GALLERY_DIR = 'assets/images/gallery'
GALLERY_OUTPUT = 'assets/gallery.json'

# --- 記事用の設定 ---
ARTICLES_DIR = 'articles'
ARTICLES_OUTPUT = 'assets/articles.json'

def generate_gallery_json():
    gallery_data = []
    
    if not os.path.exists(GALLERY_DIR):
        print(f"Directory {GALLERY_DIR} not found. Creating...")
        os.makedirs(GALLERY_DIR, exist_ok=True)

    dirs = [d for d in os.listdir(GALLERY_DIR) if os.path.isdir(os.path.join(GALLERY_DIR, d))]
    categories = sorted(dirs, reverse=True)
    
    for category in categories:
        cat_path = os.path.join(GALLERY_DIR, category)
        images = sorted([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        
        if images:
            gallery_data.append({
                "name": category,
                "images": images
            })

    os.makedirs(os.path.dirname(GALLERY_OUTPUT), exist_ok=True)
    with open(GALLERY_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {GALLERY_OUTPUT} with {len(gallery_data)} categories.")


def generate_articles_json():
    """記事フォルダ(.md)を読み込んで目次JSONを生成する"""
    articles_data = []
    
    if not os.path.exists(ARTICLES_DIR):
        print(f"Directory {ARTICLES_DIR} not found. Creating...")
        os.makedirs(ARTICLES_DIR, exist_ok=True)

    # .mdファイル一覧を取得
    files = [f for f in os.listdir(ARTICLES_DIR) if f.lower().endswith('.md')]
    
    # ファイル名で降順ソート（例：002-xxx.md が 001-xxx.md より上に来るようにする）
    files = sorted(files, reverse=True)
    
    for filename in files:
        file_path = os.path.join(ARTICLES_DIR, filename)
        article_id = os.path.splitext(filename)[0] # 拡張子.mdを除外したID（例: 001-test）
        
        title = article_id # 初期値はファイル名にしておく
        
        # ファイルを開いて1行ずつ読み、最初の「# 」で始まる行をタイトルとして抽出する
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Markdownの見出し1(h1)をタイトルとして認識
                if line.startswith('# '):
                    title = line[2:].strip() # "# " の部分を削ってタイトル文字だけにする
                    break
        
        # 配列に追加
        articles_data.append({
            "id": article_id,
            "title": title
        })

    os.makedirs(os.path.dirname(ARTICLES_OUTPUT), exist_ok=True)
    with open(ARTICLES_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {ARTICLES_OUTPUT} with {len(articles_data)} articles.")


if __name__ == "__main__":
    # 両方のJSON生成関数を実行する
    generate_gallery_json()
    generate_articles_json()