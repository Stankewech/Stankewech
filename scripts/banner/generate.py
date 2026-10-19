#!/usr/bin/env python3
"""Generate an 8-bit Pixel Art Interactive Banner for Omar Stankewech.

Run from the repository root:
    python scripts/banner/generate.py
"""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

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
        "stage_bg": "#EEF2F6",
        "line":     "#CBD5E1",
        "muted":    "#64748B",
        "text":     "#0F172A",
        "cyan":     "#0D9488",
        "chrome":   "#4F46E5",
        "accent":   "#059669",
        "shadow":   "#94A3B8",
    },
}

# Paleta de colores 8-bit (inspirada en las 3 fotos de Omar + IPN + UPIITA)
PIXEL_PALETTE = {
    "K": "#0B0C12",  # Contorno oscuro / cabello sombra profunda
    "H": "#151821",  # Cabello negro base
    "h": "#282E3D",  # Luces del cabello ondulado
    "S": "#F1C29B",  # Piel clara cálida base
    "s": "#DFAA82",  # Sombra de piel / pómulos
    "b": "#C89572",  # Sombra sutil de barba / bigote
    "M": "#C86D68",  # Labios
    "G": "#E2E8F0",  # Armazón metálico delgado (lentes geométricos)
    "g": "#94A3B8",  # Sombra del armazón de lentes
    "L": "#E879F9",  # Reflejo antirreflejante violeta/rosa en lentes
    "C": "#38BDF8",  # Brillo secundario cian en lentes
    "W": "#FFFFFF",  # Blanco puro
    "T": "#12151E",  # Playera negra cuello alto (turtleneck)
    "F": "#262936",  # Cuello interior polar gris oscuro / capucha
    "z": "#94A3B8",  # Detalle de cierres / broches laterales
    "J": "#EFECE6",  # Chamarra crema / hueso claro
    "j": "#D5CFC4",  # Sombra y pliegues de chamarra crema
    "P": "#1E293B",  # Pantalón oscuro
    "p": "#0F172A",  # Sombra pantalón
    "N": "#00F5D4",  # Acento neón / suela / energía
    # Colores Institucionales IPN y UPIITA
    "I": "#6C1D45",  # Guinda IPN
    "i": "#9B2C63",  # Guinda IPN luz
    "U": "#F59E0B",  # Dorado UPIITA
    "u": "#FDE047",  # Amarillo luz UPIITA
    "B": "#1E3A8A",  # Azul profundo UPIITA
}


# --------------------------------------------------------------------------- #
# Logos 8-Bit: IPN (Esquina Izquierda) y UPIITA (Esquina Derecha)
# --------------------------------------------------------------------------- #

IPN_GRID = [
    "......KKKKKK......",
    "....KKIIIIIIKK....",
    "...KIIWWWWWWIIK...",
    "..KIWWKIIIIKWWIK..",
    "..KIWKIWWWWIKWIK..",
    ".KIWKIWKKKKWIKWIK.",
    ".KIWKIWKIIKWIKWIK.",
    ".KIWKIWKKKKWIKWIK.",
    ".KIWKIWWWWWWIKWIK.",
    "..KIWWKIIIIKWWIK..",
    "..KIIWWWWWWWWIIK..",
    "...KIIIIIIIIIIK...",
    "....KKIIIIIIKK....",
    "......KKKKKK......",
    "..................",
    "...WWWW.WWWW.W..W.",
    "....WW..W..W.WW.W.",
    "....WW..WWWW.W.WW.",
    "...WWWW.W....W..W.",
    "..................",
]

UPIITA_GRID = [
    "......KKKKKK......",
    "....KKUUUUUUKK....",
    "...KUUuBBBBuUUK...",
    "..KUUuBKKKKBuUUK..",
    ".KUUuBKuUUuKBuUUK.",
    ".KUUuBKU..UKBuUUK.",
    ".KUUuBKU..UKBuUUK.",
    ".KUUuBKU..UKBuUUK.",
    ".KUUuBKuUUuKBuUUK.",
    "..KUUuBKKKKBuUUK..",
    "...KUUuBBBBuUUK...",
    "....KKUUUUUUKK....",
    "......KKKKKK......",
    "..................",
    ".U.U.UUU.I.I.UUU.UUU",
    ".U.U.U.U.I.I..U..U.U",
    ".U.U.UUU.I.I..U..UUU",
    ".UUU.U...I.I..U..U.U",
    "..................",
]


# --------------------------------------------------------------------------- #
# Constructor de Sprites 8-Bit de Omar (Basado en las 3 fotos de referencia)
# --------------------------------------------------------------------------- #

def build_omar_frame(
    arm_pose: str = "mid",
    blink: bool = False,
    glint_shift: bool = False,
    step: int = 0,
) -> list[str]:
    """
    Genera una matriz de 34x38 píxeles de Omar en 8-bits:
    - Cabello negro ondulado con partido en medio y mechón curvo sobre el lente derecho.
    - Lentes geométricos metálicos con reflejo violeta/cian.
    - Chamarra crema/hueso abierta, cuello interior gris oscuro y cuello alto negro.
    - Brazo izquierdo señalando hacia la derecha (up, mid, down).
    """
    L1 = "C" if glint_shift else "L"
    E_ROW = (
        "....KGGGGssGGGGK.................."
        if blink
        else f"....KG{L1}KWGssGWK{L1}GK................."
    )[:34]

    # Cabeza, cabello ondulado con mechón y lentes hexagonales
    head = [
        ".......KKKKKK..KKKKKK.............",
        ".....KKHHHHHHKKHHHHHHKK...........",
        "....KHHhHHHHHHHHHHHHhHHK..........",
        "...KHHhHHHHHHHHHHHHHHhHHK.........",
        "..KHHHHHHHHKKKKHHHHHHHHHHK........",
        "..KHHHHHHKKSSSSKKHHHHHHHHK........",
        "..KHHHHKKSSSSSSSSKKHHHHHHK........",
        "..KHHHKSSSSSssSSSSSKHHHHHK........",
        "...KHHKSSSSSssHKSSSSKHHHK.........",
        "...KHKGGGGGGssHKGGGGGKHHK.........",
        "...KHGWLLLLGssHKGLLWGHK...........",
        E_ROW,
        "...KsGWWWWWGSSGWWWWWGssK..........",
        "...KssGGGGGGSSGGGGGGsssK..........",
        "....KsssssssSSssssssssK...........",
        ".....KssssbbbbbbsssssK............",
        ".....KssssbMMMMbsssssK............",
        "......KKssssbbsssssKK.............",
        "........KKKSSSSSKKK...............",
    ]

    # Torso: Cuello alto negro (T), cuello polar oscuro (F) con broches (z) y chamarra crema (J)
    if arm_pose == "up":
        torso = [
            ".......KKFFFFFFFFKK.......NN......",
            ".....KKFFTTTTTTTTFFKK....NNNN.....",
            "....KFFzFTTTTTTTTFzFFK..NNSSN.....",
            "...KJJFFTTTTTTTTTTFFJJKSSSSSK.....",
            "..KJJJFFTTTTTTTTTTFFJJJKKKKK......",
            "..KJJjFFTTTTTTTTTTFFjJJK..........",
            "..KJJjFFTTTTTTTTTTFFjJJK..........",
            "..KJJjFFTTTTTTTTTTFFjJJK..........",
            "..KJJJJJTTTTTTTTTTJJJJJK..........",
            "...KSSSSKTTTTTTTTKSSSSK...........",
        ]
    elif arm_pose == "mid":
        torso = [
            ".......KKFFFFFFFFKK...............",
            ".....KKFFTTTTTTTTFFKK.............",
            "....KFFzFTTTTTTTTFzFFK............",
            "...KJJFFTTTTTTTTTTFFJJK...........",
            "..KJJJFFTTTTTTTTTTFFJJJKKKK.......",
            "..KJJjFFTTTTTTTTTTFFjJJJJSSK..NNN.",
            "..KJJjFFTTTTTTTTTTFFjJJJSSSSKNNNNN",
            "..KJJjFFTTTTTTTTTTFFjJJKSSSSK.NNN.",
            "..KJJJJJTTTTTTTTTTJJJJJKKKKK......",
            "...KSSSSKTTTTTTTTK.................",
        ]
    else:  # down
        torso = [
            ".......KKFFFFFFFFKK...............",
            ".....KKFFTTTTTTTTFFKK.............",
            "....KFFzFTTTTTTTTFzFFK............",
            "...KJJFFTTTTTTTTTTFFJJK...........",
            "..KJJJFFTTTTTTTTTTFFJJJK..........",
            "..KJJjFFTTTTTTTTTTFFjJJJK.........",
            "..KJJjFFTTTTTTTTTTFFjJJJJKK.......",
            "..KJJjFFTTTTTTTTTTFFjJJJJSSK..NNN.",
            "..KJJJJJTTTTTTTTTTJJJJJKSSSSKNNNNN",
            "...KSSSSKTTTTTTTTK......KKKK..NNN.",
        ]

    # Piernas y tenis retro con detalle cian
    if step == 0:
        legs = [
            "....KPPPPPPPPPPPPPPPPK............",
            "....KPPPPPPpKKpPPPPPPK............",
            "....KPPPPPPp..pPPPPPPK............",
            "....KPPPPPPp..pPPPPPPK............",
            "....KPPPPPPp..pPPPPPPK............",
            "....KJJJJJJp..pJJJJJJK............",
            "...KNNNNNNNK..KNNNNNNNK...........",
            "...KKKKKKKKK..KKKKKKKKK...........",
        ]
    else:
        legs = [
            "....KPPPPPPPPPPPPPPPPK............",
            "....KPPPPPPpKKpPPPPPPK............",
            "....KPPPPPPp..pPPPPPPK............",
            "....KPPPPPPp...KPPPPPPK...........",
            "....KPPPPPPp...KJJJJJJK...........",
            "....KJJJJJJp..KNNNNNNNK...........",
            "...KNNNNNNNK..KKKKKKKKK...........",
            "...KKKKKKKKK......................",
        ]

    grid = head + torso + legs
    return [row.ljust(34, ".")[:34] for row in grid]


def grid_to_svg_rects(grid: list[str], x0: int, y0: int, scale: int) -> str:
    """Convierte una cuadrícula de texto en rectángulos SVG optimizados por fila."""
    rects: list[str] = []
    for r_idx, row in enumerate(grid):
        y = y0 + r_idx * scale
        c_idx = 0
        n = len(row)
        while c_idx < n:
            ch = row[c_idx]
            if ch == "." or ch not in PIXEL_PALETTE:
                c_idx += 1
                continue
            run = 1
            while c_idx + run < n and row[c_idx + run] == ch:
                run += 1
            x = x0 + c_idx * scale
            w = run * scale
            color = PIXEL_PALETTE[ch]
            rects.append(f'<rect x="{x}" y="{y}" width="{w}" height="{scale}" fill="{color}"/>')
            c_idx += run
    return "".join(rects)


def render_svg(theme_name: str) -> str:
    t = THEMES[theme_name]

    # Secuencia de 6 fotogramas para lograr una animación súper fluida
    # (Coordina ángulo de brazo, parpadeo, rebote de ropa/cabello y destello en lentes)
    frame_configs = [
        {"pose": "up",   "blink": False, "glint": False, "step": 0, "dy": 0},
        {"pose": "up",   "blink": False, "glint": True,  "step": 1, "dy": 3},
        {"pose": "mid",  "blink": False, "glint": False, "step": 0, "dy": 0},
        {"pose": "mid",  "blink": True,  "glint": True,  "step": 0, "dy": 3},
        {"pose": "down", "blink": False, "glint": False, "step": 0, "dy": 0},
        {"pose": "down", "blink": False, "glint": True,  "step": 1, "dy": 3},
    ]

    total_frames = len(frame_configs)
    cycle_dur = "4.8s"

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">Omar Stankewech — 8-Bit Interactive Profile</title>',
        '<desc id="desc">8-Bit animated avatar of Omar Stankewech with IPN and UPIITA emblems pointing at his telemetry profile.</desc>',
        "<defs>",
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">'
        f'<feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="{t["shadow"]}" flood-opacity=".35"/></filter>',
        '<filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="{t["cyan"]}" flood-opacity="0.65"/></filter>',
        "</defs>",
        # Ventana Principal
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="1.2" filter="url(#shadow)"/>',
        f'<path d="M13 62H1167" stroke="{t["line"]}"/>',
        # Botones estilo macOS / Terminal
        '<circle cx="38" cy="38" r="6" fill="#FF5F57"/>'
        '<circle cx="59" cy="38" r="6" fill="#FEBC2E"/>'
        '<circle cx="80" cy="38" r="6" fill="#28C840"/>',
        f'<text x="590" y="43" text-anchor="middle" fill="{t["muted"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" '
        'letter-spacing=".6">stankewech@upiita-ipn: ~/pixel_engine/telemetry_profile.yml</text>',
        # Indicador superior derecho
        f'<circle cx="1055" cy="38" r="4" fill="{t["accent"]}">'
        '<animate attributeName="opacity" values="1;0.2;1" dur="1.5s" repeatCount="indefinite"/>'
        '</circle>',
        f'<text x="1067" y="42" fill="{t["accent"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700" letter-spacing="1">8-BIT ENGINE</text>',
        # Marco Izquierdo: Escenario 8-Bit
        f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{t["stage_bg"]}" stroke="{t["line"]}"/>',
        f'<path d="M35 124H453" stroke="{t["line"]}"/>',
        f'<text x="49" y="111" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700" letter-spacing="1.2">◈ SPRITE.STAGE // OMAR_8BIT</text>',
        f'<text x="438" y="111" text-anchor="end" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">60FPS / PIXEL-CRISP</text>',
    ]

    # Cuadrícula retro de fondo y plataforma en el escenario izquierdo
    parts.extend([
        f'<g opacity="0.18" stroke="{t["cyan"]}" stroke-width="1">',
        '<path d="M35 460H453 M35 485H453 M35 515H453"/>',
        '<path d="M120 460L60 535 M200 460L170 535 M280 460L310 535 M360 460L420 535"/>',
        '</g>',
        # Sombra elíptica pixelada bajo los pies de Omar
        '<rect x="155" y="476" width="128" height="10" rx="5" fill="#020617" opacity="0.65"/>',
    ])

    # Grupo con renderizado Pixel-Perfect (crispEdges)
    parts.append('<g shape-rendering="crispEdges">')

    # 1. LOGO 8-BIT IPN (Esquina Superior Izquierda del escenario)
    parts.append('<g>')
    parts.append(
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 0; 0 -4; 0 0" dur="2.4s" repeatCount="indefinite"/>'
    )
    parts.append(grid_to_svg_rects(IPN_GRID, x0=52, y0=138, scale=3))
    parts.append('</g>')

    # 2. LOGO 8-BIT UPIITA (Esquina Superior Derecha del escenario)
    parts.append('<g>')
    parts.append(
        '<animateTransform attributeName="transform" type="translate" '
        'values="0 -4; 0 0; 0 -4" dur="2.4s" repeatCount="indefinite"/>'
    )
    parts.append(grid_to_svg_rects(UPIITA_GRID, x0=378, y0=138, scale=3))
    parts.append('</g>')

    # 3. SPRITE ANIMADO DE OMAR (6 cuadros discretos en bucle)
    for idx, cfg in enumerate(frame_configs):
        vals = ["0"] * total_frames
        vals[idx] = "1"
        values_str = ";".join(vals)
        grid = build_omar_frame(
            arm_pose=cfg["pose"],
            blink=cfg["blink"],
            glint_shift=cfg["glint"],
            step=cfg["step"],
        )
        parts.append(f'<g opacity="{1 if idx == 0 else 0}">')
        parts.append(
            f'<animate attributeName="opacity" values="{values_str}" '
            f'dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        )
        parts.append(grid_to_svg_rects(grid, x0=126, y0=210 + cfg["dy"], scale=7))
        parts.append('</g>')

    parts.append('</g>')  # Fin de crispEdges

    # Globo de diálogo Pixel-Art sobre Omar
    parts.extend([
        f'<rect x="135" y="152" width="215" height="34" rx="4" fill="{t["panel2"]}" stroke="{t["cyan"]}" stroke-width="1.5"/>',
        f'<text x="242" y="173" text-anchor="middle" fill="{t["text"]}" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">'
        '&gt; check my telemetry! ▸</text>',
        # Pie del escenario izquierdo
        f'<text x="52" y="551" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="10">'
        'IPN · UPIITA // SPRITE: 34x37 PX · SYNC: ACTIVE</text>',
    ])

    # ----------------------------------------------------------------------- #
    # Marco Derecho: telemetry_profile.yml + Resaltador Sincronizado
    # ----------------------------------------------------------------------- #
    parts.extend([
        f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{t["panel2"]}" stroke="{t["line"]}"/>',
        f'<path d="M474 124H1146" stroke="{t["line"]}"/>',
        f'<text x="490" y="111" fill="{t["chrome"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700" letter-spacing=".5">telemetry_profile.yml</text>',
        f'<text x="665" y="111" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[YAML · RO]</text>',
        f'<rect x="984" y="94" width="146" height="24" rx="12" fill="{t["cyan"]}" opacity=".12" stroke="{t["cyan"]}"/>',
        f'<text x="1057" y="111" text-anchor="middle" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" font-weight="700">@Stankewech</text>',
    ])

    # Caja resaltadora que baja por las 3 secciones al mismo ritmo que la mano de Omar
    parts.extend([
        f'<rect x="482" y="132" width="654" height="128" rx="4" fill="{t["cyan"]}" opacity="0.07" stroke="{t["cyan"]}" stroke-width="1" stroke-dasharray="4 4">'
        f'<animate attributeName="y" values="132;132;262;262;412;412" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        f'<animate attributeName="height" values="128;128;148;148;90;90" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        '</rect>',
        # Haz láser punteado que conecta la mano de Omar con la sección activa del YAML
        f'<line x1="358" y1="360" x2="482" y2="185" stroke="{t["cyan"]}" stroke-width="2" stroke-dasharray="4 4" filter="url(#neonGlow)">'
        f'<animate attributeName="y1" values="352;355;388;391;402;405" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
        f'<animate attributeName="y2" values="185;185;330;330;455;455" dur="{cycle_dur}" calcMode="discrete" repeatCount="indefinite"/>'
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

    # Barra de estado inferior estilo Neovim
    parts.extend([
        f'<path d="M474 526H1146" stroke="{t["line"]}"/>',
        f'<rect x="475" y="527" width="670" height="32" fill="{t["panel"]}" rx="0 0 5 5"/>',
        f'<rect x="485" y="533" width="96" height="20" rx="3" fill="{t["cyan"]}"/>',
        f'<text x="533" y="547" text-anchor="middle" fill="{t["bg"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">TELEMATICS</text>',
        f'<rect x="588" y="533" width="70" height="20" rx="3" fill="{t["chrome"]}" opacity=".2"/>',
        f'<text x="623" y="547" text-anchor="middle" fill="{t["chrome"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">⎇ main</text>',
        f'<text x="672" y="547" fill="{t["text"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" font-weight="600">UPIITA-IPN</text>',
        f'<text x="770" y="547" fill="{t["muted"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11">[8-bit · interactive · ml]</text>',
        f'<text x="1134" y="547" text-anchor="end" fill="{t["cyan"]}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="11" font-weight="700">100% ☰ 17:42</text>',
        "</svg>",
    ])
    return "".join(parts)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        svg = render_svg(theme)
        output = ASSETS / f"banner-{theme}.v9.svg"
        output.write_text(svg, encoding="utf-8")
        print(f"Generado: {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()