# FamiStudio.skill

---

一个可用于各类 Agent 的**技能（Skill）**：让 AI 代理用本机安装的 [FamiStudio](https://famistudio.org/)
编曲、改曲、导出 NES/FC 芯片音乐——不点 GUI，全程"手写文本工程 + 命令行渲染校验"。

对代理说"编段旋律""来段 8-bit 战斗音乐""把这个 MIDI 转成 NES 谱""把工程导出成 WAV/NSF"，
技能会自动触发并按一套**实测验证过的工作流**执行。

### 安装

**把这个仓库链接交给你的AI，相信它会帮你解决的**

本项目在 ZCode 上完成，但在 DeepSeek Harness, Opencode 等工具上一样可用

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
