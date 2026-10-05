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
x0, y0 = (W - grid_w) / 2, 110
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
    return (f'<text x="{x}" y="72" class="mono" font-size="11" fill="{DIM}">{label}</text>'
            f'<text x="{x}" y="72" dx="{len(label) * 7 + 10}" class="sans" font-size="15" font-weight="600" fill="{TEXT}">{value}</text>')

legend_x = W - 24 - 5 * 15 - 70
legend = "".join(f'<rect x="{legend_x + 38 + i * 15}" y="{H - 30}" width="11" height="11" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<style>.sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}</style>
<defs><linearGradient id="rim" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset=".35" stop-color="#fff" stop-opacity=".06"/>
  <stop offset=".7" stop-color="#fff" stop-opacity=".03"/><stop offset="1" stop-color="#fff" stop-opacity=".25"/>
</linearGradient><clipPath id="win"><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12"/></clipPath></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{PANEL}" fill-opacity=".92"/>
<g clip-path="url(#win)"><rect width="{W}" height="38" fill="#fff" fill-opacity=".045"/><rect y="38" width="{W}" height="1" fill="#fff" fill-opacity=".07"/></g>
<circle cx="22" cy="19.5" r="6" fill="#ff5f57"/><circle cx="42" cy="19.5" r="6" fill="#febc2e"/><circle cx="62" cy="19.5" r="6" fill="#28c840"/>
<text x="84" y="24" class="mono" font-size="12.5" fill="{BLUE}">~/activity</text>
<text x="{W - 22}" y="25" text-anchor="end" class="sans" font-size="14" font-weight="600" fill="{TEXT}">Contribution activity</text>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="url(#rim)"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{BLUE}" stroke-opacity=".28"/>
{stat(x0, "contributions", f"{total:,}")}{stat(x0 + 230, "active days", active)}{stat(x0 + 420, "longest streak", f"{best}d")}
{"".join(months)}
{"".join(rects)}
<text x="{x0}" y="{H - 20}" class="mono" font-size="11" fill="{DIM}">last 12 months · updated {dt.date.today():%b %-d, %Y}</text>
<text x="{legend_x}" y="{H - 20}" class="mono" font-size="11" fill="{DIM}">less</text>{legend}
<text x="{legend_x + 38 + 5 * 15 + 4}" y="{H - 20}" class="mono" font-size="11" fill="{DIM}">more</text>
</svg>'''
open(OUT, "w").write(svg)
print(f"{OUT}: {total} contributions, {active} active days, best streak {best}")
