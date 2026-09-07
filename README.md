# FamiStudio Skill for ZCode

[中文](#中文) | [English](#english)

---

## 中文

一个可用于 [ZCode](https://github.com/) 等的**技能（Skill）**：让 AI 代理用本机安装的 [FamiStudio](https://famistudio.org/)
编曲、改曲、导出 NES/FC 芯片音乐——不点 GUI，全程"手写文本工程 + 命令行渲染校验"。

对代理说"编段旋律""来段 8-bit 战斗音乐""把这个 MIDI 转成 NES 谱""把工程导出成 WAV/NSF"，
技能会自动触发并按一套**实测验证过的工作流**执行。

### 安装

**把这个仓库链接交给你的AI，相信它会帮你解决的**（本项目在 ZCode 上完成，但在 DeepSeek Harness, Opencode 等工具上一样可用）

要求：

- Windows + [FamiStudio 4.5.x](https://famistudio.org/)，默认自动探测
  `C:\Program Files\FamiStudio\`；其它安装位置设环境变量 `FAMISTUDIO_EXE`
  或用 `render.ps1 -FamiStudio <路径>` 覆盖
- MIDI 转写功能需要 Python 3 + `pip install mido`

新开一个 ZCode 会话即可被发现。也可以放进某个仓库的 `.agents/skills/famistudio/` 作为工作区作用域，
或用 `~/.zcode/skills/`（仅 ZCode 可见、优先级更高）。

### 手动使用（不通过 AI 也可以）

```bash
# 渲染 + 时长校验
powershell -NoProfile -File scripts/render.ps1 -InputFile my.txt -OutputFile my.wav -ExpectedSeconds 12.8

# MIDI 转写（打印 expected_seconds 与声道分配统计）
python assets/midi2fms.py input.mid output.txt

# 导出 NSF / ROM
FamiStudio.exe output.txt nsf-export output.nsf
```

### 示例提示词

- "用 FamiStudio 编一段 8 小节 C 大调旋律，要有贝斯"
- "来段 8-bit 的升级/拾取音效"
- "把 `song.mid` 转成 FamiStudio 工程并渲染成 WAV"
- "把这个 `.fms` 导出成 NSF"

### 许可与致谢

- 本技能代码与文档：**GPL-3.0**，见 [LICENSE](LICENSE)——衍生作品需同样以 GPL-3.0 开源
- [FamiStudio](https://famistudio.org/) 由 BleuBleu 开发，版权归其作者所有；
  本仓库不含 FamiStudio 的任何代码或数据，只是驱动它的自动化知识

---

## English

A [ZCode](https://github.com/) **skill** that lets an AI agent compose, edit, and export
NES/Famicom chiptune with a locally installed [FamiStudio](https://famistudio.org/) —
no GUI automation, just hand-written text projects verified through the CLI renderer.

Say "compose a melody", "give me an 8-bit jingle", "convert this MIDI to a NES track",
or "export this project to WAV/NSF" and the skill triggers with a **battle-tested workflow**.

**What's inside**: a format reference for FamiStudio's text project format where every claim is
marked either `[实测]` (verified by rendering + per-frame WAV amplitude analysis on 4.5.3) or
`[示例]` (observed in official demo songs); a PowerShell render gate with an expected-duration
check; a ready-to-render 8-bar template; and `midi2fms.py`, a MIDI → FamiStudio converter
(19-channel pool across 2A03+VRC6+S5B+N163, GM drum mapping, tempo-map-accurate frame timing,
note-stealing polyphony, automatic `Expansion` instrument attributes).

**Hard-won findings** include: `Duration` is a real gate (sound stops exactly there);
`Volume=` is a sticky channel event (omitting it inherits the previous volume);
volume envelopes without `Loop` silence themselves after the last value;
expansion-channel instruments missing the `Expansion` attribute render **silent with no error**;
EPSM text import crashes 4.5.3; omitting `Groove`/`GroovePaddingMode` on the `Song` line crashes the parser.

**Install**: `git clone <this repo> ~/.agents/skills/famistudio` — requires Windows,
FamiStudio 4.5.x, and `pip install mido` for MIDI conversion. Docs are primarily Chinese.

**License**: GPL-3.0 for everything in this repo (derivatives must stay open under GPL-3.0).
FamiStudio itself is (c) BleuBleu — this repo ships no FamiStudio code or data,
only automation knowledge to drive it.
