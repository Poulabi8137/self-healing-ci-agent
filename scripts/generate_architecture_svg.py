"""Generate architecture SVG for Self-Healing CI Agent."""
import os, math

CANVAS_W = 1440
CANVAS_H = 1150
BG = "#0d1117"
TEXT_COLOR = "#f4f4f4"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
LANE_H = 74
LANE_GAP = 8
LANE_TOTAL = LANE_H + LANE_GAP
START_Y = 110

LANES = [
    ("#1565c0", "1. Input \u2014 CI/CD Events"),
    ("#7b1fa2", "2. RAG \u2014 Context Retrieval"),
    ("#e65100", "3. Root Cause Analysis"),
    ("#2e7d32", "4. Fix Generation"),
    ("#c62828", "5. Validation"),
    ("#bf360c", "6. Retry Loop"),
    ("#00695c", "7. Multi-Agent Review"),
    ("#f57f17", "8. PR Automation"),
    ("#5d4037", "9. Persistence"),
    ("#283593", "10. Dashboard & Benchmarks"),
    ("#4e342e", "11. External Integrations"),
]

NODES = [
    [("CI/CD Logs", "\U0001f4c4"), ("Repository", "\U0001f4c1")],
    [("Indexing", ""), ("Vector Store (FAISS)", "\U0001f5c4\ufe0f"), ("Semantic Retriever", "")],
    [("Log Parser", ""), ("Error Classifier", ""), ("Debug Agent", "\U0001f916")],
    [("Fix Agent", "\U0001f916")],
    [("Syntax Validator (AST)", ""), ("Build Validator", ""), ("Test Runner (pytest)", "")],
    [("Retry Agent", "\U0001f916")],
    [("Review Orchestrator", ""), ("Security Reviewer", "\U0001f512"), ("Performance Reviewer", "\u26a1"), ("Quality Reviewer", "\U0001f4d0"), ("Coverage Reviewer", "\U0001f9ea")],
    [("Branch Manager", ""), ("Commit Manager", ""), ("PR Generator", "")],
    [("SQLite Database", "\U0001f5c4\ufe0f")],
    [("Metrics Collector", ""), ("Analytics Engine", ""), ("Benchmark Service", "")],
    [("GitHub API", ""), ("DeepSeek LLM", "")],
]

# Dynamic node width: fit widest lane
MAX_NODES = max(len(n) for n in NODES)  # 5
SPACING = (CANVAS_W - 240) / (MAX_NODES + 1)
NODE_W = SPACING - 10
NODE_H = 44

def ly(li):
    return START_Y + li * LANE_TOTAL

def lcy(li):
    return ly(li) + LANE_H / 2

def nx(li, ni):
    cnt = len(NODES[li])
    sp = (CANVAS_W - 240) / (cnt + 1)
    return 240 + sp * (ni + 1) - NODE_W / 2

def nrect(li, ni):
    x = nx(li, ni)
    y = lcy(li) - NODE_H / 2
    return (x, y, NODE_W, NODE_H)

def nc(li, ni):
    x, y, w, h = nrect(li, ni)
    return (x + w/2, y + h/2)

def nl(li, ni):
    x, y, w, h = nrect(li, ni)
    return (x, y + h/2)

def nr(li, ni):
    x, y, w, h = nrect(li, ni)
    return (x + w, y + h/2)

def nt(li, ni):
    x, y, w, h = nrect(li, ni)
    return (x + w/2, y)

def nb(li, ni):
    x, y, w, h = nrect(li, ni)
    return (x + w/2, y + h)

def apath(pts, stroke=TEXT_COLOR, width=2, dashed=False, label="", loff=8):
    d = "M{:.1f},{:.1f}".format(pts[0][0], pts[0][1])
    for p in pts[1:]:
        d += " L{:.1f},{:.1f}".format(p[0], p[1])
    mid = pts[len(pts)//2]
    lbl = ""
    if label:
        lbl = '<text x="{:.1f}" y="{:.1f}" fill="{}" font-family="{}" font-size="11" text-anchor="middle">{}</text>'.format(mid[0], mid[1] - loff, TEXT_COLOR, FONT, label)
    svg = '<path d="{}" fill="none" stroke="{}" stroke-width="{}"'.format(d, stroke, width)
    if dashed:
        svg += ' stroke-dasharray="8,5"'
    svg += ' marker-end="url(#a)"' if not dashed else ' marker-end="url(#ad)"'
    svg += '/>' + lbl
    return svg

def generate(filename):
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}">'.format(CANVAS_W, CANVAS_H, CANVAS_W, CANVAS_H))
    lines.append('<defs>')
    lines.append('<marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10z" fill="#f4f4f4"/></marker>')
    lines.append('<marker id="ad" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10z" fill="#f4f4f4"/></marker>')
    lines.append('</defs>')
    lines.append('<rect width="{}" height="{}" fill="{}"/>'.format(CANVAS_W, CANVAS_H, BG))
    lines.append('<text x="{:.1f}" y="46" fill="{}" font-family="{}" font-size="24" font-weight="bold" text-anchor="middle">Self-Healing AI CI/CD Agent \u2014 System Architecture</text>'.format(CANVAS_W/2, TEXT_COLOR, FONT))

    # Lanes
    for i, (clr, lbl) in enumerate(LANES):
        y = ly(i)
        r, g, b = int(clr[1:3], 16), int(clr[3:5], 16), int(clr[5:7], 16)
        lines.append('<rect x="0" y="{:.1f}" width="{}" height="{:.1f}" fill="rgba({},{},{},0.18)" rx="4"/>'.format(y, CANVAS_W, LANE_H, r, g, b))
        lines.append('<text x="14" y="{:.1f}" fill="{}" font-family="{}" font-size="11" font-weight="bold">{}</text>'.format(y + LANE_H/2 + 4, TEXT_COLOR, FONT, lbl))

    # Nodes
    for li, nn in enumerate(NODES):
        for ni, (nm, ic) in enumerate(nn):
            x, y, w, h = nrect(li, ni)
            clr = LANES[li][0]
            lines.append('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="#1a2332" stroke="{}" stroke-width="1.5" rx="6"/>'.format(x, y, w, h, clr))
            txt = "{} {}".format(ic, nm) if ic else nm
            lines.append('<text x="{:.1f}" y="{:.1f}" fill="{}" font-family="{}" font-size="12" font-weight="bold" text-anchor="middle">{}</text>'.format(x + w/2, y + h/2 + 4, TEXT_COLOR, FONT, txt))

    # Horizontal arrows within lanes
    def h_arrow(li, f, t):
        return apath([(nr(li, f)[0], lcy(li)), (nl(li, t)[0], lcy(li))])

    def v_arrow(src_li, src_ni, dst_li, dst_ni, lab="", dashed=False, xos=0):
        sx, sy = nc(src_li, src_ni)
        dx, dy = nc(dst_li, dst_ni)
        sx += xos; dx += xos
        _, sy2, _, sh = nrect(src_li, src_ni); sb = sy2 + sh  # bottom of src
        _, dy2, _, _ = nrect(dst_li, dst_ni); dt = dy2          # top of dst
        return apath([(sx, sy), (sx, sb + 6), (dx, dt - 6), (dx, dy)], label=lab, dashed=dashed)

    def v_right(src_li, src_ni, dst_li, dst_ni, lab="", dashed=False):
        sx, sy = nr(src_li, src_ni)
        dx, dy = nc(dst_li, dst_ni)
        _, sy2, _, sh = nrect(src_li, src_ni); sb = sy2 + sh
        _, dy2, _, _ = nrect(dst_li, dst_ni); dt = dy2
        my = (sb + dt) / 2
        return apath([(sx, sy), (sx + 12, sy), (sx + 12, my), (dx, my), (dx, dt - 6), (dx, dy)], label=lab, dashed=dashed)

    def vup_arrow(src_li, src_ni, dst_li, dst_ni, lab="", xos=50):
        sx, sy = nc(src_li, src_ni)
        dx, dy = nc(dst_li, dst_ni)
        sx += xos; dx += xos
        _, yt_s, _, _ = nrect(src_li, src_ni); st = yt_s
        _, yd2, _, ydh = nrect(dst_li, dst_ni); db = yd2 + ydh
        route = [
            (sx, sy),
            (sx, st - 6),
            (sx, db + 30),
            (dx, db + 30),
            (dx, db + 6),
            (dx, dy),
        ]
        return apath(route, label=lab)

    # Same-lane horizontal
    lines.append(h_arrow(1, 0, 1))
    lines.append(h_arrow(1, 1, 2))
    lines.append(h_arrow(2, 0, 1))
    lines.append(h_arrow(2, 1, 2))
    lines.append(h_arrow(4, 0, 1))
    lines.append(h_arrow(4, 1, 2))
    lines.append(h_arrow(6, 0, 1))
    lines.append(h_arrow(6, 0, 2))
    lines.append(h_arrow(6, 0, 3))
    lines.append(h_arrow(6, 0, 4))
    lines.append(h_arrow(7, 0, 1))
    lines.append(h_arrow(7, 1, 2))
    lines.append(h_arrow(9, 0, 1))
    lines.append(h_arrow(9, 1, 2))

    # Vertical cross-lane
    lines.append(v_right(0, 1, 1, 0))  # Repository -> Indexing
    lines.append(v_right(0, 0, 2, 0))  # CI/CD Logs -> Log Parser
    lines.append(v_arrow(2, 2, 3, 0))  # Debug -> Fix
    lines.append(v_arrow(3, 0, 4, 0))  # Fix -> Syntax
    lines.append(v_arrow(4, 2, 5, 0, lab="\u2717 fail", xos=-60))  # Test -> Retry
    lines.append(vup_arrow(5, 0, 3, 0, lab="retry fix", xos=-110))  # Retry -> Fix
    lines.append(v_right(4, 2, 6, 0, lab="\u2713 pass"))  # Test -> Review Orch
    lines.append(v_arrow(7, 2, 10, 0, lab="PR", dashed=True, xos=60))  # PR Gen -> GitHub
    lines.append(v_arrow(8, 0, 9, 0))  # SQLite -> Dashboard

    # --- LLM bus ---
    llm_bus_y = ly(10) - 26
    lx = 260
    for li, ni in [(2, 2), (3, 0), (5, 0), (6, 1), (6, 2), (6, 3), (6, 4)]:
        cx, cy = nb(li, ni)
        lines.append(apath([(cx, cy), (cx, cy + 4), (lx, cy + 4), (lx, llm_bus_y)], dashed=True, width=1.5))
        lx += 100
    lines.append('<line x1="260" y1="{:.1f}" x2="940" y2="{:.1f}" stroke="{}" stroke-width="1" stroke-dasharray="8,5" opacity="0.4"/>'.format(llm_bus_y, llm_bus_y, TEXT_COLOR))
    dllm, _ = nt(10, 1)
    lines.append(apath([(dllm, llm_bus_y), (dllm, ly(10) - 4), (dllm, lcy(10))], dashed=True, label="LLM", width=1.5, loff=6))

    # --- Persist bus ---
    persist_bus_y = ly(8) - 26
    px = 280
    for li, ni in [(2, 2), (3, 0), (6, 0)]:
        cx, cy = nb(li, ni)
        lines.append(apath([(cx, cy), (cx, cy + 4), (px, cy + 4), (px, persist_bus_y)], dashed=True, width=1.5))
        px += 160
    lines.append('<line x1="280" y1="{:.1f}" x2="620" y2="{:.1f}" stroke="{}" stroke-width="1" stroke-dasharray="8,5" opacity="0.4"/>'.format(persist_bus_y, persist_bus_y, TEXT_COLOR))
    dsql, _ = nt(8, 0)
    lines.append(apath([(dsql, persist_bus_y), (dsql, ly(8) - 4), (dsql, lcy(8))], dashed=True, label="persist", width=1.5, loff=6))

    # query ctx: Debug -> Semantic Retriever
    cx, cy = nb(2, 2)
    rsx, _ = nt(1, 2)
    lines.append(apath([(cx + 80, cy), (cx + 80, cy + 4), (rsx + 40, ly(1) - 4), (rsx + 40, lcy(1))], dashed=True, label="query ctx", width=1.5, loff=6))
    # Semantic -> Vector Store
    lines.append(apath([(nr(1, 2)[0] + 6, lcy(1)), (nl(1, 1)[0] - 6, lcy(1))], dashed=True, width=1.5))

    lines.append('</svg>')

    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("Generated: {} ({} bytes)".format(filename, os.path.getsize(filename)))

if __name__ == "__main__":
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "architecture-detailed.svg")
    generate(p)
