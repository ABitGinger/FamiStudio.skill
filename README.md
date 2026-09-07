# FamiStudio Skill for ZCode

[中文](#中文) | [English](#english)

---

## 中文

一个 [ZCode](https://github.com/) **技能（Skill）**：让 AI 代理用本机安装的 [FamiStudio](https://famistudio.org/)
编曲、改曲、导出 NES/FC 芯片音乐——不点 GUI，全程"手写文本工程 + 命令行渲染校验"。

对代理说"编段旋律""来段 8-bit 战斗音乐""把这个 MIDI 转成 NES 谱""把工程导出成 WAV/NSF"，
技能会自动触发并按一套**实测验证过的工作流**执行。

### 它包含什么

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 技能入口：触发条件、标准工作流、踩坑速查 |
| `references/format.md` | FamiStudio 文本工程格式权威参考（每条标注 [实测] 或 [示例] 出处） |
| `references/midi-import.md` | MIDI → FamiStudio 转写方法：tempo map 积分、复音 stealing、GM 鼓组映射 |
| `scripts/render.ps1` | 渲染闸门：CLI 渲染 → 透传错误 → 校验 WAV 时长（±容差）→ 可选播放 |
| `assets/template.txt` | 可直接渲染的 8 小节三声部示范工程（2 方波 + 三角贝斯） |
| `assets/midi2fms.py` | MIDI → FamiStudio 文本工程转换器（19 旋律声道池 + 噪声鼓组，自动 Expansion 配置） |

### 实测得来的关键知识（区别于"凭印象写的文档"）

技能里的格式结论不是抄的，是在本机 FamiStudio 4.5.3 上渲染 + WAV 逐帧幅度分析验证的，例如：

- **`Duration` 是真实音长门限**——到点即停，后面没有音符也不延续；
- **`Volume=` 是粘性的通道音量事件**——省略不是重置为 15，而是继承上一音量；
- **无 `Loop` 的音量包络播完即静音**——衰减包络可当自动止音用；
- **PowerShell 调用 FamiStudio.exe 必须 `Start-Process -Wait`**——GUI 子系统程序，`&` 不等待、
  `$LASTEXITCODE` 恒空；
- **扩展声道（VRC6/S5B/N163）的乐器不带 `Expansion` 属性 → 整声道静音且无任何报错**；
- **EPSM 工程文本导入 4.5.3 必崩**；`Song` 行省略 `Groove`/`GroovePaddingMode` 也崩。

完整清单见 [`references/format.md`](references/format.md)。

### 安装（ZCode 用户作用域，所有工作区生效）

```bash
git clone https://github.com/<你>/famistudio-skill.git ~/.agents/skills/famistudio
```

要求：

- Windows + [FamiStudio 4.5.x](https://famistudio.org/)，默认装在
  `C:\Program Files\FamiStudio\`（其它路径用 `render.ps1 -FamiStudio <路径>` 覆盖）
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

- 本技能代码与文档：MIT，见 [LICENSE](LICENSE)
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

**License**: MIT for everything in this repo. FamiStudio itself is (c) BleuBleu —
this repo ships no FamiStudio code or data, only automation knowledge to drive it.
