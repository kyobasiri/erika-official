import os
from google import genai
from google.genai import types
import datetime

# 共通のディレクトリ設定
ASSETS_DIR = "assets"

def generate_eyecatch(date_str, news_text):
    """今日のニュースからプロンプトを生成し、画像生成APIでアイキャッチ画像を作成する"""
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("エラー: GEMINI_API_KEYが設定されていません。")
        return None
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt_maker = f"""
    以下の今日のニュースのハイライトをもとに、画像生成AI用の英語のプロンプトを1つ作成してください。
    
    【条件】
    - 今日のニュースのテーマ（AI、インフラ、サイバーセキュリティなど）を象徴する、ニューススタジオの風景。
    - 画面のどこかに「黒髪ミディアムボブで黒縁メガネをかけ、右目の下に泣きぼくろのある知的な女性（AIキャスターのエリカ）」を配置すること。
    - 画像内に文字（Text）やロゴは絶対に含めないこと。
    - 出力は英語のプロンプト（30〜50語程度）のみ。余計な解説は不要。
    
    【ニュース】
    {news_text[:1000]}
    """
    try:
        print("アイキャッチ画像用の英語プロンプトを生成中...")
        res_prompt = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt_maker
        )
        image_prompt = res_prompt.text.strip()
        print(f"画像プロンプト: {image_prompt}")
        
        print("画像を生成中...")
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="16:9"
            )
        )
        
        # 画像の保存先設定
        image_dir = os.path.join(ASSETS_DIR, "images")
        os.makedirs(image_dir, exist_ok=True)
        image_filename = f"{date_str}-eyecatch.jpg"
        image_filepath = os.path.join(image_dir, image_filename)
        
        # APIから返ってきたバイトデータを画像ファイルとして書き出す
        with open(image_filepath, "wb") as f:
            f.write(result.generated_images[0].image.image_bytes)
            
        print(f"アイキャッチ画像を保存しました: {image_filepath}")
        return image_filename
    except Exception as e:
        print(f"画像生成エラー: {e}")
        return None

# ==========================================
# 単独テスト用の実行ブロック
# ==========================================
if __name__ == "__main__":
    # ファイルが直接実行された時だけ動くテストコード
    print("アイキャッチ画像生成の単独テストを開始します...")
    
    test_date = datetime.datetime.now().strftime("%Y%m%d")
    test_news = "PFNが初の国産フルスクラッチLLMを発表。また、企業におけるランサムウェア攻撃の被害が拡大しており、バックアップとゼロトラストネットワークの重要性が高まっている。"
    
    generate_eyecatch(test_date, test_news)