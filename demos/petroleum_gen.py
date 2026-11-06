"""Generator for demos/petroleum.yaml — 一桶石油，能变出多少东西？

    python demos/petroleum_gen.py
    python -m animasis narrate demos/petroleum.yaml -o demos/output/petroleum.mp4

Narration (edge-tts zh-CN-YunjianNeural +5%) is written into the scene; the visual beats
below follow the synthesized line lengths (~92 s total).
"""
from __future__ import annotations

import re
import yaml
from pathlib import Path

F = lambda **k: k  # noqa: E731

# ------------------------------------------------------------------ narration
LINES = [
    (0.8, "一桶石油，究竟能变出多少东西？"),
    (5.2, "一桶原油，黑乎乎、黏糊糊，看起来平平无奇。"),
    (11.0, "可它其实是上千种碳氢化合物的混合物，沸点各不相同。"),
    (17.2, "送进分馏塔，加热到约 400 摄氏度，油气一路往上。"),
    (23.2, "越往上越冷：沸点高的先凝，沸点低的继续爬。"),
    (28.8, "塔顶是石油气，往下是汽油、煤油、柴油，塔底是重油——沥青就来自它。"),
    (37.2, "一桶 159 升。以美国炼厂为例：约 46% 汽油，30% 柴油，11% 航空煤油。"),
    (47.2, "但分馏只是第一步。真正的魔法，是把馏分拆开再重组。"),
    (53.4, "石脑油裂解成乙烯，乙烯再聚合成聚乙烯——塑料瓶就是这么来的。"),
    (61.4, "同样的碳和氢，还能变成涤纶衣服、橡胶轮胎、油漆、洗涤剂、阿司匹林和口红。"),
    (70.6, "从燃料到塑料、化纤、橡胶、药品、化妆品，再到沥青路，石油能变出上千种产品。"),
    (80.8, "一桶石油里装的不只是能量，还有半个现代生活。"),
    (86.6, "下一次加油时，别忘了看看周围——你正站在石油里。"),
]
# measured edge-tts durations for the 13 lines above (seconds)
DUR = [3.48, 5.26, 5.47, 5.28, 4.90, 7.61, 8.90, 5.64, 5.62, 8.14, 8.88, 4.78, 4.63]

ov: list[dict] = []
cam: list[dict] = []
tl: list[dict] = []

# ================================================================== 冷开场 (0–5.0)
ov += [
    F(kind="droplet", t=0.0, until=0.72, x=160, y=96, y0=-8, fall=0.62, r=22, color=1, edge=3),
    F(kind="splash", t=0.65, until=1.35, x=160, y=104, n=20, power=70),
    F(kind="text", t=0.80, until=5.0, x=160, y=44, text="一桶石油", size=28,
      color=7, outline=16, bold=True, reveal=9),
    F(kind="text", t=1.45, until=5.0, x=160, y=84, text="究竟能变出多少东西？", size=18,
      color=4, outline=16, bold=True, reveal=9),
]
cam += [
    F(t=0.0, shot="close", zoom=2.4, target=[160, 30], move=0.15, name="冷开场·油滴"),
    F(t=0.15, shot="close", zoom=2.3, target=[160, 60], move=0.5, ease="in", name="跟拍·油滴下落"),
    F(t=0.65, shot="close", zoom=2.2, target=[160, 92], move=0.1, name="近景·溅开"),
    F(t=0.75, shot="full", zoom=1.45, target=[160, 88], move=0.45, ease="out", name="拉远·大字"),
    F(t=1.60, shot="full", zoom=1.4, target=[160, 92], move=1.0, name="缓推·问题"),
    F(t=2.70, shot="full", zoom=1.35, target=[160, 82], move=1.4, name="缓推·问题"),
    F(t=4.20, shot="full", zoom=1.25, target=[160, 78], move=1.5, name="缓推·悬念"),
]
tl += [
    F(t=0.0, action="background", name="blueprint"),
    F(t=5.0, action="background", name="oilfield"),
    F(t=5.0, action="show", target="xiaoke"),
]

# ================================================================== A · 油田与一桶原油 (5.0–11.0)
ov += [
    F(kind="pumpjack", t=5.0, until=11.0, x=250, y=150, scale=1.5, period=3.4),
    F(kind="barrel", t=5.0, until=11.0, x=96, y=150, scale=1.2),
    F(kind="tag", t=5.8, until=11.0, x=96, y=104, space="world", text="原油", bg=25, color=4),
    F(kind="tag", t=8.4, until=11.0, x=250, y=84, space="world", text="抽油机", bg=2, color=4),
    F(kind="caption", t=5.4, until=8.2, text="一桶原油，看起来平平无奇", reveal=12),
    F(kind="caption", t=8.2, until=11.0, text="黑乎乎 · 黏糊糊", reveal=12, color=31),
]
cam += [
    F(t=5.0, shot="wide", transition="fade", fade=0.25, name="转场·油田与一桶原油"),
    F(t=6.4, shot="close", zoom=2.0, target=[96, 122], move=1.2, name="近景·油桶"),
    F(t=8.4, shot="medium", target="xiaoke", offset=[0, -6], move=1.0, name="中景·小科"),
    F(t=9.6, shot="wide", move=1.2, name="拉远·油田全景"),
]
tl += [
    F(t=5.0, action="walk_to", target="xiaoke", x=158, speed=55),
    F(t=8.4, action="face", target="xiaoke", dir=-1),
    F(t=8.8, action="pose", target="xiaoke", name="idle"),
    F(t=8.8, action="expression", target="xiaoke", name="happy"),
    F(t=9.6, action="cycle", target="xiaoke", name="wave", speed=1.3),
    F(t=10.5, action="pose", target="xiaoke", name="idle"),
]

# ================================================================== B · 它是混合物 (11.0–17.0)
ov += [
    F(kind="droplet", t=11.0, until=17.0, x=64, y=94, r=26, color=1, edge=3),
    F(kind="molecule", t=11.4, until=17.0, x=150, y=58, n=3, scale=1.4, grow=0.8),
    F(kind="molecule", t=11.8, until=17.0, x=205, y=74, n=5, scale=1.3, grow=0.9),
    F(kind="molecule", t=12.2, until=17.0, x=258, y=56, n=7, scale=1.2, grow=1.0),
    F(kind="molecule", t=12.6, until=17.0, x=188, y=112, style="ring", scale=1.5),
    F(kind="molecule", t=13.0, until=17.0, x=258, y=120, n=9, scale=1.1, grow=1.0),
    F(kind="text", t=11.8, until=17.0, x=150, y=80, space="world", text="C4H10", size=10, color=31, outline=16),
    F(kind="text", t=12.2, until=17.0, x=205, y=92, space="world", text="C8H18", size=10, color=31, outline=16),
    F(kind="text", t=12.6, until=17.0, x=188, y=130, space="world", text="苯环", size=10, color=3, outline=16),
    F(kind="text", t=13.2, until=17.0, x=258, y=128, space="world", text="C20H42", size=10, color=31, outline=16),
    F(kind="caption", t=11.2, until=13.8, text="它不是一种物质", reveal=12),
    F(kind="caption", t=13.8, until=17.0, text="而是上千种碳氢化合物的混合物", reveal=12, color=31),
]
cam += [
    F(t=11.0, shot="wide", transition="fade", fade=0.5, name="远景·一滴原油"),
    F(t=11.6, shot="close", zoom=2.2, target=[64, 94], move=1.4, name="推近·油滴"),
    F(t=13.4, shot="medium", zoom=1.7, target=[205, 88], move=1.8, name="横摇·分子群"),
    F(t=15.4, shot="wide", move=1.0, name="拉远·混合物"),
]
tl += [F(t=11.0, action="hide", target="xiaoke"), F(t=11.0, action="background", name="blueprint")]

# ================================================================== C · 分馏塔 (17.0–37.0)
CUTS = [
    F(top=True, text="石油气 <40°C", color=7, t=29.0),
    F(at=0.78, text="汽油 40–180°C", color=30, t=29.7),
    F(at=0.60, text="煤油 180–250°C", color=9, t=30.4),
    F(at=0.42, text="柴油 250–350°C", color=6, t=31.1),
    F(at=0.24, text="重油 >350°C", color=27, t=31.8),
    F(bottom=True, text="沥青 · 渣油深加工", color=2, t=32.5),
]
ov += [
    F(kind="column", t=17.0, until=37.0, x=100, y=150, w=42, h=112, label_x=156, cuts=CUTS),
    F(kind="caption", t=17.3, until=21.0, text="加热到约 400°C，原油汽化", reveal=12),
    F(kind="caption", t=21.0, until=25.0, text="油气上升，塔内越往上越冷", reveal=12),
    F(kind="caption", t=25.0, until=28.8, text="沸点高的先冷凝，沸点低的继续爬", reveal=12),
    F(kind="caption", t=28.8, until=33.0, text="不同高度 → 不同馏分", reveal=12, color=31),
    F(kind="caption", t=33.0, until=37.0, text="分馏是物理过程：一次得到 6 大馏分", reveal=12, color=31),
]
cam += [
    F(t=17.0, shot="wide", transition="fade", fade=0.5, name="远景·分馏塔"),
    F(t=17.5, shot="medium", zoom=1.8, target=[88, 138], move=1.5, name="中景·加热炉"),
    F(t=20.0, shot="medium", zoom=1.5, target=[112, 118], move=2.6, ease="linear", name="沿塔身上摇"),
    F(t=24.0, shot="full", zoom=1.3, target=[130, 95], move=2.0, name="全景·塔内上升"),
    F(t=28.5, shot="full", zoom=1.25, target=[140, 90], move=1.0, name="全景·各层馏分"),
    F(t=33.0, shot="medium", zoom=1.3, target=[145, 122], move=1.5, name="下摇·重油与沥青"),
    F(t=35.5, shot="wide", zoom=1.15, target=[150, 92], move=1.0, name="拉远·六大馏分"),
]

# ================================================================== D · 一桶能出多少 (37.0–47.0)
ov += [
    F(kind="barrel", t=37.0, until=47.0, x=54, y=150, scale=2.0),
    F(kind="cutbar", t=37.0, until=47.0, x=84, y=100, w=196, h=20, grow=0.7, stagger=0.9,
      show_labels=False,
      segments=[F(label="汽油", pct=46, color=30), F(label="柴油", pct=30, color=6),
                F(label="航空煤油", pct=11, color=9), F(label="其他", pct=13, color=11)]),
    F(kind="text", t=37.2, until=47.0, x=84, y=56, space="world", text="一桶原油 = 159 升",
      size=14, color=7, outline=16, bold=True, align="left"),
    F(kind="text", t=37.6, until=47.0, x=84, y=74, space="world", text="约 45 加仑成品油",
      size=9, color=3, outline=16, align="left"),
    F(kind="text", t=37.6, until=47.0, x=84, y=88, space="world",
      text="以美国炼厂 2023 年数据为例 · 体积占比", size=8, color=3, outline=16, align="left"),
    F(kind="tag", t=41.4, until=47.0, x=116, y=124, space="world", text="汽油 46%", bg=30, color=4),
    F(kind="tag", t=41.4, until=47.0, x=222, y=124, space="world", text="柴油 30%", bg=6, color=4),
    F(kind="tag", t=42.2, until=47.0, x=116, y=138, space="world", text="航空煤油 11%", bg=9, color=4),
    F(kind="tag", t=42.2, until=47.0, x=222, y=138, space="world", text="其他 13%", bg=11, color=4),
    F(kind="caption", t=37.2, until=41.0, text="一桶 159 升，能炼出什么？", reveal=12),
    F(kind="caption", t=41.0, until=44.0, text="大部分会变成燃料", reveal=12, color=31),
    F(kind="caption", t=44.0, until=47.0, text="各国炼厂结构不同，比例会有差异", reveal=12, color=3),
]
cam += [
    F(t=37.0, shot="wide", transition="fade", fade=0.5, name="远景·一桶原油的产出"),
    F(t=37.8, shot="close", zoom=1.25, target=[160, 110], move=1.2, name="近景·产量条形图"),
    F(t=40.6, shot="full", zoom=1.2, target=[160, 108], move=1.0, name="全景·四大去向"),
    F(t=44.0, shot="wide", move=1.0, name="拉远·比例仅供参考"),
]

# ================================================================== E · 裂解与聚合 (47.0–61.0)
ov += [
    F(kind="molecule", t=47.0, until=52.8, x=60, y=64, n=9, scale=1.2, grow=1.0),
    F(kind="tag", t=47.6, until=51.6, x=60, y=86, space="world", text="石脑油 长链烃", bg=25, color=4),
    F(kind="force", t=47.8, until=52.8, x=96, y=64, dir="right", length=22, color=7, grow=0.5),
    F(kind="text", t=48.0, until=52.8, x=126, y=46, space="world", text="裂解 850°C",
      size=10, color=6, outline=16, bold=True),
    F(kind="molecule", t=49.4, until=56.2, x=150, y=58, n=2, scale=1.6, double=True),
    F(kind="molecule", t=49.8, until=56.2, x=150, y=86, n=2, scale=1.6, double=True),
    F(kind="tag", t=50.0, until=55.8, x=150, y=104, space="world", text="乙烯 C2H4", bg=30, color=4),
    F(kind="force", t=50.8, until=56.2, x=174, y=74, dir="right", length=22, color=7, grow=0.5),
    F(kind="text", t=51.2, until=56.2, x=205, y=48, space="world", text="聚合",
      size=10, color=30, outline=16, bold=True),
    F(kind="molecule", t=52.6, until=60.0, x=255, y=72, n=8, scale=1.1, poly=True, grow=1.5),
    F(kind="tag", t=53.4, until=60.0, x=255, y=96, space="world", text="聚乙烯", bg=30, color=4),
    F(kind="product", t=54.2, until=61.0, x=282, y=128, name="bottle", label="塑料瓶", scale=2),
    F(kind="caption", t=47.4, until=50.0, text="分馏只是第一步", reveal=12),
    F(kind="caption", t=50.0, until=53.4, text="裂解：长链断成短链", reveal=12, color=31),
    F(kind="caption", t=53.4, until=56.4, text="聚合：短链变高分子", reveal=12, color=31),
    F(kind="caption", t=56.4, until=61.0, text="塑料瓶就是这么来的", reveal=12, color=7),
]
cam += [
    F(t=47.0, shot="wide", transition="fade", fade=0.5, name="远景·分馏之后"),
    F(t=47.6, shot="close", zoom=2.0, target=[62, 66], move=1.0, name="近景·长链烃"),
    F(t=49.6, shot="medium", zoom=1.7, target=[150, 74], move=1.8, name="横摇·乙烯"),
    F(t=52.8, shot="medium", zoom=1.7, target=[205, 76], move=2.0, name="横摇·聚乙烯"),
    F(t=56.0, shot="close", zoom=2.2, target=[282, 126], move=1.2, name="近景·塑料瓶"),
    F(t=58.4, shot="wide", zoom=1.15, target=[170, 90], move=1.2, name="拉远·从油到塑料"),
]

# ================================================================== F · 产品墙 (61.0–80.0)
PRODUCTS = [
    ("bottle", "塑料瓶", 36, 66), ("shirt", "涤纶衣服", 84, 66),
    ("tire", "橡胶轮胎", 132, 66), ("phonecase", "手机壳", 180, 66),
    ("paint", "油漆", 228, 66), ("detergent", "洗涤剂", 276, 66),
    ("pill", "阿司匹林", 36, 118), ("lipstick", "口红", 84, 118),
    ("road", "沥青路", 132, 118), ("mask", "口罩", 180, 118),
    ("cable", "电缆", 228, 118), ("film", "保鲜膜", 276, 118),
]
for name, label, px, py in PRODUCTS:
    ov.append(F(kind="product", t=61.0, until=80.0, x=px, y=py, name=name, label=label, scale=2))
ov += [
    F(kind="text", t=61.0, until=62.0, x=160, y=24, space="world", text="石油化工产品",
      size=11, color=7, outline=16, bold=True),
    F(kind="caption", t=61.4, until=64.0, text="同样的碳和氢", reveal=12),
    F(kind="caption", t=64.0, until=67.2, text="涤纶衣服 · 橡胶轮胎 · 油漆 · 洗涤剂", reveal=12, color=31),
    F(kind="caption", t=67.2, until=70.4, text="阿司匹林 · 口红 · 沥青路", reveal=12, color=31),
    F(kind="caption", t=70.6, until=74.0, text="塑料 · 化纤 · 橡胶 · 药品 · 化妆品", reveal=12, color=7),
    F(kind="caption", t=74.0, until=76.6, text="……还有上千种产品", reveal=12, color=7),
    F(kind="caption", t=76.6, until=80.0, text="不只是燃料，更是原材料", reveal=12, color=31),
]
cam += [
    F(t=61.0, shot="wide", transition="fade", fade=0.5, name="远景·产品墙"),
    F(t=61.4, shot="close", zoom=2.0, target=[84, 70], move=1.0, name="近景·涤纶衣服"),
    F(t=63.0, shot="close", zoom=2.0, target=[156, 70], move=1.6, name="横摇·轮胎与油漆"),
    F(t=64.8, shot="close", zoom=2.0, target=[228, 70], move=1.2, name="近景·洗涤剂"),
    F(t=66.2, shot="close", zoom=2.0, target=[60, 122], move=1.6, name="下摇·阿司匹林与口红"),
    F(t=68.4, shot="medium", zoom=1.7, target=[190, 122], move=2.0, name="横摇·沥青与口罩"),
    F(t=70.6, shot="wide", zoom=1.1, target=[160, 100], move=0.8, name="拉远·整面产品墙"),
    F(t=74.0, shot="full", zoom=1.1, target=[160, 100], move=2.0, name="缓推·上千种产品"),
    F(t=77.5, shot="wide", move=1.2, name="拉远·不只是燃料"),
]
tl += [F(t=61.0, action="background", name="shelf")]

# ================================================================== G · 结尾 (80.0–86.0)
ov += [
    F(kind="pumpjack", t=80.0, until=95.0, x=250, y=150, scale=1.5, period=3.4),
    F(kind="barrel", t=80.0, until=95.0, x=100, y=150, scale=1.4),
]
cam += [
    F(t=80.0, shot="closeup", zoom=2.6, target=[100, 118], transition="fade", fade=0.4, name="特写·油桶"),
    F(t=80.8, shot="wide", move=3.5, ease="out", name="拉远·油田落日"),
    F(t=85.0, shot="wide", move=0.8, name="缓推·半个现代生活"),
    F(t=89.0, shot="full", zoom=1.15, target=[160, 105], move=3.0, name="缓推·一桶石油"),
]
tl += [
    F(t=80.0, action="background", name="oilfield"),
    F(t=80.0, action="show", target="xiaoke"),
    F(t=80.0, action="move", target="xiaoke", x=164),
    F(t=80.0, action="pose", target="xiaoke", name="idle"),
    F(t=80.0, action="expression", target="xiaoke", name="happy"),
    F(t=80.0, action="face", target="xiaoke", dir=1),
]

# ================================================================== subtitles + ending
# Strip the old descriptive captions; rebuild exact subtitle chunks from the narration lines.
ov = [o for o in ov if o.get("kind") != "caption"]


def _chunks(text: str, maxlen: int = 22) -> list[str]:
    parts = [p.strip() for p in re.findall(r"[^。；：，、—]+[。；：，、—]?", text) if p.strip()]
    out: list[str] = []
    cur = ""
    for part in parts:
        if cur and len(cur) + len(part) > maxlen:
            out.append(cur)
            cur = part
        else:
            cur += part
    if cur:
        out.append(cur)
    return out


for idx, ((t, text), dur) in enumerate(zip(LINES, DUR)):
    if idx == 0:
        continue  # the cold-open kinetic type is the subtitle for the hook line
    chunks = _chunks(text)
    weights = [max(1, len(c.replace(" ", ""))) for c in chunks]
    total = sum(weights) or 1
    acc = 0.0
    for c, w in zip(chunks, weights):
        st = t + dur * acc / total
        acc += w
        en = t + dur * acc / total - 0.04
        ov.append(F(kind="caption", t=st, until=en, text=c, size=12, color=4, reveal=0))

ov.append(F(kind="card", t=91.3, until=95.0, bg=25, items=[
    F(text="一桶石油，半个现代生活", size=20, color=7),
    F(text="@像素万物局", size=14, color=31, at=0.6),
]))

scene = dict(
    name="petroleum",
    width=320, height=180, fps=30, duration=95.0, background="oilfield",
    ground_y=150, scale=3, gravity=420,
    characters=[F(name="xiaoke", preset="hero", x=-16, hat=7, cloth=10, pants=25,
                  hair=24, hair_style="short", expression="neutral", visible=False)],
    narration=F(voice="zh-CN-YunjianNeural", rate="+5%",
                lines=[F(t=t, text=text) for t, text in LINES]),
    camera=cam, overlays=ov, timeline=tl,
)

hdr = """# 石油科普 · 一桶石油，能变出多少东西？
# 有声成片：
#   python -m animasis narrate demos/petroleum.yaml -o demos/output/petroleum.mp4
# 镜头表：
#   python -m animasis shots demos/petroleum.yaml --markdown
# 段落：冷开场 | A 油田与原油 | B 碳氢化合物 | C 分馏塔（6 大馏分）| D 一桶的产出 |
#       E 裂解→乙烯→聚乙烯 | F 产品墙 | G 结尾 | 两行字结尾卡
"""


class Flow(yaml.SafeDumper):
    pass


def repr_list(dumper, data):
    flow = all(not isinstance(v, (dict, list)) for v in data)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow)


def repr_dict(dumper, data):
    flow = all(not isinstance(v, (dict,)) and not (isinstance(v, list) and any(isinstance(i, dict) for i in v))
               for v in data.values())
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items(), flow_style=flow)


Flow.add_representer(list, repr_list)
Flow.add_representer(dict, repr_dict)
out = hdr + yaml.dump(scene, Dumper=Flow, allow_unicode=True, sort_keys=False, width=220)
Path(__file__).with_name("petroleum.yaml").write_text(out, encoding="utf-8")
print(f"overlays={len(ov)} camera={len(cam)} timeline={len(tl)}")
