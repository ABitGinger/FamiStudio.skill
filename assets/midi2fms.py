#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""midi2fms.py — MIDI → FamiStudio 文本工程转换器

用法:
    python midi2fms.py 输入.mid 输出.txt

自动把 MIDI 声道分配到 2A03+VRC6+S5B+N163 声道池（共 19 个旋律声道 + 噪声鼓组），
乐器自动带正确的 Expansion 属性（扩展声道乐器不带 Expansion 会整声道静音）。
时间按 tempo map 逐段积分换算成帧（60.0988fps），自由速度/渐慢精确保留；
Time/Duration 不量化，长音符直接跨 Pattern 边界。

映射不满意 → 改 MANUAL_MAP 后重跑。方法与陷阱见 references/midi-import.md。
"""
import argparse
import math
import sys
from collections import defaultdict

try:
    import mido
except ImportError:
    sys.exit("需要 mido：pip install mido")

FPS = 60.0988
NOTE_LENGTH = 9       # Song NoteLength/Groove：每槽帧数
BEAT_LENGTH = 3       # Song BeatLength：每拍槽数
PATTERN_LENGTH = 12   # Song PatternLength：每 Pattern 槽数
PAT_FRAMES = NOTE_LENGTH * PATTERN_LENGTH
MAX_PITCH = 108       # C8 上限，超出降八度

# 手动映射覆盖（优先于自动分配）：
# MANUAL_MAP = {3: {"pool": ["N163Wave1", "N163Wave2"], "kind": "pluck", "transpose": 0}}
#   pool  = 该 MIDI 声道用的 FamiStudio 声道（复音>1 就给多个）
#   kind  = "const"（满音量直出）/ "sustain"（衰减后持续）/ "pluck"（拨弦衰减）
#   transpose = 半音偏移（可负）
MANUAL_MAP = {}

# 声道 → (默认乐器 kind, 音域下限：低于则升八度)
CHANNEL_KIND = {
    "Square1":     ("const",   27), "Square2":   ("const",   27),
    "Triangle":    ("const",   36),
    "VRC6Square1": ("const",   27), "VRC6Square2": ("sustain", 27),
    "VRC6Saw":     ("pluck",   36),
    "S5BSquare1":  ("sustain", 27), "S5BSquare2": ("sustain", 27), "S5BSquare3": ("sustain", 27),
    **{f"N163Wave{i}": ("sustain", 40) for i in range(1, 9)},
}
# 自动分配可用的普通声道池（Square1/Triangle/VRC6Square1/VRC6Saw 留给主旋律与贝斯）
POOL_INVENTORY = [f"N163Wave{i}" for i in range(1, 9)] + \
                 ["S5BSquare1", "S5BSquare2", "S5BSquare3", "VRC6Square2", "Square2"]

# GM 鼓组 → (乐器名, Noise Value, 衰减包络)
DRUMS = [
    ({35, 36}, "DrumKick",  "D#3", [15, 11, 7, 3, 1, 0]),
    ({38, 40}, "DrumSnare", "G#3", [15, 7, 3, 2, 1, 0]),
    ({42, 44}, "DrumHat",   "G#3", [9, 4, 1, 0]),
    ({41, 43, 45, 47, 48}, "DrumTom", "G#3", [14, 8, 5, 3, 1, 0]),
    ({49, 57}, "DrumCrash", "G#3", [14, 12, 10, 8, 7, 6, 5, 4, 3, 3, 2, 2, 1, 1, 1, 0]),
]

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def nname(p):
    return f"{NAMES[p % 12]}{p // 12 - 1}"


def expansion_of(ch):
    if ch.startswith("VRC6"):
        return "VRC6"
    if ch.startswith("S5B"):
        return "S5B"
    if ch.startswith("N163Wave"):
        return "N163"
    return None


def parse_midi(path):
    """返回 (notes, tick_to_frame, tpq)；多轨按绝对 tick 合并。"""
    m = mido.MidiFile(path)
    tpq = m.ticks_per_beat
    events = []          # (abs_tick, seq, msg)
    for seq, track in enumerate(m.tracks):
        t = 0
        for msg in track:
            t += msg.time
            events.append((t, seq, msg))
    events.sort(key=lambda e: (e[0], e[1]))

    tempo_ev, on, notes = [], {}, defaultdict(list)
    for t, _, msg in events:
        if msg.type == "set_tempo":
            tempo_ev.append((t, msg.tempo))
        elif msg.type == "note_on" and msg.velocity > 0:
            on.setdefault(msg.channel, []).append([t, msg.note])
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            lst = on.get(msg.channel, [])
            for i, (st, n) in enumerate(lst):
                if n == msg.note:
                    notes[msg.channel].append((st, t, n)); lst.pop(i)
                    break
    for c, lst in on.items():
        for st, n in lst:
            notes[c].append((st, t + tpq, n))
    if not tempo_ev or tempo_ev[0][0] != 0:
        tempo_ev.insert(0, (0, 500000))

    def tick_to_frame(tick):
        sec, prev_tick, prev_tempo = 0.0, 0, tempo_ev[0][1]
        for tt, tm in tempo_ev:
            if tick <= tt:
                return (sec + (tick - prev_tick) * prev_tempo / 1e6 / tpq) * FPS
            sec += (tt - prev_tick) * prev_tempo / 1e6 / tpq
            prev_tick, prev_tempo = tt, tm
        return sec * FPS

    return notes, tick_to_frame, tpq


def channel_stats(recs):
    evs = sorted([(st, 1) for st, _, _ in recs] + [(en, -1) for _, en, _ in recs])
    cur = mx = 0
    for _, v in evs:
        cur += v; mx = max(mx, cur)
    pitches = [n for _, _, n in recs]
    return {"count": len(recs), "poly": mx,
            "avg_pitch": sum(pitches) / len(pitches), "max_pitch": max(pitches)}


def auto_assign(notes):
    """返回 ({midi_ch: {"pool": [...], "kind": str}}, drums_channels)"""
    drum_chs = [c for c in notes if c == 9 and notes[c]]
    melodic = [c for c in notes if c not in drum_chs and notes[c]]
    stats = {c: channel_stats(notes[c]) for c in melodic}
    assign, free = {}, set(POOL_INVENTORY)

    def take(ch):
        free.discard(ch)
        return ch

    # 主旋律 = 音量最大的 3 个声道里平均音高最高者；贝斯 = 其余里平均音高最低者
    # 注意 MIDI 声道从 0 开始，判断必须用 is not None（0 是合法声道号）
    by_count = sorted(melodic, key=lambda c: -stats[c]["count"])
    lead = max(by_count[:3], key=lambda c: stats[c]["avg_pitch"]) if by_count else None
    rest = [c for c in melodic if c != lead]
    bass = min(rest, key=lambda c: stats[c]["avg_pitch"]) if rest else None
    if lead is not None:
        pool = ["Square1"] + (["VRC6Square1"] if stats[lead]["poly"] > 1 else [])
        assign[lead] = {"pool": [take(x) for x in pool], "kind": "const"}
    if bass is not None:
        pool = ["Triangle"] + (["VRC6Saw"] if stats[bass]["poly"] > 1 else [])
        assign[bass] = {"pool": [take(x) for x in pool], "kind": "const"}
    # 其余：第一轮每人 1 个（按音符数优先），第二轮按 音符数×声部缺口 贪心补足
    # （缺口 = min(复音, 4) − 现有声部；保证最密的声部先拿到富余声道）
    order = sorted((c for c in rest if c != bass), key=lambda c: -stats[c]["count"])
    for c in order:
        assign[c] = {"pool": [take(sorted(free)[0])], "kind": None}
    while free:
        c = max(order, key=lambda c: stats[c]["count"] *
                (min(stats[c]["poly"], 4) - len(assign[c]["pool"])))
        if min(stats[c]["poly"], 4) - len(assign[c]["pool"]) <= 0:
            break
        assign[c]["pool"].append(take(sorted(free)[0]))
    for c, cfg in MANUAL_MAP.items():   # 手动覆盖最后生效
        for ch in cfg.get("pool", []):
            free.discard(ch)
        assign[c] = cfg
    return assign, drum_chs


def kind_of(ch, assign):
    for cfg in assign.values():
        if ch in cfg["pool"]:
            return cfg.get("kind") or CHANNEL_KIND[ch][0]
    return CHANNEL_KIND[ch][0]


def instrument_head(ch):
    exp = expansion_of(ch)
    head = f'\tInstrument Name="V_{ch}" Color="4dd0e1"'
    if exp:
        head += f' Expansion="{exp}"'
    if exp == "N163":
        head += ' N163WavePreset="Custom" N163WaveSize="16" N163WavePos="0" N163WaveCount="1"'
    return head


def instrument_body(ch, kind):
    lines = []
    if kind == "sustain":
        lines.append('\t\tEnvelope Type="Volume" Length="9" Loop="8" Values="15,12,11,10,10,10,9,9,9"')
    elif kind == "pluck":
        lines.append('\t\tEnvelope Type="Volume" Length="11" Loop="10" Values="15,9,6,4,3,2,2,2,1,1,1"')
    if ch.startswith(("Square", "VRC6Square")):
        lines.append(f'\t\tEnvelope Type="DutyCycle" Length="1" Values="{2 if ch.endswith("1") else 3}"')
    if ch.startswith("N163Wave"):
        lines.append('\t\tEnvelope Type="N163Wave" Length="16" Loop="0" Values="' +
                     ",".join(["15"] * 8 + ["0"] * 8) + '"')
        lines.append('\t\tEnvelope Type="Repeat" Length="1" Loop="0" Values="1"')
    return lines


def drum_of(pitch):
    for pitches, name, val, env in DRUMS:
        if pitch in pitches:
            return name, val, env
    return "DrumHat", "G#3", [9, 4, 1, 0]


def main():
    ap = argparse.ArgumentParser(description="MIDI → FamiStudio 文本工程")
    ap.add_argument("midi")
    ap.add_argument("out")
    args = ap.parse_args()

    notes, t2f, tpq = parse_midi(args.midi)
    if not notes:
        sys.exit("MIDI 里没有音符")
    end_frame = max(t2f(en) for lst in notes.values() for _, en, _ in lst)
    num_pats = max(1, math.ceil((end_frame + NOTE_LENGTH * BEAT_LENGTH) / PAT_FRAMES))

    assign, drum_chs = auto_assign(notes)
    used = sorted({ch for cfg in assign.values() for ch in cfg["pool"]})
    kinds = {ch: kind_of(ch, assign) for ch in used}
    n163_n = max([int(ch[8:]) for ch in used if ch.startswith("N163Wave")] or [0])
    exps = [e for e in ("VRC6", "S5B", "N163") if any(expansion_of(ch) == e for ch in used)]

    # 音符入池：每池声道一个声部；满员时偷最早结束的声部（旧音被自然截断）
    chan_notes = defaultdict(list)
    stats = defaultdict(lambda: defaultdict(int))
    for c, cfg in sorted(assign.items()):
        tr = {ch: 0 for ch in cfg["pool"]}
        pieces = sorted(((round(t2f(st)), max(round(t2f(st)) + 1, round(t2f(en))),
                          pitch + cfg.get("transpose", 0)) for st, en, pitch in notes[c]),
                        key=lambda x: (x[0], -x[2]))
        for sf, ef, pitch in pieces:
            avail = [ch for ch in cfg["pool"] if tr[ch] <= sf]
            ch = max(avail, key=lambda x: tr[x]) if avail else \
                min(cfg["pool"], key=lambda x: tr[x])
            if not avail:
                stats[c]["stolen"] += 1
            tr[ch] = ef
            p = pitch
            while p < CHANNEL_KIND[ch][1]:
                p += 12
            while p > MAX_PITCH:
                p -= 12
            chan_notes[ch].append((sf, ef, nname(p)))
            stats[c]["kept"] += 1

    drum_notes = []
    for dc in drum_chs:
        for st, en, pitch in sorted(notes[dc], key=lambda x: x[0]):
            name, val, _ = drum_of(pitch)
            drum_notes.append((round(t2f(st)), max(round(t2f(st)) + 1, round(t2f(en))), val, name))

    # ---- 输出文本工程 ----
    title = args.midi.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    L = [f'Project Version="4.5.3" TempoMode="FamiStudio" Name="{title}"'
         + (f' Expansions="{",".join(exps)}"' if exps else "")
         + (f' NumN163Channels="{n163_n}"' if n163_n else "")]
    for ch in used:
        L.append(instrument_head(ch))
        L.extend(instrument_body(ch, kinds[ch]))
    drum_insts = {}
    for _, name, val, env in DRUMS:
        if name in {n for _, _, _, n in drum_notes} and name not in drum_insts:
            drum_insts[name] = (val, env)
            L.append(f'\tInstrument Name="{name}" Color="f06292"')
            L.append(f'\t\tEnvelope Type="Volume" Length="{len(env)}" Values="{",".join(map(str, env))}"')
    L.append(f'\tSong Name="{title}" Color="ff8a65" Length="{num_pats}" LoopPoint="-1" '
             f'PatternLength="{PATTERN_LENGTH}" BeatLength="{BEAT_LENGTH}" '
             f'NoteLength="{NOTE_LENGTH}" Groove="{NOTE_LENGTH}" GroovePaddingMode="Middle"')
    for ch in used + (["Noise"] if drum_notes else []):
        L.append(f'\t\tChannel Type="{ch}"')
        nts = chan_notes.get(ch, []) if ch != "Noise" else drum_notes
        for p in range(num_pats):
            L.append(f'\t\t\tPattern Name="P{p}" Color="ff8a65"')
            for item in nts:
                sf = item[0]
                if p * PAT_FRAMES <= sf < (p + 1) * PAT_FRAMES:
                    if ch == "Noise":
                        _, ef, val, name = item
                        L.append(f'\t\t\t\tNote Time="{sf - p * PAT_FRAMES}" Value="{val}" '
                                 f'Duration="{ef - sf}" Instrument="{name}"')
                    else:
                        _, ef, val = item
                        L.append(f'\t\t\t\tNote Time="{sf - p * PAT_FRAMES}" Value="{val}" '
                                 f'Duration="{ef - sf}" Instrument="V_{ch}"')
            L.append(f'\t\t\tPatternInstance Time="{p}" Pattern="P{p}"')
    open(args.out, "w", encoding="utf-8").write("\n".join(L) + "\n")

    # ---- 统计 ----
    total_k = sum(v["kept"] for v in stats.values()) + len(drum_notes)
    total_s = sum(v["stolen"] for v in stats.values())
    exp_sec = num_pats * PAT_FRAMES / FPS
    print(f"patterns={num_pats}  expected_seconds={exp_sec:.2f}  expansions={exps or '无'}")
    for c in sorted(assign):
        s = stats[c]
        print(f"  midi ch{c:2d} -> {'+'.join(assign[c]['pool']):30s} kept={s['kept']:4d} stolen={s['stolen']}")
    if drum_notes:
        print(f"  midi ch 9  -> Noise (鼓组)                       kept={len(drum_notes)}")
    unmapped = [c for c in notes if c not in assign and c not in drum_chs and notes[c]]
    if unmapped:
        print(f"  !! 声道池耗尽，未映射（改 MANUAL_MAP）: {unmapped}")
    print(f"TOTAL kept={total_k} stolen={total_s}（{100 * total_s / max(1, total_k):.1f}% 被截断）")
    print(f"下一步: render.ps1 -InputFile {args.out} -OutputFile out.wav "
          f"-ExpectedSeconds {exp_sec:.2f} -Tolerance 0.5")


if __name__ == "__main__":
    main()
