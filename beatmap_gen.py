import json
import os
import librosa
import numpy as np
import yt_dlp
import random

# ==========================================
# 設定項目
# ==========================================
MASTER_JSON_PATH = "public/assets/thepillows_releases_tab.json"
OUTPUT_DIR = "public/assets/beatmaps"
# TEMP_AUDIO_PATH = "temp_audio.m4a"
TEMP_AUDIO_PATH = "temp_audio.wav"
# ==========================================
# 譜面生成ロジック
# ==========================================
def generate_advanced_beatmap(audio_path, start_time=0.0, end_time=None):
    """
    librosaを使って音声を解析し、拍のグリッドとオンセット強度から
    難易度別（Easy, Normal, Hard）のノーツ配列を生成する。
    """
    # 1. 音声の読み込み（サンプリングレートを22050に下げて処理を高速化）
    y, sr = librosa.load(audio_path, sr=22050, offset=start_time, duration=end_time)
    
    # 2. 拍（四分音符）の検出
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # 3. オンセット強度（音の立ち上がりの強さ）の取得
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # 4. グリッドの生成（四分、八分、十六分）とスコア付け
    grids = []
    for i in range(len(beat_times) - 1):
        t_start = beat_times[i]
        t_end = beat_times[i+1]
        step = (t_end - t_start) / 4.0 # 1拍を4分割（十六分音符間隔）
        
        for j in range(4):
            t_grid = t_start + step * j
            grid_type = "4th" if j == 0 else "8th" if j == 2 else "16th"
            
            # グリッド周辺のオンセット強度を取得してスコア化
            frame_idx = librosa.time_to_frames(t_grid, sr=sr)
            # 前後数フレームの最大強度を取得
            score = np.max(onset_env[max(0, frame_idx-2):min(len(onset_env), frame_idx+3)])
            
            grids.append({
                "time_ms": int((t_grid + start_time) * 1000),
                "type": grid_type,
                "score": float(score)
            })

    # スコアの中央値を基準に閾値を設定（曲全体のダイナミクスに合わせる）
    scores = [g["score"] for g in grids]
    threshold = np.median(scores) if scores else 0
    
    beatmaps = {"easy": [], "normal": [], "hard": []}
    prev_lane = {"easy": 0, "normal": 0, "hard": 0}
    
    # 5. 難易度別のノーツ抽出とレーン配置アルゴリズム
    for grid in grids:
        # 確実に通常のPythonの整数(int)と浮動小数点数(float)にしておく
        time_ms = int(grid["time_ms"])
        g_type = grid["type"]
        score = float(grid["score"])

        # --- Easy: 四分音符メインで、強い音を拾う ---
        if g_type == "4th" and score > threshold * 1.0:
            lane = int(1 - prev_lane["easy"]) # 完全交互
            beatmaps["easy"].append({"time": time_ms, "lane": lane})
            prev_lane["easy"] = lane
            
        # --- Normal: 四分音符 ＋ 強い八分音符 ---
        if (g_type == "4th" and score > threshold * 0.7) or \
           (g_type == "8th" and score > threshold * 1.3):
            # 8分の場合はあえて同じレーンを叩かせるなど少しパターン化
            lane = int(1 - prev_lane["normal"] if g_type == "4th" else prev_lane["normal"])
            beatmaps["normal"].append({"time": time_ms, "lane": lane})
            prev_lane["normal"] = lane
            
        # --- Hard: 四分、八分 ＋ 強い十六分音符 ---
        if score > threshold * 0.5: # 閾値を下げて多くの音を拾う
            if g_type == "16th":
                lane = int(1 - prev_lane["hard"]) # 16分の細かい連打は必ず交互（トリル）
            else:
                # 乱数で適度に同レーンを混ぜる (Numpyの数値を確実にintに変換)
                chosen = np.random.choice([0, 1], p=[0.7, 0.3]) if prev_lane["hard"] == 0 else np.random.choice([0, 1], p=[0.3, 0.7])
                lane = int(chosen)
                
            beatmaps["hard"].append({"time": time_ms, "lane": lane})
            prev_lane["hard"] = lane

    return beatmaps

# ==========================================
# メイン処理
# ==========================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # マスタJSONの読み込み
    if not os.path.exists(MASTER_JSON_PATH):
        print(f"エラー: {MASTER_JSON_PATH} が見つかりません。")
        return
        
    with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
        songs = json.load(f)
    
    # ▼▼▼ 修正ポイント ▼▼▼
    # yt-dlpのオプション（進行状況を表示し、wavに確実に変換する）
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s', # 拡張子をyt-dlpに自動決定させる
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'quiet': False,       # TrueからFalseに変更（ダウンロードの進捗バーを表示する）
        'no_warnings': False, # 警告も念のため表示する
    }
    # ▲▲▲ 修正ポイント ▲▲▲
    
    for song in songs:
        share_url = song.get("share_url", "")
        if not share_url:
            continue
            
        # URLからYouTubeのIDを取得
        yt_id = share_url.split("/")[-1]
        output_file = os.path.join(OUTPUT_DIR, f"beatmap_{yt_id}.json")
        
        # 既に生成済みの場合はスキップ
        if os.path.exists(output_file):
            print(f"[スキップ] {song['title']} (既に生成済み)")
            continue
            
        print(f"\n[{song['title']}] の譜面を生成中... ({yt_id})")
        
        try:
            # 前回のエラーで残ったゴミファイルがあれば削除しておく
            if os.path.exists(TEMP_AUDIO_PATH):
                os.remove(TEMP_AUDIO_PATH)

            # 1. 音声の一時ダウンロード
            print("  - 音声をダウンロード中...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([share_url])
                
            # 2. 譜面生成
            print("  - 音声を解析して譜面を生成中...")
            start_time = song.get("start_time", 0.0)
            end_time = song.get("end_time", None)
            
            # wav形式に変換されたファイルを読み込む
            difficulties = generate_advanced_beatmap(TEMP_AUDIO_PATH, start_time, end_time)
            
            # 3. JSON出力
            output_data = {
                "id": yt_id,
                "title": song["title"],
                "difficulties": difficulties
            }
            
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(output_data, out, ensure_ascii=False, indent=2)
                
            print(f"  -> 生成完了: {output_file}")
            
        except Exception as e:
            print(f"  [エラー] {song['title']} の処理中にエラーが発生しました: {e}")
            
        finally:
            # 一時オーディオファイルのクリーンアップ
            if os.path.exists(TEMP_AUDIO_PATH):
                try:
                    os.remove(TEMP_AUDIO_PATH)
                except:
                    pass

    print("\nすべての譜面生成処理が完了しました！")

if __name__ == "__main__":
    main()