import os
import json

# 画像が保存されているルートディレクトリ
BASE_DIR = 'assets/images/gallery'
# 出力先をassetsフォルダ直下に設定
OUTPUT_FILE = 'assets/gallery.json'

def generate_gallery_json():
    gallery_data = {}
    
    if not os.path.exists(BASE_DIR):
        print(f"Directory {BASE_DIR} not found. Creating...")
        os.makedirs(BASE_DIR, exist_ok=True)

    # フォルダ（カテゴリ）をスキャン
    categories = sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))])
    
    for category in categories:
        cat_path = os.path.join(BASE_DIR, category)
        # 画像ファイルを取得してソート（名前順）
        images = sorted([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        if images:
            gallery_data[category] = images

    # 出力先フォルダがない場合は作成
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # JSONとして保存
    with os.fdopen(os.open(OUTPUT_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644), 'w', encoding='utf-8') as f:
        json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {OUTPUT_FILE} with {len(gallery_data)} categories.")

if __name__ == "__main__":
    generate_gallery_json()