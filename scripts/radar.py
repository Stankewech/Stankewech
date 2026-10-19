#!/usr/bin/env python3
"""
radar.py - Cyber-Telemetry HUD Radar Chart Generator (Stdlib only).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

THEMES = {
    "dark": {
        "bg": "#090F1E",
        "panel_border": "#1E2D4A",
        "header_bg": "#0D1528",
        "grid": "#1E293B",
        "grid_outer": "#334155",
        "spoke": "#1E293B",
        "label": "#E2E8F0",
        "value": "#00F5D4",
        "title": "#00F5D4",
        "subtitle": "#64748B",
        "fill_start": "#00F5D4",
        "fill_end": "#818CF8",
        "stroke": "#00F5D4",
        "vertex": "#090F1E",
        "vertex_Ring": "#00F5D4",
    },
    "light": {
        "bg": "#FFFFFF",
        "panel_border": "#CBD5E1",
        "header_bg": "#F8FAFC",
        "grid": "#E2E8F0",
        "grid_outer": "#94A3B8",
        "spoke": "#E2E8F0",
        "label": "#0F172A",
        "value": "#0D9488",
        "title": "#0F172A",
        "subtitle": "#64748B",
        "fill_start": "#0D9488",
        "fill_end": "#4F46E5",
        "stroke": "#0D9488",
        "vertex": "#FFFFFF",
        "vertex_Ring": "#0D9488",
    },
}

UA = {"User-Agent": "radar.py"}
FONT = "ui-monospace,SFMono-Regular,Consolas,monospace"
LBL, VAL, TTL = 12, 11, 13


def from_json(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    axes = [(a["label"], float(a["value"])) for a in d["axes"]]
    return d.get("title", "TELEMETRY.RADAR"), axes


def _api(url, token):
    req = urllib.request.Request(url, headers=dict(UA))
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def from_github(user: str, token: str | None, limit: int, exclude: set[str],
                curve: float):
    totals: dict[str, int] = {}
    page = 1
    while True:
        repos = _api(
            f"https://api.github.com/users/{user}/repos"
            f"?per_page=100&page={page}&type=owner&sort=pushed",
            token,
        )
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            try:
                langs = _api(repo["languages_url"], token)
            except urllib.error.HTTPError:
                continue
            for name, count in langs.items():
                if name.lower() in exclude:
                    continue
                totals[name] = totals.get(name, 0) + count
        if len(repos) < 100:
            break
        page += 1

    if not totals:
        sys.exit(f"no language data found for '{user}'")

    top = sorted(totals.items(), key=lambda kv: -kv[1])[:limit]
    peak = top[0][1]
    axes = [(n, round(100 * (c / peak) ** curve, 1)) for n, c in top]
    return f"{user.upper()} · LANGUAGE.MIX", axes


def ring(radius, n, start=-math.pi / 2):
    return [
        (radius * math.cos(start + i * 2 * math.pi / n),
         radius * math.sin(start + i * 2 * math.pi / n))
        for i in range(n)
    ]


def text_width(s, font_size):
    return len(s) * font_size * 0.62


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(title, axes, theme: str, size: int, rings: int, show_values: bool,
           animate: bool) -> str:
    c = THEMES[theme]
    n = len(axes)
    r = size / 2 - 42
    gap = 24

    vals = [max(0.0, min(100.0, v)) for _, v in axes]
    outer = ring(r, n)

    labels = []
    for i, (label, _) in enumerate(axes):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        cosv, sinv = math.cos(ang), math.sin(ang)
        lx, ly = (r + gap) * cosv, (r + gap) * sinv
        anchor = "middle" if abs(cosv) < 0.25 else ("start" if cosv > 0 else "end")
        dy = 4 if abs(sinv) < 0.25 else (12 if sinv > 0 else -6)
        labels.append((lx, ly + dy, anchor, label, vals[i]))

    minx, maxx, miny, maxy = -r - 20, r + 20, -r - 20, r + 20
    for lx, ly, anchor, label, v in labels:
        w = max(text_width(label, LBL),
                text_width(f"[{v:g}%]", VAL) if show_values else 0.0)
        if anchor == "start":
            x0, x1 = lx, lx + w
        elif anchor == "end":
            x0, x1 = lx - w, lx
        else:
            x0, x1 = lx - w / 2, lx + w / 2
        y0 = ly - LBL
        y1 = ly + 6 + (VAL + 6 if show_values else 0)
        minx, maxx = min(minx, x0), max(maxx, x1)
        miny, maxy = min(miny, y0), max(maxy, y1)

    pad = 24
    header_h = 40
    footer_h = 26
    W = max(420, round((maxx - minx) + 2 * pad))
    H = round((maxy - miny) + 2 * pad + header_h + footer_h)
    ox = W / 2
    oy = -miny + pad + header_h

    avg_score = sum(vals) / len(vals)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{esc(title)}" font-family="{FONT}">',
        "<defs>",
        '<radialGradient id="polyGrad" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{c["fill_end"]}" stop-opacity="0.15"/>'
        f'<stop offset="100%" stop-color="{c["fill_start"]}" stop-opacity="0.42"/>'
        "</radialGradient>",
        '<filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="{c["stroke"]}" flood-opacity="0.55"/>'
        "</filter>",
        "</defs>",
        # Card container
        f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="10" fill="{c["bg"]}" '
        f'stroke="{c["panel_border"]}" stroke-width="1.5"/>',
        f'<rect x="3" y="3" width="{W - 6}" height="{header_h}" rx="9" fill="{c["header_bg"]}"/>',
        f'<line x1="2" y1="{header_h}" x2="{W - 2}" y2="{header_h}" stroke="{c["panel_border"]}"/>',
        # Header title & decorative dots
        f'<text x="16" y="25" font-size="{TTL}" font-weight="700" letter-spacing="1" fill="{c["title"]}">'
        f'◈ {esc(title.upper())}</text>',
        f'<text x="{W - 16}" y="25" text-anchor="end" font-size="11" fill="{c["subtitle"]}">'
        f'AVG: {avg_score:.1f}%</text>',
        f'<g transform="translate({ox:.1f},{oy:.1f})">',
    ]

    # Concentric rings + reference circles
    for k in range(rings, 0, -1):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in ring(r * k / rings, n))
        is_outer = k == rings
        stroke_col = c["grid_outer"] if is_outer else c["grid"]
        dash = "" if is_outer else 'stroke-dasharray="3 3"'
        parts.append(
            f'<polygon points="{d}" fill="none" stroke="{stroke_col}" '
            f'stroke-width="{1.4 if is_outer else 1}" {dash}/>'
        )

    # Crosshair spokes
    for x, y in outer:
        parts.append(
            f'<line x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="{c["spoke"]}" stroke-width="1"/>'
        )

    # Data polygon with glow
    shape = [(px * v / 100, py * v / 100) for (px, py), v in zip(outer, vals)]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in shape)
    parts.append("<g>")
    if animate:
        parts.append(
            '<animateTransform attributeName="transform" type="scale" '
            'values="0.05;1" dur="1.2s" calcMode="spline" keyTimes="0;1" '
            'keySplines="0.16 1 0.3 1" fill="freeze"/>'
        )
    parts.append(
        f'<polygon points="{d}" fill="url(#polyGrad)" '
        f'stroke="{c["stroke"]}" stroke-width="2.2" stroke-linejoin="round" filter="url(#neonGlow)"/>'
    )
    for x, y in shape:
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c["vertex"]}" '
            f'stroke="{c["vertex_Ring"]}" stroke-width="2.2"/>'
        )
    parts.append("</g>")

    # Axis labels + percentage tags
    for lx, ly, anchor, label, v in labels:
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-size="{LBL}" font-weight="700" fill="{c["label"]}">'
            f'{esc(label)}</text>'
        )
        if show_values:
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + VAL + 4:.1f}" text-anchor="{anchor}" '
                f'font-size="{VAL}" font-weight="600" fill="{c["value"]}">[{v:g}%]</text>'
            )

    parts.extend([
        "</g>",
        f'<line x1="2" y1="{H - footer_h}" x2="{W - 2}" y2="{H - footer_h}" stroke="{c["panel_border"]}"/>',
        f'<text x="16" y="{H - 9}" font-size="10" fill="{c["subtitle"]}">'
        f'AXES: 0{n} · SCALE: NORMALIZED [0-100]</text>',
        f'<text x="{W - 16}" y="{H - 9}" text-anchor="end" font-size="10" fill="{c["value"]}">'
        '● TELEMETRY ACTIVE</text>',
        "</svg>",
    ])
    return "".join(parts)


def main(argv=None):
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group()
    src.add_argument("--data", type=Path, default=Path("assets/skills.json"))
    src.add_argument("--github", metavar="USER")
    p.add_argument("-o", "--out", type=Path, default=Path("assets/radar"))
    p.add_argument("--title")
    p.add_argument("--size", type=int, default=420)
    p.add_argument("--rings", type=int, default=4)
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--exclude", default="html,css,shell,makefile,dockerfile,batchfile")
    p.add_argument("--curve", type=float, default=0.5)
    p.add_argument("--values", action="store_true")
    p.add_argument("--no-animate", dest="animate", action="store_false")
    args = p.parse_args(argv)

    if args.github:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        excl = {s.strip().lower() for s in args.exclude.split(",") if s.strip()}
        title, axes = from_github(args.github, token, args.limit, excl, args.curve)
    else:
        if not args.data.exists():
            sys.exit(f"no data file: {args.data}")
        title, axes = from_json(args.data)

    if args.title is not None:
        title = args.title
    if len(axes) < 3:
        sys.exit("a radar chart needs at least 3 axes")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        svg = render(title, axes, theme, args.size, args.rings, args.values,
                     args.animate)
        dest = args.out.with_name(f"{args.out.name}-{theme}.svg")
        dest.write_text(svg, encoding="utf-8")
        print(f"wrote {dest}  ({len(axes)} axes)")


if __name__ == "__main__":
    main()