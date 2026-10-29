"""ERIKA ROCK ACTION stage planner for Cloud Run.

The server returns stage layouts, spawn schedules, scaled enemy stats and boss
metadata. All real-time combat and hit detection remain client-side, so an
unavailable API never interrupts a run.
"""
from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

MASTER_PATH = Path(__file__).with_name("game-master.json")
MASTER = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
ENEMIES = MASTER["enemies"]
BOSSES = MASTER["bosses"]
QUOTES = MASTER["quotes"]
assert len(ENEMIES) >= 7 and len(BOSSES) == 12 and len(MASTER["stages"]) >= 6

app = FastAPI(title="ERIKA Rock Action API", version="2.0.0")

# The game is public and stateless. Do not use CORS credentials or a wildcard origin.
allowed_origins = [
    "https://erika.erikakataru.com",
    "https://erikakataru.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
allowed_origins.extend(s.strip() for s in os.environ.get("CORS_ORIGINS", "").split(",") if s.strip())
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://([a-z0-9-]+\.)?erika-official\.pages\.dev$",
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def scaling(stage: int) -> dict[str, float]:
    loops = (stage - 1) // len(BOSSES)
    within_loop = (stage - 1) % len(BOSSES)
    loop_boost = 2.8 * 1.8 ** (loops - 1) if loops else 1.0
    return {
        "enemy": (1 + within_loop * 0.22) * loop_boost,
        "boss": (1 + within_loop * 0.18) * loop_boost,
        "speed": (1 + min(0.45, within_loop * 0.05)) * (1.22 if loops else 1.0),
    }


def create_stage_plan(stage: int) -> dict[str, Any]:
    """Deterministic and replayable per-stage plan, no database required."""
    if not 1 <= stage <= 120:
        raise ValueError("stage must be between 1 and 120")
    rng = random.Random(f"erika-rock-action-v2:{stage}")
    mul = scaling(stage)
    loops = (stage - 1) // len(BOSSES)
    count = 14 + min(8, (stage - 1) // 3 + loops)
    spawn_at = 900
    waves = []
    for i in range(count):
        # Early waves are less punishing; introduce the full enemy set progressively.
        pool_limit = min(len(ENEMIES), 4 + ((stage - 1) % 12) // 2 + loops)
        enemy = ENEMIES[rng.randrange(pool_limit)]
        spawn_at += rng.randint(1350, 1950)
        waves.append({
            "id": f"s{stage}-w{i}",
            "type": enemy["type"],
            "spawn_delay_ms": spawn_at,
            "hp": max(1, round(enemy["hp"] * mul["enemy"])),
            "speed": round(enemy["speed"] * mul["speed"], 3),
        })

    boss = BOSSES[(stage - 1) % len(BOSSES)]
    quote = QUOTES[rng.randrange(len(QUOTES))]
    stage_theme = MASTER["stages"][(stage - 1) % len(MASTER["stages"])]
    return {
        "stage": stage,
        "plan_version": 2,
        "theme": stage_theme["themeName"],
        "enemy_waves": waves,
        "boss": {
            "id": boss["id"],
            "name": boss["name"],
            "hp": max(1, round(boss["baseHp"] * mul["boss"])),
            "pattern": boss["pattern"],
            "cutin_quote": quote,
        },
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/stage-start")
def stage_start(stage: int = Query(default=1, ge=1, le=120)) -> dict[str, Any]:
    try:
        return create_stage_plan(stage)
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
