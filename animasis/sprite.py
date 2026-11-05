"""Layered pixel-sprite rasterizer for the humanoid rig.

Every body part is a *filled* shape (capsule limbs, rounded torso, superellipse
head) rasterised at native resolution and shaded with a 3-tone ramp.  Limbs
share joint end-points and overlap with round caps, so nothing can detach.  A
single 1px soft outline is traced around the whole silhouette afterwards, plus
thin contour lines where a front limb overlaps the body.

Layer order (back → front):
  hair_back · back arm · back leg · front leg · torso · skirt · head · face ·
  hair · hat · front arm
"""

from __future__ import annotations

import math
from typing import Callable, Iterable

from . import palette as pal
from .face import draw_face
from .skeleton import Character, Rig, Vec

Pix = tuple[int, int]
Ramp = tuple[int, int, int]


# ------------------------------------------------------------------ helpers
def snap_even(p: Vec) -> Vec:
    """Snap to a pixel corner — even-width strokes (2px) stay crisp."""
    return (float(round(p[0])), float(round(p[1])))


def snap_odd(p: Vec) -> Vec:
    """Snap to a pixel centre — odd-width strokes (3px) stay crisp."""
    return (math.floor(p[0]) + 0.5, math.floor(p[1]) + 0.5)


def _seg_dist2(px: float, py: float, a: Vec, b: Vec) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    qx, qy = a[0] + dx * t - px, a[1] + dy * t - py
    return qx * qx + qy * qy


def capsule(a: Vec, b: Vec, r: float) -> set[Pix]:
    out: set[Pix] = set()
    x0 = int(math.floor(min(a[0], b[0]) - r - 1))
    x1 = int(math.ceil(max(a[0], b[0]) + r + 1))
    y0 = int(math.floor(min(a[1], b[1]) - r - 1))
    y1 = int(math.ceil(max(a[1], b[1]) + r + 1))
    r2 = r * r + 1e-6
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if _seg_dist2(x + 0.5, y + 0.5, a, b) <= r2:
                out.add((x, y))
    return out


def superellipse(n: int, m: int, rx: float, ry: float, p: float = 2.4) -> set[Pix]:
    out: set[Pix] = set()
    for dy in range(-int(ry) - 2, int(ry) + 3):
        for dx in range(-int(rx) - 2, int(rx) + 3):
            if (abs(dx) / rx) ** p + (abs(dy) / ry) ** p <= 1.0:
                out.add((n + dx, m + dy))
    return out


def shade(mask: Iterable[Pix], ramp: Ramp, rim_light: bool = True) -> dict[Pix, int]:
    """3-tone shading: light from the upper-left, shade on the lower-right rim."""
    mask = set(mask)
    light, base, dark = ramp
    out: dict[Pix, int] = {}
    for (x, y) in mask:
        if (x + 1, y) not in mask or (x, y + 1) not in mask:
            out[(x, y)] = dark
        elif rim_light and ((x - 1, y) not in mask or (x, y - 1) not in mask):
            out[(x, y)] = light
        else:
            out[(x, y)] = base
    return out


def back_ramp(r: Ramp) -> Ramp:
    """Far-side limbs: one step darker so depth reads clearly."""
    return (r[1], r[2], r[2])


class Canvas:
    """Sparse per-character layer canvas: pixel -> (colour, group)."""

    def __init__(self) -> None:
        self.color: dict[Pix, int] = {}
        self.group: dict[Pix, str] = {}

    def paint(self, colors: dict[Pix, int], group: str) -> None:
        for p, c in colors.items():
            self.color[p] = c
            self.group[p] = group

    def put(self, group: str) -> Callable[[int, int, int], None]:
        def _put(x: int, y: int, c: int) -> None:
            self.color[(x, y)] = c
            self.group[(x, y)] = group
        return _put


# groups that get a contour line where they overlap something behind them
_CONTOUR_OVER = {
    "arm_r": {"body", "skirt", "leg_r", "leg_l", "arm_l", "head", "hair_back"},
    "leg_r": {"leg_l"},
    "skirt": {"leg_r", "leg_l"},
    "head": {"body", "arm_l", "hair_back"},
}


# ------------------------------------------------------------------ parts
def _limb(cv: Canvas, rig: Rig, side: str, kind: str, look, back: bool) -> None:
    P, pr = rig.points, rig.props
    group = f"{kind}_{side}"
    skin = pal.ramp(look.skin)
    if kind == "leg":
        cloth = pal.ramp(look.pants)
        shoes = pal.ramp(look.shoes)
        if back:
            cloth, shoes = back_ramp(cloth), back_ramp(shoes)
        hj, kn, an = (snap_odd(P[f"{k}_{side}"]) for k in ("hipj", "knee", "ankle"))
        r = pr["leg_r"]
        mask = capsule(hj, kn, r) | capsule(kn, an, r * 0.92)
        cv.paint(shade(mask, cloth), group)
        heel, toe = snap_even(P[f"heel_{side}"]), snap_even(P[f"toe_{side}"])
        shoe = capsule(heel, toe, 1.05)
        # tie the shoe to the ankle so there is never a gap
        shoe |= capsule(snap_even(P[f"ankle_{side}"]), heel, 1.05)
        cv.paint(shade(shoe, shoes), group)
    else:
        sleeve = pal.ramp(look.shirt)
        if not back:
            # near sleeve catches the light: one step brighter than the torso
            # behind it so it never melts into a flat stripe on the shirt
            sleeve = (sleeve[0], sleeve[0], sleeve[1])
        if back:
            sleeve, skin = back_ramp(sleeve), back_ramp(skin)
        sh, el, wr, hd = (snap_even(P[f"{k}_{side}"]) for k in ("shoulder", "elbow", "wrist", "hand"))
        r = pr["arm_r"]
        upper = capsule(sh, el, r + 0.15)
        lower = capsule(el, wr, r)
        hand = capsule(wr, hd, r + 0.2)
        if look.sleeves == "long":
            cv.paint(shade(upper | lower, sleeve), group)
        else:
            # short sleeve: covers the shoulder + top ~60% of the upper arm with
            # a slightly wider hem, bare skin from there to the wrist
            hem = (sh[0] + (el[0] - sh[0]) * 0.6, sh[1] + (el[1] - sh[1]) * 0.6)
            cv.paint(shade(upper | lower, skin), group)
            cv.paint(shade(capsule(sh, hem, r + 0.35), sleeve), group)
        cv.paint(shade(hand, skin, rim_light=False), group)


def _torso(cv: Canvas, rig: Rig, look) -> None:
    P, pr, f = rig.points, rig.props, rig.facing
    lean = rig.lean
    hip = snap_even(P["hip"])
    up = (math.sin(lean) * f, -math.cos(lean))
    fwd = (math.cos(lean) * f, math.sin(lean))
    L = pr["torso_len"]
    s = pr["torso_len"] / 8.0
    pants_top = 1.4 * s
    belt_top = 2.4 * s
    shirt = pal.ramp(look.shirt)
    pants = pal.ramp(look.pants)
    belt = pal.ramp(look.belt) if look.belt is not None else None
    reach = int(L + 6)
    body: set[Pix] = set()
    region: dict[Pix, str] = {}
    for y in range(int(hip[1]) - reach, int(hip[1]) + 4):
        for x in range(int(hip[0]) - 8, int(hip[0]) + 9):
            dx, dy = x + 0.5 - hip[0], y + 0.5 - hip[1]
            u = dx * up[0] + dy * up[1]
            v = dx * fwd[0] + dy * fwd[1]
            if u < -0.6 or u > L + 0.4:
                continue
            hw = pr["hw_bot"] + (pr["hw_top"] - pr["hw_bot"]) * max(0.0, min(1.0, u / L))
            if abs(v) > hw:
                continue
            if u > L - 0.5 and abs(v) > hw - 0.5:  # clip the hard corner pixel
                continue
            p = (x, y)
            body.add(p)
            if look.skirt:
                region[p] = "shirt"
            elif u < pants_top:
                region[p] = "pants"
            elif belt and u < belt_top:
                region[p] = "belt"
            else:
                region[p] = "shirt"
    # shoulder caps: a small rounded deltoid on each top corner, merged into the
    # torso mask *before* shading so the arm grows out of a rounded shoulder
    # instead of being glued to the side of a box
    cap_r = pr.get("shoulder_r", 1.45)
    for side in ("r", "l"):
        sh = snap_even(P[f"shcap_{side}"])
        for p in capsule(sh, sh, cap_r):
            dx, dy = p[0] + 0.5 - hip[0], p[1] + 0.5 - hip[1]
            if dx * up[0] + dy * up[1] > L + 0.3:  # never poke above the collar line
                continue
            if p not in body:
                body.add(p)
                region[p] = "shirt"
    shaded = shade(body, shirt)
    pshade = shade(body, pants)
    bshade = shade(body, belt) if belt else {}
    colors: dict[Pix, int] = {}
    for p in body:
        reg = region[p]
        if reg == "pants":
            colors[p] = pshade[p]
        elif reg == "belt":
            colors[p] = bshade[p]
        else:
            colors[p] = shaded[p]
    # buckle
    if belt and not look.skirt:
        bc = (hip[0] + fwd[0] * 1.0 + up[0] * 2.5, hip[1] + fwd[1] * 1.0 + up[1] * 2.5)
        bp = (int(math.floor(bc[0])), int(math.floor(bc[1])))
        if bp in colors:
            colors[bp] = pal.ACCENT
    cv.paint(colors, "body")

    if look.skirt:
        sk: set[Pix] = set()
        for y in range(int(hip[1]) - 6, int(hip[1]) + 8):
            for x in range(int(hip[0]) - 9, int(hip[0]) + 10):
                dx, dy = x + 0.5 - hip[0], y + 0.5 - hip[1]
                u = dx * up[0] + dy * up[1]
                v = dx * fwd[0] + dy * fwd[1]
                top, bot = 2.5 * s, -3.6 * s
                if bot <= u <= top:
                    k = (top - u) / (top - bot)
                    hw = pr["hw_bot"] + 0.2 + 1.9 * k
                    if abs(v) <= hw:
                        sk.add((x, y))
        cs = shade(sk, shirt)
        # hem: one row of the light tone just above the bottom edge
        for (x, y) in sk:
            if (x, y + 1) not in sk and (x, y - 1) in sk and (x, y - 1) in cs:
                cs[(x, y - 1)] = shirt[0] if cs[(x, y - 1)] != shirt[2] else shirt[2]
        cv.paint(cs, "skirt")


def _head_center(rig: Rig) -> tuple[int, int]:
    hc = snap_odd(rig.points["head_c"])
    return int(math.floor(hc[0])), int(math.floor(hc[1]))


def _hair_masks(n: int, m: int, f: int, style: str, pr: dict[str, float]) -> tuple[set[Pix], set[Pix]]:
    """Return (front_hair, back_hair) masks."""
    rx, ry = pr["head_rx"], pr["head_ry"]
    E = superellipse(n, m, rx + 1.0, ry + 1.1)
    front: set[Pix] = set()
    back: set[Pix] = set()
    for (x, y) in E:
        dx = (x - n) * f            # >0 = toward the face
        if y <= m - 4:
            front.add((x, y))
        elif style == "buzz":
            continue
        elif dx < 0 and abs(x - n) >= 4 and y <= m + (3 if style in ("long", "bob") else 1):
            front.add((x, y))           # back-of-head lock (3/4 view)
        elif dx > 0 and abs(x - n) >= 5 and y <= m + (3 if style in ("long", "bob") else -1):
            front.add((x, y))           # front side lock / sideburn
    # fringe: a few strands sweeping back over the forehead
    if style != "buzz":
        for ddx in (0, -1, -2, 3):
            front.add((n + ddx * f, m - 3))
        front.add((n - 3 * f, m - 3))
    if style == "spiky":
        for ddx, h in ((-4, 2), (-1, 3), (2, 2), (4, 1)):
            for k in range(1, h + 1):
                for w in range(0, max(1, 3 - k)):
                    front.add((n + (ddx - w) * f, m - 6 - k + 0))
    if style == "long":
        for y in range(m - 3, m + 10):
            for x in range(n - 6, n + 7):
                xx = x - f
                yy = y
                edge = abs(x - n)
                if yy >= m + 8 and edge >= 5:
                    continue
                if yy == m + 9 and edge >= 3:
                    continue
                back.add((xx, yy))
    if style == "bob":
        for (x, y) in E:
            if m - 1 <= y <= m + 3 and abs(x - n) >= 5:
                front.add((x, y))
    if style == "ponytail":
        tie = (n - 6 * f + 0.5, m - 3 + 0.5)
        back |= capsule(tie, (n - 8 * f + 0.5, m + 4 + 0.5), 1.6)
        back |= capsule(tie, (n - 7 * f + 0.5, m - 2 + 0.5), 2.2)
    if style == "topknot":  # 发髻: hair pulled up into a bun on the crown
        top = m - pr["head_ry"] - 1.0
        bun = (n - 1 * f + 0.5, top - 1.6)
        front |= capsule(bun, bun, 2.3)
        front |= {(n - 1 * f + k, int(top) + 1) for k in (-2, -1, 0, 1, 2)}
    return front, back


def _beard_mask(n: int, m: int, f: int, style: str, pr: dict[str, float]) -> set[Pix]:
    """Beard in the hair colour: ``short`` = full jaw (张飞), ``long`` = jaw + long beard (关羽)."""
    c = n + f
    rx, ry = pr["head_rx"], pr["head_ry"]
    out: set[Pix] = set()
    jaw = superellipse(n, m, rx + 0.6, ry + 1.2)
    for (x, y) in jaw:
        dx = (x - n) * f
        if y >= m + 3 and dx >= -3:
            if y == m + 3 and abs(x - c) <= 1:
                continue  # keep the mouth readable
            if y == m + 3 and dx < 1 and style == "long":
                continue
            out.add((x, y))
    # sideburn toward the ear
    for y in range(m + 1, m + 3):
        out.add((n - 3 * f, y))
    if style == "short":  # bushy: a little wider + spiky chin tufts
        for k in (-2, 0, 2):
            out.add((c + k, int(m + ry + 2)))
    if style == "long":
        y0 = int(m + ry + 1)
        for i in range(10):
            w = 2 if i < 4 else (1 if i < 8 else 0)
            cx = c + (1 if i >= 6 else 0) * f
            for k in range(-w, w + 1):
                out.add((cx + k, y0 + i))
    return out


def _hair_colors(mask: set[Pix], ramp: Ramp, n: int, m: int) -> dict[Pix, int]:
    cols = shade(mask, ramp, rim_light=False)
    # glossy highlight streak on the upper-left of the crown
    for (x, y) in mask:
        if y in (m - 5, m - 6) and -3 <= x - n <= 0 and cols[(x, y)] != ramp[2]:
            if (x + y) % 3 != 0:
                cols[(x, y)] = ramp[0]
    return cols


def draw_sprite(ch: Character, hat: int | None = None) -> Canvas:
    rig = ch.rig()
    look = ch.look
    pr = rig.props
    f = rig.facing
    cv = Canvas()
    n, m = _head_center(rig)
    hair_ramp = pal.ramp(look.hair)
    style = look.hair_style
    hat = look.hat if hat is None else hat
    front_hair, back_hair = _hair_masks(n, m, f, style, pr)

    if back_hair:
        cv.paint(shade(back_hair, back_ramp(hair_ramp) if style == "long" else hair_ramp,
                       rim_light=False), "hair_back")
    _limb(cv, rig, "l", "arm", look, back=True)
    _limb(cv, rig, "l", "leg", look, back=True)
    _limb(cv, rig, "r", "leg", look, back=False)
    _torso(cv, rig, look)

    head = superellipse(n, m, pr["head_rx"], pr["head_ry"])
    skin = pal.ramp(look.skin)
    hc = shade(head, skin)
    cv.paint(hc, "head")
    draw_face(cv.put("head"), n, m, facing=f, expression=ch.expression,
              brow_color=hair_ramp[2] if look.hair not in (1, 24) else pal.OUTLINE_SOFT,
              blush=look.blush, lashes=look.lashes, skin_shade=skin[2])
    if hat is not None:
        front_hair = {p for p in front_hair if p[1] > m - 4}
    cv.paint(_hair_colors(front_hair, hair_ramp, n, m), "head")
    if look.beard:
        cv.paint(shade(_beard_mask(n, m, f, look.beard, pr), hair_ramp, rim_light=False), "head")
    if hat is not None:
        hr = pal.ramp(hat)
        dome = {p for p in superellipse(n, m - 1, pr["head_rx"] + 1.0, pr["head_ry"] + 1.0) if p[1] <= m - 4}
        brim = {(n + k * f, m - 4) for k in range(-5, 8)} | {(n + k * f, m - 3) for k in range(3, 8)}
        cv.paint(shade(dome, hr), "head")
        band = {p for p in dome if p[1] == m - 5}
        cv.paint({p: hr[2] for p in band}, "head")
        cv.paint(shade(brim, (hr[1], hr[1], hr[2]), rim_light=False), "head")
    _limb(cv, rig, "r", "arm", look, back=False)
    # no contour line where the front arm roots into its own shoulder
    cv.seams = [(snap_even(rig.points["shoulder_r"]), pr.get("shoulder_r", 1.45) + 1.2, "arm_r", "body")]
    _contours(cv)
    _outline(cv)
    return cv


def _in_seam(cv: Canvas, q: Pix, g: str, gq: str) -> bool:
    for (c, rad, ga, gb), in zip(getattr(cv, "seams", ())):
        if g == ga and gq == gb:
            dx, dy = q[0] + 0.5 - c[0], q[1] + 0.5 - c[1]
            if dx * dx + dy * dy <= rad * rad:
                return True
    return False


def _contours(cv: Canvas) -> None:
    edits: dict[Pix, int] = {}
    for p, g in cv.group.items():
        over = _CONTOUR_OVER.get(g)
        if not over:
            continue
        x, y = p
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            gq = cv.group.get(q)
            if gq is not None and gq != g and gq in over:
                if _in_seam(cv, q, g, gq):
                    continue
                edits[q] = pal.OUTLINE_SOFT
    for q, c in edits.items():
        cv.color[q] = c


def _outline(cv: Canvas) -> None:
    ring: dict[Pix, int] = {}
    for (x, y) in cv.color:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in cv.color:
                ring[q] = pal.OUTLINE_SOFT
    for q, c in ring.items():
        cv.color[q] = c
        cv.group[q] = "outline"


def draw_shadow(put: Callable[[int, int, int], None], get: Callable[[int, int], int],
                ch: Character, ground_y: float) -> None:
    """Soft contact shadow on the floor; shrinks while airborne."""
    h = max(0.0, ground_y - ch.y)
    w = max(3.0, 7.0 * ch.skeleton.scale - h * 0.08)
    gy = int(round(ground_y))
    cx = ch.x
    for dy, ww in ((0, w), (1, w - 2.0)):
        for x in range(int(math.floor(cx - ww)), int(math.ceil(cx + ww)) + 1):
            if abs(x + 0.5 - cx) <= ww:
                put(x, gy + dy, pal.darker(get(x, gy + dy)))
