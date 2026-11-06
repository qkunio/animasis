"""Generator for demos/gnss_intro.yaml (computes the trilateration geometry, then writes the scene).

    .venv/bin/python demos/gnss_intro_gen.py && .venv/bin/python -m animasis narrate demos/gnss_intro.yaml -o demos/output/gnss_intro.mp4
"""
import math, re, sys, yaml
# narration script (one line per beat; edge-tts zh-CN-YunjianNeural +5%)
LINES = [
 "打开手机地图，小蓝点立刻知道你在哪儿。它靠的，是天上的卫星。",
 "GNSS 是全球卫星导航系统的统称：几十颗卫星，在两万多公里的高空绕着地球飞行。",
 "它有四大成员：美国的 GPS、中国的北斗、俄罗斯的格洛纳斯，还有欧洲的伽利略。",
 "每颗卫星都带着极其精准的原子钟，不停地广播：我是谁，现在几点。",
 "手机里的接收机收到信号，用收到的时间减去发出的时间，再乘以光速，就得到了到这颗卫星的距离。",
 "只知道一颗卫星的距离，你可能在一个大圆上的任何地方。",
 "加上第二颗，范围缩小到两个交点；第三颗，就能锁定位置。",
 "可手机的时钟不够精准，还需要第四颗卫星来校正时间。",
 "经度、纬度、高度，再加上时间，四个未知数，所以至少要四颗卫星。",
 "如今，开车导航、外卖骑手、共享单车、测绘和授时，都离不开 GNSS。",
 "看不见的卫星，正时时刻刻告诉你：你在这里。",
]

R = (160, 110); A = (100, 82); B = (220, 82); C = (130, 65); D = (205, 70)
d = lambda p, q: round(math.hypot(p[0]-q[0], p[1]-q[1]), 1)
ax, ay = A; bx, by = B; dx, dy = bx-ax, by-ay; L = dx*dx+dy*dy
u = ((R[0]-ax)*dx+(R[1]-ay)*dy)/L; Rp = (round(2*(ax+u*dx)-R[0]), round(2*(ay+u*dy)-R[1]))

NT = [0.1, 7.4, 15.4, 23.4, 30.6, 39.2, 44.8, 51.6, 57.3, 65.2, 73.4]
DUR = [6.62, 7.32, 7.34, 6.65, 7.94, 5.21, 6.19, 5.14, 7.13, 7.56, 4.58]
F = lambda **k: k
ov = []
# ---------------------------------------------------------------- A: phone map (0–7.0)
ov += [
 F(kind='satellite', id='skysat', t=5.2, until=7.0, x=280, y=30, bob=1, signal=[5.6, 7.0], aim=[150, 150], reach=70),
 F(kind='phone', t=1.2, until=4.4, x=160, y=86, w=56, h=100, lock=2.2, sats_from=[1.4, 0.25]),
 F(kind='text', t=1.4, until=2.4, x=160, y=24, text='定位中…', size=12, color=3, outline=16),
 F(kind='text', t=2.4, until=4.2, x=160, y=24, text='已定位', size=12, color=30, outline=16, bold=True),
 F(kind='tag', t=5.6, until=7.0, x=280, y=44, space='world', text='卫星', bg=7),
]
# ---------------------------------------------------------------- B: constellation (12.6–20.6)
E = (160, 96, 44)
orbits = [[160, 96, 100, 24, 18, 0], [160, 96, 76, 56, 15, 0], [160, 96, 128, 12, 22, 0]]
for o in orbits:
    ov.append(F(kind='orbit', t=12.6, until=20.6, orbit=o[:4], half='back', occlude=list(E)))
ov.append(F(kind='planet', t=12.6, until=20.6, x=E[0], y=E[1], r=E[2], spin=0.15))
for o in orbits:
    ov.append(F(kind='orbit', t=12.6, until=20.6, orbit=o[:4], half='front', color=3))
sid = 0
for oi, o in enumerate(orbits):
    for ph in (0, 120, 240):
        sid += 1
        ov.append(F(kind='satellite', id=f'c{sid}', t=12.6, until=20.6, orbit=o[:4], period=o[4], phase=ph + oi * 40,
                    occlude=list(E), body=7))
ov += [
 F(kind='caption', t=13.0, until=16.6, text='GNSS：全球卫星导航系统', reveal=12, color=7),
 F(kind='caption', t=16.6, until=20.6, text='几十颗卫星，在两万多公里高空绕地飞行', reveal=12),
 F(kind='tag', t=13.4, until=16.0, x=160, y=150, space='world', text='地球', bg=8),
 F(kind='text', t=16.0, until=18.6, x=236, y=8, text='轨道高度 ≈ 20,000 km', size=12, color=31, outline=16, bold=True),
]
# ---------------------------------------------------------------- C: four members (20.6–28.6)
ov.append(F(kind='planet', t=20.6, until=28.6, x=160, y=330, r=200, spin=0.05))
members = [('g1', 48, 'GPS · 美国', 9, 9, 22.6), ('g2', 124, '北斗 BDS · 中国', 5, 7, 23.9),
           ('g3', 200, 'GLONASS · 俄罗斯', 4, 3, 25.2), ('g4', 274, 'Galileo · 欧盟', 10, 10, 26.6)]
for gid, x, label, body, bg, t0 in members:
    ov.append(F(kind='satellite', id=gid, t=20.6, until=28.6, x=x, y=66, bob=2, body=body, signal=[t0, 28.6], reach=40, aim=[x, 140]))
    ov.append(F(kind='tag', t=t0, until=28.6, x=x, y=84 if gid in ('g1', 'g3') else 98, space='world', text=label, bg=bg, color=16 if bg in (3, 7, 9) else 4))
ov += [
 F(kind='caption', t=21.0, until=22.6, text='GNSS 家族的四大成员', reveal=12),
 F(kind='caption', t=22.6, until=28.6, text='GPS · 北斗 · GLONASS · Galileo', reveal=10, color=7),
 F(kind='text', t=28.0, until=28.6, x=160, y=22, space='world', text='GNSS', size=16, bold=True, color=7, outline=16),
]
# ---------------------------------------------------------------- D: atomic clock broadcast (28.6–35.9)
ov += [
 F(kind='planet', t=28.6, until=35.9, x=160, y=380, r=240, spin=0.05),
 F(kind='satellite', id='bs', t=28.6, until=35.9, x=86, y=62, scale=3, bob=1.5, signal=[30.6, 35.9], reach=110, spread=40, aim=[160, 180], wave_speed=36),
 F(kind='glyph', t=28.6, until=35.9, name='clock', x=236, y=82, scale=1),
 F(kind='tag', t=28.8, until=35.9, x=236, y=86, space='world', text='原子钟', bg=7),
 F(kind='text', t=29.6, until=35.9, x=236, y=42, space='world', fmt='12:00:{v:012.9f}', **{'from': 0.0, 'to': 7.3}, count=7.3, size=12, color=31, outline=16),
 F(kind='tag', t=31.4, until=35.9, x=150, y=94, space='world', text='我是 G07', bg=4),
 F(kind='tag', t=32.6, until=35.9, x=150, y=112, space='world', text='现在 12:00:03', bg=31),
 F(kind='caption', t=29.0, until=32.4, text='每颗卫星都带着极其精准的原子钟', reveal=12),
 F(kind='caption', t=32.4, until=35.9, text='不停广播：我是谁 · 现在几点', reveal=12, color=7),
]
# ---------------------------------------------------------------- E: ranging (35.9–44.4)
S = (66, 40); P = (232, 124)
ov += [
 F(kind='satellite', id='rs', t=35.9, until=44.4, x=S[0], y=S[1], scale=2, bob=1),
 F(kind='phone', t=35.9, until=44.4, x=P[0], y=P[1], w=22, h=38, lock=38.0),
 F(kind='range', t=36.4, until=44.4, x0=S[0] + 6, y0=S[1] + 12, x1=P[0] - 8, y1=P[1] - 14, draw=1.6, pulse=60),
 F(kind='tag', t=36.6, until=44.4, x=S[0], y=S[1] + 20, space='world', text='t发 = 12:00:00.000', bg=31, size=12),
 F(kind='tag', t=38.2, until=44.4, x=P[0] - 8, y=P[1] - 40, space='world', text='t收 = 12:00:00.067', bg=30, size=12),
 F(kind='text', t=39.6, until=44.4, x=180, y=14, space='world', text='距离 = (t收 − t发) × 光速', size=12, bold=True, color=4, outline=16),
 F(kind='text', t=41.0, until=44.4, x=180, y=32, space='world', text='= 0.067 s × 300,000 km/s', size=12, color=31, outline=16),
 F(kind='text', t=42.0, until=44.4, x=180, y=50, space='world', fmt='≈ {v:,.0f} km', **{'from': 0, 'to': 20100}, count=1.4, size=16, bold=True, color=7, outline=16),
 F(kind='caption', t=36.2, until=38.4, text='手机里的接收机收到信号', reveal=12),
 F(kind='caption', t=38.4, until=41.8, text='收到时间 − 发出时间，再 × 光速', reveal=12, color=7),
 F(kind='caption', t=41.8, until=44.4, text='= 到这颗卫星的距离', reveal=12, color=7),
]
# ---------------------------------------------------------------- F: trilateration (44.4–57.0) + G1 clock (57–62.4)
end_tri = 62.4
for nm, P0, t0, col in (('A', A, 44.4, 31), ('B', B, 50.4, 30), ('C', C, 53.6, 28)):
    ov.append(F(kind='satellite', id='s' + nm, t=t0, until=end_tri, x=P0[0], y=P0[1], bob=1))
    ov.append(F(kind='tag', t=t0 + 0.2, until=end_tri, x=P0[0] + (14 if nm != 'B' else -14), y=P0[1] - 22, space='world', text=f'卫星{nm}', bg=col))
ov += [
 F(kind='ring', t=45.8, until=57.0, x=A[0], y=A[1], r=d(A, R), grow=1.6, color=31, start=0),
 F(kind='ring', t=50.6, until=57.0, x=B[0], y=B[1], r=d(B, R), grow=1.3, color=30, start=180),
 F(kind='ring', t=53.8, until=57.0, x=C[0], y=C[1], r=d(C, R), grow=1.1, color=28, start=90),
 # fuzzy rings while the receiver clock is off, sharpened by the 4th satellite
 F(kind='ring', t=57.0, until=end_tri, x=A[0], y=A[1], r=d(A, R), grow=0, color=31, fuzz=3, sharpen=[60.6, 1.2]),
 F(kind='ring', t=57.0, until=end_tri, x=B[0], y=B[1], r=d(B, R), grow=0, color=30, fuzz=3, sharpen=[60.6, 1.2]),
 F(kind='ring', t=57.0, until=end_tri, x=C[0], y=C[1], r=d(C, R), grow=0, color=28, fuzz=3, sharpen=[60.6, 1.2]),
 F(kind='satellite', id='sD', t=59.4, until=end_tri, x=D[0], y=D[1], bob=1, body=5),
 F(kind='tag', t=59.6, until=end_tri, x=D[0] + 6, y=D[1] + 12, space='world', text='卫星D', bg=5, color=4),
 F(kind='ring', t=60.2, until=end_tri, x=D[0], y=D[1], r=d(D, R), grow=1.0, color=5, start=180),
 F(kind='pin', t=55.0, until=57.0, x=R[0], y=R[1], size=1),
 F(kind='pin', t=61.4, until=end_tri, x=R[0], y=R[1], size=1, drop=0.3),
 F(kind='tag', t=55.5, until=57.0, x=R[0], y=R[1] + 4, space='world', text='你在这里', bg=5, color=4),
 F(kind='glyph', t=57.0, until=59.4, name='clock', x=R[0] + 26, y=R[1] + 6, scale=1),
 F(kind='tag', t=57.2, until=59.6, x=R[0] + 26, y=R[1] + 8, space='world', text='手机时钟 ±0.001 s', bg=5, color=4),
 F(kind='text', t=58.0, until=60.6, x=R[0], y=R[1] - 52, space='world', text='误差 ≈ 300 km！', size=12, bold=True, color=5, outline=16),
 F(kind='tag', t=61.4, until=end_tri, x=R[0], y=R[1] + 4, space='world', text='钟差已校正', bg=30),
 F(kind='caption', t=44.8, until=50.4, text='一颗卫星：你在这个圆上的某处', reveal=12),
 F(kind='caption', t=50.4, until=53.7, text='两颗卫星：缩小到两个交点', reveal=12),
 F(kind='caption', t=53.7, until=57.0, text='三颗卫星：锁定位置！', reveal=12, color=7),
 F(kind='caption', t=57.2, until=59.4, text='可手机的时钟不够准……', reveal=12),
 F(kind='caption', t=59.4, until=62.4, text='第四颗卫星：校正时间', reveal=12, color=7),
]
# question marks along ring A (one-satellite ambiguity), then at the two intersections
for k, ang in enumerate((20, 60, 100, 140, 300, 340)):
    a = math.radians(ang); r = d(A, R)
    x, y = A[0] + r*math.cos(a), A[1] + r*math.sin(a)
    if 4 < x < 316 and 4 < y < 150:
        ov.append(F(kind='text', t=46.6 + k*0.25, until=50.4, x=round(x), y=round(y) - 7, space='world', text='?', size=12, bold=True, color=31, outline=16))
ov += [
 F(kind='text', t=51.9, until=55.0, x=R[0], y=R[1] - 8, space='world', text='?', size=16, bold=True, color=7, outline=16),
 F(kind='text', t=51.9, until=54.8, x=Rp[0], y=Rp[1] - 8, space='world', text='?', size=16, bold=True, color=7, outline=16),
 F(kind='text', t=54.8, until=56.0, x=Rp[0], y=Rp[1] - 8, space='world', text='×', size=16, bold=True, color=5, outline=16),
]
# ---------------------------------------------------------------- G2: four unknowns (62.4–70.4)
ov.append(F(kind='planet', t=62.4, until=70.4, x=160, y=390, r=240, spin=0.05))
unk = [('u1', 46, '经度 x', 63.0), ('u2', 122, '纬度 y', 63.8), ('u3', 198, '高度 z', 64.6), ('u4', 274, '时间 t', 65.5)]
RX = (160, 140)
for i, (uid, x, label, t0) in enumerate(unk):
    ov.append(F(kind='satellite', id=uid, t=62.4, until=70.4, x=x, y=34, bob=1.5, body=(9, 5, 4, 10)[i]))
    ov.append(F(kind='range', t=t0 - 0.3, until=70.4, x0=x, y0=44, x1=RX[0], y1=RX[1] - 18, draw=0.6, pulse=70, color=(9, 21, 3, 10)[i]))
    ov.append(F(kind='tag', t=t0, until=70.4, x=x, y=50, space='world', text=label, bg=(9, 5, 3, 10)[i], color=4 if i in (1, 3) else 16))
ov += [
 F(kind='phone', t=62.4, until=70.4, x=RX[0], y=RX[1], w=20, h=34, lock=62.4, sats=4),
 F(kind='text', t=66.0, until=70.4, x=160, y=80, space='world', text='4 个未知数', size=16, bold=True, color=4, outline=16),
 F(kind='text', t=67.2, until=70.4, x=160, y=98, space='world', text='→ 至少 4 颗卫星', size=16, bold=True, color=7, outline=16),
 F(kind='caption', t=62.9, until=66.0, text='经度 · 纬度 · 高度 · 时间', reveal=12),
 F(kind='caption', t=66.0, until=70.4, text='四个未知数 = 至少四颗卫星', reveal=12, color=7),
]
# ---------------------------------------------------------------- H: everyday uses (70.4–78.6)
uses = [('car', 44, '开车导航', 71.4), ('scooter', 106, '外卖骑手', 72.6), ('bike', 166, '共享单车', 73.8),
        ('tripod', 226, '测绘', 75.0), ('clock', 286, '授时', 75.8)]
for name, x, label, t0 in uses:
    ov.append(F(kind='glyph', t=70.4, until=78.6, name=name, x=x, y=150, scale=1))
    ov.append(F(kind='tag', t=t0, until=78.6, x=x, y=110, space='world', text=label, bg=7))
ov += [
 F(kind='satellite', t=70.4, until=78.6, x=160, y=22, bob=1, signal=[70.4, 78.6], reach=80, spread=60, aim=[160, 150]),
 F(kind='caption', t=70.8, until=76.7, text='导航 · 外卖 · 共享单车 · 测绘 · 授时', reveal=10),
 F(kind='caption', t=76.7, until=78.6, text='都离不开 GNSS', reveal=12, color=7),
]
# ---------------------------------------------------------------- I: outro globe (78.6–83.8)
E2 = (160, 96, 52)
ov.append(F(kind='orbit', t=78.6, until=84.2, orbit=[160, 96, 110, 30], half='back', occlude=list(E2)))
ov.append(F(kind='planet', t=78.6, until=84.2, x=E2[0], y=E2[1], r=E2[2], spin=0.15))
ov.append(F(kind='orbit', t=78.6, until=84.2, orbit=[160, 96, 110, 30], half='front', color=3))
for ph in (0, 90, 180, 270):
    ov.append(F(kind='satellite', t=78.6, until=84.2, orbit=[160, 96, 110, 30], period=16, phase=ph, occlude=list(E2)))
ov += [
 F(kind='pin', t=79.0, until=84.2, x=150, y=84, size=1),
 F(kind='tag', t=79.6, until=84.2, x=150, y=88, space='world', text='你在这里', bg=5, color=4),
 F(kind='caption', t=79.0, until=84.2, text='看不见的卫星，时时刻刻告诉你：你在这里', reveal=12, color=7),
]
# ---------------------------------------------------------------- corner tags + cards
for t0, t1, txt in ((12.6, 20.6, '什么是 GNSS'), (20.6, 28.6, '四大系统'), (28.6, 35.9, '① 卫星发信号'),
                    (35.9, 44.4, '② 接收机测距'), (44.4, 62.4, '③ 多星定位'), (62.4, 70.4, '④ 为什么至少 4 颗'),
                    (70.4, 78.6, '民用')):
    ov.append(F(kind='tag', t=t0, until=min(t1, t0 + 3.2), x=6, y=6, text=txt, bg=10, color=4, border=0, align='left'))
cards = [
 F(kind='card', t=84.2, until=88.0, bg=25, items=[
   F(text='全球导航定位系统（GNSS）', size=22, color=7),
   F(text='@像素万物局', size=14, color=31, at=0.6),
 ]),
]
ov += cards

# Retime everything from B onward: the old 0.8 s GNSS preamble line is gone,
# and the phone-map opening now runs 0–7.0 s.
SHIFT = 5.6
for o in ov:
    if o['t'] >= 12.6:
        o['t'] -= SHIFT
    if o.get('until', 1e9) >= 12.6:
        o['until'] -= SHIFT
# exact subtitles from the narration, chunked by punctuation
ov = [o for o in ov if o.get('kind') != 'caption']


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


for (t, text), dur in zip(zip(NT, LINES), DUR):
    chunks = _chunks(text)
    weights = [max(1, len(c.replace(" ", ""))) for c in chunks]
    total = sum(weights) or 1
    acc = 0.0
    for c, w in zip(chunks, weights):
        st = t + dur * acc / total
        acc += w
        en = t + dur * acc / total - 0.04
        ov.append(F(kind='caption', t=st, until=en, text=c, size=12, color=4, reveal=0))


cam = [
 F(t=0.0, shot='medium', target='xiaoming', offset=[0, -8], name='开场·小明已经在看手机'),
 F(t=1.0, shot='close', zoom=1.6, target=[160, 86], move=0.3, name='特写·手机地图'),
 F(t=1.4, shot='close', zoom=1.9, target=[160, 96], move=1.2, name='缓推·小蓝点'),
 F(t=3.2, shot='close', zoom=1.7, target=[160, 90], move=1.0, name='近景·已定位'),
 F(t=4.4, shot='medium', target='xiaoming', offset=[0, -10], name='中景·小明抬头'),
 F(t=5.2, shot='close', zoom=2.2, target='skysat', offset=[-24, 24], move=0.8, name='上摇·天上的卫星'),
 # B
 F(t=12.6, shot='wide', transition='fade', fade=0.6, name='远景·地球与卫星星座'),
 F(t=12.9, shot='full', zoom=1.35, target=[160, 96], move=3.0, ease='linear', name='缓推·星座'),
 F(t=16.0, shot='close', target='c1', name='近景跟拍·一颗导航卫星'),
 F(t=18.4, shot='wide', move=2.0, name='拉远景·几十颗卫星'),
 # C
 F(t=20.6, shot='wide', transition='fade', fade=0.6, name='远景·四颗卫星一字排开'),
 F(t=22.4, shot='close', target='g1', offset=[0, 10], move=0.6, name='近景·GPS'),
 F(t=23.8, shot='close', target='g2', offset=[0, 10], move=0.5, name='横摇·北斗'),
 F(t=25.1, shot='close', target='g3', offset=[0, 10], move=0.5, name='横摇·GLONASS'),
 F(t=26.5, shot='close', target='g4', offset=[0, 10], move=0.5, name='横摇·Galileo'),
 F(t=27.8, shot='wide', move=0.8, name='拉远景·GNSS 家族'),
 # D
 F(t=28.6, shot='closeup', zoom=2.6, target=[236, 66], transition='fade', fade=0.5, name='特写·原子钟'),
 F(t=30.6, shot='medium', target='bs', offset=[40, 20], move=1.0, name='摇到卫星·广播「我是 G07」'),
 F(t=33.0, shot='wide', move=1.2, name='拉远景·信号波射向地球'),
 # E
 F(t=35.9, shot='medium', zoom=2.0, target=[80, 52], transition='fade', fade=0.5, name='中景·卫星发出信号'),
 F(t=36.4, shot='medium', zoom=2.0, target=[214, 104], move=1.8, name='沿信号横摇到接收机'),
 F(t=38.4, shot='close', zoom=2.6, target=[226, 104], name='近景·手机记下 t收'),
 F(t=39.6, shot='wide', name='远景·测距示意全图'),
 F(t=41.8, shot='medium', zoom=1.8, target=[180, 46], move=0.8, name='推近·算出距离'),
 # F
 F(t=44.4, shot='medium', zoom=2.0, target='sA', transition='fade', fade=0.5, name='中景·卫星A'),
 F(t=45.2, shot='wide', move=0.5, name='拉远景·距离圆展开'),
 F(t=47.4, shot='full', zoom=1.15, target=[160, 92], name='全景·圆上处处是「?」'),
 F(t=47.6, shot='full', zoom=1.15, target=[160, 92], move=2.6, ease='linear', name='缓推·整个圆'),
 F(t=50.4, shot='wide', name='远景·卫星B加入'),
 F(t=52.0, shot='full', zoom=1.15, target=[160, 92], name='全景·两个交点'),
 F(t=54.8, shot='full', zoom=1.15, target=[160, 92], move=0.8, name='全景·第三颗锁定位置'),
 # G
 F(t=57.0, shot='full', zoom=1.15, target=[160, 92], name='全景·手机时钟有误差'),
 F(t=58.4, shot='wide', move=0.8, name='拉远景·圆环变模糊'),
 F(t=59.5, shot='medium', zoom=2.0, target='sD', offset=[-30, 24], name='中景·第四颗卫星D'),
 F(t=60.6, shot='full', zoom=1.15, target=[160, 92], move=1.2, name='全景·圆环收紧，重新锁定'),
 F(t=62.4, shot='wide', transition='fade', fade=0.5, name='远景·四星四线'),
 F(t=62.9, shot='close', target='u1', offset=[0, 14], move=0.4, name='近景·经度'),
 F(t=63.7, shot='close', target='u2', offset=[0, 14], move=0.4, name='横摇·纬度'),
 F(t=64.5, shot='close', target='u3', offset=[0, 14], move=0.4, name='横摇·高度'),
 F(t=65.4, shot='close', target='u4', offset=[0, 14], move=0.4, name='横摇·时间'),
 F(t=66.0, shot='wide', move=1.0, name='拉远景·四个未知数'),
 F(t=68.0, shot='medium', zoom=1.6, target=[160, 98], move=1.6, name='推·至少四颗卫星'),
 # H
 F(t=70.4, shot='wide', transition='fade', fade=0.5, name='远景·城市街道'),
 F(t=71.4, shot='close', target=[44, 128], name='近景·开车导航'),
 F(t=72.6, shot='close', target=[106, 124], name='近景·外卖骑手'),
 F(t=73.8, shot='close', target=[166, 128], name='近景·共享单车'),
 F(t=75.0, shot='close', target=[226, 124], name='近景·测绘'),
 F(t=75.8, shot='close', target=[286, 124], name='近景·授时'),
 F(t=76.7, shot='wide', move=1.2, name='拉远景·都离不开 GNSS'),
 # I
 F(t=78.6, shot='closeup', zoom=2.8, target=[150, 80], transition='fade', fade=0.5, name='特写·地球上的你'),
 F(t=79.2, shot='wide', move=4.0, ease='out', name='拉远景·地球与卫星'),
 F(t=84.2, shot='wide', transition='fade', fade=0.5, name='结尾卡'),
]

for k in cam:
    if k['t'] >= 12.6:
        k['t'] -= SHIFT

tl = [
 F(t=0.0, action='background', name='market'),
 F(t=0.0, action='pose', target='xiaoming', name='phone'),
 F(t=1.2, action='hide', target='xiaoming'),
 F(t=4.4, action='show', target='xiaoming'),
 F(t=4.4, action='pose', target='xiaoming', name='idle'),
 F(t=4.4, action='expression', target='xiaoming', name='surprise'),
 F(t=5.0, action='expression', target='xiaoming', name='happy'),
 F(t=12.6, action='hide', target='xiaoming'),
 F(t=12.6, action='background', name='space'),
 F(t=35.9, action='background', name='blueprint'),
 F(t=62.4, action='background', name='space'),
 F(t=70.4, action='background', name='market'),
 F(t=70.4, action='move', target='xiaoming', x=-20),
 F(t=70.4, action='show', target='xiaoming'),
 F(t=70.4, action='expression', target='xiaoming', name='happy'),
 F(t=76.6, action='walk_to', target='xiaoming', x=340, speed=60),
 F(t=78.6, action='hide', target='xiaoming'),
 F(t=78.6, action='background', name='space'),
]

for e in tl:
    if e['t'] >= 12.6:
        e['t'] -= SHIFT

scene = dict(
 name='gnss_intro', width=320, height=180, fps=60, duration=82.4, background='market', ground_y=150, scale=3, gravity=420,
 characters=[F(name='xiaoming', preset='hero', x=150, hair=24, hair_style='short', cloth=6, pants=25, expression='neutral')],
 objects=[F(name='phone', kind='phone', held_by='xiaoming', w=5, h=7)],
 narration=F(voice='zh-CN-YunjianNeural', rate='+5%', lines=[F(t=t, text=x) for t, x in zip(NT, LINES)]),
 camera=cam, overlays=ov, timeline=tl,
)
hdr = '''# GNSS 科普 · 全球卫星导航系统是怎么给你定位的？
# 有声成片（渲染 + edge-tts 旁白混音）:
#   .venv/bin/python -m animasis narrate demos/gnss_intro.yaml -o demos/output/gnss_intro.mp4
# 镜头表:   .venv/bin/python -m animasis shots demos/gnss_intro.yaml --markdown
# 段落: A 手机地图 | B 什么是GNSS(星座) | C 四大系统 | D 卫星发信号(原子钟) | E 接收机测距 |
#       F 多星定位(一圆→两交点→锁定) | G 第四颗星校时 + 四个未知数 | H 民用 | I 结尾地球 | 结尾卡
# (geometry: receiver R=%s, satellites A=%s B=%s C=%s D=%s, mirror point R'=%s)
''' % (R, A, B, C, D, Rp)
class Flow(yaml.SafeDumper): pass
def repr_list(dumper, data):
    flow = all(not isinstance(v, (dict, list)) for v in data)
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=flow)
def repr_dict(dumper, data):
    flow = all(not isinstance(v, (dict,)) and not (isinstance(v, list) and any(isinstance(i, dict) for i in v)) for v in data.values())
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items(), flow_style=flow)
Flow.add_representer(list, repr_list); Flow.add_representer(dict, repr_dict)
out = hdr + yaml.dump(scene, Dumper=Flow, allow_unicode=True, sort_keys=False, width=200)
open(__import__('pathlib').Path(__file__).with_name('gnss_intro.yaml'), 'w', encoding='utf-8').write(out)
print(len(ov), len(cam), Rp)
