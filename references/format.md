# FamiStudio 4.5.3 文本工程格式 · 权威参考

依据：本机 4.5.3 实测（渲染 + WAV 逐帧幅度分析）+ 全部自带示例曲导出普查。
标注约定：**[实测]** = 本机渲染并用幅度分析验证；**[示例]** = 官方示例曲导出文本中的真实用法。

## 文件与结构

- 文本工程用 `.txt`；`.fms` 是二进制（魔数 `FMS!`）。两者 GUI 都能打开，可互相另存。
- UTF-8/ASCII 纯文本，**Tab 缩进 = 层级**，一行一条记录，属性 `Key="Value"`。

```
Project Version="4.5.3" TempoMode="FamiStudio" Name="..." Author="..."
	Instrument Name="Lead" Color="81c784"          ← 1 层
		Envelope Type="DutyCycle" Length="1" Values="2"
	Arpeggio Name="Arp" Color="42a5f5" Length="8" Loop="0" Values="-7,-7,4,4,0,0,-3,-3"
	Song Name="..." Color="ff8a65" Length="8" LoopPoint="0" PatternLength="16" BeatLength="4" NoteLength="6" Groove="6" GroovePaddingMode="Middle"
		Channel Type="Square1"                     ← 2 层
			Pattern Name="L1" Color="ff8a65"       ← 3 层
				Note Time="0" Value="G4" Duration="24" Instrument="Lead"   ← 4 层
			PatternInstance Time="0" Pattern="L1"
		Channel Type="Noise"                       ← 不用的声道留空行即可 [实测]
```

## Project 行

- `TempoMode="FamiStudio"`（推荐）或 `"Classic"`（示例曲全部用 FamiStudio 模式）。
- 省略的属性取默认（无扩展芯片、NTSC）。[实测]
- 扩展芯片 **[示例]**：`Expansions="VRC6"` / `"VRC7"` / `"N163"`（配 `NumN163Channels`）/ `"S5B"` / `"EPSM"`，可逗号并列。
  声道 Type 名见「声道与噪声鼓组」一节；**EPSM 文本导入 4.5.3 必崩 [实测]，避开**。
- 混音器微调属性（可选）[示例]：`VolumeDb` `TrebleDb` `TrebleRolloffHz` `GlobalBassCutoffHz` 及各芯片同名前缀版本。

## Instrument 与 Envelope

```
Instrument Name="Lead" Color="81c784"
	Envelope Type="Volume" Length="12" Values="15,14,...,4"            ← a
	Envelope Type="Volume" Length="9" Loop="0" Release="5" Values="..." ← b
	Envelope Type="DutyCycle" Length="1" Values="2"
```

- 不写任何 Envelope = 恒定音量 15。[实测]
- `Values` 每帧一个值；`Length` = 值个数。
- **音量包络三种行为 [实测]**：
  - (a) 无 `Loop`：播完所有值后**直接静音**（音符自动结束）——衰减包络可当自动止音用。
  - (b) `Loop="i"`：从下标 i 起循环（i=0 即整体循环，可持续发声）。
  - 音符触发 `Release` 时：跳到 `Release="i"` 指定的值下标继续播到结尾。
- `DutyCycle`：值 0~3 = 12.5%/25%/50%/75% 占空比；单值 = 固定音色。[实测]
- `Type="Pitch"`（带 `Loop`）、`Type="NoiseFreq"`（噪声鼓）、`Type="Arpeggio"`（乐器级琶音，半音偏移）[示例]。
- `Type="Repeat"` 与 `N163Wave` 仅 N163 扩展芯片用。[示例]
- NES 三角波通道没有音量寄存器，音量包络对它无意义。
- 乐器可跨声道复用（同一乐器 Square/Triangle 都能挂）。[实测]
- **扩展芯片声道的乐器必须带对应 `Expansion="..."` 属性，否则整声道静音**（VRC6/S5B 实测；
  基础 2A03 声道无此要求）。N163 乐器另需波形包络，见下方配方。[实测]

### N163 乐器最小配方（实测发声）[实测]

```
Instrument Name="N163 Lead" Color="4dd0e1" Expansion="N163" N163WavePreset="Custom" N163WaveSize="16" N163WavePos="0" N163WaveCount="1"
	Envelope Type="Volume" Length="9" Loop="8" Values="15,12,11,10,10,10,9,9,9"
	Envelope Type="N163Wave" Length="16" Loop="0" Values="15,15,15,15,15,15,15,15,0,0,0,0,0,0,0,0"
	Envelope Type="Repeat" Length="1" Loop="0" Values="1"
```

- `N163Wave` 的 `Values` 是波形采样（0~15，个数 = `N163WaveSize`）；上例为 50% 方波。
- `Repeat` 包络的值 = 循环播放的波形下标（单波形写 `1`）；`N163WaveCount="1"` = 波形总数。

## Arpeggio（乐器外命名琶音）[示例]

```
Arpeggio Name="Arp: Hat" Color="f06292" Folder="Percussion" Length="2" Values="0,3"
```
`Values` 为相对音符的半音偏移（可负）；音符上用 `Arpeggio="Arp: Hat"` 引用。
噪声通道上快速交替值可合成 hi-hat/snare 质感（官方鼓组就是这么做的）。

## Song

```
Song Name="..." Color="ff8a65" Length="8" LoopPoint="0" PatternLength="16" BeatLength="4" NoteLength="6" Groove="6" GroovePaddingMode="Middle"
```

- `Length`：小节序列长度（每声道 PatternInstance 数一致）。
- `LoopPoint`：从第几个 Pattern 循环；`0`=整曲循环，`-1`=不循环 [示例]。
- `PatternLength`：每 Pattern 的 16 分音符槽数（16=一小节 4/4；32=两小节）[示例两者都有]。
- `BeatLength`：每拍槽数（4=16 分音符网格；示例中也有 2）。
- `NoteLength` + `Groove`：每个 16 分音符占的帧数。简单节奏两者写同一个数 [实测]。
  `Groove` 也支持破折号序列做摇摆/复合节奏：`"6-5-5"`、`"5-6"`、`"7-6"` [示例]——
  此时音符 Time 仍以帧计，但需按序列累加，**复杂化时间数学，初写者避开**。
- `PatternCustomSettings Time=... Length=... NoteLength=... Groove=...`：歌曲中段变速 [示例]，进阶。
- **`Groove` 与 `GroovePaddingMode` 必须显式写出**（简单节奏写 `Groove="6" GroovePaddingMode="Middle"`）：
  省略任一 → 解析崩溃 `The given key 'Groove'/'GroovePaddingMode' was not present in the dictionary`。[实测]

## 时间与速度

**所有 `Time`/`Duration`/`Release` 单位都是帧（60fps）**，`Time` 相对 Pattern 开头。[实测]

| 时值 | N=6 (150BPM) | N=7 (≈128.6) | N=5 (180BPM) |
|---|---|---|---|
| 16 分 | 6 | 7 | 5 |
| 8 分 | 12 | 14 | 10 |
| 4 分 | 24 | 28 | 20 |
| 2 分 | 48 | 56 | 40 |
| 一小节(PatternLength=16) | 96 | 112 | 80 |

- BPM = 3600 ÷ (NoteLength × BeatLength)。[实测推算，误差 <0.2%]
- **Pattern 帧长 = `PatternLength` × `NoteLength`**（槽数 × 每槽帧数）；`BeatLength` 不参与该公式
  [实测 PatternLength=12、NoteLength=9 → 108 帧/Pattern]。
- **`Time`/`Duration` 允许任意帧值**——不必是 NoteLength 的倍数、不必落在网格上 [实测]。
  MIDI 转写直接按帧写即可。
- **长音符可跨 Pattern 边界**：Note 写在起始 Pattern，`Duration` 跨界发声连续、无重触发、到点精确停止
  [实测逐帧幅度分析]。
- 音符 `Time` 超出所属 Pattern 帧长 → **静默丢弃**（不报错）；音符延到歌曲末尾之后 → 在歌尾截断 [实测]。
- 渲染帧率实为 NTSC 60.0988fps（8 小节 N=6 实测 12.78s 而非 12.80s）。校验时长按 /60 估算即可，
  需要严丝合缝时用 60.0988；逐帧幅度分析有 ±2 帧测量桶误差。[实测]
- WAV 时长 ≈ 全曲总帧数 ÷ 60；单声道 44100Hz/16bit = 88200 字节/秒。[实测]

## Note（核心）

```
Note Time="0" Value="G4" Duration="24" Instrument="Lead"                    ← 基本音符 [实测]
Note Time="0" Value="C4" Duration="20" Release="18" Instrument="Pluck"      ← 带释放 [示例]
Note Time="24" Volume="7"                                                   ← 纯音量事件（无 Value）[示例+实测]
```

- **`Duration` 是真实音长门限 [实测]**：声音在 Duration 结束处精确停止（即使后面没有别的音符）。
  同声道后一个音符会提前截断前面的音（单复调）[示例一致]。
- **休止/断奏写法**：最简单 = 把 Duration 写短，留出的时间自然无声 [实测]；
  进阶 = `Release="帧偏移"` 让包络进入释放段（需乐器音量包络带 `Release=` 索引，否则无效 [实测]）。
- **`Volume=` 是粘性的通道音量事件 [实测]**：
  - 省略 Volume = 继承上一个音量（不是重置为 15！）；
  - 恢复默认必须显式 `Volume="15"`；
  - 无 `Value` 的 Note 行 = 纯音量事件，本身不发声；
  - 实测电平：15→0.224、9→0.144、4→0.068、2→0.035（相对满幅）。
- 其它音符属性 [示例]：
  - `Attack="False"`：不重新触发乐器包络（同音连奏/滑音衔接用；默认 True）
  - `SlideTarget="A#4"`：滑向目标音高
  - `VibratoSpeed="8" VibratoDepth="4"`（0 0 = 关闭）
  - `FinePitch="-1"`：音高微调
  - `Arpeggio="名字"`：挂命名琶音
  - `DutyCycle="2"`：音符级占空比覆盖（少见）
  - `DeltaCounter=`：仅 DPCM
- `Instrument` 按**名字**引用。

## 声道与噪声鼓组

- 基础类型：`Square1` `Square2` `Triangle` `Noise` `DPCM`。[实测]
- 扩展芯片声道 Type 名 [实测/示例]：

  | 扩展 | 声道 Type |
  |---|---|
  | VRC6 | `VRC6Square1` `VRC6Square2` `VRC6Saw` |
  | S5B | `S5BSquare1` `S5BSquare2` `S5BSquare3` |
  | N163 | `N163Wave1` … `N163WaveN`（N = `NumN163Channels`，实测 8 可用） |
  | VRC7 | `VRC7FM1` … `VRC7FM6` [示例] |

- 多扩展组合 [实测]：`Expansions="VRC6,S5B,N163" NumN163Channels="8"` 共 19 声道同开渲染正常。
- **EPSM 在 4.5.3 文本导入必崩 [实测]**：单独或与其它扩展组合、有无音符均崩
  （`Index was outside the bounds of the array`）。要多声道用 VRC6+S5B+N163。
- 噪声鼓组写法 [示例]：`Value` 用音名选 16 个周期噪声预设（常用 `G#3`=高/军、`D#3`=低/底），
  配不同乐器（`NoiseFreq` 包络改变音色）+ `Arpeggio=` 快速交替做 hi-hat 质感。
- 三角波当贝斯（2~3 组音区，无包络乐器即可）。[实测]

## DPCM [示例]

```
DPCMSample Name="BassDrum" Color="4dd0e1" Data="<hex 字节>"
	DPCMMapping Note="C3" Sample="BassDrum" Pitch="15" Loop="False" Bank="0"
```

## CLI 完整参考（`FamiStudio.exe -help`，4.5.3）

```
FamiStudio <input> <command> <output> [-options]
```

- 输入：`.fms` / 文本 `.txt` / FamiTracker `.ftm`·文本 / NSF·NSFE
- 命令：`wav-export` `mp3-export` `ogg-export` `nsf-export` `rom-export` `fds-export`
  `famitracker-txt-export` `famistudio-txt-export`
  `famistudio-asm-export` `famistudio-asm-sfx-export` `famitone2-asm-export` `famitone2-asm-sfx-export`
- 通用：`-export-songs:<0,1,2>`
- WAV/MP3/OGG 共有：`-wav-export-rate:<11025|22050|44100|48000>`（mp3/ogg 为 `-mp3-/-ogg-` 前缀，
  另有 `-bitrate:<96..256>`）`-duration:<秒>`(0=一遍) `-loop:<次数>` `-wav-export-channels:<hex掩码>`
  `-wav-export-separate-channels`（每声道一个 `<输出名>_<声道名>.wav`，验证扩展声道出声就靠它）
  `-wav-export-separate-intro`。注意选项都带 `-wav-export-` 全前缀，只写 `-separate-channels` 会被静默忽略 [实测]。
- NSF/ROM：`-nsf-export-mode:<ntsc|pal>` `-nsf-nsfe` `-rom-export-mode:<ntsc|pal|dual>`
- 文本导出：`-famistudio-txt-cleanup`（清理未用数据）
- 引擎导出（nesasm/ca65/asm6）：`-famistudio-asm-format` 等，见 `-help`
- NSF 导入：`-nsf-import-*` 系列，见 `-help`

**PowerShell 注意 [实测]**：FamiStudio.exe 是 GUI 子系统程序——PowerShell 里 `&` 调用**不会等待**，
`$LASTEXITCODE` 恒为空。必须 `Start-Process -Wait -PassThru`（本技能 `scripts/render.ps1` 已封装）。
Git Bash 直接调用则会正常等待。
