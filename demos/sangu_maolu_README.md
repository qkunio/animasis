# 三顾茅庐 · 像素故事短片（带中文旁白）

- 场景：`demos/sangu_maolu.yaml`（320×180 像素，×3 输出 960×540，12fps）
- 成片：`demos/output/sangu_maolu.mp4`，**88 秒**，H.264 + AAC（单声道 24 kHz 旁白）
- 旁白：edge-tts `zh-CN-YunxiNeural`，语速 `+5%`，共 12 句
- 关键帧：`demos/frames/sangu_maolu_t{14.8,26.8,29.5,39.0,49.6,63.2,65.8,73.4}.png`（远景摇、叩门近景、反打越肩、雪景广角、递信特写、窗内 zZZ 特写、门外静候中景、隆中对近景）
- 镜头：33 个镜位（远景 / 全景 / 中景 / 近景 / 特写），硬切为主，段落间短暂黑场，含 2 处反打视角与 7 段推 / 拉 / 摇

## 人物

| 角色 | 预设 | 造型 |
|---|---|---|
| 刘备 | hero | 黑发发髻、金黄长袍、长袖 |
| 关羽 | bob | 发髻、墨绿长袍、深肤色、长髯 |
| 张飞 | bob | 刺猬头、黑衣、短须 |
| 诸葛亮 | hero（slim） | 白袍、发髻、手持羽扇（第三次才出场） |
| 书童 | kid | 发髻、绿衣 |

## 镜头表（分镜）

由 `.venv/bin/python -m animasis shots demos/sangu_maolu.yaml --markdown` 生成。景别倍率 = 舞台裁切放大倍数（远景 ×1 = 整个 320×180 舞台）。

| # | 时间 | 镜头 | 目标 | 运动 | 转场 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 0.0–4.5s | wide (×1) | stage | cut | cut | 片头标题卡 |
| 2 | 4.5–9.2s | wide (×1) | 124,110 | cut | fade | 远景·三兄弟立于山前 |
| 3 | 9.2–13.8s | medium (×1.7) | liubei,guanyu | push 4s | cut | 缓推中景·刘备愁无军师 |
| 4 | 13.8–14.0s | full (×1.3) | 90,84 | cut | cut | 远景·隆中山水（有人推荐卧龙） |
| 5 | 14.0–16.2s | full (×1.3) | 240,84 | pan 2.2s | cut | 横摇·远山 |
| 6 | 16.2–19.0s | close (×2.4) | liubei | push 2.4s | cut | 推近景·刘备喜出望外 |
| 7 | 19.0–21.5s | wide (×1) | stage | cut | fade | 卡片·一顾 |
| 8 | 21.5–22.3s | full (×1.3) | 90,112 | cut | fade | 全景·兄弟走向草庐 |
| 9 | 22.3–26.0s | full (×1.3) | hut | pan 3.5s | cut | 横摇·跟到草庐门前 |
| 10 | 26.0–27.6s | close (×2.4) | 206,122 | cut | cut | 近景·刘备叩门「咚咚」 |
| 11 | 27.6–31.2s | close (×2.4) | shutong,liubei | cut | cut (reverse angle) | 反打越肩·书童答话 |
| 12 | 31.2–34.8s | full (×1.3) | 150,112 | cut | cut | 全景·失望而归 |
| 13 | 34.8–37.3s | wide (×1) | stage | cut | fade | 卡片·二顾 |
| 14 | 37.3–41.0s | wide (×1) | stage | cut | fade | 广角·风雪赶路 |
| 15 | 41.0–44.6s | medium (×1.7) | zhangfei,liubei | cut | cut | 中景·张飞抱怨 |
| 16 | 44.6–47.0s | full (×1.3) | liubei | cut | cut | 全景跟拍·冒雪前行 |
| 17 | 47.0–48.6s | medium (×1.7) | liubei,shutong | cut | cut | 中景·先生又不在 |
| 18 | 48.6–50.4s | closeup (×3) | 208,126 | cut | cut | 特写·递书信 |
| 19 | 50.4–51.4s | medium (×1.7) | liubei | cut | cut | 中景·刘备作揖 |
| 20 | 51.4–53.8s | wide (×1) | stage | cut | cut | 远景·风雪中离去 |
| 21 | 53.8–56.3s | wide (×1) | stage | cut | fade | 卡片·三顾 |
| 22 | 56.3–56.9s | medium (×1.7) | hut | cut | fade | 中景·春日草庐 |
| 23 | 56.9–59.6s | wide (×1) | stage | pull 2.6s | cut | 拉远景·兄弟入画 |
| 24 | 59.6–62.8s | medium (×1.7) | 200,116 | cut | cut | 中景·门前（书童：嘘） |
| 25 | 62.8–63.8s | closeup (×3) | 278,120 | cut | cut | 特写·窗内午睡 zZZ |
| 26 | 63.8–64.4s | medium (×1.7) | zhangfei,liubei | cut | cut | 中景·门外静候 |
| 27 | 64.4–67.5s | medium (×2) | zhangfei,liubei | push 3s | cut | 缓推·张飞不耐 |
| 28 | 67.5–69.0s | close (×2.4) | zhuge | cut | cut | 近景·孔明出门 |
| 29 | 69.0–71.3s | close (×2.4) | liubei,zhuge | cut | cut (reverse angle) | 反打·刘备再拜 |
| 30 | 71.3–72.2s | close (×2.4) | liubei,zhuge | cut | cut | 近景双人·隆中对 |
| 31 | 72.2–74.6s | closeup (×2.8) | liubei,zhuge | push 2.4s | cut | 缓推·三分天下 |
| 32 | 74.6–78.4s | wide (×1) | stage | cut | cut | 远景·一同出山 |
| 33 | 78.4–88.0s | wide (×1) | stage | cut | fade | 成语卡 |

镜头语言概要：

- **片头 → 推荐卧龙**：远景交代三兄弟 → 缓推中景（刘备愁无军师）→ 全景横摇隆中远山（推荐卧龙）→ 推近景（刘备喜出望外）。
- **一顾**：黑场进 → 全景横摇跟随兄弟走到草庐 → 硬切近景叩门「咚咚」→ **反打越肩**（镜像视角，从门内看书童答话）→ 全景失望而归。
- **二顾**：黑场进雪景广角 → 中景张飞抱怨 → 全景跟拍冒雪前行 → 中景「先生又出门了」→ **特写递书信** → 中景作揖 → 远景离去。
- **三顾**：中景春日草庐 → 拉成远景（兄弟入画）→ 中景门前书童「嘘」→ **特写窗内 zZZ** → 中景门外静候并缓推（张飞不耐）→ 近景孔明出门 → **反打**刘备再拜 → 近景双人「隆中对」缓推 → 远景一同出山 → 黑场进成语卡。

## 分镜 / 剧情

| 时间 | 画面 | 旁白 |
|---|---|---|
| 0–4.5s | 标题卡「三顾茅庐 · 刘备三请诸葛亮」+ 羽扇 | 三顾茅庐。 |
| 4.5–19s | 竹林山前，三兄弟名牌；刘备愁「军师…?」，有人推荐「卧龙」 | 东汉末年…缺少军师；有人推荐卧龙先生诸葛亮 |
| 19–21.5s | 卡片「一顾」 | — |
| 21.5–34.8s | 走到草庐，刘备叩门「咚咚」，书童：「先生出门了」，失望而归 | 来到隆中草庐…先生一早出门，失望而归 |
| 34.8–37.3s | 卡片「二顾」 | — |
| 37.3–53.8s | 大雪背景；张飞：「村夫而已！」；书童：「先生又出门了」；刘备留下书信并作揖 | 天降大雪…张飞抱怨…留下一封书信 |
| 53.8–56.3s | 卡片「三顾」 | — |
| 56.3–78.4s | 春天花瓣；书童「嘘——在午睡」，窗外 zZZ；刘备门外作揖久候，张飞「等到几时？！」；诸葛亮出门，「三分天下」挥扇，众人欢喜，一同离去 | 第三次来到草庐…诸葛亮被诚意打动，提出三分天下，答应出山 |
| 78.4–88s | 成语卡：比喻真心诚意，一再邀请、拜访有才能的人 | 后来，人们用三顾茅庐… |

## 相机系统（`animasis/camera.py`）

场景 YAML 顶层写 `camera:` 关键帧列表：

```yaml
camera:
  - { t: 0,    shot: wide }                                              # 硬切（默认）
  - { t: 9.2,  shot: medium, target: [liubei, guanyu], offset: [0, -6], move: 4.0 }   # 4 秒推镜
  - { t: 19.0, shot: wide, transition: fade, fade: 0.6 }                 # 以 t 为中心短暂黑场
  - { t: 27.6, shot: close, target: [shutong, liubei], flip: true }      # 反打（镜像视角）
```

- `shot`：`wide/远景 1.0`、`full/全景 1.3`、`medium/中景 1.7`、`close/近景 2.4`、`closeup/特写 3.0`、`ecu/大特写 3.6`；`zoom` 可直接覆盖（≥1）。
- `target`：角色名（实时跟随，取身体中点）、角色列表（取中点，双人镜头）、`[x, y]`、`{x:, y:}`、overlay 的 `id`（如草庐 `id: hut`），或 `stage`；`offset: [dx, dy]` 微调构图。
- `move`：秒数，从上一镜位平滑推 / 拉 / 摇（缩放按对数插值），`ease: linear|in|out|inout`；不写即硬切。
- `transition: fade` + `fade` 秒数：以关键帧时间为中心的黑场转场；`flip: true`：反打视角，草庐牌匾文字预先镜像，翻转后仍正读，气泡尾巴方向自动对调。
- 取景自动夹在舞台内；舞台在输出分辨率上裁切放大（最近邻），像素保持方正。字幕条、标题卡、角标、雪 / 花瓣属于屏幕层，不随镜头缩放；`follow` 的气泡 / 名牌、`space: world` 的文字（如「咚咚」、zZZ）随镜头移动，但保持原字号，并夹在画面内；说话人出画或隐藏时，气泡不显示。
- `animasis shots <scene>` 打印镜头表（`--markdown` 输出表格）。

## 本轮新增的引擎能力

- 背景：`cottage` / `cottage_snow` / `cottage_spring`（远山、竹林、土路；雪地 / 春花），可用 `background` 动作在时间轴上切换。
- 叠加层：`hut`（茅草屋，`open` 时间段开门、`lamp` 亮窗、`snow` 屋顶积雪、`sign` 牌匾）、`fence`、天气 `snow` / `petals`。
- 人物：`beard: short|long`、`hair_style: topknot`、`visible: false`；动作 `show` / `hide` / `attach`；姿势 `bow`（作揖）、`knock`（叩门）。
- 道具图标：`fan`（羽扇）、`letter`（书信）。
- 旁白模块 `animasis/narrate.py`：读取场景 YAML 的 `narration:`（voice / rate / lines[t, text]），逐句 edge-tts 合成（按内容哈希缓存），检查重叠，用 ffmpeg `adelay + amix` 按时间点对齐，静音补齐到视频时长，再 `-c:v copy` 混入 AAC。

## 重新渲染

```bash
cd /workspace/animasis
# 画面 + 旁白一步到位（需联网调用 edge-tts；已生成的句子会走缓存）
.venv/bin/python -m animasis narrate demos/sangu_maolu.yaml -o demos/output/sangu_maolu.mp4

# 仅无声画面
.venv/bin/python -m animasis render demos/sangu_maolu.yaml -o /tmp/sangu_silent.mp4
# 用已有无声视频只做配音
.venv/bin/python -m animasis narrate demos/sangu_maolu.yaml -o demos/output/sangu_maolu.mp4 --video /tmp/sangu_silent.mp4

# 镜头表
.venv/bin/python -m animasis shots demos/sangu_maolu.yaml --markdown

# 关键帧
for t in 14.8 26.8 29.5 39.0 49.6 63.2 65.8 73.4; do
  ffmpeg -v error -y -ss $t -i demos/output/sangu_maolu.mp4 -frames:v 1 demos/frames/sangu_maolu_t$t.png
done
```

换语音：改 YAML 里 `narration.voice`（如 `zh-CN-XiaoxiaoNeural`），或给单句加 `voice:` / `rate:`。改旁白文字后只会重新合成变动的句子。

## 音频文件

- 逐句 mp3：`demos/audio/sangu_maolu/01_*.mp3 … 12_*.mp3`
- 对齐后的整轨：`demos/audio/sangu_maolu_narration.wav`（88 s）
