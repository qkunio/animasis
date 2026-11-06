# Animasis

**EN** · Pixel animation toolkit for AI agents — skeleton, poses, light physics, YAML/JSON DSL, MP4/GIF export.  
**中文** · 面向 AI agent 的像素动画开发环境：骨架绑定、姿态库、轻量物理、场景 DSL、渲染导出。

---

## Quick Start | 快速开始

```bash
cd /workspace/animasis
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# needs ffmpeg on PATH for MP4

# Render one scene
animasis render demos/indoor_pickup.yaml -o demos/output/indoor_pickup.mp4

# Render all demos
python -m animasis.demos
# or: animasis demos
```

Requirements | 依赖: Python 3.11+, Pillow, PyYAML, ffmpeg (system). Optional: numpy.

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
| `demos/indoor_pickup.yaml` | Indoor: walk to a bouncing ball, pick it up, wave. / 室内捡球并挥手 |
| `demos/two_person_handoff.yaml` | Two people wave, approach, hand over a gift. / 两人互动递物 |
| `demos/outdoor_jump.yaml` | Outdoor run–jump with ball bounce physics. / 室外跳跃与弹跳物理 |

Outputs land in `demos/output/*.mp4`.

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
python -m animasis.demos
```

---

## License

MIT

---

## Story demo: 经济学科普「机会成本」

`demos/econ_opportunity_cost.yaml` → `demos/output/econ_opportunity_cost.mp4`：36 秒像素科普短片，用 `overlays:` 层（标题卡、字幕、价签、思考气泡、钱包 HUD、摊位道具）讲清机会成本。详见 [demos/econ_README.md](demos/econ_README.md)。重新渲染：`.venv/bin/python -m animasis render demos/econ_opportunity_cost.yaml -o demos/output/econ_opportunity_cost.mp4`

## Story demo: 三顾茅庐（edge-tts 中文旁白）

`demos/sangu_maolu.yaml` → `demos/output/sangu_maolu.mp4`：88 秒有声像素短片，刘备三请诸葛亮（草庐 / 雪天 / 春日三种背景，关羽、张飞、书童配角），旁白为 edge-tts `zh-CN-YunxiNeural`。带相机分镜：33 个镜位，包括远景、中景、近景和特写，以及推拉摇、硬切、黑场和反打视角，由 YAML `camera:` 关键帧控制，可用 `animasis shots` 打印镜头表。详见 [demos/sangu_maolu_README.md](demos/sangu_maolu_README.md)。重新渲染：`.venv/bin/python -m animasis narrate demos/sangu_maolu.yaml -o demos/output/sangu_maolu.mp4`

## Story demo: 九子夺嫡（多角度体位 + edge-tts 旁白）

`demos/jiuzi_duodi.yaml` → `demos/output/jiuzi_duodi.mp4`：清史像素短片。开场康熙用 `view: front` + `pose: sit` 正体位坐于御座；行走/物理场景仍用默认 `side`。详见 [demos/jiuzi_duodi_README.md](demos/jiuzi_duodi_README.md)。

## Story demo: GNSS 卫星导航科普（相机分镜 + edge-tts 旁白）

`demos/gnss_intro.yaml` → `demos/output/gnss_intro.mp4`：89 秒有声像素科普，讲什么是 GNSS、四大系统、卫星发信号 → 接收机测距 → 多星定位、为什么至少要 4 颗卫星，最后带一下民用用途。画面包括自转地球与卫星星座、手机地图特写和测距示意图，共 53 个镜位。旁白为 `zh-CN-YunxiNeural`。详见 [demos/gnss_README.md](demos/gnss_README.md)。重新渲染：`.venv/bin/python -m animasis narrate demos/gnss_intro.yaml -o demos/output/gnss_intro.mp4`
