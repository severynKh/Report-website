"""Charts that replace the number tables, as inline SVG fragments in the site's colours.

Each chart is written to <page folder>/charts/<name>.html and placed on the page with
    {{< include charts/<name>.html >}}
The SVG uses the classes styled in custom.scss (.chart ...), which read the theme's colour
variables, so every chart follows light and dark mode. Hovering a mark shows its value.
Every number here is copied from the page's sources; edit DATA, not the drawing code.

Run:  python tools/make_charts.py
"""
import html
import math
import os

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = 640  # viewBox width; the SVG scales to the column


def esc(s):
    return html.escape(str(s), quote=True)


def write(page, name, svg, caption):
    folder = os.path.join(SITE, page, "charts")
    os.makedirs(folder, exist_ok=True)
    body = "\n".join(line for line in svg.splitlines() if line.strip())
    with open(os.path.join(folder, name + ".html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f'```{{=html}}\n<figure class="chart">\n{body}\n<figcaption>{esc(caption)}</figcaption>\n</figure>\n```\n')
    print(f"{page}/charts/{name}.html")


def svg_open(h, label):
    return f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="{esc(label)}">'


def bar(x0, y, length, thick, cls="c-bar", tip=""):
    """Horizontal bar from x0, square at the baseline, 4 px rounded at the data end."""
    r = min(4, thick / 2, max(length, 0) / 2)
    x1 = x0 + max(length, 0)
    d = (f"M{x0:.1f},{y:.1f} H{x1 - r:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} "
         f"V{y + thick - r:.1f} Q{x1:.1f},{y + thick:.1f} {x1 - r:.1f},{y + thick:.1f} H{x0:.1f} Z")
    return f'<path class="{cls}" d="{d}"><title>{esc(tip)}</title></path>'


def hbars(rows, xmax, label_w=190, tick_step=None, fmt="{:.3f}", note=None, highlight=(), unit=""):
    """rows: (label, value, tooltip). One series of horizontal bars, value at the tip."""
    top, band, thick = 26, 34, 18
    plot_w = W - label_w - 70
    h = top + band * len(rows) + 30
    s = [svg_open(h, "bar chart")]
    sx = lambda v: label_w + v / xmax * plot_w
    step = tick_step or xmax / 4
    t = 0.0
    while t <= xmax + 1e-9:
        x = sx(t)
        s.append(f'<line class="c-grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top - 6}" y2="{top + band * len(rows)}"/>')
        s.append(f'<text class="c-tick" x="{x:.1f}" y="{top + band * len(rows) + 16}" text-anchor="middle">{t:g}{unit}</text>')
        t += step
    for i, (lab, v, tip) in enumerate(rows):
        y = top + i * band + (band - thick) / 2
        cls = "c-bar" if (not highlight or lab in highlight) else "c-bar c-soft"
        s.append(f'<text class="c-label" x="{label_w - 10}" y="{y + thick / 2 + 4:.1f}" text-anchor="end">{esc(lab)}</text>')
        s.append(bar(sx(0), y, v / xmax * plot_w, thick, cls, tip or f"{lab}: {fmt.format(v)}"))
        s.append(f'<text class="c-value" x="{sx(v) + 6:.1f}" y="{y + thick / 2 + 4:.1f}">{fmt.format(v)}</text>')
    if note:
        s.append(f'<text class="c-tick" x="{label_w}" y="14">{esc(note)}</text>')
    s.append("</svg>")
    return "\n".join(s)


def legend(items, x, y):
    out = []
    for cls, lab in items:
        out.append(f'<circle class="{cls}" cx="{x + 5}" cy="{y - 4}" r="5"/>')
        out.append(f'<text class="c-label" x="{x + 15}" y="{y}">{esc(lab)}</text>')
        x += 24 + 7.2 * len(lab)
    return "\n".join(out)


def dot_pairs(title, rows, xmax, unit, x_left, width, top, band):
    """rows: (label, mode1, mode2). Two dots on a hairline per row; None = not reported."""
    out = [f'<text class="c-head" x="{x_left}" y="{top - 14}">{esc(title)}</text>']
    sx = lambda v: x_left + v / xmax * width
    for t in (0, xmax / 2, xmax):
        out.append(f'<text class="c-tick" x="{sx(t):.1f}" y="{top + band * len(rows) + 4}" text-anchor="middle">{t:g}{unit}</text>')
    for i, (lab, a, b) in enumerate(rows):
        y = top + i * band + band / 2 - 6
        out.append(f'<line class="c-grid" x1="{sx(0):.1f}" x2="{sx(xmax):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
        if a is None:
            out.append(f'<text class="c-tick" x="{sx(xmax / 2):.1f}" y="{y + 4:.1f}" text-anchor="middle">not reported</text>')
            continue
        if b is None:  # two values whose modes are not stated
            lo, hi = a
            out.append(f'<circle class="c-dot c-neutral" cx="{sx(lo):.1f}" cy="{y:.1f}" r="5"><title>{lab}: {lo:g}{unit} and {hi:g}{unit}, modes not stated</title></circle>')
            out.append(f'<circle class="c-dot c-neutral" cx="{sx(hi):.1f}" cy="{y:.1f}" r="5"><title>{lab}: {lo:g}{unit} and {hi:g}{unit}, modes not stated</title></circle>')
            continue
        out.append(f'<line class="c-link" x1="{sx(a):.1f}" x2="{sx(b):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<circle class="c-dot c-m1" cx="{sx(a):.1f}" cy="{y:.1f}" r="5"><title>{lab}, mode 1: {a:g}{unit}</title></circle>')
        out.append(f'<circle class="c-dot c-m2" cx="{sx(b):.1f}" cy="{y:.1f}" r="5"><title>{lab}, mode 2: {b:g}{unit}</title></circle>')
    return out


# ------------------------------------------------------------------ cell differentiation
def cell_modes():
    colonies = ["HUVEC", "MDCK", "MDA-MB-231"]
    top, band, lab_w = 58, 34, 92
    h = top + band * 3 + 34
    s = [svg_open(h, "Behaviour modes per colony"), legend([("c-dot c-m1", "mode 1"), ("c-dot c-m2", "mode 2")], lab_w, 16)]
    for i, c in enumerate(colonies):
        s.append(f'<text class="c-label" x="{lab_w - 10}" y="{top + i * band + band / 2 - 2:.1f}" text-anchor="end">{c}</text>')
    pw, gap = 150, 30
    s += dot_pairs("Neighbours", [("HUVEC", 11.2, 7.8), ("MDCK", (12.3, 12.6), None), ("MDA-MB-231", None, None)], 16, "", lab_w + 8, pw, top, band)
    # speed ratio: one bar per colony
    x0 = lab_w + 8 + pw + gap
    s.append(f'<text class="c-head" x="{x0}" y="{top - 14}">Speed, mode 2 ÷ mode 1</text>')
    for i, v in enumerate([1.39, 1.17, 4.5]):
        y = top + i * band + band / 2 - 13
        s.append(bar(x0, y, v / 5 * pw, 14, "c-bar", f"{colonies[i]}: mode 2 is {v:g} times faster"))
        s.append(f'<text class="c-value" x="{x0 + v / 5 * pw + 5:.1f}" y="{y + 11:.1f}">{v:g}×</text>')
    s += dot_pairs("Mean turn per step", [("HUVEC", 36.1, 24), ("MDCK", 32.5, 51.5), ("MDA-MB-231", 58.5, 109.9)], 120, "°", x0 + pw + gap + 10, pw - 10, top, band)
    s.append("</svg>")
    write("research/artificial-cell-differentiation", "modes",
          "\n".join(s), "Hover a mark for its value. MDCK's two neighbour counts are not assigned to modes in the source; MDA-MB-231 neighbours were not reported.")


# ------------------------------------------------------------------ continuous fields
def erk_frames():
    rows = [("1 frame", 0.62, "1 frame: masked R² 0.62"),
            ("3 frames (4 min)", 0.82, "3 frames: masked R² 0.82"),
            ("17 frames", 0.65, "17 frames: masked R² 0.65")]
    svg = hbars(rows, 1.0, label_w=150, tick_step=0.25, fmt="{:.2f}", highlight=("3 frames (4 min)",), note="masked R² (1 = perfect)")
    write("research/artificial-cell-continuous-fields", "frames", svg,
          "Masked R² by number of input frames. The single sample shown above, with 3 frames, scores 0.88.")


# ------------------------------------------------------------------ diffusion controller
def dc_data():
    rows = [("16 × 16", 369, "16 × 16: 500 drawn, 410 kept, 369 for training"),
            ("32 × 32", 1923, "32 × 32: 2000 drawn, 1973 kept, 1923 for training"),
            ("64 × 64", 1950, "64 × 64: 2000 drawn, 2000 kept, 1950 for training")]
    svg = hbars(rows, 2000, label_w=110, tick_step=500, fmt="{:,.0f}", note="training scenes per grid")
    write("research/diffusion-controller", "data", svg,
          "Training scenes per grid. Kept of drawn: 410 of 500, 1,973 of 2,000, 2,000 of 2,000.")


def dc_unets():
    rows = [("UNet++", 0.085, ""), ("DDPM++ (default)", 0.095, ""), ("Attention U-Net", 0.097, ""), ("U²-Net", 0.104, "")]
    svg = hbars(rows, 0.12, label_w=150, tick_step=0.03, fmt="{:.3f}", highlight=("DDPM++ (default)",), note="median re-simulation error, 20 held-out 16 × 16 scenes (lower is better)")
    write("research/diffusion-controller", "unets", svg,
          "The spread between scenes (interquartile range ±0.03–0.06) is larger than the gaps between designs.")


def dc_windows():
    rows = [("step 50 → 100 (default)", 0.080, "50 → 100: 0.080, 369 training scenes"),
            ("step 50 → 150", 0.428, "50 → 150: 0.428, 238 training scenes"),
            ("step 50 → 200, 16 × 16", 0.492, "50 → 200 at 16 × 16: 0.492, about 9,500 training scenes"),
            ("step 50 → 200, 32 × 32", 0.818, "50 → 200 at 32 × 32: 0.818, about 9,500 training scenes")]
    svg = hbars(rows, 1.0, label_w=190, tick_step=0.25, fmt="{:.3f}", highlight=("step 50 → 100 (default)",), note="re-simulation error (lower is better)")
    write("research/diffusion-controller", "windows", svg,
          "Training scenes: 369, 238, about 9,500 and about 9,500. More data did not rescue the long windows.")


def dc_physics():
    pts = [("Blobs", 8, 0.094, "12 of 20 simpler and ≤ 0.1"), ("Blobs and lines", 9, 0.068, "14 of 20 simpler and ≤ 0.1"),
           ("Lines", 12, 0.082, "10 of 20 simpler and ≤ 0.1"), ("Diffusion Controller, pixel start", 512, 0.009, "5 of 20 simpler and ≤ 0.1")]
    left, right, top, bottom = 70, W - 30, 30, 230
    h = bottom + 46
    lx = lambda n: left + (math.log10(n) - math.log10(5)) / (math.log10(800) - math.log10(5)) * (right - left)
    ly = lambda e: bottom - e / 0.12 * (bottom - top)
    s = [svg_open(h, "Simplicity against accuracy")]
    for e in (0, 0.03, 0.06, 0.09, 0.12):
        s.append(f'<line class="c-grid" x1="{left}" x2="{right}" y1="{ly(e):.1f}" y2="{ly(e):.1f}"/>')
        s.append(f'<text class="c-tick" x="{left - 8}" y="{ly(e) + 4:.1f}" text-anchor="end">{e:g}</text>')
    for n in (10, 24, 100, 512):
        s.append(f'<text class="c-tick" x="{lx(n):.1f}" y="{bottom + 16}" text-anchor="middle">{n}</text>')
    s.append(f'<line class="c-ref" x1="{lx(24):.1f}" x2="{lx(24):.1f}" y1="{top}" y2="{bottom}"/>')
    s.append(f'<text class="c-tick" x="{lx(24) + 6:.1f}" y="{top + 10}">true starts, median 24 numbers</text>')
    s.append(f'<text class="c-tick" x="{(left + right) / 2:.0f}" y="{bottom + 36}" text-anchor="middle">numbers needed to write the start (log scale)</text>')
    s.append(f'<text class="c-tick" x="{left}" y="14">re-simulation error (lower is better)</text>')
    offsets = {"Blobs": (-9, 4), "Blobs and lines": (10, 14), "Lines": (10, 4), "Diffusion Controller, pixel start": (-8, -12)}
    for lab, n, e, extra in pts:
        cls = "c-dot c-m2" if n == 512 else "c-dot c-m1"
        s.append(f'<circle class="{cls}" cx="{lx(n):.1f}" cy="{ly(e):.1f}" r="5"><title>{lab}: {n} numbers, error {e:.3f}; {extra}</title></circle>')
        dx, dy = offsets[lab]
        anchor = "end" if dx < 0 else "start"
        s.append(f'<text class="c-label" x="{lx(n) + dx:.1f}" y="{ly(e) + dy:.1f}" text-anchor="{anchor}">{esc(lab)}</text>')
    s.append("</svg>")
    write("research/diffusion-controller", "physics", "\n".join(s),
          "Physics search (left of the line) needs fewer numbers than the true starts; the Diffusion Controller is more accurate but needs 512.")


# ------------------------------------------------------------------ FNO
def grouped_hbars(groups, xmax, tick_step, fmt, note, unit="", label_w=190):
    """groups: (heading, [(label, value, tooltip, emphasis)]). One series, grouped under headings."""
    band, thick, head = 30, 16, 26
    rows = sum(len(g[1]) for g in groups)
    top = 26
    h = top + rows * band + len(groups) * head + 34
    plot_w = W - label_w - 70
    sx = lambda v: label_w + v / xmax * plot_w
    s = [svg_open(h, "bar chart")]
    if note:
        s.append(f'<text class="c-tick" x="{label_w}" y="14">{esc(note)}</text>')
    bottom = h - 30
    t = 0.0
    while t <= xmax + 1e-9:
        s.append(f'<line class="c-grid" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top}" y2="{bottom}"/>')
        s.append(f'<text class="c-tick" x="{sx(t):.1f}" y="{bottom + 16}" text-anchor="middle">{t:g}{unit}</text>')
        t += tick_step
    y = top
    for heading, items in groups:
        s.append(f'<text class="c-head" x="0" y="{y + 17}">{esc(heading)}</text>')
        y += head
        for lab, v, tip, strong in items:
            by = y + (band - thick) / 2
            s.append(f'<text class="c-label" x="{label_w - 10}" y="{by + thick / 2 + 4:.1f}" text-anchor="end">{esc(lab)}</text>')
            s.append(bar(sx(0), by, v / xmax * plot_w, thick, "c-bar" if strong else "c-bar c-soft", tip))
            s.append(f'<text class="c-value" x="{sx(v) + 6:.1f}" y="{by + thick / 2 + 4:.1f}">{fmt.format(v)}{unit}</text>')
            y += band
    s.append("</svg>")
    return "\n".join(s)


def fno_16():
    rows = [("Diffusion, one guided draw", 0.427, "Guided U²-Net diffusion, one draw: 0.427, 4 of 20 patterns died", False),
            ("FNO, trained on the past", 0.202, "FNO with cosine basis trained on the start state: 0.202, 2 died", False),
            ("FNO, trained on the future", 0.108, "FNO with cosine basis trained on the re-simulated future: 0.108, 1 died", True),
            ("Diffusion, best of 8 + polish", 0.0095, "Guided U²-Net, best of 8 draws + solver polish: 0.0095, none died", False),
            ("FNO, 8 views + polish", 0.0038, "FNO + 8 symmetry views + solver polish: 0.0038, none died; a tie with diffusion (lower on 12 of 20, p = 0.105)", True)]
    svg = grouped_hbars([("One pass", rows[:3]), ("With the solver polish", rows[3:])], 0.45, 0.15, "{:.4g}",
                        "median re-simulation error at step 300, 20 held-out scenes (lower is better)")
    write("research/fno", "grid16", svg, "16 × 16: recover the step-50 state from 50 observed pixels at step 300. Hover a bar for how many patterns died.")


def fno_32():
    def g(name, sup, warm, nov):
        return (name, [("supervised", sup, f"{name}, supervised: {sup:g}% of draws", False),
                       ("physics fit, warm start", warm, f"{name}, physics fit from the supervised weights: {warm:g}%", True),
                       ("fit + novelty, warm start", nov, f"{name}, fit plus novelty from the supervised weights: {nov:g}%", True)])
    svg = grouped_hbars([g("8 study shapes", 12.5, 75, 83), g("24 held-out Gray-Scott masks", 71, 96, 99), g("16 held-out drawn shapes", 12.5, 100, 97)],
                        100, 25, "{:g}", "share of draws that reproduce the target, MCC ≥ 0.8, horizon 300 steps", unit="%")
    write("research/fno", "grid32", svg, "32 × 32: parameter maps a, b, d from a fixed central blob. 8 draws per target.")


def fno_64():
    rows = [("published FNO layer", 0.4507, "Published 1×1 layer, 250 steps: 0.4507", False),
            ("+ local 3×3 to 7×7 kernels", 0.2693, "Local kernels added, 250 steps: 0.2693", False),
            ("+ fine-tuned on the future", 0.1683, "Local kernels, fine-tuned 4 kimg on the re-simulated future, 250 steps: 0.1683, none died", True),
            ("local kernels", 0.8708, "500 steps: 0.8708, 16 of 40 patterns died", False),
            ("+ future in the loss", 0.5249, "500 steps with the future in the loss: 0.5249, none died", True),
            ("any objective tried", 1.0, "1000 steps: 1.000, all 40 patterns died", False)]
    svg = grouped_hbars([("250 steps back", rows[:3]), ("500 steps back", rows[3:5]), ("1000 steps back", rows[5:])], 1.0, 0.25, "{:.4g}",
                        "re-simulation error, 40 held-out scenes (lower is better)")
    write("research/fno", "grid64", svg, "64 × 64: recover an earlier state from 800 of 4,096 pixels. At 1000 steps every recovered start dies out.")


if __name__ == "__main__":
    cell_modes()
    erk_frames()
    dc_data()
    dc_unets()
    dc_windows()
    dc_physics()
    fno_16()
    fno_32()
    fno_64()
