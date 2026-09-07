# MIDI → FamiStudio 文本工程转写

用户要求把 MIDI（`.mid`）转成 FamiStudio 谱/工程时读本文。首选工具：`assets/midi2fms.py`；
映射不满意时改脚本顶部配置重跑，不要手写几百个 Note 行。

## 快速路径

```bash
python <skill>/assets/midi2fms.py 输入.mid 输出.txt
# 脚本会打印 expected_seconds 和各声道分配/丢失统计
powershell -NoProfile -File <skill>/scripts/render.ps1 \
    -InputFile 输出.txt -OutputFile 输出.wav -ExpectedSeconds <脚本打印值> -Tolerance 0.5
```

## 解析要点（实测）

- 用 `mido`（`pip install mido`）。单轨多声道很常见（十几个声道挤在 track 0）。
- **必须把 `note_on` velocity=0 当作 note_off 处理**，否则复音统计全是假的。
- 未配对的 note_on（曲终没关）按曲末 +1 拍补齐。
- 每个音符的事件顺序：同 tick 先 off 后 on，避免同音连击被并掉。

## 时间换算（无需量化）

- tempo map 逐段积分：每段 `(tick差) × tempo/1e6 / TPQ` 累加成秒，`× 60.0988 = 帧`。
  渐慢/自由速度精确保留，音符位置误差 ≤1 帧。
- 文本工程的 `Time`/`Duration` 允许任意帧值，不必落在网格上（见 format.md [实测]）；
  长音符可直接跨 Pattern 边界，不需要切段。
- `Pattern 帧长 = PatternLength × NoteLength`；总 Pattern 数 = ceil(总帧数 ÷ Pattern 帧长)。

## 复音与声部分配

NES 每声道单音。每个 MIDI 声道 → 一个 FamiStudio 声道池（pool）：

- 按复音数给池子配声道数；满员时 **stealing（偷最早结束的声部）优于丢弃**——
  实测密集钢琴/铺底声部（≥5 复音）按池大小损失 5~15%，且丢的都是最内层和弦音，
  顶端旋律与低音线完整。
- 排序：同 tick 先高音后低音入池（保旋律）。
- 音域 clamp（低于下限升八度）：Square/VRC6 方波/S5B ≥27，VRC6Saw/Triangle ≥36，N163 ≥40。

## 鼓组（GM ch9）

按 GM 打击乐音高映射到 Noise 预设 + 衰减包络乐器（无 Loop，播完自动止音）：

| GM 音高 | 部件 | Noise `Value` |
|---|---|---|
| 35/36 | 底鼓 | `D#3` |
| 38/40 | 军鼓 | `G#3` |
| 42/44 | 踩镲/开镲 | `G#3` + 短包络区分 |
| 41/43/45/47/48 | 通鼓 | `G#3` |
| 49/57 | 吊镲 | `G#3` + 长衰减包络 |

噪声声道单音，重叠鼓点互相截断——这是真硬件行为，不算损失。

## 乐器规则（踩过的坑）

- **扩展声道（VRC6/S5B/N163/VRC7）的乐器必须带对应 `Expansion="..."` 属性，
  否则整声道静音且无任何报错** [实测]。渲染完必须逐声道确认出声。
- N163 乐器还需要 `N163Wave` + `Repeat` 包络（最小配方见 format.md）。
- `Song` 行 `Groove`/`GroovePaddingMode` 必填，省略即解析崩溃。
- 音色近似思路：钢琴/尼龙弦 = 拨弦衰减包络；弦乐/铺底 = 慢起音 + 低音量持续包络；
  电钢 = 衰减到持续点后 Loop。

## 验证清单（必做）

1. `render.ps1` + `-ExpectedSeconds`（用脚本打印的 60.0988 精确值，`-Tolerance 0.5`）。
2. 幅度扫描 WAV：长静音段应只出现在首尾；记录峰值防削波。
3. `famistudio-txt-export` 往返导出能解析 = 语法健全。
4. **逐声道出声检查**（扩展现声道静音陷阱无报错，只能这么抓）：
   `FamiStudio.exe 工程.txt wav-export sep/x.wav -wav-export-separate-channels`
   → 每声道一个 `x_<声道名>.wav`，逐个测幅度（numpy 逐帧包络），有声率应与该声道
   音符量级相符；峰值 >0 即乐器配置正确。
5. 向用户如实报告：保留率、截断/丢弃的都是什么（如"最内层和弦音"）、哪些音色是芯片近似。
