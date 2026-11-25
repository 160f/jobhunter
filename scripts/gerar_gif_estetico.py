import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 880
HEIGHT = 520

# Modern, refined typography
FONT_BRAND = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
FONT_HERO = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 26)
FONT_SUB = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
FONT_PILL = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 12)
FONT_TAG = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 12)

# Aesthetic light palette (Apple / Linear style)
BG_COLOR = (250, 250, 252)        # Ultra soft white-slate
WHITE = (255, 255, 255)
SHADOW_SOFT = (235, 238, 243)     # Subtle ground shadow
LINE_SUBTLE = (238, 242, 246)     # Very light dividers

TEXT_DARK = (15, 23, 42)          # Slate-900
TEXT_MUTED = (100, 116, 139)      # Slate-500
TEXT_LIGHT = (148, 163, 184)      # Slate-400

# Refined accents
ACCENT_BLUE = (2, 132, 199)       # Sky blue
BLUE_TINT = (240, 249, 255)
BLUE_BORDER = (186, 230, 253)

ACCENT_GREEN = (16, 185, 129)     # Emerald
GREEN_TEXT = ACCENT_GREEN
GREEN_TINT = (236, 253, 245)
GREEN_BORDER = (167, 243, 208)

ACCENT_AMBER = (217, 119, 6)      # Amber / Warm light
AMBER_TINT = (254, 252, 232)
AMBER_BORDER = (254, 240, 138)

ACCENT_ROSE = (225, 29, 72)       # Rose / Red
ROSE_TINT = (255, 241, 242)
ROSE_BORDER = (254, 205, 211)

ROBOT_LINE = (71, 85, 105)        # Soft slate line
ROBOT_FILL = (255, 255, 255)
VISOR_FILL = (15, 23, 42)


def draw_minimalist_robot(draw, x, y, action="search"):
    """
    Draws a clean, aesthetic minimalist robot centered at (x, y).
    y is the ground contact level (bottom of feet).
    """
    # 1. Soft ground shadow
    draw.ellipse((x - 42, y - 6, x + 42, y + 8), fill=SHADOW_SOFT)
    
    # Coordinates
    body_w, body_h = 62, 58
    body_x = x - body_w // 2
    body_y = y - 76
    
    head_w, head_h = 68, 50
    head_x = x - head_w // 2
    head_y = body_y - head_h - 4
    
    # 2. Antenna
    draw.line([(x, head_y), (x, head_y - 14)], fill=ROBOT_LINE, width=2)
    orb_color = ACCENT_GREEN if action == "celebrate" else ACCENT_BLUE
    draw.ellipse((x - 6, head_y - 24, x + 6, head_y - 12), fill=orb_color, outline=ROBOT_LINE, width=2)
    
    # 3. Head
    draw.rounded_rectangle((head_x, head_y, head_x + head_w, head_y + head_h), radius=14, fill=WHITE, outline=ROBOT_LINE, width=2)
    
    # Ears
    draw.rounded_rectangle((head_x - 4, head_y + 16, head_x, head_y + 32), radius=2, fill=LINE_SUBTLE, outline=ROBOT_LINE, width=1)
    draw.rounded_rectangle((head_x + head_w, head_y + 16, head_x + head_w + 4, head_y + 32), radius=2, fill=LINE_SUBTLE, outline=ROBOT_LINE, width=1)
    
    # Visor screen
    screen_w, screen_h = 50, 30
    screen_x = x - screen_w // 2
    screen_y = head_y + 10
    draw.rounded_rectangle((screen_x, screen_y, screen_x + screen_w, screen_y + screen_h), radius=8, fill=VISOR_FILL)
    
    # Eyes
    if action == "celebrate":
        # Happy eyes: ^ ^
        draw.line([(x - 16, screen_y + 18), (x - 10, screen_y + 12)], fill=ACCENT_GREEN, width=3)
        draw.line([(x - 10, screen_y + 12), (x - 4, screen_y + 18)], fill=ACCENT_GREEN, width=3)
        draw.line([(x + 4, screen_y + 18), (x + 10, screen_y + 12)], fill=ACCENT_GREEN, width=3)
        draw.line([(x + 10, screen_y + 12), (x + 16, screen_y + 18)], fill=ACCENT_GREEN, width=3)
    else:
        # Clean round glowing cyan eyes
        draw.ellipse((x - 15, screen_y + 10, x - 5, screen_y + 20), fill=ACCENT_BLUE)
        draw.ellipse((x + 5, screen_y + 10, x + 15, screen_y + 20), fill=ACCENT_BLUE)
        draw.ellipse((x - 13, screen_y + 12, x - 10, screen_y + 15), fill=WHITE)
        draw.ellipse((x + 7, screen_y + 12, x + 10, screen_y + 15), fill=WHITE)
        
    # 4. Body
    draw.rounded_rectangle((body_x, body_y, body_x + body_w, body_y + body_h), radius=12, fill=WHITE, outline=ROBOT_LINE, width=2)
    # Minimalist status dot on body
    draw.ellipse((x - 4, body_y + 16, x + 4, body_y + 24), fill=orb_color)
    
    # 5. Feet
    draw.rounded_rectangle((x - 20, y - 18, x - 7, y - 2), radius=4, fill=WHITE, outline=ROBOT_LINE, width=2)
    draw.rounded_rectangle((x + 7, y - 18, x + 20, y - 2), radius=4, fill=WHITE, outline=ROBOT_LINE, width=2)
    
    # 6. Arms & Objects by Action
    if action == "search":
        # Left arm neutral
        draw.line([(body_x, body_y + 18), (body_x - 12, body_y + 36)], fill=ROBOT_LINE, width=3)
        # Right arm holding flashlight
        draw.line([(body_x + body_w, body_y + 18), (body_x + body_w + 16, body_y + 30)], fill=ROBOT_LINE, width=3)
        fl_x = body_x + body_w + 16
        fl_y = body_y + 28
        draw.rounded_rectangle((fl_x, fl_y - 6, fl_x + 16, fl_y + 6), radius=3, fill=(100, 116, 139), outline=ROBOT_LINE, width=1)
        draw.ellipse((fl_x + 14, fl_y - 7, fl_x + 20, fl_y + 7), fill=AMBER_BORDER, outline=ROBOT_LINE, width=1)
        return (fl_x + 20, fl_y) # Light beam origin
        
    elif action == "filter":
        # Arms raised in sorting posture
        draw.line([(body_x, body_y + 18), (body_x - 18, body_y + 24)], fill=ROBOT_LINE, width=3)
        draw.line([(body_x + body_w, body_y + 18), (body_x + body_w + 18, body_y + 24)], fill=ROBOT_LINE, width=3)
        
    elif action == "cv":
        # Holding resume paper
        draw.line([(body_x, body_y + 18), (body_x + 10, body_y + 36)], fill=ROBOT_LINE, width=3)
        draw.line([(body_x + body_w, body_y + 18), (body_x + body_w - 10, body_y + 36)], fill=ROBOT_LINE, width=3)
        
    elif action == "apply":
        # Launching paper airplane
        draw.line([(body_x, body_y + 18), (body_x - 10, body_y + 36)], fill=ROBOT_LINE, width=3)
        draw.line([(body_x + body_w, body_y + 18), (body_x + body_w + 22, body_y + 4)], fill=ROBOT_LINE, width=3)
        # Airplane
        ax, ay = body_x + body_w + 24, body_y + 2
        draw.polygon([(ax, ay), (ax + 24, ay - 8), (ax + 10, ay + 12)], fill=WHITE, outline=ROBOT_LINE)
        draw.line([(ax, ay), (ax + 16, ay + 1)], fill=ROBOT_LINE, width=1)
        
    elif action == "celebrate":
        # Arms up cheering \o/
        draw.line([(body_x, body_y + 20), (body_x - 18, body_y - 6)], fill=ROBOT_LINE, width=3)
        draw.line([(body_x + body_w, body_y + 20), (body_x + body_w + 18, body_y - 6)], fill=ROBOT_LINE, width=3)
        
    return (x, y)


STEPS = [
    {
        "action": "search",
        "tag": "1. PROCURA INTELIGENTE",
        "tag_bg": BLUE_TINT, "tag_border": BLUE_BORDER, "tag_txt": ACCENT_BLUE,
        "title": "Varredura contínua de vagas",
        "desc": "O robô monitora APIs oficiais em busca de oportunidades 100% remotas.",
        "robot_x": 230, "robot_y": 285
    },
    {
        "action": "filter",
        "tag": "2. FILTRO RIGOROSO",
        "tag_bg": ROSE_TINT, "tag_border": ROSE_BORDER, "tag_txt": ACCENT_ROSE,
        "title": "Zero perda de tempo",
        "desc": "Descarta na hora falsos positivos, vagas presenciais e exigências irreais.",
        "robot_x": 230, "robot_y": 285
    },
    {
        "action": "cv",
        "tag": "3. CURRÍCULO ATS",
        "tag_bg": GREEN_TINT, "tag_border": GREEN_BORDER, "tag_txt": ACCENT_GREEN,
        "title": "Currículo sob medida em PDF",
        "desc": "Alinha palavras-chave para robôs de RH (ATS) usando apenas seus fatos reais.",
        "robot_x": 230, "robot_y": 285
    },
    {
        "action": "apply",
        "tag": "4. CANDIDATURA SEGURA",
        "tag_bg": BLUE_TINT, "tag_border": BLUE_BORDER, "tag_txt": ACCENT_BLUE,
        "title": "Envio ético com controle total",
        "desc": "Aplica de forma automatizada e pausa para o humano em CAPTCHAs ou 2FA.",
        "robot_x": 230, "robot_y": 285
    },
    {
        "action": "celebrate",
        "tag": "5. CONVITES DE ENTREVISTA",
        "tag_bg": AMBER_TINT, "tag_border": AMBER_BORDER, "tag_txt": ACCENT_AMBER,
        "title": "Auditoria de e-mails diária",
        "desc": "A IA avisa quando você é chamado para entrevista. Foco total em se preparar!",
        "robot_x": 230, "robot_y": 285
    }
]


def render_minimal_frame(idx):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)
    
    st = STEPS[idx]
    
    # 1. Subtle top header
    draw.text((45, 30), "JOB HUNTER", font=FONT_BRAND, fill=TEXT_DARK)
    draw.text((140, 30), "•  Agente Autônomo de Carreira", font=FONT_TAG, fill=TEXT_MUTED)
    
    # 2. Main central stage card (Floating white card with gentle shadow)
    cw, ch = WIDTH - 90, 360
    cx, cy = 45, 75
    # Card soft outline
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=20, fill=WHITE, outline=LINE_SUBTLE, width=2)
    
    # Pill Tag (Minimalist)
    draw.rounded_rectangle((cx + 40, cy + 35, cx + 230, cy + 62), radius=14, fill=st["tag_bg"], outline=st["tag_border"], width=1)
    draw.text((cx + 52, cy + 41), st["tag"], font=FONT_PILL, fill=st["tag_txt"])
    
    # Title & Description
    draw.text((cx + 40, cy + 78), st["title"], font=FONT_HERO, fill=TEXT_DARK)
    draw.text((cx + 40, cy + 116), st["desc"], font=FONT_SUB, fill=TEXT_MUTED)
    
    # 3. Dynamic Visual Area inside card
    rx = cx + 180
    ry = cy + 280
    
    if idx == 0:
        # STEP 1: Search light beam and clean floating pills
        beam_origin = draw_minimalist_robot(draw, rx, ry, action="search")
        bx, by = beam_origin
        
        # Soft warm/yellow beam
        draw.polygon([(bx, by), (cx + cw - 30, cy + 140), (cx + cw - 30, cy + 320)], fill=(254, 252, 232))
        draw.line([(bx, by), (cx + cw - 30, cy + 140)], fill=(254, 240, 138), width=2)
        draw.line([(bx, by), (cx + cw - 30, cy + 320)], fill=(254, 240, 138), width=2)
        
        # Redraw robot on top
        draw_minimalist_robot(draw, rx, ry, action="search")
        
        # Minimalist Job Pills floating in light
        pills = [
            ("Python Developer • 100% Remoto", cx + 440, cy + 165, GREEN_TINT, GREEN_BORDER, GREEN_TEXT),
            ("AI Agent Engineer • Contrato Global USD", cx + 420, cy + 225, BLUE_TINT, BLUE_BORDER, ACCENT_BLUE),
            ("Data Analyst • Home Office Brasil", cx + 460, cy + 285, AMBER_TINT, AMBER_BORDER, ACCENT_AMBER)
        ]
        for p_txt, px, py_pos, p_bg, p_brd, p_col in pills:
            draw.rounded_rectangle((px, py_pos, px + 280, py_pos + 42), radius=12, fill=WHITE, outline=p_brd, width=2)
            draw.text((px + 18, py_pos + 13), p_txt, font=FONT_PILL, fill=p_col)
            
    elif idx == 1:
        # STEP 2: Filter (Clean separation of Discarded vs Approved)
        draw_minimalist_robot(draw, rx, ry, action="filter")
        
        # Rejected pill (faded with cross)
        draw.rounded_rectangle((cx + 430, cy + 175, cx + 700, cy + 225), radius=14, fill=ROSE_TINT, outline=ROSE_BORDER, width=1)
        draw.text((cx + 450, cy + 192), "✕  Híbrido / Presencial / Exige Diploma", font=FONT_PILL, fill=ACCENT_ROSE)
        
        # Approved pill (glowing with checkmark)
        draw.rounded_rectangle((cx + 430, cy + 250, cx + 700, cy + 305), radius=14, fill=GREEN_TINT, outline=GREEN_BORDER, width=2)
        draw.text((cx + 450, cy + 268), "✔  100% Remoto  •  Aceita Brasil  •  PJ/CLT", font=FONT_PILL, fill=GREEN_TEXT)
        
    elif idx == 2:
        # STEP 3: ATS Resume (Minimalist sheet mockup with green stamp)
        draw_minimalist_robot(draw, rx, ry, action="cv")
        
        sheet_x, sheet_y, sheet_w, sheet_h = cx + 450, cy + 155, 230, 160
        draw.rounded_rectangle((sheet_x, sheet_y, sheet_x + sheet_w, sheet_y + sheet_h), radius=10, fill=WHITE, outline=LINE_SUBTLE, width=2)
        # Inner decorative lines
        draw.text((sheet_x + 18, sheet_y + 16), "Currículo Personalizado", font=FONT_PILL, fill=TEXT_DARK)
        draw.line([(sheet_x + 18, sheet_y + 40), (sheet_x + sheet_w - 18, sheet_y + 40)], fill=LINE_SUBTLE, width=1)
        draw.line([(sheet_x + 18, sheet_y + 58), (sheet_x + 150, sheet_y + 58)], fill=TEXT_LIGHT, width=2)
        draw.line([(sheet_x + 18, sheet_y + 74), (sheet_x + 190, sheet_y + 74)], fill=TEXT_LIGHT, width=2)
        draw.line([(sheet_x + 18, sheet_y + 90), (sheet_x + 130, sheet_y + 90)], fill=TEXT_LIGHT, width=2)
        
        # Minimal ATS Stamp
        draw.rounded_rectangle((sheet_x + 85, sheet_y + 110, sheet_x + sheet_w - 16, sheet_y + 145), radius=8, fill=GREEN_TINT, outline=GREEN_BORDER, width=1)
        draw.text((sheet_x + 98, sheet_y + 120), "ATS Score: 95%", font=FONT_PILL, fill=GREEN_TEXT)
        
    elif idx == 3:
        # STEP 4: Apply (Airplane flight trajectory)
        draw_minimalist_robot(draw, rx, ry, action="apply")
        
        # Dotted gentle arc
        dots = [(rx + 60, ry - 60), (rx + 110, ry - 75), (rx + 165, ry - 82), (rx + 220, ry - 80), (rx + 270, ry - 70)]
        for dx, dy in dots:
            draw.ellipse((dx, dy, dx + 4, dy + 4), fill=BORDER_LIGHT if "BORDER_LIGHT" in globals() else (203, 213, 225))
            
        # Target Company Card
        tx, ty = cx + 460, cy + 180
        draw.rounded_rectangle((tx, ty, tx + 240, ty + 105), radius=14, fill=WHITE, outline=BLUE_BORDER, width=2)
        draw.text((tx + 20, ty + 24), "Candidatura Oficial", font=FONT_PILL, fill=TEXT_DARK)
        draw.text((tx + 20, ty + 48), "Formulário enviado com sucesso", font=FONT_TAG, fill=TEXT_MUTED)
        draw.text((tx + 20, ty + 70), "✔ Pausa em CAPTCHA ou 2FA", font=FONT_TAG, fill=ACCENT_BLUE)
        
    elif idx == 4:
        # STEP 5: Celebrate & Interview Invitation!
        draw_minimalist_robot(draw, rx, ry, action="celebrate")
        
        # Cute warm envelope
        env_x, env_y = cx + 430, cy + 165
        draw.rounded_rectangle((env_x, env_y, env_x + 270, env_y + 125), radius=16, fill=AMBER_TINT, outline=AMBER_BORDER, width=2)
        draw.text((env_x + 24, env_y + 24), "Convite para Entrevista! 🎉", font=FONT_HERO, fill=TEXT_DARK)
        draw.text((env_x + 24, env_y + 60), "Detectado na checagem diária do Gmail.", font=FONT_TAG, fill=TEXT_MUTED)
        draw.text((env_x + 24, env_y + 85), "Menos tempo na busca, foco na entrevista.", font=FONT_TAG, fill=ACCENT_AMBER)
        
    # 4. Minimalist Progress Dots at the bottom
    dot_y = HEIGHT - 40
    start_dot_x = WIDTH // 2 - 60
    for d in range(len(STEPS)):
        dx = start_dot_x + d * 26
        if d == idx:
            # Active pill dot
            draw.rounded_rectangle((dx - 6, dot_y - 4, dx + 14, dot_y + 4), radius=4, fill=ACCENT_BLUE)
        elif d < idx:
            # Past dot
            draw.ellipse((dx, dot_y - 4, dx + 8, dot_y + 4), fill=ACCENT_GREEN)
        else:
            # Future dot
            draw.ellipse((dx, dot_y - 4, dx + 8, dot_y + 4), fill=(226, 232, 240))
            
    return im


def main():
    frames = []
    durations = []
    
    for i in range(len(STEPS)):
        frame = render_minimal_frame(i)
        frames.append(frame)
        
        # Pacing: clean, calm, pleasant
        if i == 4:
            durations.append(3800) # Celebrate slide: 3.8s
        elif i == 0:
            durations.append(3400) # Light beam slide: 3.4s
        else:
            durations.append(3000) # 3.0s
            
    out_path = "jobhunter_aesthetic.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"GIF Estético Minimalista gerado com sucesso: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    main()
