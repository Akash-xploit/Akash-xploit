#!/usr/bin/env python3
"""Render assets/activity.svg from the public GitHub contribution calendar."""
import datetime as dt
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "Akash-xploit"
OUT = "assets/activity.svg"

PANEL, TEXT, MUTED, DIM, BLUE = "#101826", "#f2f6fb", "#a9b6c6", "#6b7a8c", "#3fa9f5"
LEVELS = ["#1a2433", "#0e4a73", "#1672b0", "#2a8fd8", "#3fa9f5"]
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"

req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "activity-svg"})
page = urllib.request.urlopen(req, timeout=30).read().decode()

days = {}
for m in re.finditer(r'data-date="(\d{4}-\d\d-\d\d)" id="(contribution-day-component-[\d-]+)" data-level="(\d)"', page):
    days[m.group(2)] = [dt.date.fromisoformat(m.group(1)), int(m.group(3)), 0]
for m in re.finditer(r'for="(contribution-day-component-[\d-]+)"[^>]*>(\d+) contributions?', page):
    if m.group(1) in days:
        days[m.group(1)][2] = int(m.group(2))
if not days:
    sys.exit("no contribution data found")

cells = sorted(days.values())
total = sum(c[2] for c in cells)
active = sum(1 for c in cells if c[2])
streak = best = 0
for _, _, n in cells:
    streak = streak + 1 if n else 0
    best = max(best, streak)

W, CELL, GAP = 1200, 17, 4
weeks = (cells[-1][0] - cells[0][0]).days // 7 + 1
grid_w = weeks * (CELL + GAP) - GAP
x0, y0 = (W - grid_w) / 2, 76
H = y0 + 7 * (CELL + GAP) + 52

start = cells[0][0] - dt.timedelta(days=(cells[0][0].weekday() + 1) % 7)
rects, months, last_month = [], [], None
for d, lvl, n in cells:
    col = (d - start).days // 7
    row = (d.weekday() + 1) % 7
    x, y = x0 + col * (CELL + GAP), y0 + row * (CELL + GAP)
    rects.append(f'<rect x="{x:.0f}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{LEVELS[lvl]}"><title>{n} on {d:%b %-d, %Y}</title></rect>')
    if row == 0 and d.month != last_month:
        last_month = d.month
        months.append(f'<text x="{x:.0f}" y="{y0 - 10}" class="mono" font-size="11" fill="{DIM}">{d:%b}</text>')

def stat(x, label, value):
    return (f'<text x="{x}" y="36" class="mono" font-size="11" fill="{DIM}">{label}</text>'
            f'<text x="{x}" y="36" dx="{len(label) * 7 + 10}" class="sans" font-size="15" font-weight="600" fill="{TEXT}">{value}</text>')

legend_x = W - 24 - 5 * 15 - 70
legend = "".join(f'<rect x="{legend_x + 38 + i * 15}" y="{H - 30}" width="11" height="11" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<style>.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{PANEL}" stroke="#fff" stroke-opacity=".08"/>
{stat(x0, "contributions", f"{total:,}")}{stat(x0 + 230, "active days", active)}{stat(x0 + 420, "longest streak", f"{best}d")}
{"".join(months)}
{"".join(rects)}
<text x="{x0}" y="{H - 20}" class="mono" font-size="11" fill="{DIM}">last 12 months · updated {dt.date.today():%b %-d, %Y}</text>
<text x="{legend_x}" y="{H - 20}" class="mono" font-size="11" fill="{DIM}">less</text>{legend}
<text x="{legend_x + 38 + 5 * 15 + 4}" y="{H - 20}" class="mono" font-size="11" fill="{DIM}">more</text>
</svg>'''
open(OUT, "w").write(svg)
print(f"{OUT}: {total} contributions, {active} active days, best streak {best}")
