#!/usr/bin/env python3
"""Generates index.html for the house design site. Dimensions in feet from builder plans P-7 / P-8."""
import html, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "index.html"

def ft(v):
    v = abs(v)
    inches = round(v * 12)
    f, i = divmod(inches, 12)
    return f"{f}'-{i}\""

def esc(s):
    return html.escape(s, quote=True)

# ---------------------------------------------------------------- plan drawing
class Plan:
    def __init__(self, S, ox, oy, w, h, title):
        self.S, self.ox, self.oy, self.w, self.h = S, ox, oy, w, h
        self.title = title
        self.parts = []
        self.top = []

    def P(self, x): return round(self.ox + x * self.S, 1)
    def Q(self, y): return round(self.oy + y * self.S, 1)

    def rect(self, x1, y1, x2, y2, cls, top=False, extra=""):
        s = f'<rect class="{cls}" x="{self.P(x1)}" y="{self.Q(y1)}" width="{round((x2-x1)*self.S,1)}" height="{round((y2-y1)*self.S,1)}" {extra}/>'
        (self.top if top else self.parts).append(s)

    def circle(self, cx, cy, r, cls):
        self.parts.append(f'<circle class="{cls}" cx="{self.P(cx)}" cy="{self.Q(cy)}" r="{round(r*self.S,1)}"/>')

    def text(self, x, y, s, cls, anchor="start"):
        self.top.append(f'<text class="{cls}" x="{self.P(x)}" y="{self.Q(y)}" text-anchor="{anchor}">{esc(s)}</text>')

    def poly(self, pts, cls):
        d = " ".join(f"{self.P(x)},{self.Q(y)}" for x, y in pts)
        self.parts.append(f'<polygon class="{cls}" points="{d}"/>')

    def line(self, x1, y1, x2, y2, cls, top=False):
        s = f'<line class="{cls}" x1="{self.P(x1)}" y1="{self.Q(y1)}" x2="{self.P(x2)}" y2="{self.Q(y2)}"/>'
        (self.top if top else self.parts).append(s)

    def room(self, x1, y1, x2, y2, name, dims, kind="room", lx=None, ly=None):
        self.rect(x1, y1, x2, y2, kind)
        lx = x1 + 0.45 if lx is None else lx
        ly = y1 + 1.15 if ly is None else ly
        self.text(lx, ly, name, "rl" if kind != "svc" else "sl")
        if dims:
            self.text(lx, ly + 0.95, dims, "rd")

    def window_h(self, x1, x2, y):
        self.line(x1, y, x2, y, "win", top=True)

    def window_v(self, y1, y2, x):
        self.line(x, y1, x, y2, "win", top=True)

    def door_h(self, x1, x2, y, d, hinge="left"):
        L = x2 - x1
        hx, ox_ = (x1, x2) if hinge == "left" else (x2, x1)
        sweep = 1 if (d == 1) == (hinge == "right") else 0
        self.line(x1, y, x2, y, "gap", top=True)
        self.top.append(f'<line class="leaf" x1="{self.P(hx)}" y1="{self.Q(y)}" x2="{self.P(hx)}" y2="{self.Q(y+d*L)}"/>')
        self.top.append(f'<path class="swing" d="M{self.P(hx)},{self.Q(y+d*L)} A{round(L*self.S,1)},{round(L*self.S,1)} 0 0,{sweep} {self.P(ox_)},{self.Q(y)}"/>')

    def door_v(self, y1, y2, x, d, hinge="top"):
        L = y2 - y1
        hy, oy_ = (y1, y2) if hinge == "top" else (y2, y1)
        sweep = 0 if (d == 1) == (hinge == "bottom") else 1
        self.line(x, y1, x, y2, "gap", top=True)
        self.top.append(f'<line class="leaf" x1="{self.P(x)}" y1="{self.Q(hy)}" x2="{self.P(x+d*L)}" y2="{self.Q(hy)}"/>')
        self.top.append(f'<path class="swing" d="M{self.P(x+d*L)},{self.Q(hy)} A{round(L*self.S,1)},{round(L*self.S,1)} 0 0,{sweep} {self.P(x)},{self.Q(oy_)}"/>')

    def furn(self, x1, y1, x2, y2, label="", cls="furn", lab_dy=0.0, rx=2):
        self.rect(x1, y1, x2, y2, cls, extra=f'rx="{rx}"')
        if label:
            self.text((x1+x2)/2, (y1+y2)/2 + 0.3 + lab_dy, label, "fl", "middle")

    def dim(self, x1, y1, x2, y2, label, tx=None, ty=None, anchor="middle"):
        self.top.append(f'<line class="dimln" x1="{self.P(x1)}" y1="{self.Q(y1)}" x2="{self.P(x2)}" y2="{self.Q(y2)}" marker-start="url(#tick)" marker-end="url(#tick)"/>')
        tx = (x1+x2)/2 if tx is None else tx
        ty = (y1+y2)/2 - 0.25 if ty is None else ty
        self.top.append(f'<text class="dimtx" x="{self.P(tx)}" y="{self.Q(ty)}" text-anchor="{anchor}">{esc(label)}</text>')

    def svg(self, desc):
        defs = ('<defs>'
                '<pattern id="hatch-{id}" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                '<line class="hatchln" x1="0" y1="0" x2="0" y2="8"/></pattern>'
                '<marker id="tick" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="6" markerHeight="6" orient="auto">'
                '<line class="dimln" x1="3" y1="0" x2="3" y2="6"/></marker></defs>')
        pid = self.title.replace(" ", "").lower()
        body = "".join(self.parts + self.top).replace("url(#hatch)", f"url(#hatch-{pid})")
        return (f'<svg class="plan" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t-{pid}">'
                f'<title id="t-{pid}">{esc(desc)}</title>' + defs.replace("{id}", pid) + body + '</svg>')


def scalebar(p, x, y):
    p.line(x, y, x + 5, y, "scale", top=True)
    p.line(x, y - 0.25, x, y + 0.25, "scale", top=True)
    p.line(x + 5, y - 0.25, x + 5, y + 0.25, "scale", top=True)
    p.text(x + 5.4, y + 0.3, "5 ft", "rd")


def main_plan():
    S = 14
    p = Plan(S, 20 + 8.5 * S, 22, round(20 + 8.5*S + 40.5*S + 24), round(22 + 27.5*S + 46), "main")
    # deck
    p.rect(-8.5, 0, 0, 16, "deck")
    p.text(-4.25, 8.3, "Deck", "sl", "middle")
    p.text(-4.25, 9.3, "8'-6\" × 16'", "rd", "middle")
    # exterior
    p.poly([(0, 0), (36.33, 0), (36.33, 16.0), (40.5, 16.0), (40.5, 27.5), (0, 27.5)], "slab")
    p.poly([(0.5, 0.5), (35.83, 0.5), (35.83, 16.5), (40, 16.5), (40, 27), (0.5, 27)], "hall")
    # rooms
    p.room(0.5, 0.5, 11, 15.17, "Dining nook", "10'-6\" × 14'-8\"", "roomo", lx=0.9, ly=1.6)
    p.room(11, 0.5, 23, 12.67, "Kitchen", "12'-0\" × 12'-2\"", "roomo", lx=11.4, ly=4.3)
    p.room(23.3, 0.5, 30.6, 5.9, "Pantry", "", "svc", lx=23.7, ly=3.4)
    p.room(24.6, 6.3, 30.6, 11.8, "Powder", "", "svc", lx=25.0, ly=9.3)
    p.room(31, 0.5, 35.83, 10.83, "Mudroom", "", "svc", lx=31.4, ly=3.4)
    p.room(0.5, 15.17, 14.67, 27, "Great room", "14'-2\" × 11'-10\"", "roomo", lx=0.9, ly=21.6)
    p.room(15.17, 17, 25.17, 27, "Office (den)", "10'-0\" × 10'-0\"", lx=15.5, ly=20.0)
    p.room(25.6, 17, 32.9, 27, "Stairs", "", "svc", lx=26.0, ly=17.95)
    p.room(33.3, 16.33, 40, 27, "Foyer", "6'-8\" × 10'-8\"", lx=33.7, ly=19.3)
    # stair treads
    for i in range(11):
        yy = 18.2 + i * 0.75
        p.line(26.0, yy, 32.5, yy, "tread")
    p.line(29.25, 17.6, 29.25, 26.0, "tread")
    # builder fixtures
    p.furn(11, 0.5, 20.5, 2.67, "Counter + cooktop", "fix")
    p.furn(20.5, 0.5, 23, 2.67, "Ovens", "fix")
    p.furn(21.3, 5.4, 23, 8.6, "Fridge", "fix")
    p.furn(12.9, 6.2, 19.9, 10.2, "Island (sink, DW)", "fix", lab_dy=-0.5)
    p.line(12.9, 9.2, 19.9, 9.2, "fixln")
    p.furn(4.6, 26.35, 10.6, 27, "", "fire")
    # walls with openings
    p.window_v(4.0, 11.0, 0.25)
    p.window_v(19.5, 26.5, 0.25)
    p.door_v(15.4, 18.07, 0.5, 1, "top")
    p.door_h(17.2, 19.53, 17, 1, "left")
    p.door_h(19.53, 21.87, 17, 1, "right")
    p.door_h(35.6, 39.1, 27, -1, "right")
    p.door_h(26.0, 28.67, 27, -1, "left")
    p.door_v(7.0, 9.67, 35.83, -1, "top")
    p.text(37.2, 6.5, "to garage", "rd")
    # rugs (under furniture)
    p.rect(2.58, 18.6, 12.58, 26.1, "rug")
    p.rect(16.17, 20.6, 24.17, 25.6, "rug")
    # dining
    p.furn(4.25, 4.6, 7.25, 10.6, "Table 72×36\"")
    for (x1, y1, x2, y2) in [(2.65, 5.25, 4.1, 6.75), (2.65, 8.45, 4.1, 9.95), (7.4, 5.25, 8.85, 6.75), (7.4, 8.45, 8.85, 9.95), (5.0, 3.05, 6.5, 4.45), (5.0, 10.75, 6.5, 12.15)]:
        p.furn(x1, y1, x2, y2, "", "chair", rx=3)
    # stools
    for cx in (14.3, 16.4, 18.5):
        p.circle(cx, 10.95, 0.72, "chair")
    p.text(16.4, 12.45, "3 counter stools", "fl", "middle")
    # living
    p.furn(3.92, 16.4, 11.25, 19.57, "Sofa bed 88\"")
    p.rect(5.08, 19.57, 10.08, 23.9, "ghost", extra='rx="2"')
    p.text(7.58, 23.35, "bed open", "ghl", "middle")
    p.circle(9.1, 21.4, 0.8, "chair")
    p.circle(12.25, 17.95, 0.72, "furn")
    p.circle(13.75, 18.95, 0.42, "lamp")
    p.line(5.2, 26.15, 9.97, 26.15, "tv", top=True)
    p.text(1.0, 25.0, "65\" TV over", "fl")
    p.text(1.0, 25.9, "fireplace", "fl")
    # office
    p.furn(17.67, 21.3, 22.67, 23.63, "Desk 60\"")
    p.circle(20.17, 24.75, 0.95, "chair")
    p.furn(22.5, 17.1, 25.07, 18.1, "Shelf", lab_dy=0.05)
    p.circle(16.0, 26.2, 0.42, "lamp")
    # dims
    p.dim(0.5, 7.6, 4.25, 7.6, ft(4.25 - 0.5), ty=7.35)
    p.dim(5.75, 12.15, 5.75, 16.4, ft(16.4 - 12.15), tx=6.05, ty=14.5, anchor="start")
    p.dim(7.58, 23.9, 7.58, 27.0, ft(27 - 23.9), tx=7.88, ty=25.25, anchor="start")
    p.dim(0.5, 17.4, 3.92, 17.4, ft(3.92 - 0.5), ty=17.15)
    p.dim(23.4, 23.63, 23.4, 27.0, ft(27 - 23.63), tx=23.6, ty=25.5, anchor="start")
    scalebar(p, 26.0, 29.6)
    p.text(0, 29.9, "Main floor · 1,078 sq ft · north is up", "rd")
    return p.svg("Main floor plan with furniture: dining nook, kitchen with three stools, great room with sofa bed facing the electric fireplace and TV, and office with desk.")


def upper_plan():
    S = 14
    p = Plan(S, 20, 22, round(20 + 54.67*S + 20), round(22 + 27.5*S + 46), "upper")
    p.poly([(0, 0), (54.67, 0), (54.67, 27.5), (0, 27.5)], "slab")
    p.poly([(0.5, 0.5), (54.17, 0.5), (54.17, 27), (0.5, 27)], "hall")
    p.room(0.5, 0.5, 14.67, 14.83, "Primary bedroom", "14'-2\" × 14'-4\"", lx=0.9, ly=10.4)
    p.room(15.17, 0.5, 25.5, 11.33, "Ensuite", "5-piece", "svc", lx=15.6, ly=6.0)
    p.room(25.83, 0.5, 33.17, 8.17, "Walk-in", "", "svc", lx=26.3, ly=4.6)
    p.room(25.83, 8.5, 33.17, 14.17, "Laundry", "", "svc", lx=26.3, ly=11.6)
    p.room(33.5, 0.5, 41.33, 5.33, "Closet", "", "svc", lx=34.0, ly=3.3)
    p.room(33.5, 5.67, 41.33, 14.17, "Bath", "", "svc", lx=34.0, ly=10.3)
    p.room(21.9, 11.67, 25.5, 14.17, "Linen", "", "svc", lx=22.2, ly=13.3)
    p.room(41.67, 0.5, 54.17, 12.83, "Bedroom 3", "12'-6\" × 12'-4\"", lx=42.1, ly=9.2)
    p.room(15.17, 14.67, 26.17, 27, "Bonus room", "11'-0\" × 12'-4\"", lx=15.6, ly=16.0)
    p.room(41.67, 14.67, 54.17, 27, "Bedroom 2", "11'-6\" × 12'-4\"", lx=46.2, ly=17.4)
    p.room(41.67, 20.5, 45.67, 25.17, "W.I.C.", "", "svc", lx=42.0, ly=23.2)
    p.room(26.5, 17.5, 33.83, 27, "Stairs", "", "svc", lx=26.9, ly=26.3)
    p.rect(0.5, 15.33, 14.67, 27, "openbg")
    p.rect(0.5, 15.33, 14.67, 27, "open")
    p.text(7.58, 21.0, "Open to great room below", "sl", "middle")
    p.rect(33.83, 17.5, 41.33, 27, "openbg")
    p.rect(33.83, 17.5, 41.33, 27, "open")
    p.text(37.58, 22.0, "Open to", "sl", "middle")
    p.text(37.58, 22.9, "foyer", "sl", "middle")
    for i in range(11):
        yy = 18.6 + i * 0.75
        p.line(26.9, yy, 33.4, yy, "tread")
    p.line(15.17, 15.33, 15.17, 27, "rail", top=True)
    p.line(26.17, 17.5, 26.17, 27, "rail", top=True)
    # windows
    p.window_v(4.0, 11.0, 0.25)
    p.window_v(17.5, 24.5, 0.25)
    p.window_v(3.5, 9.5, 54.42)
    p.window_v(17.5, 23.5, 54.42)
    # doors
    p.door_h(12.0, 14.5, 14.83, -1, "right")
    p.door_v(2.5, 4.83, 14.67, 1, "top")
    p.door_h(42.0, 44.33, 12.83, -1, "left")
    p.door_v(1.5, 3.83, 41.67, -1, "top")
    p.door_h(42.0, 44.5, 14.67, 1, "left")
    # rugs
    p.rect(2.58, 4.3, 12.58, 12.3, "rug")
    p.rect(16.17, 19.5, 25.17, 25.5, "rug")
    # primary
    p.furn(4.17, 0.5, 11.0, 7.83, "King bed", lab_dy=0.6)
    p.rect(4.6, 0.9, 7.4, 2.1, "pillow", extra='rx="3"')
    p.rect(7.77, 0.9, 10.57, 2.1, "pillow", extra='rx="3"')
    p.furn(1.9, 0.5, 3.9, 2.0, "", rx=2)
    p.furn(11.27, 0.5, 13.27, 2.0, "", rx=2)
    p.furn(2.0, 13.33, 7.0, 14.83, "Dresser (later)", "later")
    # bedroom 3
    p.furn(44.5, 0.5, 51.33, 7.83, "King bed", lab_dy=0.6)
    p.rect(44.9, 0.9, 47.7, 2.1, "pillow", extra='rx="3"')
    p.rect(48.13, 0.9, 50.93, 2.1, "pillow", extra='rx="3"')
    p.furn(42.83, 0.5, 44.33, 1.83, "", rx=2)
    p.furn(51.5, 0.5, 53.0, 1.83, "", rx=2)
    # bonus
    p.furn(16.9, 20.2, 19.4, 22.6, "Chair", "chair", rx=8)
    p.furn(21.94, 20.2, 24.44, 22.6, "Chair", "chair", rx=8)
    p.circle(20.67, 24.25, 1.33, "furn")
    p.text(20.67, 24.55, "Table", "fl", "middle")
    p.circle(25.2, 19.0, 0.42, "lamp")
    p.text(20.67, 26.6, "Feature wall", "fxl", "middle")
    # bedroom 2 note
    p.text(50.0, 25.0, "Later: guest room", "rd", "middle")
    p.text(50.0, 25.9, "or second office", "rd", "middle")
    # dims
    p.dim(9.5, 7.83, 9.5, 13.33, ft(13.33 - 7.83), tx=9.8, ty=12.2, anchor="start")
    p.dim(0.5, 5.4, 4.17, 5.4, ft(4.17 - 0.5), ty=5.15)
    p.dim(50.5, 7.83, 50.5, 12.83, ft(12.83 - 7.83), tx=50.8, ty=10.6, anchor="start")
    p.dim(51.33, 5.4, 54.17, 5.4, ft(54.17 - 51.33), ty=5.15)
    p.dim(23.2, 14.67, 23.2, 20.2, ft(20.2 - 14.67), tx=23.5, ty=18.0, anchor="start")
    scalebar(p, 26.6, 29.6)
    p.text(0, 29.9, "Upper floor · 1,167 sq ft · north is up", "rd")
    return p.svg("Upper floor plan with furniture: king bed in the primary bedroom and bedroom 3, two chairs and a round table in the bonus room, bedroom 2 left for later.")

# ---------------------------------------------------------------- room scenes
W, H, FL = 800, 450, 382

def scene(inner, label):
    floor = (f'<rect x="0" y="{FL}" width="{W}" height="{H-FL}" fill="#C9A57A"/>'
             + "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#B8925F" stroke-width="1"/>' for y in (398, 418, 440))
             + f'<rect x="0" y="{FL-10}" width="{W}" height="10" fill="#F6F2EA"/>')
    return (f'<svg class="scene" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">'
            f'<rect width="{W}" height="{FL}" fill="#ECE6DC"/>' + floor + inner + '</svg>')

def lamp_table(cx, base_y, h=46, shade="#F4F0EA", base="#E6DED1"):
    return (f'<rect x="{cx-11}" y="{base_y-h}" width="22" height="{h}" rx="9" fill="{base}"/>'
            f'<polygon points="{cx-26},{base_y-h} {cx+26},{base_y-h} {cx+18},{base_y-h-38} {cx-18},{base_y-h-38}" fill="{shade}"/>')

def plant(x, y):
    return (f'<rect x="{x-22}" y="{y-46}" width="44" height="46" rx="6" fill="#B9A78E"/>'
            f'<ellipse cx="{x-14}" cy="{y-92}" rx="18" ry="40" fill="#6E7A52" transform="rotate(-20 {x-14} {y-92})"/>'
            f'<ellipse cx="{x+14}" cy="{y-100}" rx="17" ry="44" fill="#5E6A45" transform="rotate(18 {x+14} {y-100})"/>'
            f'<ellipse cx="{x}" cy="{y-118}" rx="14" ry="42" fill="#7B8760"/>')

def window(x, y, w, h, curtains=True):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#2B2826"/>'
         f'<rect x="{x+6}" y="{y+6}" width="{w-12}" height="{h-12}" fill="#D3DEE0"/>'
         f'<line x1="{x+w/2}" y1="{y+6}" x2="{x+w/2}" y2="{y+h-6}" stroke="#2B2826" stroke-width="5"/>'
         f'<polygon points="{x+12},{y+h-12} {x+w*0.45},{y+12} {x+w*0.55},{y+12} {x+22},{y+h-12}" fill="#E4ECEE" opacity=".7"/>')
    if curtains:
        s += (f'<rect x="{x-34}" y="{y-40}" width="42" height="{FL-10-(y-40)}" fill="#F7F3EC" opacity=".92"/>'
              f'<rect x="{x+w-8}" y="{y-40}" width="42" height="{FL-10-(y-40)}" fill="#F7F3EC" opacity=".92"/>'
              f'<line x1="{x-44}" y1="{y-42}" x2="{x+w+44}" y2="{y-42}" stroke="#2B2826" stroke-width="3"/>')
    return s

def living():
    s = window(46, 96, 120, 200)
    s += '<rect x="214" y="0" width="372" height="372" fill="#3E3933"/>'
    s += "".join(f'<rect x="{x}" y="0" width="7" height="372" fill="#4A443D"/>' for x in range(220, 586, 14))
    s += '<rect x="244" y="298" width="312" height="56" rx="2" fill="#1C1A18"/>'
    s += '<rect x="258" y="316" width="284" height="20" rx="4" fill="#C8742E"/>'
    s += '<rect x="270" y="322" width="260" height="8" rx="4" fill="#F0B85A"/>'
    s += '<rect x="286" y="138" width="228" height="132" rx="3" fill="#121110"/>'
    s += '<rect x="291" y="143" width="218" height="122" fill="#1F2225"/>'
    s += '<polygon points="291,265 360,143 400,143 331,265" fill="#2A2F33"/>'
    s += plant(640, 382)
    s += '<path d="M742 382 L742 120 Q742 70 640 92" fill="none" stroke="#B8964F" stroke-width="5"/>'
    s += '<path d="M612 104 A30 30 0 0 1 672 104 Z" fill="#B8964F"/>'
    s += '<rect x="716" y="374" width="52" height="10" rx="5" fill="#2B2826"/>'
    s += '<polygon points="96,450 704,450 664,400 136,400" fill="#BFB3A2"/>'
    s += '<rect x="196" y="304" width="58" height="40" rx="10" fill="#4F5638"/>'
    s += '<rect x="250" y="300" width="56" height="44" rx="12" fill="#EFE9DF"/>'
    s += '<rect x="494" y="300" width="56" height="44" rx="12" fill="#EFE9DF"/>'
    s += '<rect x="546" y="304" width="58" height="40" rx="10" fill="#4F5638"/>'
    s += '<rect x="150" y="326" width="500" height="100" rx="22" fill="#CFC4B3"/>'
    s += '<rect x="150" y="326" width="500" height="22" rx="11" fill="#D9CFBF"/>'
    s += '<rect x="126" y="340" width="44" height="86" rx="16" fill="#C6BAA8"/>'
    s += '<rect x="630" y="340" width="44" height="86" rx="16" fill="#C6BAA8"/>'
    return scene(s, "Great room: fluted feature wall with linear electric fireplace and 65-inch TV above, sofa bed in linen with olive pillows, sheer curtains and an arc floor lamp.")

def dining():
    s = window(300, 92, 200, 210)
    s += '<line x1="400" y1="0" x2="400" y2="112" stroke="#2B2826" stroke-width="2"/>'
    s += '<rect x="318" y="112" width="164" height="6" rx="3" fill="#B8964F"/>'
    s += "".join(f'<line x1="{x}" y1="118" x2="{x}" y2="132" stroke="#B8964F" stroke-width="2"/><circle cx="{x}" cy="146" r="16" fill="#F5F0E7" stroke="#D9D0C2"/>' for x in (346, 400, 454))
    for x in (262, 470):
        s += f'<rect x="{x}" y="218" width="68" height="84" rx="22" fill="#E9E3D8"/>'
    s += '<rect x="206" y="292" width="388" height="13" rx="2" fill="#B8925F"/>'
    s += '<rect x="214" y="305" width="372" height="10" fill="#A47F50"/>'
    s += '<rect x="226" y="315" width="14" height="67" fill="#A47F50"/><rect x="560" y="315" width="14" height="67" fill="#A47F50"/>'
    for (bx, sx, legs) in ((118, 132, (138, 182)), (664, 612, (614, 660))):
        s += f'<rect x="{bx}" y="236" width="18" height="98" rx="8" fill="#E9E3D8"/>'
        s += f'<rect x="{min(bx, sx)}" y="320" width="74" height="18" rx="8" fill="#E9E3D8"/>'
        s += "".join(f'<rect x="{lx}" y="338" width="6" height="44" fill="#B8925F"/>' for lx in legs)
    s += '<rect x="388" y="258" width="24" height="34" rx="9" fill="#E7E1D6"/>'
    s += '<path d="M400 258 Q392 220 372 196 M400 258 Q406 214 428 192 M400 258 L400 206" fill="none" stroke="#6B4A33" stroke-width="2"/>'
    s += "".join(f'<ellipse cx="{x}" cy="{y}" rx="7" ry="4" fill="#6E7A52"/>' for x, y in ((378, 204), (424, 198), (400, 210), (386, 222), (414, 216)))
    s += '<rect x="290" y="288" width="60" height="4" rx="2" fill="#2B2826"/><rect x="452" y="288" width="60" height="4" rx="2" fill="#2B2826"/>'
    return scene(s, "Dining nook: oak table for six with ivory boucle chairs, a brass three-globe pendant and sheer curtains on the west window.")

def kitchen():
    s = '<rect x="60" y="56" width="250" height="150" fill="#E2DCD1"/><rect x="490" y="56" width="250" height="150" fill="#E2DCD1"/>'
    s += "".join(f'<line x1="{x}" y1="56" x2="{x}" y2="206" stroke="#D3CBBE" stroke-width="2"/>' for x in (143, 226, 573, 656))
    s += '<polygon points="330,56 470,56 470,150 446,206 354,206 330,150" fill="#EAE4DA"/>'
    s += '<rect x="60" y="206" width="680" height="72" fill="#F3F0EB"/>'
    s += '<rect x="56" y="276" width="688" height="10" fill="#F5F3EF"/><rect x="60" y="286" width="680" height="86" fill="#E2DCD1"/>'
    s += "".join(f'<line x1="{x}" y1="286" x2="{x}" y2="372" stroke="#D3CBBE" stroke-width="2"/>' for x in (170, 280, 390, 500, 610))
    s += "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="160" stroke="#2B2826" stroke-width="2"/><path d="M{x-28} 190 A28 28 0 0 1 {x+28} 190 Z" fill="#B8964F"/>' for x in (270, 400, 530))
    s += '<rect x="132" y="296" width="536" height="14" rx="2" fill="#F5F3EF"/><rect x="140" y="310" width="520" height="116" fill="#2E2B28"/>'
    s += "".join(f'<line x1="{x}" y1="316" x2="{x}" y2="420" stroke="#3A3633" stroke-width="2"/>' for x in range(170, 660, 30))
    s += '<ellipse cx="584" cy="290" rx="34" ry="8" fill="#B8925F"/><circle cx="574" cy="282" r="9" fill="#C8742E"/><circle cx="592" cy="281" r="9" fill="#9CA36A"/>'
    s += '<rect x="214" y="286" width="70" height="10" rx="3" fill="#6B4A33"/>'
    for cx in (270, 400, 530):
        s += (f'<line x1="{cx-22}" y1="356" x2="{cx-30}" y2="446" stroke="#B8925F" stroke-width="6"/>'
              f'<line x1="{cx+22}" y1="356" x2="{cx+30}" y2="446" stroke="#B8925F" stroke-width="6"/>'
              f'<line x1="{cx-27}" y1="414" x2="{cx+27}" y2="414" stroke="#B8925F" stroke-width="4"/>'
              f'<rect x="{cx-34}" y="342" width="68" height="16" rx="8" fill="#EFE9DF"/>')
    return scene(s, "Kitchen island seen from the great room: three backless oak counter stools with ivory boucle seats and three brass dome pendants.")

def office():
    s = '<rect width="800" height="372" fill="#E1D9CC"/>'
    s += '<rect x="292" y="58" width="216" height="150" fill="#2B2826"/><rect x="302" y="68" width="196" height="130" fill="#F4F0EA"/>'
    s += '<path d="M330 198 L330 140 A40 40 0 0 1 410 140 L410 198 Z" fill="#A8998A"/><circle cx="452" cy="112" r="24" fill="#4F5638"/><rect x="420" y="160" width="58" height="38" fill="#B8964F"/>'
    s += '<rect x="342" y="170" width="116" height="118" rx="26" fill="#2B2826"/>'
    s += '<rect x="330" y="214" width="140" height="64" rx="4" fill="#3A3735"/><rect x="392" y="278" width="16" height="6" fill="#3A3735"/>'
    s += '<rect x="214" y="284" width="372" height="13" rx="2" fill="#6B4A33"/>'
    s += '<rect x="230" y="297" width="6" height="85" fill="#2B2826"/><rect x="564" y="297" width="6" height="85" fill="#2B2826"/><rect x="230" y="372" width="340" height="5" fill="#2B2826"/>'
    s += '<rect x="516" y="276" width="34" height="8" rx="3" fill="#B8964F"/><line x1="533" y1="276" x2="552" y2="232" stroke="#B8964F" stroke-width="4"/><line x1="552" y1="232" x2="520" y2="214" stroke="#B8964F" stroke-width="4"/><path d="M502 222 L530 206 L536 226 Z" fill="#B8964F"/>'
    s += '<rect x="250" y="276" width="44" height="8" rx="2" fill="#EFE9DF"/><rect x="254" y="268" width="36" height="8" rx="2" fill="#A8998A"/>'
    s += '<line x1="120" y1="168" x2="120" y2="380" stroke="#2B2826" stroke-width="4"/><rect x="98" y="374" width="44" height="8" rx="4" fill="#2B2826"/><polygon points="90,168 150,168 142,124 98,124" fill="#F4F0EA"/>'
    s += plant(680, 382)
    s += '<polygon points="130,450 670,450 640,398 160,398" fill="#BFB3A2"/>'
    return scene(s, "Office: walnut desk floating in the room facing the doors, black task chair, framed art as the video-call backdrop, brass desk lamp and a floor lamp.")

def bonus():
    s = '<rect x="250" y="0" width="300" height="372" fill="#6B4A33"/>'
    s += "".join(f'<rect x="{x}" y="0" width="6" height="372" fill="#7C5A3F"/>' for x in range(256, 550, 16))
    s += '<rect x="292" y="120" width="216" height="64" rx="2" fill="#1C1A18"/><rect x="304" y="140" width="192" height="22" rx="4" fill="#C8742E"/><rect x="316" y="146" width="168" height="9" rx="4" fill="#F0B85A"/>'
    s += '<rect x="20" y="244" width="160" height="7" fill="#2B2826"/>' + "".join(f'<rect x="{x}" y="251" width="3" height="121" fill="#2B2826"/>' for x in range(28, 178, 16))
    s += '<rect x="606" y="110" width="110" height="140" fill="#B8925F"/><rect x="614" y="118" width="94" height="124" fill="#F4F0EA"/><path d="M630 242 L630 190 A31 31 0 0 1 692 190 L692 242 Z" fill="#4F5638"/>'
    s += '<polygon points="140,450 680,450 640,396 180,396" fill="#BFB3A2"/>'
    for cx in (318, 500):
        s += (f'<rect x="{cx-64}" y="276" width="128" height="114" rx="38" fill="#4F5638"/>'
              f'<rect x="{cx-48}" y="314" width="96" height="34" rx="14" fill="#5D6644"/>'
              f'<rect x="{cx-50}" y="388" width="8" height="14" fill="#2B2826"/><rect x="{cx+42}" y="388" width="8" height="14" fill="#2B2826"/>')
    s += '<ellipse cx="409" cy="392" rx="70" ry="12" fill="#D9CFBF"/><rect x="384" y="392" width="50" height="40" fill="#CFC3B1"/><ellipse cx="409" cy="432" rx="34" ry="6" fill="#C2B5A2"/>'
    s += '<rect x="394" y="374" width="30" height="12" rx="3" fill="#2B2826"/><rect x="398" y="368" width="22" height="6" rx="2" fill="#B8964F"/>'
    s += '<line x1="740" y1="150" x2="740" y2="380" stroke="#B8964F" stroke-width="4"/><rect x="718" y="374" width="44" height="8" rx="4" fill="#B8964F"/><polygon points="712,150 768,150 760,108 720,108" fill="#F4F0EA"/>'
    return scene(s, "Bonus room: walnut slat feature wall with a linear fireplace, two olive velvet barrel chairs, a round stone-look table and the stair railing at left.")

def primary():
    s = '<rect width="800" height="372" fill="#E6DFD4"/>'
    for (x1, x2) in ((60, 220), (240, 560), (580, 740)):
        s += f'<rect x="{x1}" y="52" width="{x2-x1}" height="130" fill="none" stroke="#D3C9BB" stroke-width="3"/>'
        s += f'<rect x="{x1}" y="200" width="{x2-x1}" height="150" fill="none" stroke="#D3C9BB" stroke-width="3"/>'
    s += '<rect x="226" y="150" width="348" height="190" rx="12" fill="#CFC4B3"/>' + "".join(f'<line x1="{x}" y1="160" x2="{x}" y2="330" stroke="#C1B5A2" stroke-width="3"/>' for x in range(262, 560, 34))
    s += '<rect x="252" y="250" width="140" height="44" rx="14" fill="#F7F4EE"/><rect x="408" y="250" width="140" height="44" rx="14" fill="#F7F4EE"/>'
    s += '<rect x="330" y="282" width="140" height="28" rx="10" fill="#4F5638"/>'
    s += '<rect x="204" y="300" width="392" height="74" rx="10" fill="#F2EEE7"/><rect x="204" y="340" width="392" height="22" fill="#A8998A"/><rect x="212" y="372" width="376" height="20" rx="4" fill="#CFC4B3"/>'
    for nx in (108, 612):
        s += f'<rect x="{nx}" y="296" width="80" height="86" rx="3" fill="#6B4A33"/><line x1="{nx+6}" y1="324" x2="{nx+74}" y2="324" stroke="#5A3E2B" stroke-width="2"/><line x1="{nx+6}" y1="352" x2="{nx+74}" y2="352" stroke="#5A3E2B" stroke-width="2"/>'
        s += f'<circle cx="{nx+40}" cy="310" r="3" fill="#B8964F"/><circle cx="{nx+40}" cy="338" r="3" fill="#B8964F"/>'
        s += lamp_table(nx + 40, 296, 52, "#F4F0EA", "#B8964F")
    s += '<polygon points="120,450 680,450 650,404 150,404" fill="#BFB3A2"/>'
    return scene(s, "Primary bedroom: picture-frame moulding feature wall, channel-tufted linen king headboard, ivory bedding with taupe throw and olive lumbar pillow, walnut nightstands with brass lamps.")

def bed3():
    s = '<rect x="296" y="62" width="208" height="150" fill="#B8925F"/><rect x="304" y="70" width="192" height="134" fill="#F4F0EA"/>'
    s += '<path d="M322 204 L322 150 A50 50 0 0 1 422 150 L422 204 Z" fill="#A8998A"/><circle cx="452" cy="112" r="22" fill="#4F5638"/><line x1="440" y1="182" x2="486" y2="182" stroke="#B8964F" stroke-width="5"/>'
    s += '<rect x="236" y="236" width="328" height="92" rx="6" fill="#6B4A33"/>'
    s += '<rect x="258" y="262" width="132" height="40" rx="14" fill="#F2EEE7"/><rect x="410" y="262" width="132" height="40" rx="14" fill="#F2EEE7"/>'
    s += '<rect x="220" y="298" width="360" height="76" rx="8" fill="#3B3733"/><rect x="220" y="298" width="360" height="16" rx="6" fill="#F2EEE7"/><rect x="226" y="372" width="348" height="18" fill="#6B4A33"/>'
    for nx in (142, 592):
        s += f'<rect x="{nx}" y="312" width="66" height="70" rx="3" fill="#B8925F"/><line x1="{nx+6}" y1="340" x2="{nx+60}" y2="340" stroke="#A47F50" stroke-width="2"/>'
        s += lamp_table(nx + 33, 312, 40, "#F4F0EA", "#2B2826")
    s += '<rect x="726" y="40" width="48" height="332" fill="#F7F3EC" opacity=".92"/><line x1="700" y1="38" x2="800" y2="38" stroke="#2B2826" stroke-width="3"/>'
    return scene(s, "Bedroom 3: low walnut king bed with charcoal duvet, oak nightstands with black lamps and a large framed abstract print.")

# ---------------------------------------------------------------- content data
MOVE, SOON, LATER = "Move-in", "Months 1–3", "Later"
ROOMS = [
 dict(id="great-room", name="Great room", floor="Main floor", dims="14'-2\" × 11'-10\", open to above", scene=living,
      photos=[("images/great-room-staged-1.jpg", "Staged listing photo: sectional facing the black-frame fireplace wall, two accent chairs by the window."),
              ("images/great-room-staged-2.jpg", "Staged listing photo, second angle: sectional along the east side with a wood and marble coffee table.")],
      notes=["The sofa bed faces the electric fireplace on the south wall. The 65-inch TV mounts above the fireplace, so no media console takes up floor space.",
             "Skip a fixed coffee table. A pouf and a small side table move out of the way when the bed opens.",
             "The room is two storeys tall. Hang the sheer curtains from just under the upper window so the wall feels finished."],
      checks=[("ok", "Sofa to TV viewing distance is about 8'-6\", right for a 65-inch screen."),
              ("ok", f"With the bed open, {ft(27-23.9)} is left to the fireplace wall."),
              ("ok", f"Path to the deck door, beside the sofa: {ft(3.92-0.5)}."),
              ("ok", f"Walkway between the dining chairs and the sofa back: {ft(16.4-12.15)}."),
              ("warn", "A TV mount above a fireplace needs wood blocking behind the drywall. Ask the builder if it was installed.")],
      items=[("Sofa bed with queen pull-out, performance linen-look fabric in greige", "86–90\" W × 36–38\" D; about 90\" open", "Structube, Wayfair.ca, The Brick", 1800, MOVE),
             ("65-inch 4K TV", "about 57\" W × 33\" H", "Costco", 800, MOVE),
             ("Low-profile tilting wall mount and in-wall cord kit", "matches the TV's VESA pattern", "Costco, Best Buy", 120, MOVE),
             ("Pouf in leather or bouclé", "20\" round", "Structube, HomeSense", 150, SOON),
             ("Round side table, walnut or travertine-look", "18–20\" round", "Structube, Article", 150, SOON),
             ("Low-pile rug in warm greige", "8' × 10'", "Wayfair.ca, Costco, HomeSense", 350, SOON),
             ("Brass arc floor lamp", "about 70\" tall", "Structube, Article", 180, SOON),
             ("Linen sheer curtains, 2 panels, hung high", "for an 84\" × 60\" window", "IKEA, HomeSense", 120, SOON),
             ("Pillows (2 olive velvet, 2 ivory bouclé) and a chunky throw", "", "HomeSense, Costco", 120, LATER)]),
 dict(id="dining", name="Dining nook", floor="Main floor", dims="10'-6\" × 14'-8\", 8\" dropped ceiling", scene=dining,
      notes=["The table runs north to south under the window, so chairs pull out freely on every side.",
             "The nook has a ceiling dropped by 8 inches. Hang the pendant 30–34 inches above the tabletop."],
      checks=[("ok", f"Table to the west wall: {ft(4.25-0.5)}. Chairs need 3'-0\" to pull out."),
              ("ok", f"Table to the north wall: {ft(4.6-0.5)}."),
              ("ok", f"Table to the kitchen edge: {ft(11-7.25)}, so the kitchen path stays open.")],
      items=[("Oak dining table", "72\" × 36–40\", seats 6", "Structube, Article", 900, MOVE),
             ("6 upholstered dining chairs, ivory bouclé or greige on oak or black legs", "18–20\" W each, about $130 each", "Structube, Wayfair.ca", 780, MOVE),
             ("Brass and opal-glass pendant, linear or 3-globe", "36–48\" long", "Wayfair.ca, Structube", 250, LATER),
             ("Linen sheer curtains for the nook window", "for an 84\" × 60\" window", "IKEA, HomeSense", 100, LATER)]),
 dict(id="kitchen", name="Kitchen", floor="Main floor", dims="12'-0\" × 12'-2\", island with 12\" eating bar", scene=kitchen,
      notes=["The seller is including Whirlpool appliances, so only stools and a few styling pieces are on the list.",
             "The cabinets in the drawing are generic. Your builder's finishes will look different."],
      checks=[("ok", "Three stools fit along the island at 24-inch spacing."),
              ("warn", "The eating bar overhang is only 12 inches, which leaves little knee room. Choose backless or low-back stools with a 24–26 inch seat that slide fully under the counter.")],
      items=[("3 counter stools, backless or low-back, oak legs with bouclé seat", "24–26\" seat height, 16–18\" wide", "Structube, Article, Wayfair.ca", 450, SOON),
             ("Counter styling: wood board, stone tray, fruit bowl", "", "HomeSense", 80, LATER)]),
 dict(id="office", name="Office", floor="Main floor", dims="10'-0\" × 10'-0\", double doors", scene=office,
      notes=["The desk floats in the middle of the room facing the double doors, with your back to the south wall. Whatever hangs behind you becomes your video-call backdrop.",
             "The shelf goes in the corner beside the doors, where it stays clear of the door swing."],
      checks=[("ok", f"The open doors clear the desk by {ft(21.3-19.33)}."),
              ("ok", f"Chair roll-back space behind the desk: {ft(27-23.63)}."),
              ("warn", "The builder plans show no window in this room. Its south wall is a fire-rated wall with no openings. Plan on a bright desk lamp and a floor lamp with 4000K bulbs, and confirm at the walkthrough.")],
      items=[("Desk in walnut or oak, open legs", "60\" × 28–30\"", "Structube, Article", 400, MOVE),
             ("Ergonomic task chair with adjustable lumbar support", "", "Costco, Staples", 300, MOVE),
             ("Desk lamp and floor lamp, 4000K bulbs", "", "Structube, Costco", 200, MOVE),
             ("Bookshelf, black metal and wood", "31\" W × 12\" D", "Structube, Wayfair.ca", 200, SOON),
             ("Rug", "5' × 8'", "Wayfair.ca, HomeSense", 150, LATER),
             ("Large framed art behind the desk", "30\" × 40\"", "HomeSense, a local print shop", 150, LATER)]),
 dict(id="bonus", name="Bonus room", floor="Upper floor", dims="11'-0\" × 12'-4\", 12\" raised ceiling", scene=bonus,
      notes=["Two chairs face the feature wall, with a round table in front of them.",
             "The room opens to the great room and the stairs on two sides, so keep both railing sides clear."],
      checks=[("ok", f"Walkway behind the chairs: {ft(20.2-14.67)}."),
              ("warn", "The listing mentions a fireplace here, but the builder plans show the only fireplace on the main floor. Confirm before you plan this wall.")],
      items=[("2 barrel or swivel accent chairs in olive velvet", "28–30\" W each", "Structube, Article, Wayfair.ca", 700, SOON),
             ("Round coffee table, walnut or travertine-look", "32–36\" round", "Structube, Article", 250, SOON),
             ("Rug", "6' × 9'", "Wayfair.ca, HomeSense", 200, LATER),
             ("Floor lamp", "", "HomeSense", 120, LATER)]),
 dict(id="primary", name="Primary bedroom", floor="Upper floor", dims="14'-2\" × 14'-4\", 12\" raised ceiling", scene=primary,
      notes=["The king bed goes against the north wall. That wall has no windows on the plans, which makes it the natural spot for the feature wall.",
             "Add a dresser on the south wall later. It still leaves room to open the drawers."],
      checks=[("ok", f"Foot of the bed to the dresser: {ft(13.33-7.83)}."),
              ("ok", f"Bed to the window wall: {ft(4.17-0.5)}."),
              ("ok", f"Bed to the ensuite-door wall: {ft(14.67-11.0)}.")],
      items=[("King upholstered bed, channel or panel headboard in greige", "about 82\" W × 88\" L", "Structube, Wayfair.ca, Costco", 800, MOVE),
             ("King mattress, hybrid, medium-firm", "76\" × 80\"", "Costco", 900, MOVE),
             ("King bedding: duvet and insert, sheets, 4 pillows", "", "Costco, HomeSense", 250, MOVE),
             ("Blackout curtains or roller blind", "for an 84\" × 60\" window", "IKEA, Costco, Blinds.ca", 150, MOVE),
             ("2 nightstands in walnut", "22–24\" W", "Structube, Article", 300, SOON),
             ("2 table lamps, brass or ceramic", "", "Structube, HomeSense", 140, SOON),
             ("6-drawer dresser in walnut", "60\" W × 18\" D", "Structube, Article", 500, LATER),
             ("Rug", "8' × 10'", "Wayfair.ca, Costco", 300, LATER)]),
 dict(id="bedroom-3", name="Bedroom 3", floor="Upper floor", dims="12'-6\" × 12'-4\", walk-in closet", scene=bed3,
      notes=["The second king goes here. This is the larger of the two secondary bedrooms.",
             "Use slim nightstands, 18 inches or narrower, so the closet side stays usable."],
      checks=[("ok", f"Foot of the bed to the south wall: {ft(12.83-7.83)}."),
              ("ok", f"Bed to the window wall: {ft(54.17-51.33)}."),
              ("warn", "The walk-in closet door must swing into the closet. If it swings into the bedroom, it will hit the nightstand. Check this on site.")],
      items=[("King bed, low platform in walnut", "about 80\" W × 86\" L", "Structube, Costco, Wayfair.ca", 650, MOVE),
             ("King mattress, hybrid", "76\" × 80\"", "Costco", 900, MOVE),
             ("King bedding set", "", "Costco, HomeSense", 200, MOVE),
             ("Blackout roller blind", "for a 72\" × 60\" window", "IKEA, Blinds.ca", 120, MOVE),
             ("2 slim nightstands", "18\" W maximum", "Structube, Wayfair.ca", 200, SOON),
             ("2 table lamps", "", "HomeSense", 100, SOON),
             ("Large framed print above the bed", "40\" × 30\"", "HomeSense", 120, LATER)]),
 dict(id="bedroom-2", name="Bedroom 2 and entry", floor="Both floors", dims="Bedroom 2 is 11'-6\" × 12'-4\"; foyer is open to above", scene=None,
      notes=["Leave bedroom 2 for later, as a guest room or a second office. A blackout blind now is enough.",
             "The foyer and stairwell are two storeys tall. One large piece of art on the tall wall looks better there than several small ones."],
      checks=[("warn", "The stairs are 3'-6\" wide with a landing. Boxed foam mattresses are easy to carry up, but check the sofa bed and any pre-assembled bed frame against the turn before you order.")],
      items=[("Blackout roller blind for bedroom 2", "for a 72\" × 60\" window", "IKEA, Blinds.ca", 120, MOVE),
             ("Round entry mirror and wall hooks", "30\" round", "HomeSense, Structube", 150, LATER),
             ("Large art for the double-height stair wall", "36\" × 48\" or larger", "Edmonton artists, HomeSense", 250, LATER)]),
]

PROMPT_ITEMS = {
 "great-room": "a 88-inch sofa bed in greige linen facing the fireplace wall, a 65-inch TV mounted above the electric fireplace, a 20-inch leather pouf, a small round walnut side table, an 8x10 low-pile greige rug, a brass arc floor lamp, two olive velvet and two ivory boucle pillows, and linen sheer curtains hung high",
 "dining": "a 72x36-inch natural oak dining table running toward the window, six ivory boucle dining chairs on oak legs, a brass three-globe pendant over the table, and linen sheer curtains",
 "kitchen": "the included Whirlpool stainless appliances, three backless counter stools with oak legs and ivory boucle seats tucked under the island's eating bar, and a walnut board with a bowl of fruit on the counter",
 "office": "a 60-inch walnut desk floating in the middle of the room facing the doors, a black ergonomic chair, a brass desk lamp, a black metal and wood bookshelf in the corner, a 5x8 greige rug, and a large framed abstract print on the wall behind the desk",
 "bonus": "two olive velvet barrel chairs facing the feature wall, a 34-inch round travertine-look coffee table, a 6x9 greige rug and a slim floor lamp, with the railing sides left clear",
 "primary": "a king upholstered bed with a channel-tufted greige linen headboard against the feature wall, ivory bedding with a taupe throw and an olive lumbar pillow, two walnut nightstands with brass table lamps, an 8x10 rug, and blackout linen curtains",
 "bedroom-3": "a low walnut king platform bed with a charcoal duvet and ivory sheets, two slim oak nightstands with black table lamps, and a large framed abstract print in taupe, olive and brass above the bed",
 "bedroom-2": "a round brass-framed entry mirror, a few black wall hooks, and one large abstract artwork on the tall stair wall",
}

def prompt_for(r):
    room = r["name"].lower() if r["id"] != "bedroom-2" else "foyer and stairwell"
    return (f"Virtually stage this empty {room} in a warm modern, lux organic style. Keep the walls, windows, doors, flooring, "
            f"ceiling, light fixtures and any feature wall or fireplace exactly as they are in the photo. Add {PROMPT_ITEMS[r['id']]}. "
            "Colours: warm ivory, linen greige, mushroom taupe, natural oak and walnut, matte black and brushed brass, with olive velvet "
            "as the only accent. Keep it uncluttered with clear walkways. Photorealistic, soft natural daylight, eye-level camera, no text.")

# ---------------------------------------------------------------- totals
phase_tot = {MOVE: 0, SOON: 0, LATER: 0}
for r in ROOMS:
    r["total"] = sum(i[3] for i in r["items"])
    for i in r["items"]:
        phase_tot[i[4]] += i[3]
GRAND = sum(phase_tot.values())
assert GRAND == sum(r["total"] for r in ROOMS)

def money(v): return f"${v:,.0f}"

PHASE_CLS = {MOVE: "p1", SOON: "p2", LATER: "p3"}

# ---------------------------------------------------------------- html
CSS = r"""
/* Layout: one reading column (max 1120px) with a sticky room index; plans and room views break wide. */
:root{
  --bg:#F3F1EC; --surface:#FBFAF7; --ink:#25221F; --muted:#6C655C; --line:#DDD6CB;
  --brass:#8F6F35; --olive:#4F5638; --olive-soft:#E3E5D8; --warn:#9A5B1E; --warn-soft:#F4E7D6;
  --plan-room:#FFFEFB; --plan-svc:#ECE8E1; --plan-wall:#3A3631; --furn:#E6D9C3; --furn-line:#8F6F35; --furn-ink:#3D3428;
  --chair:#D8DCC8; --rug:#EEE6D8; --fix:#E3DFD8; --win:#6E8F98; --deck:#EFE8DC;
  --display:"Marcellus", "Cormorant", Georgia, serif;
  --sans:"Jost", "Avenir Next", "Segoe UI", system-ui, sans-serif;
  --mono:"DM Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#181614; --surface:#211E1B; --ink:#EDE7DD; --muted:#A79D90; --line:#38332E;
  --brass:#CDA862; --olive:#A6B086; --olive-soft:#2C3025; --warn:#E3A867; --warn-soft:#3A2B1C;
  --plan-room:#24211E; --plan-svc:#2D2925; --plan-wall:#D9D1C4; --furn:#4A3F30; --furn-line:#CDA862; --furn-ink:#F1E6D3;
  --chair:#3B4030; --rug:#2F2A24; --fix:#35312C; --win:#8FB4BE; --deck:#2A2622; color-scheme:dark }}
:root[data-theme="dark"]{
  --bg:#181614; --surface:#211E1B; --ink:#EDE7DD; --muted:#A79D90; --line:#38332E;
  --brass:#CDA862; --olive:#A6B086; --olive-soft:#2C3025; --warn:#E3A867; --warn-soft:#3A2B1C;
  --plan-room:#24211E; --plan-svc:#2D2925; --plan-wall:#D9D1C4; --furn:#4A3F30; --furn-line:#CDA862; --furn-ink:#F1E6D3;
  --chair:#3B4030; --rug:#2F2A24; --fix:#35312C; --win:#8FB4BE; --deck:#2A2622; color-scheme:dark }
*{box-sizing:border-box}
body{background:var(--bg); color:var(--ink); font:400 17px/1.65 var(--sans); margin:0}
body::before{content:""; position:fixed; inset:0 0 auto; height:env(safe-area-inset-top,0px); z-index:10; background:var(--bg)}
a{color:inherit}
.wrap{max-width:1120px; margin:0 auto; padding-left:max(16px, env(safe-area-inset-left,0px)); padding-right:max(16px, env(safe-area-inset-right,0px))}
nav.index{position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter:blur(6px); border-bottom:1px solid var(--line)}
nav.index .wrap{display:flex; gap:4px 18px; align-items:center; overflow-x:auto; padding-block:10px; white-space:nowrap; scrollbar-width:none}
nav.index .mark{font-family:var(--display); font-size:19px; margin-right:8px}
nav.index a{font-size:14px; text-decoration:none; color:var(--muted); letter-spacing:.02em}
nav.index a:hover, nav.index a:focus-visible{color:var(--ink)}
a:focus-visible, button:focus-visible{outline:2px solid var(--brass); outline-offset:3px; border-radius:3px}
h1,h2,h3{font-family:var(--display); font-weight:400; text-wrap:balance; margin:0; line-height:1.15}
h1{font-size:clamp(40px, 6vw, 68px); letter-spacing:.005em}
h2{font-size:clamp(28px, 3.6vw, 38px)}
h3{font-size:24px}
.eyebrow{font:500 12px/1.4 var(--sans); letter-spacing:.14em; text-transform:uppercase; color:var(--brass)}
.mono{font-family:var(--mono); font-size:.86em}
p{margin:0}
.measure{max-width:65ch}
section{padding-block:56px; border-top:1px solid var(--line)}
section.hero{border-top:0; padding-block:56px 40px}
.hero-grid{display:grid; grid-template-columns:minmax(0,1.3fr) minmax(0,1fr); gap:40px; align-items:end}
.hero .lede{font-size:19px; color:var(--muted); margin-top:16px}
.facts{display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:1px; background:var(--line); border:1px solid var(--line)}
.facts div{background:var(--surface); padding:14px 16px}
.facts dt{font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted)}
.facts dd{margin:2px 0 0; font-family:var(--display); font-size:26px; font-variant-numeric:tabular-nums}
.swatches{display:grid; grid-template-columns:repeat(8, minmax(0,1fr)); margin-top:40px; border-radius:4px; overflow:hidden}
.swatches div{height:86px; padding:10px; display:flex; flex-direction:column; justify-content:flex-end; font-size:12px; line-height:1.3}
.sec-head{display:grid; gap:10px; margin-bottom:28px}
.rules{display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:28px; margin-top:8px}
.rules h3{font-size:21px; margin-bottom:6px}
.rules p{color:var(--muted); font-size:16px}
.plan-wrap{overflow-x:auto; border:1px solid var(--line); background:var(--surface); border-radius:4px; padding:8px}
.plan-wrap + .plan-wrap{margin-top:20px}
.plan-cap{display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin:22px 0 8px}
.plan-cap h3{font-size:22px}
svg.plan{display:block; width:100%; min-width:680px; height:auto}
.plan .slab{fill:var(--plan-wall)} .plan .deck{fill:var(--deck); stroke:var(--plan-wall); stroke-width:.8; stroke-dasharray:4 3}
.plan .hall{fill:var(--plan-room)} .plan .room, .plan .room2{fill:var(--plan-room); stroke:var(--plan-wall); stroke-width:2.5} .plan .roomo{fill:var(--plan-room); stroke:var(--muted); stroke-width:.8; stroke-dasharray:2 4} .plan .svc{fill:var(--plan-svc); stroke:var(--plan-wall); stroke-width:2.5} .plan .openbg{fill:var(--plan-svc)}
.plan .open{fill:url(#hatch)} .plan .hatchln{stroke:var(--line); stroke-width:3}
.plan .fix{fill:var(--fix); stroke:var(--muted); stroke-width:.8} .plan .fixln{stroke:var(--muted); stroke-width:.8}
.plan .fire{fill:var(--warn); opacity:.8}
.plan .furn{fill:var(--furn); stroke:var(--furn-line); stroke-width:1.2}
.plan .later{fill:none; stroke:var(--furn-line); stroke-width:1.2; stroke-dasharray:4 3}
.plan .chair{fill:var(--chair); stroke:var(--olive); stroke-width:1.1}
.plan .pillow{fill:var(--plan-room); stroke:var(--furn-line); stroke-width:.8}
.plan .rug{fill:var(--rug)} .plan .lamp{fill:var(--brass)}
.plan .ghost{fill:none; stroke:var(--brass); stroke-width:1.4; stroke-dasharray:5 4}
.plan .win{stroke:var(--win); stroke-width:5}
.plan .gap{stroke:var(--plan-room); stroke-width:7}
.plan .leaf{stroke:var(--plan-wall); stroke-width:1.4} .plan .swing{fill:none; stroke:var(--muted); stroke-width:.9; stroke-dasharray:3 2}
.plan .tread{stroke:var(--muted); stroke-width:.6} .plan .rail{stroke:var(--plan-wall); stroke-width:2; stroke-dasharray:1 3}
.plan .tv{stroke:var(--ink); stroke-width:4}
.plan .scale{stroke:var(--ink); stroke-width:1.5}
.plan .dimln{stroke:var(--brass); stroke-width:1.2}
.plan text{font-family:var(--sans)}
.plan .rl{font-size:12.5px; font-weight:500; fill:var(--ink)} .plan .sl{font-size:11px; fill:var(--muted)}
.plan .rd{font-family:var(--mono); font-size:10px; fill:var(--muted)}
.plan .fl{font-size:9.5px; fill:var(--furn-ink); font-weight:500} .plan .fxl{font-size:9.5px; fill:var(--muted)}
.plan .ghl{font-size:9.5px; fill:var(--brass); font-style:italic}
.plan .dimtx{font-family:var(--mono); font-size:10px; font-weight:500; fill:var(--brass); paint-order:stroke; stroke:var(--plan-room); stroke-width:3px}
.legend{display:flex; flex-wrap:wrap; gap:8px 20px; font-size:13px; color:var(--muted); margin-top:12px}
.legend span{display:inline-flex; align-items:center; gap:7px}
.legend i{display:inline-block; width:16px; height:11px; border-radius:2px}
.room{display:grid; gap:22px; padding-block:44px; border-top:1px solid var(--line)}
.room:first-of-type{border-top:0; padding-top:8px}
.room-head{display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:6px 18px}
.room-head .meta{font-family:var(--mono); font-size:13px; color:var(--muted); text-align:right}
.link3d{font-family:var(--sans); font-size:14px; color:var(--brass); text-decoration:none; font-weight:500}
.link3d:hover{text-decoration:underline}
.btn{display:inline-block; margin-top:22px; background:var(--ink); color:var(--bg); text-decoration:none; font-weight:500; font-size:15px; padding:11px 20px; border-radius:999px}
.btn:hover{background:var(--brass)}
nav.index a.nav3d{color:var(--brass); font-weight:500}
.room-body{display:grid; grid-template-columns:minmax(0,1.25fr) minmax(0,1fr); gap:28px; align-items:start}
.room-body.noscene{grid-template-columns:minmax(0,1fr)}
figure{margin:0}
.photos{display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap:18px}
.photos img{display:block; width:100%; height:auto; border-radius:4px}
svg.scene{display:block; width:100%; height:auto; border-radius:4px}
figcaption{font-size:13px; color:var(--muted); margin-top:8px}
.notes{display:grid; gap:14px; min-width:0}
.notes ul{margin:0; padding-left:1.1em; display:grid; gap:8px}
.checks{list-style:none; padding:0; margin:0; display:grid; gap:8px}
.checks li{display:grid; grid-template-columns:22px minmax(0,1fr); gap:8px; font-size:15px; line-height:1.5; padding:8px 10px; border-radius:4px}
.checks li.ok{background:var(--olive-soft)} .checks li.warn{background:var(--warn-soft)}
.checks b{font-weight:500; text-align:center} .checks li.ok b{color:var(--olive)} .checks li.warn b{color:var(--warn)}
.label{font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted)}
.tbl{overflow-x:auto}
table{width:100%; border-collapse:collapse; font-size:15px}
th{font-weight:500; font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); text-align:left; padding:8px 10px; border-bottom:1px solid var(--ink)}
td{padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:top}
td.num, th.num{text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap}
td.size{font-family:var(--mono); font-size:13px; color:var(--muted)}
tfoot td{border-bottom:0; font-weight:500}
.pill{display:inline-block; font-size:12px; padding:2px 9px; border-radius:999px; white-space:nowrap}
.pill.p1{background:var(--ink); color:var(--bg)} .pill.p2{background:var(--furn); color:var(--furn-ink)} .pill.p3{border:1px solid var(--line); color:var(--muted)}
.bar{display:flex; height:46px; border-radius:4px; overflow:hidden; margin-top:6px}
.bar div{display:flex; align-items:center; padding:0 12px; font-size:14px; white-space:nowrap; overflow:hidden; min-width:0}
.bar .p1{background:var(--ink); color:var(--bg)} .bar .p2{background:var(--furn); color:var(--furn-ink)} .bar .p3{background:var(--line); color:var(--ink)}
.phases{display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:24px; margin-top:28px}
.phases h3{font-size:21px; display:flex; justify-content:space-between; gap:10px; font-variant-numeric:tabular-nums}
.phases ul{margin:10px 0 0; padding:0; list-style:none; display:grid; gap:6px; font-size:15px}
.phases li{display:flex; justify-content:space-between; gap:12px; border-bottom:1px dotted var(--line); padding-bottom:5px}
.phases li span:last-child{font-variant-numeric:tabular-nums; white-space:nowrap}
.tip{margin-top:28px; padding:16px 18px; border-left:3px solid var(--brass); background:var(--surface); border-radius:0}
.grid2{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:32px}
.prompts{display:grid; gap:16px}
.prompt{border:1px solid var(--line); background:var(--surface); border-radius:4px; padding:16px 18px; display:grid; gap:10px}
.prompt-head{display:flex; justify-content:space-between; align-items:center; gap:12px}
.prompt p{font-size:15px; color:var(--ink)}
button.copy{font:500 13px var(--sans); background:transparent; color:var(--ink); border:1px solid var(--ink); border-radius:999px; padding:5px 14px; cursor:pointer}
button.copy:hover{background:var(--ink); color:var(--bg)}
ol.steps{margin:0; padding-left:1.2em; display:grid; gap:6px}
footer{padding-block:40px 64px; border-top:1px solid var(--line); color:var(--muted); font-size:14px}
@media (max-width:860px){
  .hero-grid, .room-body, .grid2{grid-template-columns:minmax(0,1fr)}
  .rules, .phases{grid-template-columns:minmax(0,1fr)}
  .swatches{grid-template-columns:repeat(4, minmax(0,1fr))}
}
@media (prefers-reduced-motion: no-preference){ html{scroll-behavior:smooth} }
"""

SWATCHES = [("#EFE9DF", "Warm ivory", "#3D3428"), ("#D6CCBD", "Linen greige", "#3D3428"), ("#A8998A", "Mushroom taupe", "#2B2620"),
            ("#2B2826", "Soft charcoal", "#EFE9DF"), ("#B8925F", "Natural oak", "#2B2620"), ("#6B4A33", "Walnut", "#F4EDE2"),
            ("#B8964F", "Brushed brass", "#2B2620"), ("#4F5638", "Olive velvet", "#EFE9DF")]

THREED = {'great-room':'great-room','dining':'dining','kitchen':'kitchen','office':'office','bonus':'bonus','primary':'primary','bedroom-3':'bedroom-3','bedroom-2':'entry'}

def room_html(r):
    rows = "".join(
        f'<tr><td>{esc(n)}</td><td class="size">{esc(s)}</td><td>{esc(w)}</td><td class="num">{money(p)}</td>'
        f'<td><span class="pill {PHASE_CLS[ph]}">{ph}</span></td></tr>' for n, s, w, p, ph in r["items"])
    checks = "".join(f'<li class="{k}"><b aria-hidden="true">{"✓" if k=="ok" else "!"}</b><span>{esc(t)}</span></li>' for k, t in r["checks"])
    notes = "".join(f"<li>{esc(n)}</li>" for n in r["notes"])
    photos = ""
    if r.get("photos"):
        photos = '<div class="photos">' + "".join(f'<figure><img src="{esc(src)}" alt="{esc(cap)}" loading="lazy" width="1264" height="848"><figcaption>{esc(cap)}</figcaption></figure>' for src, cap in r["photos"]) + '</div>'
    fig = ""
    if r["scene"]:
        fig = f'<figure>{r["scene"]()}<figcaption>Illustration of the finished room, drawn in the palette. Proportions are approximate.</figcaption></figure>'
    return f"""
<article class="room" id="{r['id']}">
  <div class="room-head"><div><div class="eyebrow">{esc(r['floor'])}</div><h3>{esc(r['name'])}</h3></div><div class="meta">{esc(r['dims'])}<br><a class="link3d" href="walkthrough.html#{THREED[r['id']]}">View this room in 3D →</a></div></div>
  <div class="room-body{'' if fig else ' noscene'}">
    {fig}
    <div class="notes">
      <ul>{notes}</ul>
      <div class="label">Fit check</div>
      <ul class="checks">{checks}</ul>
    </div>
  </div>
  {photos}
  <div class="tbl"><table>
    <thead><tr><th>Item</th><th>Size</th><th>Where to look</th><th class="num">Est. CAD</th><th>When</th></tr></thead>
    <tbody>{rows}</tbody>
    <tfoot><tr><td colspan="3">{esc(r['name'])} total</td><td class="num">{money(r['total'])}</td><td></td></tr></tfoot>
  </table></div>
</article>"""

def phases_html():
    out = []
    for ph, title in ((MOVE, "Before move-in"), (SOON, "Months 1–3"), (LATER, "When ready")):
        lis = []
        for r in ROOMS:
            sub = sum(i[3] for i in r["items"] if i[4] == ph)
            if sub:
                lis.append(f'<li><span>{esc(r["name"])}</span><span>{money(sub)}</span></li>')
        out.append(f'<div><h3><span>{title}</span><span>{money(phase_tot[ph])}</span></h3><ul>{"".join(lis)}</ul></div>')
    return "".join(out)

def bar_html():
    segs = []
    for ph in (MOVE, SOON, LATER):
        pct = phase_tot[ph] / GRAND * 100
        segs.append(f'<div class="{PHASE_CLS[ph]}" style="width:{pct:.2f}%">{money(phase_tot[ph])}</div>')
    return '<div class="bar" role="img" aria-label="Budget split by phase">' + "".join(segs) + "</div>"

def prompts_html():
    out = []
    for r in ROOMS:
        pid = f"prompt-{r['id']}"
        label = r["name"] if r["id"] != "bedroom-2" else "Foyer and stairwell"
        out.append(f'<div class="prompt"><div class="prompt-head"><h3 style="font-size:20px">{esc(label)}</h3>'
                   f'<button class="copy" type="button" id="btn-{pid}" data-copy="{pid}">Copy prompt</button></div>'
                   f'<p id="{pid}">{esc(prompt_for(r))}</p></div>')
    return "".join(out)

must = ["sofa bed", "65-inch TV", "2 king beds and mattresses", "dining table and chairs"]

page = f"""<title>Our Devon Home</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Room-by-room furniture and decor plan for our new home in Devon, Alberta.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Jost:wght@400;500&family=Marcellus&display=swap">
<style>{CSS}</style>
<nav class="index" aria-label="Sections"><div class="wrap">
  <span class="mark">Our Devon Home</span>
  <a href="walkthrough.html" class="nav3d">3D walk-through</a><a href="#style">Style</a><a href="#plans">Floor plans</a><a href="#rooms">Rooms</a><a href="#budget">Budget</a><a href="#checks">Before buying</a><a href="#photos">Staged photos</a>
</div></nav>
<main class="wrap">
<section class="hero">
  <div class="hero-grid">
    <div>
      <div class="eyebrow">Furniture and decor plan · October 2026</div>
      <h1>Our Devon Home</h1>
      <p class="lede measure">How each room will be furnished: what to buy, where it goes, what it costs, and what to buy first. Layouts are drawn to scale from the builder's plans.</p>
      <a class="btn" href="walkthrough.html">Walk through the house in 3D →</a>
    </div>
    <dl class="facts">
      <div><dt>Living space</dt><dd>2,245 sq ft</dd></div>
      <div><dt>Bedrooms</dt><dd>3 + office</dd></div>
      <div><dt>Ceilings</dt><dd>9'-1"</dd></div>
      <div><dt>Full plan</dt><dd>{money(GRAND)}</dd></div>
    </dl>
  </div>
  <div class="swatches" aria-label="Colour palette">
    {''.join(f'<div style="background:{c};color:{t}"><span>{esc(n)}</span><span class="mono">{c}</span></div>' for c, n, t in SWATCHES)}
  </div>
</section>

<section id="style">
  <div class="sec-head"><div class="eyebrow">Style direction</div><h2>Warm, calm and a little regal</h2>
  <p class="measure" style="color:var(--muted)">This brings together the four looks you asked for: lux organic, sleek monochrome, warm and cozy, and modern royale. One base runs through every room, so the house feels like a single home rather than separate rooms.</p></div>
  <div class="rules">
    <div><h3>One warm base</h3><p>Ivory walls, greige and taupe fabrics, and oak and walnut wood in every room. Natural textures do the work: linen, bouclé, travertine-look stone.</p></div>
    <div><h3>Black and brass for edges</h3><p>Matte black on frames, chair legs and the TV wall. Brushed brass on lamps and pendants. This is where the sleek, monochrome look comes from.</p></div>
    <div><h3>One olive accent per room</h3><p>Olive velvet on a pillow, a chair or a print, and only once per room. That restraint is what keeps the royal touch elegant.</p></div>
  </div>
  <div class="tip measure"><b style="font-weight:500">Walkable by rule:</b> every main path stays at least 3 feet wide, and nothing is bought just to fill a corner. Each fit check below gives the actual clearance.</div>
</section>

<section id="plans">
  <div class="sec-head"><div class="eyebrow">Layouts to scale</div><h2>Floor plans with furniture</h2>
  <p class="measure" style="color:var(--muted)">Drawn from your builder's plans (sheets P-7 and P-8). Brass numbers are clearances between furniture and walls. Confirm the room sizes with a tape measure at your walkthrough before ordering large pieces.</p></div>
  <div class="plan-cap"><h3>Main floor</h3><span class="mono" style="color:var(--muted)">dining · kitchen · great room · office</span></div>
  <div class="plan-wrap">{main_plan()}</div>
  <div class="plan-cap"><h3>Upper floor</h3><span class="mono" style="color:var(--muted)">primary · bonus · bedrooms 2 and 3</span></div>
  <div class="plan-wrap">{upper_plan()}</div>
  <div class="legend">
    <span><i style="background:var(--furn);border:1px solid var(--furn-line)"></i>Furniture</span>
    <span><i style="background:var(--chair);border:1px solid var(--olive)"></i>Seating</span>
    <span><i style="background:var(--rug)"></i>Rug</span>
    <span><i style="background:var(--fix);border:1px solid var(--muted)"></i>Builder cabinets</span>
    <span><i style="background:var(--win)"></i>Window</span>
    <span><i style="border:1.5px dashed var(--brass)"></i>Sofa bed opened / bought later</span>
  </div>
</section>

<section id="rooms">
  <div class="sec-head"><div class="eyebrow">Room by room</div><h2>What goes where</h2>
  <p class="measure" style="color:var(--muted)">Prices are estimates in Canadian dollars for mid-range pieces at the stores listed. Check current prices before buying, and watch the Black Friday and Boxing Day sales.</p></div>
  {''.join(room_html(r) for r in ROOMS)}
</section>

<section id="budget">
  <div class="sec-head"><div class="eyebrow">Budget</div><h2>{money(GRAND)} in three steps</h2>
  <p class="measure" style="color:var(--muted)">The must-haves ({', '.join(must)}) are all in the first step. That step comes to {money(phase_tot[MOVE])}, which leaves room inside the $15,000 budget for everything else.</p></div>
  {bar_html()}
  <div class="phases">{phases_html()}</div>
  <div class="tip measure"><b style="font-weight:500">Timing tip:</b> Black Friday is November 27. TVs and mattresses are usually discounted then. If you take possession around that date, buying these two items on sale could save $300–500.</div>
</section>

<section id="checks">
  <div class="sec-head"><div class="eyebrow">Before buying</div><h2>Check these at your walkthrough</h2></div>
  <div class="grid2">
    <div class="notes">
      <ul>
        <li><b style="font-weight:500">Office window.</b> The builder plans show no window in the office (the den). The listing calls it a bedroom, which normally needs a window. Confirm what was actually built.</li>
        <li><b style="font-weight:500">Fireplace location.</b> The plans show one electric fireplace, in the main-floor great room. The listing describes a fireplace in the bonus room. Check which rooms have one.</li>
        <li><b style="font-weight:500">TV wall.</b> Measure the space above the fireplace, and ask whether there is wood blocking and a power outlet behind it for the mount.</li>
        <li><b style="font-weight:500">Island overhang.</b> The plans show a 12-inch eating bar. Measure it and take the stool seat height (24–26 inches) when you shop.</li>
        <li><b style="font-weight:500">Bedroom 3 closet door.</b> Check which way it swings before choosing nightstands.</li>
        <li><b style="font-weight:500">Delivery path.</b> The stairs are 3'-6" wide with a landing, and the front door is 42 inches. Check large items against these before ordering.</li>
      </ul>
    </div>
    <div class="tbl"><table>
      <thead><tr><th>Window, from the plans</th><th class="num">Width × height</th></tr></thead>
      <tbody>
        <tr><td>Dining nook (west)</td><td class="num mono">84" × 60"</td></tr>
        <tr><td>Great room (west)</td><td class="num mono">84" × 60"</td></tr>
        <tr><td>Great room upper, fixed</td><td class="num mono">84" × 60"</td></tr>
        <tr><td>Primary bedroom (west)</td><td class="num mono">84" × 60"</td></tr>
        <tr><td>Bedroom 2 (east)</td><td class="num mono">72" × 60"</td></tr>
        <tr><td>Bedroom 3 (east)</td><td class="num mono">72" × 60"</td></tr>
        <tr><td>Office</td><td class="num mono">none shown</td></tr>
      </tbody>
    </table>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Window sizes on drawings are approximate. Measure each frame before ordering blinds.</p></div>
  </div>
</section>

<section id="photos">
  <div class="sec-head"><div class="eyebrow">Photo-real pictures</div><h2>See your actual rooms furnished</h2>
  <p class="measure" style="color:var(--muted)">The drawings above show the plan. For a realistic photo of each room, use an AI virtual-staging app with the listing photos:</p></div>
  <ol class="steps measure" style="margin-bottom:24px">
    <li>Save the listing photo of a room from Zillow.</li>
    <li>Upload it to a virtual-staging app.</li>
    <li>Copy that room's prompt below, paste it in, and generate. If the walls or windows change, try again.</li>
  </ol>
  <div class="prompts">{prompts_html()}</div>
</section>

<footer>
  <p class="measure">Prepared October 18, 2026. The 3D walk-through uses real 3D product models (sofa, chairs, pouf, plant, vase) from the Khronos glTF sample library, by Wayfair and others, under CC BY 4.0 and CC0. Layouts are based on the builder's drawings, which can differ from the finished house, so measure before you order. Prices are estimates.</p>
</footer>
</main>
<script>
document.querySelectorAll('button.copy').forEach(function(btn){{
  btn.addEventListener('click', function(){{
    var el = document.getElementById(btn.dataset.copy);
    var text = el.textContent;
    function done(){{ btn.textContent = 'Copied'; setTimeout(function(){{ btn.textContent = 'Copy prompt'; }}, 1600); }}
    function fallback(){{
      var r = document.createRange(); r.selectNodeContents(el);
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      btn.textContent = 'Selected, press Ctrl+C';
    }}
    try {{ navigator.clipboard.writeText(text).then(done, fallback); }} catch (e) {{ fallback(); }}
  }});
}});
</script>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)
print("ok", OUT, len(page), "bytes; total", GRAND, phase_tot)
