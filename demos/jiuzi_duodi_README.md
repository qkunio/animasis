# 九子夺嫡 · 像素历史短片（带中文旁白）

- 场景：`demos/jiuzi_duodi.yaml`（320×180 像素舞台，×3 输出 960×540，**60fps**）
- 成片：`demos/output/jiuzi_duodi.mp4`，**106 秒**，H.264 + AAC（edge-tts 旁白，单声道 24 kHz）
- 旁白：edge-tts `zh-CN-YunxiNeural`，语速 `+5%`，共 15 句，无重叠
- 镜头：53 个镜位（远景 / 全景 / 中景 / 近景 / 特写），含 4 处反打、十余段推 / 拉 / 摇、多处黑场转场
- 关键帧：`demos/frames/jiuzi_duodi_t*.png`（16 张）

## 故事线（史实取向）

只用通行史书里的大事与年号，台词气泡只是示意，不是史料原话。

| 时间 | 段落 | 画面 | 史实要点 |
|---|---|---|---|
| 0–4.6s | 片头 | 标题卡「九子夺嫡」+ 太子印、诏书 | — |
| 4.6–13.1s | A 乾清宫 | 康熙**正体位**坐于御座（`view: front` + `pose: sit`），镜头横摇，九位皇子名牌依次出现 | 康熙在位六十一年，是中国在位最久的皇帝 |
| 13.1–18.4s | B 闪回 | 少年康熙把诏书交给年幼的胤礽 | 康熙十四年立胤礽为皇太子 |
| 18.4–26.1s | C 一废 | 太子骄纵 → 康熙震怒（反打）→ 太子跪地，**太子印掉落弹跳（物理）** | 康熙四十七年一废太子 |
| 26.1–32.5s | D 魇镇 | 大阿哥拿着巫蛊人偶，三阿哥指认（反打），**圈禁木笼落下** | 胤禔被胤祉揭发魇镇太子，终身圈禁 |
| 32.5–39.4s | E 推举 | 两位大臣向八阿哥作揖「请立八阿哥！」，康熙「哼……」 | 群臣推举胤禩，引起康熙猜忌 |
| 39.4–46.1s | F 复立再废 | 胤礽复立 → 再废，印再次落地，太子入笼；镜头推向空着的储位 | 康熙四十八年复立，五十一年再废，从此不再公开立储 |
| 46.1–61.0s | G 宫院 | 「八爷党」旗下四人振臂；四阿哥手持念珠「天下第一闲人」，十三阿哥前来交好；拉成远景「八爷党 VS 四爷」 | 八、九、十、十四阿哥结为八爷党；胤禛低调，与胤祥交好 |
| 61.0–67.2s | H 西北 | 边塞沙丘与烽火台，十四阿哥举令旗领兵，兵士**跳起欢呼（重力弹道）** | 康熙五十七年胤禵任抚远大将军，出征西北 |
| 67.2–69.9s | 卡片 | 「康熙六十一年冬（公元1722年）」 | — |
| 69.9–77.9s | I 畅春园 | 夜色寝宫、烛火；康熙倒下 → 黑场；隆科多手持遗诏宣布，众皇子愕然；角标「十四阿哥远在西北」 | 康熙病逝于畅春园，隆科多宣布皇四子胤禛继位 |
| 77.9–86.0s | J 即位 | 雍正立于龙椅前，众兄弟行礼；传说卡「传位十四子 → 传位于四子」 | 「十改于」只是民间传说，遗诏满汉文并书，并无实据 |
| 86.0–93.4s | K 结局 | 黄昏宫院，八、九阿哥入笼；十四阿哥走向「景陵」 | 胤禩、胤禟圈禁而死；胤禵被派去守景陵 |
| 93.4–100.4s | L 秘密立储 | 雍正手捧锦匣 → 上摇到「正大光明」匾 → 特写匾后锦匣 | 雍正元年创立秘密立储，密旨藏于乾清宫正大光明匾后 |
| 100.4–106s | 结尾 | 大事记卡 | 立太子 → 一废 → 复立 / 再废 → 雍正继位 → 秘密立储 |

「九子」按通行说法：大阿哥胤禔、二阿哥胤礽、三阿哥胤祉、四阿哥胤禛、八阿哥胤禩、九阿哥胤禟、十阿哥胤䄉、十三阿哥胤祥、十四阿哥胤禵（五阿哥胤祺、七阿哥胤祐不在争储的核心阵营里，没有出场）。

## 人物造型

全员清式辫发（`hair_style: queue`）+ 暖帽红缨（`hat_style: qing`），帝王用金顶帝冠（`hat_style: crown`）。每人一种袍色，方便辨认：

| 角色 | 造型 |
|---|---|
| 康熙（晚年） | 明黄龙袍、金顶帝冠、花白长髯；开场 `view: front` + `pose: sit` 正体位坐龙椅；闪回时另有一位无须的少年康熙 |
| 胤禔（大） | 灰袍、壮实体型，手持巫蛊人偶 |
| 胤礽（二） | 杏黄袍，手持太子印；闪回时是缩小 0.8 倍的孩童 |
| 胤祉（三） | 天蓝袍、清瘦 |
| 胤禛（四）→ 雍正 | 石青袍、手持念珠；即位后换明黄龙袍、帝冠、短须 |
| 胤禩（八） | 紫袍、清瘦 |
| 胤禟（九） | 深紫袍 |
| 胤䄉（十） | 橙褐袍、壮实 |
| 胤祥（十三） | 墨绿袍 |
| 胤禵（十四） | 红袍金带，手持帅旗 |
| 隆科多 / 大臣 / 兵士 | 褐袍短须 / 黑、蓝补服 / 蓝衣 |

## 本片新增的引擎能力

- `animasis/palace.py`（新模块）
  - 背景：`palace_hall`（乾清宫式殿内：彩画梁枋、红柱、格扇门、金砖地、红毯）、`palace_hall_night`（夜色 + 月光窗格）、`palace_court`（太和殿式宫院：黄琉璃重檐、三层汉白玉须弥座、红墙）、`palace_court_dusk`（黄昏）、`frontier`（西北：雪山、沙丘、烽火台）
  - 叠加层：`throne`（台阶 + 龙椅 + 金屏风）、`plaque`（匾额，反打时文字预先镜像）、`banner`（会飘的军旗 / 党旗）、`lantern`（宫灯）、`candle`（烛火闪烁）、`bars`（圈禁木笼，从上方落下罩住角色，画在角色之前的图层上）
- 人物：`hair_style: queue`（辫发）、`hat_style: qing | crown`（暖帽红缨 / 金顶帝冠）
- 道具图标：`edict`（圣旨）、`seal`（太子印）、`doll`（巫蛊人偶）、`beads`（念珠）、`flag`（帅旗）、`casket`（锦匣）
- 渲染：`render_scene` 输出 mp4 时改成流式（`stream_mp4`：rawvideo 管道直接喂给 ffmpeg，编码参数不变）。106 秒 × 60fps = 6360 帧，不再全部放进内存。

## 重新渲染

```bash
cd /workspace/animasis
# 画面 + 旁白一步到位（需联网调用 edge-tts；已生成的句子会走缓存）
.venv/bin/python -m animasis narrate demos/jiuzi_duodi.yaml -o demos/output/jiuzi_duodi.mp4

# 仅无声画面
.venv/bin/python -m animasis render demos/jiuzi_duodi.yaml -o /tmp/jiuzi_silent.mp4
# 用已有无声视频只做配音
.venv/bin/python -m animasis narrate demos/jiuzi_duodi.yaml -o demos/output/jiuzi_duodi.mp4 --video /tmp/jiuzi_silent.mp4

# 镜头表
.venv/bin/python -m animasis shots demos/jiuzi_duodi.yaml --markdown

# 关键帧
for t in 2.5 10.5 15.8 23.9 29.2 34.0 43.6 51.0 58.5 65.8 75.0 80.0 83.9 88.5 98.8 103.5; do
  ffmpeg -v error -y -ss $t -i demos/output/jiuzi_duodi.mp4 -frames:v 1 demos/frames/jiuzi_duodi_t$t.png
done
```

在这台机器上，整片渲染加配音大约需要 2 分钟。

## 音频文件

- 逐句 mp3：`demos/audio/jiuzi_duodi/01_*.mp3 … 15_*.mp3`
- 对齐后的整轨：`demos/audio/jiuzi_duodi_narration.wav`（106 s）

## 镜头表（分镜）

由 `.venv/bin/python -m animasis shots demos/jiuzi_duodi.yaml --markdown` 生成。

| # | 时间 | 镜头 | 目标 | 运动 | 转场 | 说明 |
|---|---|---|---|---|---|---|
| 1 | 0.0–4.6s | wide (×1) | stage | cut | cut | 片头标题卡 |
| 2 | 4.6–6.2s | wide (×1) | stage | cut | fade | 远景·乾清宫，康熙立于御座前 |
| 3 | 6.2–8.6s | medium (×1.7) | kangxi | push 2.2s | cut | 缓推中景·康熙帝 |
| 4 | 8.6–8.8s | close (×2.4) | 52,116 | cut | cut | 近景·皇子们（左列） |
| 5 | 8.8–12.0s | close (×2.4) | 262,116 | pan 3.2s | cut | 横摇·九位皇子一一亮相 |
| 6 | 12.0–13.1s | wide (×1) | stage | pull 0.9s | cut | 拉远景·皇位只有一个 |
| 7 | 13.1–15.0s | medium (×1.7) | er_kid,kangxi_young | cut | fade | 中景·闪回 康熙十四年 |
| 8 | 15.0–16.8s | close (×2.4) | er_kid,kangxi_young | push 1.4s | cut | 缓推近景·授诏立储 |
| 9 | 16.8–18.4s | close (×2.4) | er_kid | cut | cut | 近景·小太子作揖 |
| 10 | 18.4–19.6s | full (×1.3) | er,kangxi | cut | fade | 全景·太子长大 |
| 11 | 19.6–22.4s | medium (×1.7) | er | push 1.6s | cut | 推中景·太子骄纵 |
| 12 | 22.4–23.0s | close (×2.4) | kangxi | cut | cut (reverse angle) | 反打近景·康熙震怒 |
| 13 | 23.0–23.5s | medium (×1.7) | er,kangxi | cut | cut | 中景·一废太子 |
| 14 | 23.5–24.8s | closeup (×3) | 172,138 | cut | cut | 特写·太子印落地弹跳 |
| 15 | 24.8–26.1s | medium (×1.7) | er | cut | cut | 中景·废太子跪地 |
| 16 | 26.1–26.6s | medium (×1.7) | da,san | cut | cut | 中景·大阿哥与三阿哥 |
| 17 | 26.6–28.6s | close (×2.4) | da | push 1.2s | cut | 推近景·巫蛊人偶 |
| 18 | 28.6–30.0s | close (×2.4) | san | cut | cut (reverse angle) | 反打·三阿哥揭发 |
| 19 | 30.0–32.5s | medium (×1.7) | da,san | cut | cut | 中景·圈禁之笼落下 |
| 20 | 32.5–35.8s | medium (×1.7) | dachen2,ba | cut | cut | 中景·大臣推举胤禩 |
| 21 | 35.8–37.2s | close (×2.4) | kangxi | cut | cut | 近景·康熙猜忌 |
| 22 | 37.2–39.4s | full (×1.3) | dachen2,kangxi | cut | cut | 全景·君臣对峙 |
| 23 | 39.4–42.6s | medium (×1.7) | er,kangxi | cut | cut | 中景·胤礽复立 |
| 24 | 42.6–43.4s | close (×2.4) | er | cut | cut | 近景·再废 |
| 25 | 43.4–44.4s | full (×1.3) | er,kangxi | cut | cut | 全景·太子被圈禁 |
| 26 | 44.4–46.1s | medium (×1.7) | 160,116 | push 1.4s | cut | 缓推·空悬的储位 |
| 27 | 46.1–46.9s | wide (×1) | stage | cut | fade | 远景·紫禁城宫院 |
| 28 | 46.9–50.0s | medium (×1.7) | shi,shisi | push 1.6s | cut | 推中景·八爷党 |
| 29 | 50.0–53.2s | close (×2.4) | ba,jiu | cut | cut | 近景·八阿哥振臂 |
| 30 | 53.2–56.6s | close (×2.4) | si | cut | cut | 近景·四阿哥念佛 |
| 31 | 56.6–59.4s | medium (×1.7) | si,shisan | pull 1s | cut | 中景·十三阿哥到来 |
| 32 | 59.4–61.0s | wide (×1) | stage | pull 1s | cut | 拉远景·两派暗斗 |
| 33 | 61.0–62.2s | wide (×1) | stage | cut | fade | 远景·西北边塞 |
| 34 | 62.2–65.2s | full (×1.3) | shisi | cut | cut | 全景跟拍·大军出征 |
| 35 | 65.2–67.2s | medium (×1.7) | shisi | cut | cut | 中景·十四阿哥振旗 |
| 36 | 67.2–69.9s | wide (×1) | stage | cut | fade | 卡片·康熙六十一年冬 |
| 37 | 69.9–70.6s | wide (×1) | stage | cut | fade | 远景·畅春园寝宫，烛火 |
| 38 | 70.6–72.9s | medium (×1.7) | kangxi | push 2s | cut | 缓推·病重的康熙 |
| 39 | 72.9–73.6s | wide (×1) | stage | cut | fade | 黑场·驾崩 |
| 40 | 73.6–74.8s | medium (×1.7) | longkeduo | cut | cut | 中景·隆科多宣遗命 |
| 41 | 74.8–75.8s | close (×2.4) | si | cut | cut | 近景·四阿哥 |
| 42 | 75.8–76.8s | close (×2.4) | ba,jiu | cut | cut | 近景·八、九阿哥愕然 |
| 43 | 76.8–77.9s | full (×1.3) | 160,112 | cut | cut | 全景·众人 |
| 44 | 77.9–78.6s | wide (×1) | stage | cut | fade | 远景·雍正登基，群臣行礼 |
| 45 | 78.6–81.2s | medium (×1.7) | yongzheng | push 2s | cut | 缓推·雍正帝 |
| 46 | 81.2–86.0s | wide (×1) | stage | cut | fade | 卡片·十改于 传说 |
| 47 | 86.0–87.0s | full (×1.3) | ba,jiu | cut | fade | 全景·黄昏宫院 |
| 48 | 87.0–89.6s | medium (×1.7) | ba,jiu | push 0.8s | cut | 推中景·八、九被圈禁 |
| 49 | 89.6–93.4s | full (×1.3) | shisi | cut | cut | 全景跟拍·十四去守陵 |
| 50 | 93.4–95.0s | medium (×1.7) | yongzheng | cut | fade | 中景·雍正手捧锦匣 |
| 51 | 95.0–97.6s | close (×2.4) | 160,52 | push 1.8s | cut | 上摇·正大光明匾 |
| 52 | 97.6–100.4s | closeup (×3) | 152,34 | push 1.2s | cut | 特写·匾后锦匣 |
| 53 | 100.4–106.0s | wide (×1) | stage | cut | fade | 结尾大事记卡 |


## 多角度体位（框架 API）

Animasis 角色除了左右 `facing: ±1`，还有 **`view`** 控制身体朝向（体位）：

| `view` | 别名 | 效果 |
|---|---|---|
| `side`（默认） | `侧` / `侧面` | 经典 3/4 侧影，走路/跳跃/递物 |
| `front` | `正` / `正面` / `正体位` | 正面朝向镜头；搭配 `pose: sit` 为坐姿皇帝 |
| `three_quarter` | `3/4` | 与 side 相同的 3/4 剪影 |
| `back` | `背` / `背面` | 背影（无五官，辫发居中） |

YAML 示例：

```yaml
characters:
  - { name: kangxi, view: front, pose: sit, y: 141, ... }   # 正体位坐御座
timeline:
  - { t: 0.0, action: view, target: kangxi, name: front }
  - { t: 0.0, action: pose, target: kangxi, name: sit }
  - { t: 22.2, action: view, target: kangxi, name: side }   # 切回侧影做 reach / walk
```

Python：`SceneBuilder(...).character("kangxi", view="front", pose="sit")` 或 `ch.set_view("正体位")`。
