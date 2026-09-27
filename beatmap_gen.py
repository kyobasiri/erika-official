from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import os
import tempfile

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import librosa
import numpy as np
import yt_dlp


# ============================================================
# 設定
# ============================================================

MASTER_JSON_PATH = Path("public/assets/thepillows_releases_tab.json")
OUTPUT_DIR = Path("public/assets/beatmaps")

GENERATOR_VERSION = "erika-musical-v3"

SAMPLE_RATE = 22050
HOP_LENGTH = 256
N_FFT = 2048

# TrueにするとHardの強いアクセントに同時押しを追加。
# 最初はFalseで譜面の感触を確認することを推奨。
ENABLE_HARD_DOUBLES = False

# 近いグリッドへの吸着許容幅。
# 同じオンセットを複数ノーツには使わない。
MAX_SNAP_SECONDS = 0.055

DIFFICULTIES = ("veryeasy", "easy", "normal", "hard")

CONFIG = {
    "veryeasy": {
        "min_gap_ms": 650,
        "hand_gap_ms": 650,
        "phrase_limit": 4,
        "max_nps": 2,
    },
    "easy": {
        "min_gap_ms": 300,
        "hand_gap_ms": 350,
        "phrase_limit": 8,
        "max_nps": 4,
    },
    "normal": {
        "min_gap_ms": 160,
        "hand_gap_ms": 220,
        "phrase_limit": 14,
        "max_nps": 6,
    },
    "hard": {
        "min_gap_ms": 90,
        "hand_gap_ms": 170,
        "phrase_limit": 24,
        "max_nps": 9,
    },
}

# 4拍＝16スロットとして、Normalで使用するリズム型。
# 0,4,8,12が四分音符、2,6,10,14が裏拍。
NORMAL_PATTERNS = (
    frozenset((0, 4, 6, 8, 12, 14)),
    frozenset((0, 2, 4, 8, 10, 12)),
    frozenset((0, 4, 8, 10, 12, 14)),
    frozenset((0, 2, 4, 6, 8, 12)),
)

LANE_PATTERNS = (
    (0, 1, 0, 1),
    (0, 0, 1, 1),
    (0, 1, 1, 0),
    (1, 0, 0, 1),
)


@dataclass(frozen=True)
class Candidate:
    time_ms: int
    beat: int
    subdivision: int
    phrase: int
    strength: float
    energy: float

    @property
    def slot(self) -> int:
        return (self.beat % 4) * 4 + self.subdivision


def stable_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def extract_video_id(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        parts = [part for part in parsed.path.split("/") if part]

        video_id = None

        if host == "youtu.be" and parts:
            video_id = parts[0]

        elif host in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtube-nocookie.com",
            "www.youtube-nocookie.com",
        }:
            video_id = parse_qs(parsed.query).get("v", [None])[0]

            if not video_id and len(parts) >= 2:
                if parts[0] in {"embed", "shorts", "live"}:
                    video_id = parts[1]

        if (
            isinstance(video_id, str)
            and len(video_id) == 11
            and all(
                character.isascii()
                and (character.isalnum() or character in "_-")
                for character in video_id
            )
        ):
            return video_id

    except (TypeError, ValueError):
        pass

    return None


def atomic_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                data,
                handle,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )

        os.replace(temporary_path, path)

    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def normalize_envelope(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    positive = values[values > 0]

    if not positive.size:
        return np.zeros_like(values)

    scale = float(np.percentile(positive, 90))
    return np.clip(values / max(scale, 1e-9), 0.0, 2.0)


def analysis_options(song: dict) -> dict:
    start = float(song.get("start_time", 0.0) or 0.0)
    raw_end = song.get("end_time")
    end = None if raw_end is None else float(raw_end)
    raw_bpm = song.get("bpm")
    bpm = None if raw_bpm is None else float(raw_bpm)
    offset_ms = float(song.get("offset_ms", 0.0) or 0.0)

    if not math.isfinite(start) or start < 0:
        raise ValueError("start_timeが不正です。")

    if end is not None and (
        not math.isfinite(end) or end <= start
    ):
        raise ValueError("end_timeはstart_timeより後にしてください。")

    if bpm is not None and (
        not math.isfinite(bpm) or not 30 <= bpm <= 300
    ):
        raise ValueError("bpmは30～300の範囲で指定してください。")

    if not math.isfinite(offset_ms) or abs(offset_ms) > 5000:
        raise ValueError("offset_msは-5000～5000の範囲で指定してください。")

    return {
        "start_time": start,
        "end_time": end,
        "bpm": bpm,
        "offset_ms": offset_ms,
    }


def generation_signature(song: dict, options: dict) -> str:
    specification = {
        "version": GENERATOR_VERSION,
        "options": options,
        "config": CONFIG,
        "hard_doubles": ENABLE_HARD_DOUBLES,
        "sample_rate": SAMPLE_RATE,
        "hop_length": HOP_LENGTH,
        "snap_seconds": MAX_SNAP_SECONDS,
        "audio_path": song.get("audio_path"),
    }

    local_path = song.get("audio_path")
    if local_path and Path(local_path).is_file():
        stat = Path(local_path).stat()
        specification["audio_size"] = stat.st_size
        specification["audio_mtime_ns"] = stat.st_mtime_ns

    serialized = json.dumps(
        specification,
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def analyze_audio(audio_path: Path, options: dict):
    start = options["start_time"]
    end = options["end_time"]
    duration = None if end is None else end - start

    y, sr = librosa.load(
        str(audio_path),
        sr=SAMPLE_RATE,
        mono=True,
        offset=start,
        duration=duration,
    )

    if len(y) < sr:
        raise ValueError("解析対象の音声が1秒未満です。")

    if not np.all(np.isfinite(y)):
        raise ValueError("音声に不正な数値が含まれています。")

    if float(np.max(np.abs(y))) < 1e-6:
        raise ValueError("解析対象の音声が無音です。")

    audio_duration = len(y) / sr

    # 全帯域と低域の立ち上がりを組み合わせる。
    # メロディだけでなく、キック・ベースのアクセントも拾う。
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=64,
        power=2.0,
    )

    mel_db = librosa.power_to_db(mel, ref=np.max)

    full_onset = librosa.onset.onset_strength(
        S=mel_db,
        sr=sr,
        hop_length=HOP_LENGTH,
    )

    bass_onset = librosa.onset.onset_strength(
        S=mel_db[:16],
        sr=sr,
        hop_length=HOP_LENGTH,
    )

    onset_env = (
        normalize_envelope(full_onset) * 0.75
        + normalize_envelope(bass_onset) * 0.25
    )

    if float(np.max(onset_env)) <= 1e-8:
        raise ValueError("音の立ち上がりを検出できませんでした。")

    beat_arguments = {
        "onset_envelope": onset_env,
        "sr": sr,
        "hop_length": HOP_LENGTH,
        "trim": False,
        "start_bpm": 120.0,
    }

    if options["bpm"] is not None:
        beat_arguments["bpm"] = options["bpm"]

    _, beat_frames = librosa.beat.beat_track(**beat_arguments)

    beat_times = librosa.frames_to_time(
        beat_frames,
        sr=sr,
        hop_length=HOP_LENGTH,
    )

    beat_times = np.unique(
        beat_times[
            (beat_times >= 0)
            & (beat_times < audio_duration)
        ]
    )

    if len(beat_times) < 4:
        raise ValueError(
            "拍を十分に検出できませんでした。"
            "曲マスタにbpmを指定して再試行してください。"
        )

    median_interval = float(np.median(np.diff(beat_times)))
    estimated_bpm = 60.0 / median_interval

    # 最後の検出拍も処理できるよう、終端の境界だけ追加する。
    final_boundary = min(
        audio_duration,
        float(beat_times[-1] + median_interval),
    )
    boundaries = np.append(beat_times, final_boundary)

    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=HOP_LENGTH,
        backtrack=False,
        units="frames",
        normalize=True,
    )

    if len(onset_frames) == 0:
        raise ValueError("配置に使えるオンセットがありません。")

    onset_times = librosa.frames_to_time(
        onset_frames,
        sr=sr,
        hop_length=HOP_LENGTH,
    )

    rms = librosa.feature.rms(
        y=y,
        frame_length=N_FFT,
        hop_length=HOP_LENGTH,
    )[0]

    rms_reference = max(float(np.percentile(rms, 90)), 1e-9)

    # 検出した拍に追従するグリッドを作る。
    # 曲全体を固定BPMで機械的に分割しない。
    grid = []

    for beat_index in range(len(boundaries) - 1):
        beat_start = float(boundaries[beat_index])
        beat_end = float(boundaries[beat_index + 1])
        interval = beat_end - beat_start

        if interval < 0.15:
            continue

        for subdivision in range(4):
            time = beat_start + interval * subdivision / 4.0

            grid.append({
                "time": time,
                "beat": beat_index,
                "subdivision": subdivision,
                "phrase": beat_index // 8,
                "step": interval / 4.0,
            })

    if not grid:
        raise ValueError("拍グリッドを作成できませんでした。")

    grid_times = np.array([item["time"] for item in grid])

    # 1つのオンセットは、最も近いグリッド1か所にだけ対応させる。
    matched = {}
    matched_count = 0

    for frame, onset_time in zip(onset_frames, onset_times):
        position = int(np.searchsorted(grid_times, onset_time))
        possible = [
            index for index in (position - 1, position)
            if 0 <= index < len(grid)
        ]

        nearest = min(
            possible,
            key=lambda index: abs(grid[index]["time"] - onset_time),
        )

        item = grid[nearest]
        distance = abs(item["time"] - float(onset_time))

        tolerance = min(
            MAX_SNAP_SECONDS,
            item["step"] * 0.45,
        )

        if distance > tolerance:
            continue

        energy = float(
            rms[min(int(frame), len(rms) - 1)] / rms_reference
        )

        # 無音・極端に小さい音には配置しない。
        if energy < 0.035:
            continue

        raw_strength = float(onset_env[int(frame)])
        previous = matched.get(nearest)

        if previous is None or raw_strength > previous["raw_strength"]:
            matched[nearest] = {
                "raw_strength": raw_strength,
                "energy": min(1.5, energy),
            }

        matched_count += 1

    if not matched:
        raise ValueError(
            "拍に合う音を検出できませんでした。"
            "bpm指定や解析区間を確認してください。"
        )

    global_scale = max(
        float(np.percentile(
            [item["raw_strength"] for item in matched.values()],
            85,
        )),
        1e-9,
    )

    phrase_strengths = defaultdict(list)
    for index, item in matched.items():
        phrase_strengths[grid[index]["phrase"]].append(
            item["raw_strength"]
        )

    phrase_scales = {
        phrase: max(float(np.percentile(values, 80)), 1e-9)
        for phrase, values in phrase_strengths.items()
    }

    candidates = []

    for index, match in matched.items():
        item = grid[index]
        phrase = item["phrase"]

        # 曲全体と8拍区間内の両方で強さを評価する。
        strength = (
            0.65 * match["raw_strength"] / global_scale
            + 0.35 * match["raw_strength"] / phrase_scales[phrase]
        )

        absolute_ms = round(
            (item["time"] + start) * 1000
            + options["offset_ms"]
        )

        if absolute_ms < 0:
            continue

        if absolute_ms > round((start + audio_duration) * 1000):
            continue

        candidates.append(Candidate(
            time_ms=int(absolute_ms),
            beat=int(item["beat"]),
            subdivision=int(item["subdivision"]),
            phrase=int(phrase),
            strength=float(min(1.5, strength)),
            energy=float(match["energy"]),
        ))

    candidates.sort(key=lambda candidate: candidate.time_ms)

    match_ratio = matched_count / len(onset_frames)

    warnings = []
    if match_ratio < 0.35:
        warnings.append(
            "拍グリッドと音の一致率が低めです。"
            "スウィング・変拍子・テンポ推定違いの可能性があります。"
        )

    metadata = {
        "estimated_bpm": round(estimated_bpm, 3),
        "analysis_start_ms": round(start * 1000),
        "analysis_end_ms": round((start + audio_duration) * 1000),
        "analysis_duration_ms": round(audio_duration * 1000),
        "onset_grid_match_ratio": round(match_ratio, 4),
        "offset_ms": options["offset_ms"],
        "warnings": warnings,
    }

    return candidates, metadata


def preferred_half_beat_phase(candidates: list[Candidate]) -> int:
    # Very Easyで、検出拍の偶数側・奇数側のうち
    # 強い音が多い方を採用する。小節頭の推定ではない。
    scores = [0.0, 0.0]

    for candidate in candidates:
        if candidate.subdivision == 0:
            scores[candidate.beat % 2] += candidate.strength

    return 0 if scores[0] >= scores[1] else 1


def candidate_allowed(
    candidate: Candidate,
    difficulty: str,
    seed: int,
    half_phase: int,
) -> bool:
    strength = candidate.strength
    subdivision = candidate.subdivision

    if difficulty == "veryeasy":
        return (
            subdivision == 0
            and candidate.beat % 2 == half_phase
            and strength >= 0.22
        )

    if difficulty == "easy":
        return subdivision == 0 and strength >= 0.18

    if difficulty == "normal":
        pattern = NORMAL_PATTERNS[
            (seed + candidate.phrase // 2) % len(NORMAL_PATTERNS)
        ]

        if subdivision == 0:
            return strength >= 0.16

        return (
            subdivision == 2
            and candidate.slot in pattern
            and strength >= 0.50
        )

    if subdivision == 0:
        return strength >= 0.14

    if subdivision == 2:
        return strength >= 0.35

    # 十六分は、8拍区間の最後の2拍か、
    # 音量とアクセントの両方が強い場所に限定する。
    is_fill = candidate.beat % 8 >= 6
    is_strong = candidate.energy >= 0.70 and strength >= 0.90

    return (
        strength >= 0.62
        and (is_fill or is_strong)
    )


def violates_density(
    times: list[int],
    proposed_time: int,
    maximum: int,
) -> bool:
    left = bisect.bisect_left(times, proposed_time - 1000)
    right = bisect.bisect_right(times, proposed_time + 1000)

    local = times[left:right]
    bisect.insort(local, proposed_time)

    start = 0
    for end, value in enumerate(local):
        # 半開区間で1秒の密度を数える。
        while value - local[start] >= 1000:
            start += 1

        if end - start + 1 > maximum:
            return True

    return False


def can_insert_time(
    times: list[int],
    time_ms: int,
    min_gap_ms: int,
) -> bool:
    index = bisect.bisect_left(times, time_ms)

    if index > 0 and time_ms - times[index - 1] < min_gap_ms:
        return False

    if index < len(times) and times[index] - time_ms < min_gap_ms:
        return False

    return True


def select_candidates(
    candidates: list[Candidate],
    difficulty: str,
    inherited: list[dict],
    seed: int,
    half_phase: int,
) -> list[Candidate]:
    config = CONFIG[difficulty]
    candidate_by_time = {
        candidate.time_ms: candidate for candidate in candidates
    }

    # 下位難易度の配置時刻を保持する。
    selected = {
        note["time"]: candidate_by_time[note["time"]]
        for note in inherited
    }

    times = sorted(selected)
    phrase_counts = defaultdict(int)

    for candidate in selected.values():
        phrase_counts[candidate.phrase] += 1

    eligible = [
        candidate for candidate in candidates
        if candidate.time_ms not in selected
        and candidate_allowed(candidate, difficulty, seed, half_phase)
    ]

    # 拍の柱と強いアクセントを優先して、空いた場所を埋める。
    def priority(candidate):
        beat_bonus = (
            0.45 if candidate.subdivision == 0
            else 0.15 if candidate.subdivision == 2
            else 0.0
        )
        return (
            -(candidate.strength + beat_bonus),
            candidate.time_ms,
        )

    for candidate in sorted(eligible, key=priority):
        if phrase_counts[candidate.phrase] >= config["phrase_limit"]:
            continue

        if not can_insert_time(
            times,
            candidate.time_ms,
            config["min_gap_ms"],
        ):
            continue

        if violates_density(
            times,
            candidate.time_ms,
            config["max_nps"],
        ):
            continue

        selected[candidate.time_ms] = candidate
        bisect.insort(times, candidate.time_ms)
        phrase_counts[candidate.phrase] += 1

    return [selected[time] for time in sorted(selected)]


def assign_lanes(
    selected: list[Candidate],
    inherited: list[dict],
    difficulty: str,
    seed: int,
) -> list[dict]:
    config = CONFIG[difficulty]

    # 下位難易度のノーツはレーンも引き継ぐ。
    result = [
        {"time": int(note["time"]), "lane": int(note["lane"])}
        for note in inherited
    ]

    inherited_times = {note["time"] for note in inherited}

    lane_times = [
        sorted(note["time"] for note in inherited if note["lane"] == lane)
        for lane in (0, 1)
    ]

    previous_lane = 1
    previous_time = -10**12
    phrase_positions = defaultdict(int)

    inherited_by_time = {
        note["time"]: note["lane"] for note in inherited
    }

    for candidate in selected:
        time_ms = candidate.time_ms

        if time_ms in inherited_times:
            previous_lane = inherited_by_time[time_ms]
            previous_time = time_ms
            phrase_positions[candidate.phrase] += 1
            continue

        position = phrase_positions[candidate.phrase]

        if difficulty in {"veryeasy", "easy"}:
            preferred_lane = 1 - previous_lane

        elif time_ms - previous_time < 240:
            # 細かい連打は交互を優先する。
            preferred_lane = 1 - previous_lane

        else:
            pattern = LANE_PATTERNS[
                (seed + candidate.phrase // 2) % len(LANE_PATTERNS)
            ]
            preferred_lane = pattern[position % len(pattern)]

        assigned_lane = None

        for lane in (preferred_lane, 1 - preferred_lane):
            if can_insert_time(
                lane_times[lane],
                time_ms,
                config["hand_gap_ms"],
            ):
                assigned_lane = lane
                break

        if assigned_lane is None:
            continue

        result.append({
            "time": int(time_ms),
            "lane": int(assigned_lane),
        })

        bisect.insort(lane_times[assigned_lane], time_ms)
        previous_lane = assigned_lane
        previous_time = time_ms
        phrase_positions[candidate.phrase] += 1

    result.sort(key=lambda note: (note["time"], note["lane"]))
    return result


def add_hard_doubles(
    notes: list[dict],
    candidates: list[Candidate],
) -> list[dict]:
    if not ENABLE_HARD_DOUBLES:
        return notes

    result = [dict(note) for note in notes]
    candidate_by_time = {
        candidate.time_ms: candidate for candidate in candidates
    }
    lane_times = [
        sorted(note["time"] for note in notes if note["lane"] == lane)
        for lane in (0, 1)
    ]
    all_times = sorted(note["time"] for note in notes)
    used_phrases = set()
    previous_double = -10**12

    for note in notes:
        candidate = candidate_by_time[note["time"]]
        time_ms = note["time"]

        if (
            candidate.subdivision != 0
            or candidate.strength < 1.0
            or candidate.energy < 0.65
            or candidate.phrase in used_phrases
            or time_ms - previous_double < 2500
        ):
            continue

        # 前後が詰まっている位置には同時押しを置かない。
        index = bisect.bisect_left(all_times, time_ms)

        if index > 0 and time_ms - all_times[index - 1] < 230:
            continue

        if (
            index + 1 < len(all_times)
            and all_times[index + 1] - time_ms < 230
        ):
            continue

        other_lane = 1 - note["lane"]

        if not can_insert_time(lane_times[other_lane], time_ms, 250):
            continue

        if violates_density(all_times, time_ms, CONFIG["hard"]["max_nps"]):
            continue

        result.append({"time": time_ms, "lane": other_lane})
        bisect.insort(lane_times[other_lane], time_ms)
        bisect.insort(all_times, time_ms)
        used_phrases.add(candidate.phrase)
        previous_double = time_ms

    return sorted(result, key=lambda note: (note["time"], note["lane"]))


def chart_statistics(notes: list[dict], duration_ms: int) -> dict:
    times = sorted(note["time"] for note in notes)
    peak_nps = 0
    start = 0

    for end, time_ms in enumerate(times):
        while time_ms - times[start] >= 1000:
            start += 1
        peak_nps = max(peak_nps, end - start + 1)

    lane_gaps = []

    for lane in (0, 1):
        lane_times = [
            note["time"] for note in notes if note["lane"] == lane
        ]
        lane_gaps.extend(
            second - first
            for first, second in zip(lane_times, lane_times[1:])
        )

    return {
        "note_count": len(notes),
        "average_nps": round(
            len(notes) / max(duration_ms / 1000.0, 1.0),
            3,
        ),
        "peak_nps": peak_nps,
        "min_same_lane_gap_ms": min(lane_gaps) if lane_gaps else None,
        "double_count": len(times) - len(set(times)),
    }


def generate_advanced_beatmap(
    audio_path: Path,
    options: dict,
    song_id: str,
):
    candidates, metadata = analyze_audio(audio_path, options)
    seed = stable_seed(song_id)
    half_phase = preferred_half_beat_phase(candidates)

    beatmaps = {}
    inherited = []

    for difficulty in DIFFICULTIES:
        selected = select_candidates(
            candidates,
            difficulty,
            inherited,
            seed,
            half_phase,
        )

        # 拍の位相によってVery Easyが空になった場合だけ反対側を試す。
        if difficulty == "veryeasy" and not selected:
            selected = select_candidates(
                candidates,
                difficulty,
                inherited,
                seed,
                1 - half_phase,
            )

        if not selected:
            raise ValueError(
                f"{difficulty}に配置可能な音がありません。"
                "bpmまたは解析区間を調整してください。"
            )

        chart = assign_lanes(
            selected,
            inherited,
            difficulty,
            seed,
        )

        if difficulty == "hard":
            chart = add_hard_doubles(chart, candidates)

        beatmaps[difficulty] = chart
        inherited = chart

    metadata["statistics"] = {
        difficulty: chart_statistics(
            chart,
            metadata["analysis_duration_ms"],
        )
        for difficulty, chart in beatmaps.items()
    }

    return beatmaps, metadata


def is_current_chart(path: Path, signature: str) -> bool:
    if not path.is_file():
        return False

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        difficulties = data.get("difficulties", {})

        return (
            data.get("generator_version") == GENERATOR_VERSION
            and data.get("generator_signature") == signature
            and all(
                isinstance(difficulties.get(difficulty), list)
                and len(difficulties[difficulty]) > 0
                for difficulty in DIFFICULTIES
            )
        )

    except (OSError, ValueError, TypeError, AttributeError):
        return False


def download_audio(url: str, directory: Path) -> Path:
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(directory / "audio.%(ext)s"),
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        "quiet": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        result = downloader.download([url])

    path = directory / "audio.wav"

    if result != 0 or not path.is_file():
        raise RuntimeError("音声を取得・変換できませんでした。")

    return path


def rebuild_index(output_dir: Path) -> None:
    songs = []

    for path in sorted(output_dir.glob("beatmap_*.json")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            charts = data.get("difficulties", {})
            available = {
                difficulty: len(charts[difficulty])
                for difficulty in DIFFICULTIES
                if isinstance(charts.get(difficulty), list)
                and charts[difficulty]
            }

            if not available or not isinstance(data.get("id"), str):
                continue

            songs.append({
                "id": data["id"],
                "title": data.get("title", data["id"]),
                "file": path.name,
                "difficulties": available,
                "generator_version": data.get("generator_version"),
                "statistics": data.get("analysis", {}).get("statistics", {}),
            })

        except (OSError, ValueError, TypeError, AttributeError):
            continue

    atomic_write_json(output_dir / "index.json", {
        "version": 1,
        "songs": songs,
    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ERIKA BEAT用の4難易度譜面を生成します。"
    )
    parser.add_argument("--master", type=Path, default=MASTER_JSON_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--id",
        action="append",
        dest="ids",
        help="対象動画ID。複数回指定できます。",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    with args.master.open("r", encoding="utf-8-sig") as handle:
        songs = json.load(handle)

    if not isinstance(songs, list):
        raise ValueError("曲マスタは配列形式にしてください。")

    requested = set(args.ids or [])
    seen = set()
    generated = 0
    failed = 0
    skipped = 0
    attempted = 0

    for song in songs:
        if not isinstance(song, dict):
            continue

        video_id = (
            extract_video_id(song.get("share_url", ""))
            or extract_video_id(song.get("embed_url", ""))
        )

        if not video_id or video_id in seen:
            continue

        seen.add(video_id)

        if requested and video_id not in requested:
            continue

        title = str(song.get("title", video_id))
        output_file = args.output / f"beatmap_{video_id}.json"

        try:
            options = analysis_options(song)
            signature = generation_signature(song, options)

            if not args.force and is_current_chart(output_file, signature):
                print(f"[スキップ] {title}")
                skipped += 1
                continue

            if args.limit > 0 and attempted >= args.limit:
                break

            attempted += 1
            print(f"\n[生成] {title} / {video_id}")

            # audio_pathがあればローカル音声を使用する。
            # 動画と同じ先頭位置の音声を指定すること。
            local_audio = song.get("audio_path")

            with tempfile.TemporaryDirectory(prefix="erika_beat_") as temp:
                if local_audio:
                    audio_path = Path(local_audio)
                    if not audio_path.is_file():
                        raise FileNotFoundError(audio_path)
                else:
                    audio_path = download_audio(
                        f"https://www.youtube.com/watch?v={video_id}",
                        Path(temp),
                    )

                charts, metadata = generate_advanced_beatmap(
                    audio_path,
                    options,
                    video_id,
                )

            output_data = {
                "id": video_id,
                "title": title,
                "generator_version": GENERATOR_VERSION,
                "generator_signature": signature,
                "analysis": metadata,
                "difficulties": charts,
            }

            # 生成完了後に置き換える。失敗時は既存譜面を残す。
            atomic_write_json(output_file, output_data)
            generated += 1

            print(
                f"  推定BPM: {metadata['estimated_bpm']} / "
                f"グリッド一致率: "
                f"{metadata['onset_grid_match_ratio'] * 100:.1f}%"
            )

            for difficulty in DIFFICULTIES:
                stats = metadata["statistics"][difficulty]
                print(
                    f"  {difficulty:8s}: "
                    f"{stats['note_count']:5d} notes / "
                    f"最大 {stats['peak_nps']} notes/sec / "
                    f"同一レーン最短 "
                    f"{stats['min_same_lane_gap_ms']} ms"
                )

            for warning in metadata["warnings"]:
                print(f"  [確認] {warning}")

        except KeyboardInterrupt:
            print("\n中断しました。完成済みの譜面は保存されています。")
            break

        except Exception as error:
            failed += 1
            print(f"  [エラー] {title}: {error}")

    rebuild_index(args.output)

    print(
        f"\n完了: 生成 {generated} / "
        f"スキップ {skipped} / エラー {failed}"
    )
    print(f"譜面一覧: {args.output / 'index.json'}")


if __name__ == "__main__":
    main()