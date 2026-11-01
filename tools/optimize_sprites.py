"""ERIKA ROCK ACTION 用スプライト最適化スクリプト.

public/sprites 以下の PNG（1枚 約1MB・1254px 前後）から、ゲーム内の表示サイズに
見合った軽量 WebP を同じ場所に生成します。元の PNG は残し、ゲーム側は
WebP → PNG の順で読み込むため、WebP が無い新規画像もそのまま動きます。

すでに WebP だけを置いている場合（PNG が無い場合）は、その WebP が大きすぎれば
同じファイルを表示サイズに合わせて縮小して上書きします。

使い方（プロジェクト直下で）:
    pip install pillow
    python tools/optimize_sprites.py          # 新しい/更新された PNG だけ変換
    python tools/optimize_sprites.py --force  # 全部作り直す

透明余白はトリミングしません（描画位置・当たり判定の見た目を変えないため）。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "public" / "sprites"

# 長辺の上限(px)。画面上の最大表示サイズ × Retina(2〜3倍) を目安にしています。
MAX_SIDE = {
    "player": 320,      # 表示 約78px
    "enemies": 256,     # 表示 約61px
    "bosses": 512,      # 表示 約110〜205px
    "sunflower": 768,   # 最終ボスは 約300px で表示
}
QUALITY = 86


def limit_for(path: Path) -> int:
    if "sunflower" in path.name:
        return MAX_SIDE["sunflower"]
    if path.parent.name in MAX_SIDE:
        return MAX_SIDE[path.parent.name]
    return MAX_SIDE["player"]


def convert(src: Path, force: bool) -> tuple[int, int] | None:
    dst = src.with_suffix(".webp")
    if not force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return None
    with Image.open(src) as im:
        im = im.convert("RGBA")
        limit = limit_for(src)
        scale = min(1.0, limit / max(im.size))
        if scale < 1.0:
            size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
            im = im.resize(size, Image.LANCZOS)
        im.save(dst, "WEBP", quality=QUALITY, method=6, alpha_quality=90)
    return src.stat().st_size, dst.stat().st_size


def shrink_webp(path: Path) -> tuple[int, int] | None:
    """PNG の無い WebP を、上限より大きいときだけ縮小して上書きする。"""
    before = path.stat().st_size
    with Image.open(path) as im:
        limit = limit_for(path)
        if max(im.size) <= limit:
            return None
        im = im.convert("RGBA")
        scale = limit / max(im.size)
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    im.save(path, "WEBP", quality=QUALITY, method=6, alpha_quality=90)
    return before, path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="既存の WebP も作り直す")
    args = parser.parse_args()

    before = after = 0
    for src in sorted(ROOT.rglob("*.png")):
        result = convert(src, args.force)
        if result:
            before += result[0]
            after += result[1]
            print(f"{src.relative_to(ROOT)}: {result[0] // 1024}KB -> {result[1] // 1024}KB")
    for webp in sorted(ROOT.rglob("*.webp")):
        if webp.with_suffix(".png").exists():
            continue
        result = shrink_webp(webp)
        if result:
            before += result[0]
            after += result[1]
            print(f"{webp.relative_to(ROOT)}: {result[0] // 1024}KB -> {result[1] // 1024}KB (縮小)")
    if before:
        print(f"合計 {before / 1048576:.1f}MB -> {after / 1048576:.2f}MB")
    else:
        print("変換が必要な PNG はありませんでした。")


if __name__ == "__main__":
    main()
