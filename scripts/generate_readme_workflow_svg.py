"""Generate README end-to-end workflow diagram — 8-stage executive overview."""
import os

W, H = 1600, 900
BG = "#0d1117"
FG = "#f0f6fc"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

def tx(x, y, s, size=20, bold=False, anchor="middle", fill=FG):
    fw = ' font-weight="bold"' if bold else ""
    return '<text x="{:.1f}" y="{:.1f}" fill="{}" font-family="{}" font-size="{}"{} text-anchor="{}">{}</text>'.format(
        x, y, fill, FONT, size, fw, anchor, s)

def generate(filename):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}">'.format(W, H, W, H)]
    out.append('<defs>')
    out.append('<marker id="a" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="6" markerHeight="6" orient="auto">')
    out.append('<path d="M0 0 L12 6 L0 12z" fill="#8b949e"/>')
    out.append('</marker>')
    out.append('<marker id="ar" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="6" markerHeight="6" orient="auto">')
    out.append('<path d="M0 0 L12 6 L0 12z" fill="#f85149"/>')
    out.append('</marker>')
    out.append('</defs>')
    out.append('<rect width="{}" height="{}" fill="{}"/>'.format(W, H, BG))
    out.append(tx(W/2, 50, "End-to-End Workflow", size=30, bold=True))

    # 8 stages in 2 rows of 4
    stages = [
        ("\U0001f4e5", "Issue Received", "CI/CD failure submitted", "#58a6ff"),
        ("\U0001f4da", "Context Retrieval", "RAG indexes repo code", "#7b1fa2"),
        ("\U0001f50d", "Root Cause Analysis", "Debug Agent classifies error", "#d29922"),
        ("\U0001f527", "Fix Generation", "Fix Agent creates patch", "#3fb950"),
        ("\u2705", "Validation", "Syntax \u00b7 Build \u00b7 Test", "#f85149"),
        ("\U0001f504", "Retry", "Adaptive self-healing loop", "#bf360c"),
        ("\U0001f680", "PR Creation", "Branch \u00b7 Commit \u00b7 PR", "#f57f17"),
        ("\U0001f4ca", "Reporting", "Persist \u00b7 Dashboard update", "#56d4dd"),
    ]

    BW, BH = 300, 130
    GAP = 40
    # Total 4 blocks per row: 4*300 + 3*40 = 1200+120 = 1320
    # Left margin: (1600 - 1320) / 2 = 140
    LM = 140
    R1Y = 120
    R2Y = 340

    # Draw row 1 (stages 0-3)
    for i, (ic, title, desc, clr) in enumerate(stages[:4]):
        x = LM + i * (BW + GAP)
        y = R1Y
        r, g, b = int(clr[1:3], 16), int(clr[3:5], 16), int(clr[5:7], 16)
        bg = "rgba({},{},{},0.10)".format(r, g, b)
        out.append('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="{}" stroke="{}" stroke-width="2" rx="12"/>'.format(x, y, BW, BH, bg, clr))
        out.append(tx(x + 30, y + 35, str(i+1), size=13, fill="#8b949e", anchor="start"))
        out.append(tx(x + BW/2, y + 55, ic, size=30))
        out.append(tx(x + BW/2, y + 88, title, size=18, bold=True))
        out.append(tx(x + BW/2, y + 113, desc, size=13, fill="#8b949e"))

        # Arrow to next (except last in row)
        if i < 3:
            ax1 = x + BW
            ay = y + BH/2
            ax2 = x + BW + GAP
            out.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="#30363d" stroke-width="3" marker-end="url(#a)"/>'.format(ax1, ay, ax2, ay))

    # Down arrow from stage 4 -> stage 5
    s4_x = LM + 3*(BW+GAP) + BW/2
    out.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="#3fb950" stroke-width="3" marker-end="url(#a)"/>'.format(s4_x, R1Y + BH, s4_x, R2Y))

    # Draw row 2 (stages 4-7)
    for i, (ic, title, desc, clr) in enumerate(stages[4:]):
        idx = i + 4
        x = LM + i * (BW + GAP)
        y = R2Y
        r, g, b = int(clr[1:3], 16), int(clr[3:5], 16), int(clr[5:7], 16)
        bg = "rgba({},{},{},0.10)".format(r, g, b)
        out.append('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="{}" stroke="{}" stroke-width="2" rx="12"/>'.format(x, y, BW, BH, bg, clr))
        out.append(tx(x + 30, y + 35, str(idx+1), size=13, fill="#8b949e", anchor="start"))
        out.append(tx(x + BW/2, y + 55, ic, size=30))
        out.append(tx(x + BW/2, y + 88, title, size=18, bold=True))
        out.append(tx(x + BW/2, y + 113, desc, size=13, fill="#8b949e"))

        # Arrow to next (except last)
        if i < 3:
            ax1 = x + BW
            ay = y + BH/2
            ax2 = x + BW + GAP
            out.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="#30363d" stroke-width="3" marker-end="url(#a)"/>'.format(ax1, ay, ax2, ay))

    # Down arrow from stage 4 -> stage 5
    mid4_x = LM + 3*(BW+GAP) + BW/2
    out.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" stroke="#3fb950" stroke-width="3" marker-end="url(#a)"/>'.format(mid4_x, R1Y + BH, mid4_x, R2Y))

    # Retry loop arrow (stage 6 right -> stage 3 right, clean curve)
    s6_rx = LM + 1*(BW+GAP) + BW
    s6_ry = R2Y + BH/2
    s3_rx = LM + 2*(BW+GAP) + BW
    s3_ry = R1Y + BH/2
    cx = (s6_rx + s3_rx) / 2
    out.append('<path d="M {:.1f} {:.1f} C {:.1f} {:.1f}, {:.1f} {:.1f}, {:.1f} {:.1f}" fill="none" stroke="#f85149" stroke-width="2" stroke-dasharray="8,5" marker-end="url(#ar)"/>'.format(s6_rx, s6_ry, cx + 40, s6_ry, cx + 40, s3_ry, s3_rx, s3_ry))
    out.append(tx(cx + 60, (s6_ry + s3_ry)/2, "Retry loop", size=12, fill="#f85149", anchor="start"))

    out.append('</svg>')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    sz = os.path.getsize(filename)
    print("Wrote {} ({} bytes)".format(filename, sz))

if __name__ == "__main__":
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "workflow-readme.svg")
    generate(p)
