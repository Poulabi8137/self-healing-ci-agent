"""Generate README architecture diagram — 9-block executive overview, SaaS-style."""
import os

W, H = 1600, 900
BG = "#0d1117"
FG = "#f0f6fc"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

def tx(x, y, s, size=20, bold=False, anchor="middle", fill=FG):
    fw = ' font-weight="bold"' if bold else ""
    return '<text x="{:.1f}" y="{:.1f}" fill="{}" font-family="{}" font-size="{}"{} text-anchor="{}">{}</text>'.format(
        x, y, fill, FONT, size, fw, anchor, s)

def bx(x, y, w, h, color, icon, label, subtitle=""):
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    bg = "rgba({},{},{},0.10)".format(r, g, b)
    out = '<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="{}" stroke="{}" stroke-width="2" rx="12"/>'.format(x, y, w, h, bg, color)
    out += tx(x + w/2, y + 42, icon, size=26)
    out += tx(x + w/2, y + 74, label, size=17, bold=True)
    if subtitle:
        out += tx(x + w/2, y + 96, subtitle, size=12, fill="#8b949e")
    return out

def ar(x1, y1, x2, y2, color="#30363d", width=3):
    return '<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="{}" stroke-width="{}" marker-end="url(#a)"/>'.format(x1, y1, x2, y2, color, width)

def va(x, y1, y2, color="#30363d", width=3):
    return ar(x, y1, x, y2, color, width)

def generate(filename):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}">'.format(W, H, W, H)]
    out.append('<defs><marker id="a" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="6" markerHeight="6" orient="auto">')
    out.append('<path d="M0 0 L12 6 L0 12z" fill="#8b949e"/>')
    out.append('</marker></defs>')
    out.append('<rect width="{}" height="{}" fill="{}"/>'.format(W, H, BG))
    out.append(tx(W/2, 50, "System Architecture", size=30, bold=True))

    BW, BH = 180, 100
    GAP = 30
    COL = (W - 3*BW - 2*GAP) / 2
    C = W / 2

    rows = [
        (92,  [C]),                                   # User
        (222, [C]),                                   # API
        (352, [C]),                                   # Orchestrator
        (482, [C - BW - GAP, C, C + BW + GAP]),      # RAG / Agents / Val
        (612, [C]),                                   # Database (wide)
        (742, [C - GAP/2 - BW, C + GAP/2]),           # GitHub / Monitor
    ]

    colors = [
        "#58a6ff", "#d2a8ff", "#d29922",
        "#7b1fa2", "#3fb950", "#f85149",
        "#8b949e",
        "#f0f6fc", "#56d4dd",
    ]

    labels = [
        ("User", "Developer / CI"),
        ("API Gateway", "FastAPI / REST"),
        ("Orchestrator", "Workflow Engine"),
        ("RAG Engine", "FAISS + Embeddings"),
        ("AI Agents", "8 Specialized Agents"),
        ("Validation", "Syntax \u00b7 Build \u00b7 Test"),
        ("Database", "SQLite / Metrics Store"),
        ("GitHub", "PR / Branch / Commit"),
        ("Monitoring", "Dashboard / Metrics"),
    ]

    icons = ["\U0001f464", "\U0001f50c", "\u2699\ufe0f",
             "\U0001f9e0", "\U0001f916", "\u2705",
             "\U0001f5c4\ufe0f",
             "\U0001f419", "\U0001f4ca"]

    node_data = []
    idx = 0
    for ri, (y, xs) in enumerate(rows):
        for xi, cx in enumerate(xs):
            if ri == 4:  # Database — wider block
                w = BW * 2 + GAP
                x = cx - w/2
            else:
                w = BW
                x = cx - w/2
            clr = colors[idx]
            ic = icons[idx]
            lb, sub = labels[idx]
            node_data.append((x, y, w, BH, clr, ic, lb, sub, cx, y + BH))
            idx += 1

    for nd in node_data:
        x, y, w, h, clr, ic, lb, sub, _, _ = nd
        out.append(bx(x, y, w, h, clr, ic, lb, sub))

    # Arrows: Row 0 -> Row 1
    out.append(va(C, 192, 222, "#58a6ff"))
    # Row 1 -> Row 2
    out.append(va(C, 322, 352, "#d2a8ff"))
    # Row 2 -> Row 3 (3 arrows)
    for cx in [C - BW - GAP, C, C + BW + GAP]:
        out.append(ar(C, 452, cx, 482))
    # Row 3 -> Row 4 (3 arrows converge to DB center)
    for cx in [C - BW - GAP, C, C + BW + GAP]:
        out.append(ar(cx, 582, C, 612))
    # Row 4 -> Row 5
    out.append(ar(C - (BW*2+GAP)/4, 712, C - GAP/2 - BW, 742))
    out.append(ar(C + (BW*2+GAP)/4, 712, C + GAP/2, 742))

    out.append('</svg>')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    sz = os.path.getsize(filename)
    print("Wrote {} ({} bytes)".format(filename, sz))

if __name__ == "__main__":
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "architecture-readme.svg")
    generate(p)
