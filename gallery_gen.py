import os
import json

BASE_DIR = 'assets/images/gallery'
OUTPUT_FILE = 'assets/gallery.json'

def generate_gallery_json():
    # JavaScriptの勝手なソートを防ぐため、辞書{}ではなく配列[]を使います
    gallery_data = []
    
    if not os.path.exists(BASE_DIR):
        print(f"Directory {BASE_DIR} not found. Creating...")
        os.makedirs(BASE_DIR, exist_ok=True)

    # フォルダ一覧を取得
    dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    
    # ★ポイント：タイムスタンプではなく「フォルダ名」で降順（Z→A、大きい数字→小さい数字）ソート
    categories = sorted(dirs, reverse=True)
    
    for category in categories:
        cat_path = os.path.join(BASE_DIR, category)
        # 画像はファイル名順（昇順）でOK
        images = sorted([f for f in os.listdir(cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        
        if images:
            # カテゴリ名と画像のリストをセットにして配列に追加
            gallery_data.append({
                "name": category,
                "images": images
            })

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(gallery_data, f, indent=4, ensure_ascii=False)
    
    print(f"Generated {OUTPUT_FILE} with {len(gallery_data)} categories.")

if __name__ == "__main__":
    generate_gallery_json()