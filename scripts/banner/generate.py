#!/usr/bin/env python3
"""Generate an animated 8-bit SVG banner using custom PNG sprites (sprite_01..sprite_16).

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
SPRITES_DIR = ASSETS / "sprites" / "sprites_extraidos"

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
        "stage_bg": "#080D1A",
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
        "stage_bg": "#E2E8F0",
        "line":     "#CBD5E1",
        "muted":    "#64748B",
        "text":     "#0F172A",
        "cyan":     "#0D9488",
        "chrome":   "#4F46E5",
        "accent":   "#059669",
        "shadow":   "#94A3B8",
    },
}


# --------------------------------------------------------------------------- #
# Procesamiento de Sprites PNG (Limpieza de fondo + Escalado Pixel-Perfect)
# --------------------------------------------------------------------------- #

def edge_connected(mask: np.ndarray) -> np.ndarray:
    """Devuelve True para los píxeles de fondo conectados a los bordes."""
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


def clean_and_crop_sprite(path: Path, target_height: int = 230) -> str:
    """
    Carga un sprite PNG, elimina automáticamente el color de fondo sólido de
    las esquinas (respetando el blanco interior de la chamarra), alinea los pies
    en un lienzo uniforme y devuelve el Data URI Base64 con Nearest-Neighbor.
    """
    img = Image.open(path).convert("RGBA")
    arr = np.asarray(img).copy()
    alpha = arr[:, :, 3]

    # Si el PNG tiene fondo sólido (opaco en las esquinas), lo quitamos por flood-fill
    corners = [arr[0, 0], arr[0, -1], arr[-1, 0], arr[-1, -1]]
    opaque_corners = [c[:3] for c in corners if c[3] > 200]
    if opaque_corners:
        bg_rgb = np.median(opaque_corners, axis=0)
        diff = np.linalg.norm(arr[:, :, :3].astype(float) - bg_rgb, axis=2)
        bg_mask = edge_connected((diff < 32.0) | (alpha < 20))
        arr[bg_mask, 3] = 0

    cleaned = Image.fromarray(arr, "RGBA")
    bbox = cleaned.getchannel("A").getbbox()
    if bbox:
        cleaned = cleaned.crop(bbox)

    # Escalar conservando bordes duros 8-bit (NEAREST)
    scale = target_height / max(1, cleaned.height)
    new_w = max(1, int(round(cleaned.width * scale)))
    new_h = max(1, int(round(cleaned.height * scale)))
    resized = cleaned.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Lienzo fijo de 240x250 con los pies alineados exactamente en la base (y=244)
    canvas_w, canvas_h = 240, 250
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    offset_x = (canvas_w - new_w) // 2
    offset_y = canvas_h - new_h - 6
    canvas.alpha_composite(resized, (max(0, offset_x), max(0, offset_y)))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def load_pixel_badge(name: str) -> str | None:
    """Si existe ipn.png o upiita.png en assets/sprites/, lo pixeliza a 8-bits."""
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
                # Reducir a resolución 8-bit (32x32) y re-escalar con NEAREST a 64x64
                small = cleaned.resize((32, 32), Image.Resampling.BILINEAR)
                pixelated = small.resize((64, 64), Image.Resampling.NEAREST)
                buf = io.BytesIO()
                pixelated.save(buf, format="PNG", optimize=True)
                return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
    return None


def fallback_corner_emblems(t: dict[str, str]) -> str:
    """Escudos 8-bit integrados para IPN (izquierda) y UPIITA (derecha) si no hay PNG."""
    return (
        # Esquina Izquierda: Badge 8-Bit IPN (Guinda y Blanco)
        '<g shape-rendering="crispEdges">'
        '<animateTransform attributeName="transform" type="translate" values="0 0; 0 -3; 0 0" dur="2.4s" repeatCount="indefinite"/>'
        '<rect x="48" y="136" width="64" height="64" fill="#090F1E" stroke="#6C1D45" stroke-width="3"/>'
        '<rect x="54" y="142" width="52" height="36" fill="#6C1D45"/>'
        '<rect x="62" y="146" width="36" height="28" fill="#FFFFFF"/>'
        '<rect x="68" y="150" width="24" height="20" fill="#6C1D45"/>'
        '<rect x="76" y="154" width="8" height="12" fill="#FFFFFF"/>'
        '<text x="80" y="193" text-anchor="middle" fill="#FFFFFF" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" font-weight="700" letter-spacing="2">IPN</text>'
        '</g>'
        # Esquina Derecha: Badge 8-Bit UPIITA (Dorado, Azul y Negro)
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


def load_sprites() -> dict[str, str]:
    """Busca sprite_01..sprite_16 en assets/sprites/ (o en la raíz/assets)."""
    loaded: dict[str, str] = {}
    search_dirs = [SPRITES_DIR, ASSETS, ROOT]
    for folder in search_dirs:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("sprite_*.*")):
            if path.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}:
                key = path.stem.lower()
                if key not in loaded:
                    loaded[key] = clean_and_crop_sprite(path)
    if not loaded:
        raise SystemExit(
            f"No se encontraron archivos 'sprite_XX.png' en {SPRITES_DIR.relative_to(ROOT)}.\n"
            "Crea la carpeta 'assets/sprites/' y coloca ahí tus imágenes sprite_01.png a sprite_16.png."
        )
    return loaded


def build_timeline(sprites: dict[str, str]) -> list[tuple[str, int, int, int]]:
    """
    Construye la secuencia de cuadros:
    Retorna tuplas (sprite_key, dx_offset, highlight_section, laser_active)
      - highlight_section: 0 = telemetry_node, 1 = core_stack, 2 = network_uplink
      - laser_active: 1 cuando está señalando con el brazo extendido (sprite_11 / sprite_12)
    """
    # Secuencia ideal de 20 pasos (0.35s cada paso = 7.0s por ciclo completo)
    desired_sequence = [
        # Entrada caminando desde la izquierda (sprite_05 y sprite_06)
        ("sprite_05", -45, 0, 0),
        ("sprite_06", -22, 0, 0),
        # Idle respirando de frente (sprite_01 a sprite_04) y paso frontal (07, 08)
        ("sprite_01",   0, 0, 0),
        ("sprite_02",   0, 0, 0),
        ("sprite_03",   0, 0, 0),
        ("sprite_04",   0, 0, 0),
        ("sprite_07",   0, 0, 0),
        ("sprite_08",   0, 0, 0),
        # Preparación para señalar (sprite_09 y sprite_10)
        ("sprite_09",   4, 0, 0),
        ("sprite_10",   6, 0, 0),
        # Señalando Sección 1: telemetry_node (sprite_11 y sprite_12)
        ("sprite_11",  10, 0, 1),
        ("sprite_12",  10, 0, 1),
        # Señalando Sección 2: core_stack (sprite_11 y sprite_12)
        ("sprite_11",  10, 1, 1),
        ("sprite_12",  10, 1, 1),
        ("sprite_11",  10, 1, 1),
        # Señalando Sección 3: network_uplink (sprite_12 y sprite_11)
        ("sprite_12",  10, 2, 1),
        ("sprite_11",  10, 2, 1),
        # Emote final (sprite_16) y regreso suave a Idle
        ("sprite_16",   0, 2, 0),
        ("sprite_16",   0, 2, 0),
        ("sprite_01",   0, 0, 0),
    ]

    fallback_key = sorted(sprites.keys())[0]
    timeline = []
    for key, dx, sec, laser in desired_sequence:
        actual_key = key if key in sprites else fallback_key
        timeline.append((actual_key, dx, sec, laser))
    return timeline


def render_svg(theme_name: str, sprites: dict[str, str], ipn_b64: str | None, upiita_b64: str | None) -> str:
    t = THEMES[theme_name]
    timeline = build_timeline(sprites)
    n_steps = len(timeline)
    cycle_dur = f"{n_steps * 0.36:.2f}s"

    # Coordenadas de las 3 secciones del YAML para el resaltador
    sec_y = {0: 132, 1: 262, 2: 412}
    sec_h = {0: 128, 1: 148, 2: 90}
    sec_mid_y = {0: 190, 1: 335, 2: 455}

    y_vals = ";".join(str(sec_y[step[2]]) for step in timeline)
    h_vals = ";".join(str(sec_h[step[2]]) for step in timeline)
    laser_y2_vals = ";".join(str(sec_mid_y[step[2]]) for step in timeline)
    laser_op_vals = ";".join("0.9" if step[3] else "0" for step in timeline)

    # Textos dinámicos del globo de diálogo según lo que hace el personaje
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
        # Ventana Principal
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="1.2" filter="url(#shadow)"/>',
        f'<path d="M13 62H1167" stroke="{t["line"]}"/>',
        # Botones de ventana
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
        # Escenario Izquierdo
        f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["stage_bg"]}" stroke="{t["line"]}"/>',
        f'<path d="M35 124H453" stroke="{t["line"]}"/>',
        f'<text x="49" y="111" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700" letter-spacing="1.2">◈ PLAYER.01 // STANKEWECH</text>',
        f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">8-BIT / CUSTOM SPRITES</text>',
        # Piso con rejilla cyber-retro
        f'<g opacity="0.22" stroke="{t["cyan"]}" stroke-width="1">',
        '<path d="M35 465H453 M35 490H453 M35 518H453"/>',
        '<path d="M120 465L60 535 M200 465L165 535 M288 465L320 535 M368 465L428 535"/>',
        '</g>',
        # Plataforma holográfica bajo los pies de Omar
        f'<ellipse cx="244" cy="482" rx="68" ry="11" fill="{t["cyan"]}" opacity="0.16"/>',
        f'<ellipse cx="244" cy="482" rx="52" ry="7" fill="none" stroke="{t["cyan"]}" stroke-width="1.5" stroke-dasharray="6 4" opacity="0.65"/>',
    ]

    # Logos 8-Bit IPN y UPIITA en las esquinas superiores
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

    # Renderizar cada paso de la secuencia de sprites de Omar
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

    # Globo de diálogo retro encima del sprite
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
        f'IPN · UPIITA // SPRITES LOADED: {len(sprites):02d} · LOOP: {cycle_dur}</text>',
    ])

    # ----------------------------------------------------------------------- #
    # Panel Derecho: telemetry_profile.yml + Sincronización con sprite_11/12
    # ----------------------------------------------------------------------- #
    parts.extend([
        f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>',
        f'<path d="M474 124H1146" stroke="{t["line"]}"/>',
        f'<text x="490" y="111" fill="{t["chrome"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700" letter-spacing=".5">telemetry_profile.yml</text>',
        f'<text x="665" y="111" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[YAML · RO]</text>',
        f'<rect x="984" y="94" width="146" height="24" rx="12" fill="{t["cyan"]}" opacity=".12" stroke="{t["cyan"]}"/>',
        f'<text x="1057" y="111" text-anchor="middle" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700">@Stankewech</text>',
        # Resaltador dinámico de sección YAML
        f'<rect x="482" y="132" width="654" height="128" rx="4" fill="{t["cyan"]}" opacity="0.08" stroke="{t["cyan"]}" stroke-width="1.2" stroke-dasharray="4 4">'
        f'<animate attributeName="y" values="{y_vals}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        f'<animate attributeName="height" values="{h_vals}" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        '</rect>',
        # Haz puntero que sale exactamente de la mano en sprite_11 y sprite_12
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

    # Barra de estado inferior Neovim
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

    sprites = load_sprites()
    ipn_b64 = load_pixel_badge("ipn")
    upiita_b64 = load_pixel_badge("upiita")

    for theme in THEMES:
        svg = render_svg(theme, sprites, ipn_b64, upiita_b64)
        output = ASSETS / f"banner-{theme}.v9.svg"
        output.write_text(svg, encoding="utf-8")
        print(
            f"Generado: {output.relative_to(ROOT)} "
            f"({output.stat().st_size / 1024:.1f} KiB, {len(sprites)} sprites integrados)"
        )


if __name__ == "__main__":
    main()