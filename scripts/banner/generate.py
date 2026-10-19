#!/usr/bin/env python3
"""Generate the animated GitHub profile banners (Cyber-Telemetry HUD Edition).

Run from the repository root:
    python scripts/banner/generate.py
"""

from __future__ import annotations

import html
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets/source/portrait.png"
ASSETS = ROOT / "assets"
LOGOS = Path(__file__).resolve().parent / "logos"

W, H = 1180, 610
INTRO_SECONDS = 3.2
TRANSITION_SECONDS = 1.3
LOGO_HOLD_SECONDS = 4.0
TRAVELLER_COUNT = 900
HOLD_PARTICLE_COUNT = 2_400
SEED = 314159
LOGO_SUFFIXES = {".png", ".webp"}
LOGO_ALIASES = {"kube": "kubernetes"}
PREFERRED_LOGO_ORDER = ("linux", "kubernetes")

YAML_ROWS = [
    (0, "telemetry_node", ""),
    (1, "engineer", "Omar Stankewech Marta Olvera"),
    (1, "role", "Telematics Engineer · Backend & AI"),
    (1, "institution", "UPIITA - IPN · Ciudad de Mexico"),
    (1, "architecture", "REST APIs · Microservices · Predictive ML"),
    (1, "certification", "CENEVAL Liderazgo SIC · Avanzado"),
    (0, "core_stack", ""),
    (1, "backend_api", "Python · FastAPI · Flask · SQLModel"),
    (1, "data_layer", "PostgreSQL · MySQL · SQLAlchemy"),
    (1, "machine_learning", "TensorFlow · Scikit-Learn · XGBoost · SHAP"),
    (1, "telematics_net", "5G-NR (ns-3) · Wireshark · Linux"),
    (1, "embedded_iot", "ESP32 · STM32 · C/C++ · NFC (AES)"),
    (1, "cross_platform", "Flutter · Dart · Git · Docker"),
    (0, "network_uplink", ""),
    (1, "github", "github.com/Stankewech"),
    (1, "linkedin", "/in/omar-stankewech"),
    (1, "status", "ONLINE · OPEN TO OPPORTUNITIES (UTC-6)"),
]

THEMES = {
    "dark": {
        "bg":       "#050811",
        "panel":    "#090F1E",
        "panel2":   "#0D1528",
        "line":     "#1E2D4A",
        "muted":    "#64748B",
        "text":     "#E2E8F0",
        "portrait": "#00F5D4",   # Cyber Electric Cyan
        "chrome":   "#818CF8",   # Neon Indigo
        "accent":   "#10B981",   # Emerald Telemetry LED
        "shadow":   "#010307",
    },
    "light": {
        "bg":       "#F1F5F9",
        "panel":    "#FFFFFF",
        "panel2":   "#F8FAFC",
        "line":     "#CBD5E1",
        "muted":    "#64748B",
        "text":     "#0F172A",
        "portrait": "#0D9488",   # Deep Cyber Teal
        "chrome":   "#4F46E5",   # Royal Indigo
        "accent":   "#059669",
        "shadow":   "#94A3B8",
    },
}


def edge_connected(mask: np.ndarray) -> np.ndarray:
    connected = np.zeros(mask.shape, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    height, width = mask.shape
    for x in range(width):
        queue.extend(((0, x), (height - 1, x)))
    for y in range(height):
        queue.extend(((y, 0), (y, width - 1)))
    while queue:
        y, x = queue.popleft()
        if connected[y, x] or not mask[y, x]:
            continue
        connected[y, x] = True
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < height and 0 <= nx < width:
                queue.append((ny, nx))
    return connected


def normalize_logo(image: Image.Image) -> Image.Image:
    icon = image.convert("RGBA")
    alpha = icon.getchannel("A")
    if alpha.getextrema() == (255, 255):
        gray = np.asarray(ImageOps.grayscale(icon))
        background = edge_connected(gray >= 220)
        visible = ~background
        visible = np.asarray(
            Image.fromarray((visible * 255).astype("uint8"))
            .filter(ImageFilter.MaxFilter(3))
        ) > 0
        exterior = edge_connected(~visible)
        icon.putalpha(Image.fromarray(np.where(exterior, 0, 255).astype("uint8")))
    icon.thumbnail((320, 320), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    offset = ((400 - icon.width) // 2, (400 - icon.height) // 2)
    canvas.alpha_composite(icon, offset)
    if canvas.getchannel("A").getbbox() is None:
        raise ValueError("icon has no visible pixels")
    return canvas


def load_logo_files() -> dict[str, Image.Image]:
    loaded: dict[str, Image.Image] = {}
    for path in sorted(LOGOS.iterdir()):
        if not path.is_file() or path.suffix.lower() not in LOGO_SUFFIXES:
            continue
        name = LOGO_ALIASES.get(path.stem.lower(), path.stem.lower())
        with Image.open(path) as image:
            loaded[name] = normalize_logo(image)
    return loaded


def make_logos() -> dict[str, Image.Image]:
    LOGOS.mkdir(parents=True, exist_ok=True)
    logos = load_logo_files()
    if not logos:
        raise SystemExit(f"No PNG or WebP icons found in {LOGOS.relative_to(ROOT)}")
    ordered_names = [name for name in PREFERRED_LOGO_ORDER if name in logos]
    ordered_names.extend(name for name in sorted(logos) if name not in ordered_names)
    return {name: logos[name] for name in ordered_names}


def floyd_steinberg(gray: np.ndarray) -> np.ndarray:
    work = gray.astype(np.float32) / 255.0
    out = np.zeros_like(work, dtype=bool)
    height, width = work.shape
    for y in range(height):
        left_to_right = y % 2 == 0
        xs = range(width) if left_to_right else range(width - 1, -1, -1)
        direction = 1 if left_to_right else -1
        for x in xs:
            old = work[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = bool(new)
            err = old - new
            nx = x + direction
            if 0 <= nx < width:
                work[y, nx] += err * 7 / 16
            if y + 1 < height:
                if 0 <= x - direction < width:
                    work[y + 1, x - direction] += err * 3 / 16
                work[y + 1, x] += err * 5 / 16
                if 0 <= nx < width:
                    work[y + 1, nx] += err * 1 / 16
    return out


def portrait_points(theme: str, rng: np.random.Generator) -> np.ndarray:
    source = Image.open(SOURCE).convert("RGBA")
    w, h = source.size
    crop_w = int(w * 0.60)
    crop_h = int(crop_w * (340 / 300))
    left = (w - crop_w) // 2
    top = int(h * 0.08)
    crop = source.crop((left, top, left + crop_w, top + crop_h)).resize((300, 340), Image.Resampling.LANCZOS)
    alpha = np.asarray(crop.getchannel("A"), dtype=np.float32) / 255.0

    if theme == "dark":
        bg = Image.new("RGBA", crop.size, "black")
        bg.alpha_composite(crop)
        prepared = ImageOps.grayscale(bg.convert("RGB"))
        prepared = ImageOps.autocontrast(prepared, cutoff=1)
        prepared = ImageEnhance.Contrast(prepared).enhance(1.35)
        prepared = ImageEnhance.Brightness(prepared).enhance(1.05)
        prepared = prepared.filter(ImageFilter.UnsharpMask(radius=2.0, percent=160, threshold=1))
        select_lit = True
    else:
        bg = Image.new("RGBA", crop.size, "white")
        bg.alpha_composite(crop)
        prepared = ImageOps.grayscale(bg.convert("RGB"))
        prepared = ImageOps.autocontrast(prepared, cutoff=1)
        prepared = ImageEnhance.Contrast(prepared).enhance(1.25)
        prepared = ImageEnhance.Brightness(prepared).enhance(1.05)
        prepared = prepared.filter(ImageFilter.UnsharpMask(radius=2.0, percent=150, threshold=1))
        select_lit = False

    bits = floyd_steinberg(np.asarray(prepared))
    active = bits if select_lit else ~bits
    if theme == "dark":
        active &= alpha > 0.08

    ys, xs = np.where(active)
    if len(xs) == 0:
        return np.zeros((0, 2), dtype=np.float32)
    points = np.column_stack((74 + xs, 154 + ys)).astype(np.float32)
    if len(points) > 18000:
        points = points[rng.choice(len(points), 18000, replace=False)]
    return points


def logo_silhouette_points(image: Image.Image) -> np.ndarray:
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.where(alpha > 127)
    return np.column_stack((89 + xs * 0.675, 188 + ys * 0.675)).astype(np.float32)


def sample_logo_points(image: Image.Image, rng: np.random.Generator, count: int) -> np.ndarray:
    points = logo_silhouette_points(image)
    if not len(points):
        raise ValueError("icon has no visible pixels")
    chosen = rng.choice(len(points), count, replace=len(points) < count)
    return points[chosen]


def transport(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    rows, cols = linear_sum_assignment(cdist(source, target, metric="sqeuclidean"))
    ordered = np.empty_like(target)
    ordered[rows] = target[cols]
    return ordered


def num(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def time_num(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def point_path(points: np.ndarray) -> str:
    if not len(points):
        return ""
    integer = np.rint(points).astype(int)
    unique = sorted({(int(x), int(y)) for x, y in integer}, key=lambda p: (p[1], p[0]))
    chunks: list[str] = []
    i = 0
    while i < len(unique):
        x0, y = unique[i]
        x1 = x0
        i += 1
        while i < len(unique) and unique[i][1] == y and unique[i][0] <= x1 + 1:
            x1 = unique[i][0]
            i += 1
        chunks.append(f"M{x0} {y}h{x1 - x0 + 1}")
    return "".join(chunks)


def particle_path(points: np.ndarray) -> str:
    integer = np.rint(points).astype(int)
    unique = sorted({(int(x), int(y)) for x, y in integer}, key=lambda p: (p[1], p[0]))
    return "".join(f"M{x} {y}h1" for x, y in unique)


def animate_values(points: list[np.ndarray], index: int) -> str:
    return ";".join(f"{num(p[index, 0])} {num(p[index, 1])}" for p in points)


def render_svg(
    theme_name: str,
    portrait: np.ndarray,
    logo_points: dict[str, np.ndarray],
    logo_hold_particles: dict[str, np.ndarray],
    rng: np.random.Generator,
) -> str:
    t = THEMES[theme_name]
    n = min(TRAVELLER_COUNT, len(portrait))
    source = portrait[rng.choice(len(portrait), n, replace=False)]
    targets: list[np.ndarray] = []
    current = source
    for name, points in logo_points.items():
        current = transport(current, points[:n])
        targets.append(current)

    times = [0.0, 3.0]
    frames = [source, source]
    for target in targets:
        times.extend((times[-1] + TRANSITION_SECONDS,
                      times[-1] + TRANSITION_SECONDS + LOGO_HOLD_SECONDS))
        frames.extend((target, target))
    times.append(times[-1] + TRANSITION_SECONDS)
    frames.append(source)
    loop_seconds = times[-1]
    loop_duration = time_num(loop_seconds)
    key_times = ";".join(time_num(v / loop_seconds) for v in times)
    opacity_values = ";".join(["0", "0"] + ["1"] * (len(frames) - 3) + ["0"])

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        'aria-labelledby="title desc">',
        '<title id="title">Omar Stankewech — Telematics &amp; AI System Profile</title>',
        '<desc id="desc">Animated cyber-telemetry terminal profile for Omar Stankewech.</desc>',
        "<defs>",
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
        f'<feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="{t["shadow"]}" '
        'flood-opacity=".35"/></filter>',
        '<linearGradient id="scanGrad" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{t["portrait"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{t["portrait"]}" stop-opacity="0.45"/>'
        f'<stop offset="100%" stop-color="{t["portrait"]}" stop-opacity="0"/>'
        '</linearGradient>',
        '<clipPath id="visualClip"><rect x="49" y="124" width="390" height="414" rx="3"/></clipPath>',
        "</defs>",
        # Outer Window
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" '
        f'stroke="{t["line"]}" stroke-width="1.2" filter="url(#shadow)"/>',
        f'<path d="M13 62H1167" stroke="{t["line"]}"/>',
        # Window Controls
        '<circle cx="38" cy="38" r="6" fill="#FF5F57"/>'
        '<circle cx="59" cy="38" r="6" fill="#FEBC2E"/>'
        '<circle cx="80" cy="38" r="6" fill="#28C840"/>',
        f'<text x="590" y="43" text-anchor="middle" fill="{t["muted"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
        'letter-spacing=".6">stankewech@upiita-ipn: ~/telemetry/profile.yml — nvim</text>',
        # Top-right Telemetry Uplink Indicator
        f'<circle cx="1065" cy="38" r="4" fill="{t["accent"]}">'
        '<animate attributeName="opacity" values="1;0.25;1" dur="1.8s" repeatCount="indefinite"/>'
        '</circle>',
        f'<text x="1077" y="42" fill="{t["accent"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" '
        'font-weight="700" letter-spacing="1">5G-NR UPLINK</text>',
        # Left Visual Frame (LiDAR / Biometric Scan)
        f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["panel2"]}" '
        f'stroke="{t["line"]}"/>',
        f'<path d="M35 124H453" stroke="{t["line"]}"/>',
        f'<text x="49" y="111" fill="{t["portrait"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
        'font-weight="700" letter-spacing="1.2">◈ BIOMETRIC.LIDAR</text>',
        f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">300×340 / MATRIX</text>',
        # Subtle HUD Crosshairs & Corner Brackets
        f'<path d="M244 134v394M59 331h370" stroke="{t["line"]}" stroke-dasharray="3 6" opacity=".45"/>',
        f'<path d="M49 141h14M49 141v14M439 141h-14M439 141v14M49 539h14M49 539v-14'
        f'M439 539h-14M439 539v-14" fill="none" stroke="{t["portrait"]}" stroke-width="1.5" opacity=".75"/>',
        '<g clip-path="url(#visualClip)" shape-rendering="crispEdges">',
        '<g opacity="1">',
    ]

    first_centroid = targets[0].mean(axis=0)
    band_ids = rng.integers(0, 94, size=len(portrait))
    noise = rng.normal(0, 4, size=(94, 2))
    for band in range(94):
        pts = portrait[band_ids == band]
        if not len(pts):
            continue
        centroid = pts.mean(axis=0)
        delta = (first_centroid - centroid) * 0.18 + noise[band]
        drift_positions = ["0 0", "0 0", f"{num(delta[0])} {num(delta[1])}",
                           f"{num(delta[0])} {num(delta[1])}"]
        drift_positions.extend(["0 0"] * (len(frames) - len(drift_positions)))
        drift_opacity = [".94", ".94", "0", "0"]
        drift_opacity.extend(["0"] * (len(frames) - len(drift_opacity) - 1))
        drift_opacity.append(".94")
        d = point_path(pts)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{t["portrait"]}" stroke-width="1" '
            'opacity=".94">'
            f'<animateTransform attributeName="transform" type="translate" begin="{INTRO_SECONDS}s" '
            f'dur="{loop_duration}s" repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{key_times}" values="{";".join(drift_positions)}"/>'
            f'<animate attributeName="opacity" begin="{INTRO_SECONDS}s" dur="{loop_duration}s" '
            f'repeatCount="indefinite" keyTimes="{key_times}" '
            f'values="{";".join(drift_opacity)}"/></path>'
        )

    for i in range(n):
        positions = animate_values(frames, i)
        parts.append(
            f'<path d="M-.65-.65h1.3v1.3h-1.3z" fill="{t["portrait"]}">'
            f'<animateTransform attributeName="transform" type="translate" begin="{INTRO_SECONDS}s" '
            f'dur="{loop_duration}s" repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{key_times}" values="{positions}"/>'
            f'<animate attributeName="opacity" begin="{INTRO_SECONDS}s" dur="{loop_duration}s" '
            f'repeatCount="indefinite" calcMode="linear" keyTimes="{key_times}" '
            f'values="{opacity_values}"/></path>'
        )

    for index, (name, particles) in enumerate(logo_hold_particles.items()):
        visible = ["0"] * len(frames)
        visible[index * 2 + 2] = ".85"
        visible[index * 2 + 3] = ".85"
        parts.append(
            f'<path d="{particle_path(particles)}" fill="none" stroke="{t["portrait"]}" '
            'stroke-width="1" opacity="0">'
            f'<animate attributeName="opacity" begin="{INTRO_SECONDS}s" dur="{loop_duration}s" '
            f'repeatCount="indefinite" calcMode="linear" keyTimes="{key_times}" '
            f'values="{";".join(visible)}"/></path>'
        )
    parts.append("</g>")

    intro_ids = rng.integers(0, 60, size=len(portrait))
    order = rng.permutation(60)
    starts = np.empty(60)
    starts[order] = np.linspace(0.05, 1.2, 60)
    for group in range(60):
        pts = portrait[intro_ids == group]
        if not len(pts):
            continue
        parts.append(
            f'<path d="{point_path(pts)}" fill="none" stroke="{t["portrait"]}" '
            'stroke-width="1" opacity="0">'
            f'<animate attributeName="opacity" begin="{num(starts[group])}s" dur=".8s" '
            'values="0;1" fill="freeze"/>'
            '<animate attributeName="opacity" begin="3.08s" dur=".12s" values="1;0" fill="freeze"/>'
            "</path>"
        )

    # Animated LiDAR Scanline sweeping vertically across the portrait frame
    parts.extend(
        [
            '<rect x="52" y="135" width="384" height="2" fill="url(#scanGrad)">'
            '<animate attributeName="y" values="135;530;135" dur="6s" repeatCount="indefinite"/>'
            '</rect>',
            "</g>",
            # Left Frame Telemetry Footer
            f'<text x="58" y="551" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="10">'
            f'NODES: {len(portrait):05d} · OPTIMAL TRANSPORT · DTYPE: FP32</text>',
            # Right Information Panel (Neovim Telemetry View)
            f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" '
            f'stroke="{t["line"]}"/>',
            f'<path d="M474 124H1146" stroke="{t["line"]}"/>',
            f'<text x="490" y="111" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
            'font-weight="700" letter-spacing=".5">telemetry_profile.yml</text>',
            f'<text x="665" y="111" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[YAML · RO]</text>',
            f'<rect x="984" y="94" width="146" height="24" rx="12" fill="{t["portrait"]}" opacity=".12" '
            f'stroke="{t["portrait"]}"/>',
            f'<text x="1057" y="111" text-anchor="middle" fill="{t["portrait"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
            'font-weight="700">@Stankewech</text>',
        ]
    )

    row_y = 148.0
    for idx, (indent, key, value) in enumerate(YAML_ROWS, 1):
        line_num = f"{idx:2d}"
        if indent == 0:
            content = f'<tspan fill="{t["chrome"]}" font-weight="700">▸ {html.escape(key)}:</tspan>'
            text_x = 522.0
        else:
            content = (
                f'<tspan fill="{t["portrait"]}">{html.escape(key)}: </tspan>'
                f'<tspan fill="{t["text"]}">{html.escape(value)}</tspan>'
            )
            text_x = 542.0

        parts.extend(
            [
                f'<text x="506" y="{num(row_y)}" text-anchor="end" fill="{t["muted"]}" opacity=".45" '
                'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13">'
                f"{line_num}</text>",
                f'<text x="{num(text_x)}" y="{num(row_y)}" '
                'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13">'
                f"{content}</text>",
            ]
        )
        row_y += 21.5

    # Blinking cursor on the last line
    last_y = row_y - 21.5
    parts.append(
        f'<rect x="855" y="{num(last_y - 11)}" width="8" height="14" fill="{t["portrait"]}">'
        '<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
        '</rect>'
    )

    # Neovim / Tmux Status Bar at bottom of panel
    parts.extend(
        [
            f'<path d="M474 526H1146" stroke="{t["line"]}"/>',
            f'<rect x="475" y="527" width="670" height="32" fill="{t["panel"]}" rx="0 0 5 5"/>',
            f'<rect x="485" y="533" width="96" height="20" rx="3" fill="{t["portrait"]}"/>',
            f'<text x="533" y="547" text-anchor="middle" fill="{t["bg"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">TELEMATICS</text>',
            f'<rect x="588" y="533" width="70" height="20" rx="3" fill="{t["chrome"]}" opacity=".2"/>',
            f'<text x="623" y="547" text-anchor="middle" fill="{t["chrome"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">⎇ main</text>',
            f'<text x="672" y="547" fill="{t["text"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" font-weight="600">UPIITA-IPN</text>',
            f'<text x="770" y="547" fill="{t["muted"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[python · fastapi · ml]</text>',
            f'<text x="1134" y="547" text-anchor="end" fill="{t["portrait"]}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">100% ☰ 17:42</text>',
            "</svg>",
        ]
    )
    return "".join(parts)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source portrait: {SOURCE}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    logos = make_logos()

    portraits: dict[str, np.ndarray] = {}
    for index, theme in enumerate(THEMES):
        rng = np.random.default_rng(SEED + index)
        points = portrait_points(theme, rng)
        portraits[theme] = points

    for index, theme in enumerate(THEMES):
        rng = np.random.default_rng(SEED + 100 + index)
        sampled = {
            name: sample_logo_points(image, rng, TRAVELLER_COUNT)
            for name, image in logos.items()
        }
        hold_particles = {
            name: sample_logo_points(image, rng, HOLD_PARTICLE_COUNT)
            for name, image in logos.items()
        }
        svg = render_svg(theme, portraits[theme], sampled, hold_particles, rng)
        output = ASSETS / f"banner-{theme}.v9.svg"
        output.write_text(svg, encoding="utf-8")
        byte_size = output.stat().st_size
        print(
            f"{output.relative_to(ROOT)}: {byte_size:,} bytes "
            f"({byte_size / 1024:.1f} KiB), {len(portraits[theme]):,} portrait dots"
        )


if __name__ == "__main__":
    main()