# Animasis

**EN** · Pixel animation toolkit for AI agents — skeleton, poses, light physics, YAML/JSON DSL, MP4/GIF export, and social publishing.
**中文** · 面向 AI agent 的像素动画全流程环境：骨架绑定、姿态库、轻量物理、场景 DSL、渲染配音、封面与多平台发布。

---

## Quick Start | 快速开始

```bash
cd /workspace/animasis
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# needs ffmpeg on PATH for MP4

# Render one scene
animasis render demos/econ_opportunity_cost.yaml -o demos/output/econ_opportunity_cost.mp4

# Render all demos
python -m animasis.demos
# or: animasis demos
```

Requirements | 依赖: Python 3.11+, Pillow, PyYAML, ffmpeg (system). Optional: numpy；自动发布使用 `.[publish]` 额外依赖与 Patchright Chromium。

---

## Architecture | 架构

```
skeleton → pose → physics → composite → export
   │         │        │          │          └─ MP4 (ffmpeg) / GIF (Pillow)
   │         │        │          └─ palette + nearest-neighbor upscale
   │         │        └─ gravity / AABB / bounce / held attachments
   │         └─ idle / walk / jump / wave / pickup / …
   └─ bones + face + apparel hang points
```

| Layer | Module | Role |
|-------|--------|------|
| Skeleton | `skeleton.py` | Humanoid bones, joint angles, attach points |
| Face / apparel | `face.py`, `apparel.py` | Expressions, hats, props on hang points |
| Pose | `poses.py` | Library + cycle blending (no broken limbs) |
| Physics | `physics.py` | Gravity, ground/wall collision, restitution |
| Sprite | `sprite.py` | Capsule-limb rasteriser, 3-tone shading, layered hair/clothes, soft outline |
| Render | `render.py` | Fixed 33-color palette (light/base/shade ramps), NN scale, export |
| DSL | `scene.py`, `builder.py` | YAML/JSON scenes + Python fluent builder |
| CLI | `cli.py` | `animasis render scene.yaml -o out.mp4` |
| Publishing | `publishing/`, `publishing/_sau/` | `animasis publish` / `sau`：账号登录、视频/图文发布、定时发布 |

---

## DSL Example | DSL 示例

```yaml
name: hello
width: 320
height: 180
fps: 12
duration: 3.0
background: outdoor   # indoor | outdoor | room
ground_y: 150
scale: 3

characters:
  - name: hero
    x: 40
    cloth: blue
    pants: red
    hat: gold
    expression: happy
    # view: front   # 正体位 (also: side | 3/4 | back); facing: ±1 still mirrors side views

objects:
  - name: ball
    kind: ball
    x: 160
    y: 40
    bounce: 0.65
    color: orange

timeline:
  - { t: 0.0, action: walk_to, target: hero, x: 140, speed: 50 }
  - { t: 1.5, action: jump, target: hero, vy: -220 }
  - { t: 2.0, action: pickup, target: hero, object: ball }
```

### Python builder | Python 构建器

```python
from animasis import SceneBuilder

SceneBuilder("hi") \
    .background("outdoor").ground(150).duration(3) \
    .character("hero", x=40, cloth="blue", hat="gold") \
    .object("ball", x=160, y=40) \
    .at(0.0, "walk_to", "hero", x=140, speed=50) \
    .at(1.5, "jump", "hero", vy=-220) \
    .render("out.mp4")
```

### Timeline actions | 时间轴动作

`pose` · `cycle` · `expression` · `face` · `view` · `move` · `walk_to` · `jump` · `pickup` · `drop` · `give` · `impulse` · `say`

Character presets | 角色预设: `hero`, `alice`, `bob`, `runner`, `kid` (`preset:`; override with `hair_style` short/spiky/long/bob/ponytail/buzz/queue/topknot, `body` default/slim/stocky, `skin` light/medium/tan, `cloth`, `pants`, `hair`, `shoes`, `skirt`, `sleeves`, `belt`, `hat`)  
Body view / 体位 | `view:` `side` (default 3/4), `front` / `正` / `正面` / `正体位`, `three_quarter` / `3/4`, `back` / `背` — also timeline action `view` and `face: {view: …}`  
Built-in poses | 内置姿态: `idle`, `walk_a/b`, `walk_pass_a/b`, `jump`, `crouch`, `land`, `wave`, `pickup`, `reach`, `give`, `receive`, `sit`, `sit_wave`, `bow`, `knock`, `hold`  
Cycles | 循环: `idle`, `walk`, `wave`, `jump`, `pickup`, `sit`

---

## Demos | 演示场景

| File | One-liner |
|------|-----------|
| `demos/econ_opportunity_cost.yaml` | 经济学科普「机会成本」 |
| `demos/sangu_maolu.yaml` | 历史故事「三顾茅庐」，带中文旁白与相机分镜 |
| `demos/jiuzi_duodi.yaml` | 清史短片「九子夺嫡」，带多角度体位与中文旁白 |
| `demos/gnss_intro.yaml` | GNSS 卫星导航科普，带中文旁白与相机分镜 |
| `demos/petroleum.yaml` | 石油科普：原油分馏与石油化工 |

Outputs land in `demos/output/*.mp4`.

### 短片开头与结尾规范

以 GNSS（`demos/gnss_intro.yaml`）的前后格式为准：

- 一进入画面就直入主题，用有吸引力的内容引入。
- 不要标题栏或开场标题卡。
- 结尾只保留本片标题和 `@像素万物局` 两行字。

### 旁白默认音色

默认使用 edge-tts 云健音色 `zh-CN-YunjianNeural`。可通过 YAML 的 `narration.voice` 或单句 `voice` 覆盖。

---

## Aesthetic defaults | 审美默认

- Unified 33-color retro palette (16 base + shading ramps) (`animasis.palette.PALETTE`)
- Readable silhouettes with dark outlines
- Face presets that stay simple (not uncanny)
- Pose angles constrained so limbs do not fold backward
- Nearest-neighbor upscale keeps crisp pixels

---

## CLI

```bash
animasis render scene.yaml -o out.mp4
animasis render scene.json -o out.gif --scale 4
animasis poses
animasis demos -o demos/output
animasis publish douyin --help
sau --help
python -m animasis.demos
```

---

## Publish | 从成片到多平台发布

Animasis 内置 [social-auto-upload](https://github.com/dreammis/social-auto-upload)（SAU）主线运行时，将 `render` / `narrate` 生成的视频直接发布到抖音、快手、小红书、Bilibili、视频号、YouTube 等平台。抖音上传包含 [PR #305](https://github.com/dreammis/social-auto-upload/pull/305) 的 `bypass_csp=True` 修复，解决上传 Worker 被 CSP 拦截的问题。

### 1. 安装发布依赖

```bash
pip install -e ".[publish]"
patchright install chromium
```

发布功能与 SAU 一样支持 Python 3.11–3.12；仅渲染动画时仍使用项目的 Python 3.11+ 要求。

### 2. 生成成片并登录

```bash
animasis narrate demos/jiuzi_duodi.yaml -o demos/output/jiuzi_duodi.mp4
animasis publish douyin login --account creator --headed
animasis publish douyin check --account creator
```

登录二维码由 SAU 生成并展示。`--account` 是本地账号别名，不要求与平台昵称相同。`sau douyin ...` 与 `animasis publish douyin ...` 等价，可按习惯选择。

### 3. 发布视频、封面和话题

```bash
animasis publish douyin upload-video \
  --account creator \
  --file demos/output/jiuzi_duodi.mp4 \
  --title "106秒看懂九子夺嫡" \
  --desc "从两废太子到雍正继位，用像素动画梳理康熙晚年九子夺嫡的始末。" \
  --tags "vibe知识大赏,九子夺嫡,历史,像素动画,雍正" \
  --thumbnail demos/covers/jiuzi_duodi.png
```

不传 `--schedule` 时立即提交发布；平台受理后可能仍处于审核中。其他平台的登录、发布和定时参数通过 `animasis publish <platform> --help` 查看。

Cookie、日志和短信验证码默认保存在当前项目的 `.animasis/sau/`，该目录已加入 `.gitignore`，不要提交账号文件。可用 `ANIMASIS_SAU_HOME` 指定其他运行目录。发布过程中如需短信验证码，可写入 `.animasis/sau/verify_code.txt`，验证后程序会自动清理。

SAU 源码位于 `animasis/publishing/_sau/`，基于上游 `3847fff` 并包含上述 CSP 修复；其 MIT 许可证保留在同目录的 `LICENSE` 中。

---

## License

MIT。内置 SAU 的独立许可证见 `animasis/publishing/_sau/LICENSE`。

---

## Story demo: 经济学科普「机会成本」

`demos/econ_opportunity_cost.yaml` → `demos/output/econ_opportunity_cost.mp4`：36 秒像素科普短片，用 `overlays:` 层（标题卡、字幕、价签、思考气泡、钱包 HUD、摊位道具）讲清机会成本。详见 [demos/econ_README.md](demos/econ_README.md)。重新渲染：`.venv/bin/python -m animasis render demos/econ_opportunity_cost.yaml -o demos/output/econ_opportunity_cost.mp4`

## Story demo: 三顾茅庐（edge-tts 中文旁白）

`demos/sangu_maolu.yaml` → `demos/output/sangu_maolu.mp4`：88 秒有声像素短片，刘备三请诸葛亮（草庐 / 雪天 / 春日三种背景，关羽、张飞、书童配角），旁白为 edge-tts `zh-CN-YunjianNeural`。带相机分镜：33 个镜位，包括远景、中景、近景和特写，以及推拉摇、硬切、黑场和反打视角，由 YAML `camera:` 关键帧控制，可用 `animasis shots` 打印镜头表。详见 [demos/sangu_maolu_README.md](demos/sangu_maolu_README.md)。重新渲染：`.venv/bin/python -m animasis narrate demos/sangu_maolu.yaml -o demos/output/sangu_maolu.mp4`

## Story demo: 九子夺嫡（多角度体位 + edge-tts 旁白）

`demos/jiuzi_duodi.yaml` → `demos/output/jiuzi_duodi.mp4`：清史像素短片。开场康熙用 `view: front` + `pose: sit` 正体位坐于御座；行走/物理场景仍用默认 `side`。详见 [demos/jiuzi_duodi_README.md](demos/jiuzi_duodi_README.md)。

## Story demo: GNSS 卫星导航科普（相机分镜 + edge-tts 旁白）

`demos/gnss_intro.yaml` → `demos/output/gnss_intro.mp4`：82 秒有声像素科普，没有标题卡，结尾只有“全球导航定位系统（GNSS） / @像素万物局”两行字。讲什么是 GNSS、四大系统、卫星发信号 → 接收机测距 → 多星定位、为什么至少要 4 颗卫星，最后带一下民用用途。画面包括自转地球与卫星星座、手机地图特写和测距示意图，共 52 个镜位。旁白为 `zh-CN-YunjianNeural`。详见 [demos/gnss_README.md](demos/gnss_README.md)。重新渲染：`.venv/bin/python -m animasis narrate demos/gnss_intro.yaml -o demos/output/gnss_intro.mp4`

## Story demo: 石油科普「一桶石油，能变出多少东西？」（原油分馏 + 石油化工）

`demos/petroleum.yaml` → `demos/output/petroleum.mp4`：95 秒有声像素科普，冷开场用油滴坠落 + 逐字大字抓人，字幕与旁白逐句对齐，结尾只有“一桶石油，半个现代生活 / @像素万物局”两行字。讲原油是上千种碳氢化合物的混合物、分馏塔如何按沸点分出 6 大馏分、一桶 159 升原油大致能产出多少汽油/柴油/航煤，以及石脑油 → 乙烯 → 聚乙烯 → 塑料瓶的裂解聚合链条，最后用 12 个产品组成一面“石油产品墙”。共 45 个镜位，旁白为 `zh-CN-YunjianNeural`。详见 [demos/petroleum_README.md](demos/petroleum_README.md)。重新渲染：`python -m animasis narrate demos/petroleum.yaml -o demos/output/petroleum.mp4`
