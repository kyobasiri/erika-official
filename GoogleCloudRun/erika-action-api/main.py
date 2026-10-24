import asyncio
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Erika Rock Action Cloud Run API")

# Cloudflare Pagesの本番ドメインとローカル開発環境からのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://erika.erikakataru.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 作成した7体の敵キャラ定義
ENEMY_CATALOG = [
    {"type": "soot",      "name": "煤玉モンスター",   "hp": 10, "speed": 2.2, "score": 100, "stompable": True},
    {"type": "lime",      "name": "ライム豆っこ",     "hp": 10, "speed": 3.0, "score": 150, "stompable": True},
    {"type": "jelly",     "name": "桃色ゼリー",       "hp": 15, "speed": 2.0, "score": 200, "stompable": True},
    {"type": "note_ghost","name": "音符のおばけ",     "hp": 15, "speed": 2.5, "score": 250, "stompable": True},
    {"type": "turtle",    "name": "ずんぐりカメ",     "hp": 35, "speed": 1.2, "score": 300, "stompable": True,  "armored": True},
    {"type": "mole",      "name": "鉱夫モグラ",       "hp": 20, "speed": 0.0, "score": 350, "stompable": False, "helmet": True},
    {"type": "hedgehog",  "name": "赤いハリネズミ",   "hp": 25, "speed": 6.5, "score": 400, "stompable": False, "spiky": True},
]

QUOTES = [
    {"quote": "手探りでもただ前に進むしかない。いずれなんとかなるだろってな。", "source": "『シャーマンキング』麻倉葉"},
    {"quote": "お前が信じる、お前を信じろ！", "source": "『天元突破グレンラガン』カミナ"},
]

async def generate_enemy_waves(stage: int):
    """非同期でステージの敵出現タイムライン（ウェーブ）を構築"""
    await asyncio.sleep(0.02)
    waves = []
    current_delay = 1000  # 1秒後から出現開始
    for i in range(6 + stage * 2):
        enemy = random.choice(ENEMY_CATALOG)
        waves.append({
            "id": f"enemy_{i}",
            "spawn_delay_ms": current_delay,
            **enemy
        })
        current_delay += random.randint(1800, 3200)  # 1.8〜3.2秒間隔で次の敵が出現
    return waves

async def generate_boss_data(stage: int):
    """非同期でボス情報とカットイン名言を選出"""
    await asyncio.sleep(0.02)
    return {
        "boss_name": f"SHADOW ERIKA // STAGE {stage}",
        "hp": 120 + (stage * 30),
        "cutin_quote": random.choice(QUOTES)
    }

@app.get("/api/health")
async def health():
    """タイトル画面でCloud Runのコールドスタート（スリープ）を起こす用"""
    return {"status": "ok"}

@app.get("/api/stage-start")
async def stage_start(stage: int = 1):
    """敵ウェーブ生成とボス情報生成を asyncio.gather で並列実行して一括返却"""
    waves, boss = await asyncio.gather(
        generate_enemy_waves(stage),
        generate_boss_data(stage)
    )
    return {
        "stage": stage,
        "enemy_waves": waves,
        "boss": boss
    }