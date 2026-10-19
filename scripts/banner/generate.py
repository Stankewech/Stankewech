#!/usr/bin/env python3
"""Generate a Fluid Animated 8-bit SVG banner using custom PNG sprites.
Seamless background integration with high-resolution 56-frame timeline.

Run from the repository root:
    python scripts/banner/generate.py
"""

from __future__ import annotations

import base64
import html
import io
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
SPRITES_DIR = ASSETS / "sprites"

W, H = 1180, 610

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
        "cyan":     "#00F5D4",
        "chrome":   "#818CF8",
        "accent":   "#10B981",
        "shadow":   "#010307",
    },
    "light": {
        "bg":       "#F1F5F9",
        "panel":    "#FFFFFF",
        "panel2":   "#F8FAFC",
        "line":     "#CBD5E1",
        "muted":    "#64748B",
        "text":     "#0F172A",
        "cyan":     "#0D9488",
        "chrome":   "#4F46E5",
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


def load_pixel_badge(name: str) -> str | None:
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        for folder in (SPRITES_DIR, ROOT / "scripts/banner/logos"):
            candidate = folder / f"{name}{ext}"
            if candidate.exists():
                img = Image.open(candidate).convert("RGBA")
                arr = np.asarray(img).copy()
                if arr[0, 0, 3] > 200:
                    bg_rgb = arr[0, 0, :3].astype(float)
                    diff = np.linalg.norm(arr[:, :, :3].astype(float) - bg_rgb, axis=2)
                    bg_mask = edge_connected(diff < 35.0)
                    arr[bg_mask, 3] = 0
                cleaned = Image.fromarray(arr, "RGBA")
                bbox = cleaned.getchannel("A").getbbox()
                if bbox:
                    cleaned = cleaned.crop(bbox)
                small = cleaned.resize((32, 32), Image.Resampling.BILINEAR)
                pixelated = small.resize((64, 64), Image.Resampling.NEAREST)
                buf = io.BytesIO()
                pixelated.save(buf, format="PNG", optimize=True)
                return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
    return None


def fallback_corner_emblems(t: dict[str, str]) -> str:
    return (
        '<g shape-rendering="crispEdges">'
        '<animateTransform attributeName="transform" type="translate" values="0 0; 0 -3; 0 0" dur="2.4s" repeatCount="indefinite"/>'
        '<rect x="48" y="136" width="64" height="64" fill="#090F1E" stroke="#6C1D45" stroke-width="3"/>'
        '<rect x="54" y="142" width="52" height="36" fill="#6C1D45"/>'
        '<rect x="62" y="146" width="36" height="28" fill="#FFFFFF"/>'
        '<rect x="68" y="150" width="24" height="20" fill="#6C1D45"/>'
        '<rect x="76" y="154" width="8" height="12" fill="#FFFFFF"/>'
        '<text x="80" y="193" text-anchor="middle" fill="#FFFFFF" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" font-weight="700" letter-spacing="2">IPN</text>'
        '</g>'
        '<g shape-rendering="crispEdges">'
        '<animateTransform attributeName="transform" type="translate" values="0 -3; 0 0; 0 -3" dur="2.4s" repeatCount="indefinite"/>'
        '<rect x="376" y="136" width="64" height="64" fill="#090F1E" stroke="#F59E0B" stroke-width="3"/>'
        '<rect x="382" y="142" width="52" height="36" fill="#1E3A8A"/>'
        '<rect x="392" y="146" width="32" height="28" fill="#F59E0B"/>'
        '<rect x="398" y="152" width="20" height="16" fill="#090F1E"/>'
        '<rect x="404" y="156" width="8" height="8" fill="#F59E0B"/>'
        '<text x="408" y="193" text-anchor="middle" fill="#F59E0B" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700" letter-spacing="1">UPIITA</text>'
        '</g>'
    )


def load_sprites() -> tuple[dict[str, str], str]:
    loaded: dict[str, str] = {}
    search_dirs = [SPRITES_DIR, ASSETS, ROOT]
    global_bg_hex = "#080D1A"

    for folder in search_dirs:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("sprite_*.*")):
            if path.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}:
                key = path.stem.lower()
                if key not in loaded:
                    img = Image.open(path).convert("RGB")
                    arr = np.asarray(img)
                    
                    bg_rgb = tuple(arr[0, 0, :3])
                    current_bg_hex = "#{:02x}{:02x}{:02x}".format(*bg_rgb)
                    
                    if not loaded:
                        global_bg_hex = current_bg_hex

                    target_height = 230
                    scale = target_height / max(1, img.height)
                    new_w = max(1, int(round(img.width * scale)))
                    new_h = max(1, int(round(img.height * scale)))
                    resized = img.resize((new_w, new_h), Image.Resampling.NEAREST)

                    canvas_w, canvas_h = 240, 250
                    canvas = Image.new("RGB", (canvas_w, canvas_h), bg_rgb)
                    offset_x = (canvas_w - new_w) // 2
                    offset_y = canvas_h - new_h - 6
                    canvas.paste(resized, (max(0, offset_x), max(0, offset_y)))

                    buf = io.BytesIO()
                    canvas.save(buf, format="PNG", optimize=True)
                    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    loaded[key] = f"data:image/png;base64,{b64}"

    if not loaded:
        raise SystemExit(f"No se encontraron 'sprite_XX.png' en {SPRITES_DIR.relative_to(ROOT)}.")
    
    return loaded, global_bg_hex


def build_timeline(sprites: dict[str, str]) -> list[tuple[str, int, int, int]]:
    """Línea de tiempo de Alta Resolución (56 frames) para una animación super fluida."""
    desired_sequence = [
        # Idle (16 cuadros = respiración natural fluida)
        ("sprite_01", 0, 0, 0), ("sprite_01", 0, 0, 0),
        ("sprite_02", 0, 0, 0), ("sprite_02", 0, 0, 0),
        ("sprite_03", 0, 0, 0), ("sprite_03", 0, 0, 0),
        ("sprite_04", 0, 0, 0), ("sprite_04", 0, 0, 0),
        ("sprite_01", 0, 0, 0), ("sprite_01", 0, 0, 0),
        ("sprite_02", 0, 0, 0), ("sprite_02", 0, 0, 0),
        ("sprite_03", 0, 0, 0), ("sprite_03", 0, 0, 0),
        ("sprite_04", 0, 0, 0), ("sprite_04", 0, 0, 0),

        # Preparación del brazo suave (4 cuadros)
        ("sprite_09", 0, 0, 0), ("sprite_09", 0, 0, 0),
        ("sprite_10", 0, 0, 0), ("sprite_10", 0, 0, 0),

        # Señalar Sección 1 (8 cuadros)
        ("sprite_11", 0, 0, 1), ("sprite_11", 0, 0, 1),
        ("sprite_12", 0, 0, 1), ("sprite_12", 0, 0, 1),
        ("sprite_11", 0, 0, 1), ("sprite_11", 0, 0, 1),
        ("sprite_12", 0, 0, 1), ("sprite_12", 0, 0, 1),

        # Señalar Sección 2 (8 cuadros)
        ("sprite_11", 0, 1, 1), ("sprite_11", 0, 1, 1),
        ("sprite_12", 0, 1, 1), ("sprite_12", 0, 1, 1),
        ("sprite_11", 0, 1, 1), ("sprite_11", 0, 1, 1),
        ("sprite_12", 0, 1, 1), ("sprite_12", 0, 1, 1),

        # Señalar Sección 3 (8 cuadros)
        ("sprite_11", 0, 2, 1), ("sprite_11", 0, 2, 1),
        ("sprite_12", 0, 2, 1), ("sprite_12", 0, 2, 1),
        ("sprite_11", 0, 2, 1), ("sprite_11", 0, 2, 1),
        ("sprite_12", 0, 2, 1), ("sprite_12", 0, 2, 1),

        # Guardar brazo suavemente (4 cuadros)
        ("sprite_10", 0, 2, 0), ("sprite_10", 0, 2, 0),
        ("sprite_09", 0, 2, 0), ("sprite_09", 0, 2, 0),

        # Emote de cierre fluido (8 cuadros)
        ("sprite_16", 0, 2, 0), ("sprite_16", 0, 2, 0),
        ("sprite_16", 0, 2, 0), ("sprite_16", 0, 2, 0),
        ("sprite_16", 0, 2, 0), ("sprite_16", 0, 2, 0),
        ("sprite_16", 0, 2, 0), ("sprite_16", 0, 2, 0),
    ]

    fallback_key = sorted(sprites.keys())[0]
    timeline = []
    for key, dx, sec, laser in desired_sequence:
        actual_key = key if key in sprites else fallback_key
        timeline.append((actual_key, dx, sec, laser))
    return timeline


def render_svg(theme_name: str, sprites: dict[str, str], sprite_bg: str, ipn_b64: str | None, upiita_b64: str | None) -> str:
    t = THEMES[theme_name]
    timeline = build_timeline(sprites)
    n_steps = len(timeline)
    # 0.12s por frame a 56 cuadros = 6.72s por ciclo (extremadamente fluido)
    cycle_dur = f"{n_steps * 0.12:.2f}s"

    sec_y = {0: 132, 1: 262, 2: 412}
    sec_h = {0: 128, 1: 148, 2: 90}
    sec_mid_y = {0: 190, 1: 335, 2: 455}

    y_vals = ";".join(str(sec_y[step[2]]) for step in timeline)
    h_vals = ";".join(str(sec_h[step[2]]) for step in timeline)
    laser_y2_vals = ";".join(str(sec_mid_y[step[2]]) for step in timeline)
    laser_op_vals = ";".join("0.9" if step[3] else "0" for step in timeline)

    speech_0_op = ";".join("1" if not step[3] else "0" for step in timeline)
    speech_1_op = ";".join("1" if step[3] else "0" for step in timeline)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">Omar Stankewech — 8-Bit Interactive Telemetry Profile</title>',
        '<desc id="desc">Animated pixel-art sprite profile of Omar Stankewech pointing at his engineering stack.</desc>',
        "<defs>",
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
        f'<feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="{t["shadow"]}" flood-opacity=".35"/></filter>',
        '<filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="{t["cyan"]}" flood-opacity="0.75"/></filter>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="1.2" filter="url(#shadow)"/>',
        f'<path d="M13 62H1167" stroke="{t["line"]}"/>',
        '<circle cx="38" cy="38" r="6" fill="#FF5F57"/>'
        '<circle cx="59" cy="38" r="6" fill="#FEBC2E"/>'
        '<circle cx="80" cy="38" r="6" fill="#28C840"/>',
        f'<text x="590" y="43" text-anchor="middle" fill="{t["muted"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
        'letter-spacing=".6">stankewech@upiita-ipn: ~/pixel_engine/telemetry_profile.yml</text>',
        f'<circle cx="1055" cy="38" r="4" fill="{t["accent"]}">'
        '<animate attributeName="opacity" values="1;0.2;1" dur="1.5s" repeatCount="indefinite"/>'
        '</circle>',
        f'<text x="1067" y="42" fill="{t["accent"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700" letter-spacing="1">SPRITE ENGINE</text>',
        
        # Fondo limpio sin rejilla que delate el recuadro del PNG
        f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{sprite_bg}" stroke="{t["line"]}"/>',
        f'<path d="M35 124H453" stroke="{t["line"]}"/>',
        f'<text x="49" y="111" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700" letter-spacing="1.2">◈ PLAYER.01 // STANKEWECH</text>',
        f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">8-BIT / CUSTOM SPRITES</text>',
    ]

    if ipn_b64 and upiita_b64:
        parts.extend([
            f'<image x="48" y="136" width="64" height="64" href="{ipn_b64}" style="image-rendering: pixelated;">'
            '<animateTransform attributeName="transform" type="translate" values="0 0; 0 -4; 0 0" dur="2.4s" repeatCount="indefinite"/>'
            '</image>',
            f'<image x="376" y="136" width="64" height="64" href="{upiita_b64}" style="image-rendering: pixelated;">'
            '<animateTransform attributeName="transform" type="translate" values="0 -4; 0 0; 0 -4" dur="2.4s" repeatCount="indefinite"/>'
            '</image>',
        ])
    else:
        parts.append(fallback_corner_emblems(t))

    for step_idx, (sp_key, dx, _, _) in enumerate(timeline):
        op_list = ["0"] * n_steps
        op_list[step_idx] = "1"
        op_values = ";".join(op_list)
        b64_uri = sprites[sp_key]
        x_pos = 124 + dx
        y_pos = 238
        parts.append(
            f'<image x="{x_pos}" y="{y_pos}" width="240" height="250" href="{b64_uri}" '
            f'style="image-rendering: pixelated;" opacity="{1 if step_idx == 0 else 0}">'
            f'<animate attributeName="opacity" values="{op_values}" dur="{cycle_dur}" '
            'calcMode="discrete" repeatCount="indefinite"/>'
            '</image>'
        )

    parts.extend([
        f'<rect x="132" y="192" width="224" height="32" rx="5" fill="{t["panel2"]}" stroke="{t["cyan"]}" stroke-width="1.5"/>',
        f'<text x="244" y="212" text-anchor="middle" fill="{t["text"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">'
        f'&gt; Hola, soy Omar! 👋'
        f'<animate attributeName="opacity" values="{speech_0_op}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        '</text>',
        f'<text x="244" y="212" text-anchor="middle" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">'
        f'&gt; Mira mi stack &amp; perfil ▸'
        f'<animate attributeName="opacity" values="{speech_1_op}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        '</text>',
        f'<text x="52" y="551" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="10">'
        f'IPN · UPIITA // FLUID MODE (56 FPS) // SYNC: ACTIVE</text>',
    ])

    parts.extend([
        f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>',
        f'<path d="M474 124H1146" stroke="{t["line"]}"/>',
        f'<text x="490" y="111" fill="{t["chrome"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700" letter-spacing=".5">telemetry_profile.yml</text>',
        f'<text x="665" y="111" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[YAML · RO]</text>',
        f'<rect x="984" y="94" width="146" height="24" rx="12" fill="{t["cyan"]}" opacity=".12" stroke="{t["cyan"]}"/>',
        f'<text x="1057" y="111" text-anchor="middle" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700">@Stankewech</text>',
        f'<rect x="482" y="132" width="654" height="128" rx="4" fill="{t["cyan"]}" opacity="0.08" stroke="{t["cyan"]}" stroke-width="1.2" stroke-dasharray="4 4">'
        f'<animate attributeName="y" values="{y_vals}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        f'<animate attributeName="height" values="{h_vals}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        '</rect>',
        f'<line x1="335" y1="362" x2="482" y2="190" stroke="{t["cyan"]}" stroke-width="2.2" stroke-dasharray="5 4" filter="url(#neonGlow)">'
        f'<animate attributeName="y2" values="{laser_y2_vals}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="{laser_op_vals}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        '</line>',
    ])

    row_y = 148.0
    for idx, (indent, key, value) in enumerate(YAML_ROWS, 1):
        line_num = f"{idx:2d}"
        if indent == 0:
            content = f'<tspan fill="{t["chrome"]}" font-weight="700">▸ {html.escape(key)}:</tspan>'
            text_x = 522.0
        else:
            content = (
                f'<tspan fill="{t["cyan"]}">{html.escape(key)}: </tspan>'
                f'<tspan fill="{t["text"]}">{html.escape(value)}</tspan>'
            )
            text_x = 542.0

        parts.extend([
            f'<text x="506" y="{row_y:.1f}" text-anchor="end" fill="{t["muted"]}" opacity=".45" '
            f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13">{line_num}</text>',
            f'<text x="{text_x:.1f}" y="{row_y:.1f}" '
            f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13">{content}</text>',
        ])
        row_y += 21.5

    parts.extend([
        f'<path d="M474 526H1146" stroke="{t["line"]}"/>',
        f'<rect x="475" y="527" width="670" height="32" fill="{t["panel"]}" rx="0 0 5 5"/>',
        f'<rect x="485" y="533" width="96" height="20" rx="3" fill="{t["cyan"]}"/>',
        f'<text x="533" y="547" text-anchor="middle" fill="{t["bg"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">TELEMATICS</text>',
        f'<rect x="588" y="533" width="70" height="20" rx="3" fill="{t["chrome"]}" opacity=".2"/>',
        f'<text x="623" y="547" text-anchor="middle" fill="{t["chrome"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">⎇ main</text>',
        f'<text x="672" y="547" fill="{t["text"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" font-weight="600">UPIITA-IPN</text>',
        f'<text x="770" y="547" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[custom-sprites · 8-bit · ml]</text>',
        f'<text x="1134" y="547" text-anchor="end" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">100% ☰ 17:42</text>',
        "</svg>",
    ])
    return "".join(parts)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)

    sprites, global_bg = load_sprites()
    ipn_b64 = load_pixel_badge("ipn")
    upiita_b64 = load_pixel_badge("upiita")

    for theme in THEMES:
        svg = render_svg(theme, sprites, global_bg, ipn_b64, upiita_b64)
        output = ASSETS / f"banner-{theme}.v9.svg"
        output.write_text(svg, encoding="utf-8")
        print(f"Generado: {output.relative_to(ROOT)} (Fondo UI adaptado a {global_bg} - Grid eliminado)")


if __name__ == "__main__":
    main()