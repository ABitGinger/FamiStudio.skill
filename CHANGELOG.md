# Changelog

## 1.2.1 — 2026-09-05

- 发布准备：SKILL.md 去本机化——安装路径改为"定位流程"（`FAMISTUDIO_EXE` 环境变量 →
  标准位置探测 → 询问用户），不再写死本机路径
- `render.ps1`：支持 `FAMISTUDIO_EXE` 环境变量与标准位置自动探测
- 许可：MIT → **GPL-3.0**

## 1.2 — 2026-09-05

- 新增 MIDI 转写：`assets/midi2fms.py`（2A03+VRC6+S5B+N163 声道池、GM 鼓组映射、
  tempo map 逐段积分精确到帧、复音 note-stealing、自动 Expansion 乐器属性），
  方法与陷阱见 `references/midi-import.md`
- 新增实测结论：EPSM 文本导入 4.5.3 崩溃；`Song` 行省略 `Groove`/`GroovePaddingMode` 崩溃；
  扩展声道乐器缺 `Expansion` 属性 → 静音无报错（渲染后必须逐声道查出声）

## 1.1 — 2026-09-04

- 技能目录规范化（`references/` + `assets/` + `scripts/`），触发描述增强
- 实测修正：`Duration` 是真实音长门限（非"持续到下一音符"）；
  `Volume=` 为粘性通道音量事件（省略=继承）；无 `Loop` 音量包络播完即静音；
  PowerShell 调用需 `Start-Process -Wait`
- 新增 `scripts/render.ps1` 渲染校验闸门（退出码 + WAV 头解析 + 预期时长 ±容差）

## 1.0 — 2026-09-04

- 首版：文本工程格式速查、8 小节三声部模板、CLI 渲染工作流
