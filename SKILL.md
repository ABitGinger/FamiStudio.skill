---
name: famistudio
description: >-
  Compose, edit, and render NES/Famicom chiptune music with the locally installed
  FamiStudio (4.5.x). Use whenever the user wants to
  编曲/作曲/写旋律/做一段音乐/来段8-bit, create or edit any FamiStudio project
  (.fms / .txt), convert FamiTracker/NSF material, or export/render to
  WAV/MP3/OGG/NSF/NES ROM — even if they don't say the word "FamiStudio"
  (8-bit music, chip音乐, game sound effects count too).
---

# FamiStudio 本机编曲

方法：**手写文本工程 + CLI 渲染校验**。不要用 GUI 自动化点钢琴卷帘——命令行只能转换格式，
编曲全靠写文本工程文件。完整格式规范（全部实测/示例验证）在 `references/format.md`，
动笔前先读它；下面的速查只够最小改动。

## 环境要求

- 需要 [FamiStudio](https://famistudio.org/) 桌面版 **4.5.x**（文本格式与 4.5.3 实测结论匹配）。
- **定位可执行文件**，按序尝试，找到即用：
  1. 环境变量 `FAMISTUDIO_EXE`（render.ps1 也认它）；
  2. Windows 默认 `C:\Program Files\FamiStudio\FamiStudio.exe`；
  3. `where.exe FamiStudio.exe` / 常见自定义安装盘符；
  4. 问用户要路径。
- **`.fms` 是二进制；文本工程是 `.txt`**——GUI 两种都能打开编辑
- 学习语法的素材：`<安装目录>/Demo Songs/`（二进制示例曲）
- Windows 下 Git Bash 直接调用会等待；**PowerShell 里必须 `Start-Process -Wait`**（GUI 子系统
  程序，`&` 不等待且 `$LASTEXITCODE` 恒空）

## 标准工作流

1. **写文本工程**：复制本技能 `assets/template.txt`（可直接运行的 8 小节三声部示范）改 Note 行。
2. **渲染 + 校验**（封装脚本：透传解析错误 → 校验退出码 → 解析 WAV 头 → 按预期时长闸门 → 可选播放；
   `<skill>` = 本 SKILL.md 所在目录）：

   ```bash
   powershell -NoProfile -File <skill>/scripts/render.ps1 \
       -InputFile 输入.txt -OutputFile 输出.wav -ExpectedSeconds 12.8 [-Play]
   ```

   `-ExpectedSeconds` = 总帧数 ÷ 60。报 DURATION MISMATCH 说明 Time/Duration 单位或音符数学错了；
   这是必设的闸门，不要跳过。
3. **交付**：`-Play` 播放一次；再打开 GUI 给用户看/继续编辑（Windows 示例，路径按上面定位结果替换）：

   ```bash
   powershell -NoProfile -Command "Start-Process '<FamiStudio.exe 路径>' '<工程路径>'"
   ```

## 修改已有二进制工程

`FamiStudio.exe 原文件.fms famistudio-txt-export 导出.txt` → 编辑 → 上面流程渲染。
学语法捷径：把任意示例曲转成文本对照（`famistudio-txt-export`）。

## MIDI 转写

用户给 MIDI（.mid）要转 FamiStudio 谱/工程 → 先读 `references/midi-import.md`，
再跑 `assets/midi2fms.py 输入.mid 输出.txt`（自动把声道分配到 2A03+VRC6+S5B+N163 声道池，
乐器自动带正确 Expansion 属性）。映射不满意改脚本顶部 `MANUAL_MAP` 重跑。
渲染后必须逐声道查出声（`-wav-export-separate-channels`）——扩展声道配错乐器是**静音**，无任何报错。

## 速查（细节与依据见 references/format.md）

- 时间单位 = 帧（60fps）。`BPM = 3600 ÷ (NoteLength × BeatLength)`；
  N=6、BeatLength=4 → 150BPM：16 分=6 帧、4 分=24 帧、一小节(PatternLength=16)=96 帧。
- **`Duration` 是真实音长**（到点即停，后面没音符也不延续）；休止 = 缩短 Duration。
- **`Volume=` 粘性**：省略=继承上一音量，恢复默认要显式 `Volume="15"`；
  无 `Value` 的 Note 行 = 纯音量事件（不发声）。
- 无 `Loop` 的音量包络播完即静音（可当自动止音）；`Loop="i"` 循环；
  音符 `Release="帧偏移"` 触发包络释放段（需包络带 `Release=` 索引）。
- 乐器无 Envelope = 恒定音量 15；`DutyCycle` 0~3 = 12.5%~75% 占空比；
  三角波没有音量包络（NES 硬件限制），当贝斯用 2~3 组音区。
- 噪声鼓组：`Value` 音名选 16 个预设（`G#3` 高 / `D#3` 低），`Arpeggio=` 快速交替做 hi-hat。
- 扩展芯片：Project 行 `Expansions="VRC6|VRC7|N163|S5B"`（N163 配 `NumN163Channels`；声道 Type 名、
  N163 最小乐器配方见 format.md）。**扩展声道的乐器必须带对应 `Expansion="..."` 属性，否则静音无报错**；
  **EPSM 文本导入 4.5.3 必崩，避开**。`Song` 行 `Groove`/`GroovePaddingMode` 必填（省略即崩）。
- `LoopPoint="0"` 整曲循环，`"-1"` 不循环；`Groove="6-5-5"` 摇摆节奏（初写避开）。
