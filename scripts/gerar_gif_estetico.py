import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 960
HEIGHT = 540

# Fonts (Segoe UI Family)
FONT_LOGO = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 14)
FONT_LOGO_SUB = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 13)
FONT_HERO = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 24)
FONT_STAGE_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 16)
FONT_DESC = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 14)
FONT_BADGE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 11)
FONT_CARD_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
FONT_CARD_SUB = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 12)
FONT_FOOTER = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 11)

# Aesthetic Palette (Light Mode - Linear / Apple inspired)
BG_CANVAS = (248, 250, 252)       # Slate-50
WHITE = (255, 255, 255)
CARD_BG = (255, 255, 255)
CARD_BORDER = (226, 232, 240)     # Slate-200
DIVIDER_COLOR = (241, 245, 249)   # Slate-100
SHADOW_COLOR = (235, 240, 246)

TEXT_DARK = (15, 23, 42)          # Slate-900 (High contrast)
TEXT_MUTED = (71, 85, 105)        # Slate-600
TEXT_LIGHT = (148, 163, 184)      # Slate-400

# Refined Soft Accents
BLUE_TINT = (238, 246, 255)
BLUE_BORDER = (186, 230, 253)
BLUE_TEXT = (2, 132, 199)

GREEN_TINT = (240, 253, 244)
GREEN_BORDER = (187, 247, 208)
GREEN_TEXT = (22, 163, 74)

ORANGE_TINT = (255, 247, 237)
ORANGE_BORDER = (254, 215, 170)
ORANGE_TEXT = (234, 88, 12)

PURPLE_TINT = (250, 245, 255)
PURPLE_BORDER = (233, 213, 255)
PURPLE_TEXT = (147, 51, 234)

YELLOW_TINT = (254, 252, 232)
YELLOW_BORDER = (254, 240, 138)
YELLOW_TEXT = (202, 138, 4)

ROSE_TINT = (255, 241, 242)
ROSE_BORDER = (254, 205, 211)
ROSE_TEXT = (225, 29, 72)

ROBOT_LINE = (71, 85, 105)
ROBOT_SCREEN = (15, 23, 42)
ROBOT_EYE_CYAN = (56, 189, 248)
ROBOT_EYE_GREEN = (52, 211, 153)


def draw_robot(draw, cx, cy, pose="search"):
    """
    Draws a clean minimalist vector robot strictly inside [cx-45, cx+45].
    cy is the ground level (bottom of feet).
    Total height from antenna top to feet is ~140px.
    """
    # Soft ground shadow
    draw.ellipse((cx - 36, cy - 6, cx + 36, cy + 6), fill=SHADOW_COLOR)
    
    # Body measurements
    bw, bh = 56, 52
    bx = cx - bw // 2
    by = cy - 68
    
    # Head measurements
    hw, hh = 62, 46
    hx = cx - hw // 2
    hy = by - hh - 4
    
    # 1. Antenna (stretching up from hy)
    draw.line([(cx, hy), (cx, hy - 14)], fill=ROBOT_LINE, width=2)
    orb_col = ROBOT_EYE_GREEN if pose == "celebrate" else ROBOT_EYE_CYAN
    draw.ellipse((cx - 6, hy - 24, cx + 6, hy - 12), fill=orb_col, outline=ROBOT_LINE, width=2)
    
    # 2. Head
    draw.rounded_rectangle((hx, hy, hx + hw, hy + hh), radius=12, fill=WHITE, outline=ROBOT_LINE, width=2)
    # Ears
    draw.rounded_rectangle((hx - 4, hy + 14, hx, hy + 30), radius=2, fill=(226, 232, 240), outline=ROBOT_LINE, width=1)
    draw.rounded_rectangle((hx + hw, hy + 14, hx + hw + 4, hy + 30), radius=2, fill=(226, 232, 240), outline=ROBOT_LINE, width=1)
    
    # Visor screen
    vw, vh = 44, 28
    vx = cx - vw // 2
    vy = hy + 9
    draw.rounded_rectangle((vx, vy, vx + vw, vy + vh), radius=7, fill=ROBOT_SCREEN)
    
    # Eyes
    if pose == "celebrate":
        # Happy eyes: ^ ^
        draw.line([(cx - 14, vy + 17), (cx - 9, vy + 11)], fill=ROBOT_EYE_GREEN, width=3)
        draw.line([(cx - 9, vy + 11), (cx - 4, vy + 17)], fill=ROBOT_EYE_GREEN, width=3)
        draw.line([(cx + 4, vy + 17), (cx + 9, vy + 11)], fill=ROBOT_EYE_GREEN, width=3)
        draw.line([(cx + 9, vy + 11), (cx + 14, vy + 17)], fill=ROBOT_EYE_GREEN, width=3)
    else:
        # Glowing cyan eyes with white shine
        draw.ellipse((cx - 14, vy + 9, cx - 4, vy + 19), fill=ROBOT_EYE_CYAN)
        draw.ellipse((cx + 4, vy + 9, cx + 14, vy + 19), fill=ROBOT_EYE_CYAN)
        draw.ellipse((cx - 12, vy + 11, cx - 9, vy + 14), fill=WHITE)
        draw.ellipse((cx + 6, vy + 11, cx + 9, vy + 14), fill=WHITE)
        
    # 3. Body
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=10, fill=WHITE, outline=ROBOT_LINE, width=2)
    # Status light on torso
    draw.ellipse((cx - 4, by + 14, cx + 4, by + 22), fill=orb_col)
    
    # 4. Feet
    draw.rounded_rectangle((cx - 18, cy - 16, cx - 6, cy - 2), radius=3, fill=WHITE, outline=ROBOT_LINE, width=2)
    draw.rounded_rectangle((cx + 6, cy - 16, cx + 18, cy - 2), radius=3, fill=WHITE, outline=ROBOT_LINE, width=2)
    
    # 5. Arms & Accessories by pose
    if pose == "search":
        draw.line([(bx, by + 16), (bx - 10, by + 34)], fill=ROBOT_LINE, width=3)
        draw.line([(bx + bw, by + 16), (bx + bw + 14, by + 28)], fill=ROBOT_LINE, width=3)
        # Flashlight
        fl_x = bx + bw + 14
        fl_y = by + 26
        draw.rounded_rectangle((fl_x, fl_y - 6, fl_x + 14, fl_y + 6), radius=2, fill=(100, 116, 139), outline=ROBOT_LINE, width=1)
        draw.ellipse((fl_x + 12, fl_y - 7, fl_x + 18, fl_y + 7), fill=YELLOW_BORDER, outline=ROBOT_LINE, width=1)
        return (fl_x + 18, fl_y) # Light origin
        
    elif pose == "filter":
        draw.line([(bx, by + 16), (bx - 16, by + 22)], fill=ROBOT_LINE, width=3)
        draw.line([(bx + bw, by + 16), (bx + bw + 16, by + 22)], fill=ROBOT_LINE, width=3)
        
    elif pose == "cv":
        draw.line([(bx, by + 16), (bx + 8, by + 34)], fill=ROBOT_LINE, width=3)
        draw.line([(bx + bw, by + 16), (bx + bw - 8, by + 34)], fill=ROBOT_LINE, width=3)
        
    elif pose == "apply":
        draw.line([(bx, by + 16), (bx - 10, by + 34)], fill=ROBOT_LINE, width=3)
        draw.line([(bx + bw, by + 16), (bx + bw + 20, by + 4)], fill=ROBOT_LINE, width=3)
        # Paper plane
        ax, ay = bx + bw + 22, by + 2
        draw.polygon([(ax, ay), (ax + 22, ay - 8), (ax + 10, ay + 10)], fill=WHITE, outline=ROBOT_LINE)
        draw.line([(ax, ay), (ax + 14, ay + 1)], fill=ROBOT_LINE, width=1)
        
    elif pose == "celebrate":
        # Cheering arms \o/
        draw.line([(bx, by + 16), (bx - 16, by - 6)], fill=ROBOT_LINE, width=3)
        draw.line([(bx + bw, by + 16), (bx + bw + 16, by - 6)], fill=ROBOT_LINE, width=3)
        
    return (cx, cy)


STEPS = [
    {
        "step_num": "ETAPA 1 DE 5",
        "badge": "1. PROCURA INTELIGENTE",
        "badge_bg": BLUE_TINT, "badge_border": BLUE_BORDER, "badge_txt": BLUE_TEXT,
        "title": "Varredura Contínua",
        "desc_1": "O robô monitora APIs oficiais em busca",
        "desc_2": "de oportunidades 100% remotas.",
        "highlight": "✔ Greenhouse, Ashby e RemoteOK (+5.800 vagas)",
        "robot_pose": "search"
    },
    {
        "step_num": "ETAPA 2 DE 5",
        "badge": "2. FILTRO RIGOROSO",
        "badge_bg": ROSE_TINT, "badge_border": ROSE_BORDER, "badge_txt": ROSE_TEXT,
        "title": "Filtro Sem Desperdício",
        "desc_1": "Descarta de imediato vagas híbridas,",
        "desc_2": "presenciais e exigências irreais.",
        "highlight": "✔ Zero perda de tempo com falsos positivos",
        "robot_pose": "filter"
    },
    {
        "step_num": "ETAPA 3 DE 5",
        "badge": "3. CURRÍCULO ATS",
        "badge_bg": GREEN_TINT, "badge_border": GREEN_BORDER, "badge_txt": GREEN_TEXT,
        "title": "Currículo sob Medida",
        "desc_1": "Reorganiza competências técnicas para ATS",
        "desc_2": "utilizando apenas fatos reais do seu perfil.",
        "highlight": "✔ Palavras-chave alinhadas sem inventar nada",
        "robot_pose": "cv"
    },
    {
        "step_num": "ETAPA 4 DE 5",
        "badge": "4. CANDIDATURA SEGURA",
        "badge_bg": BLUE_TINT, "badge_border": BLUE_BORDER, "badge_txt": BLUE_TEXT,
        "title": "Candidatura Segura",
        "desc_1": "Aplica de forma automatizada com",
        "desc_2": "pausa para humano em CAPTCHAs ou 2FA.",
        "highlight": "✔ Controle total: Envio automático ou sob aprovação",
        "robot_pose": "apply"
    },
    {
        "step_num": "ETAPA 5 DE 5",
        "badge": "5. CONVITES DE ENTREVISTA",
        "badge_bg": YELLOW_TINT, "badge_border": YELLOW_BORDER, "badge_txt": YELLOW_TEXT,
        "title": "Mais Entrevistas",
        "desc_1": "Audita retornos diários no Gmail para",
        "desc_2": "você focar apenas em se preparar.",
        "highlight": "✔ Menos rotina repetitiva, foco na contratação",
        "robot_pose": "celebrate"
    }
]


def render_scene(idx):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(im)
    
    st = STEPS[idx]
    
    # -------------------------------------------------------------------------
    # 1. TOP HEADER (Completely outside and above the main card)
    # -------------------------------------------------------------------------
    draw.text((45, 24), "🤖 JOB HUNTER", font=FONT_LOGO, fill=TEXT_DARK)
    draw.text((160, 25), "•  Agente Autônomo de Carreira Tech", font=FONT_LOGO_SUB, fill=TEXT_MUTED)
    
    # Step indicator pill on the top right
    step_pill_x = WIDTH - 150
    draw.rounded_rectangle((step_pill_x, 20, step_pill_x + 105, 44), radius=12, fill=WHITE, outline=CARD_BORDER, width=1)
    draw.text((step_pill_x + 15, 26), st["step_num"], font=FONT_BADGE, fill=TEXT_MUTED)
    
    # -------------------------------------------------------------------------
    # 2. MAIN CARD (Clean white floating canvas with rounded corners)
    # -------------------------------------------------------------------------
    card_x, card_y, card_w, card_h = 40, 60, WIDTH - 80, 420
    draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    
    # Vertical divider separating Left Text Zone and Right Illustration Zone
    divider_x = card_x + 380
    draw.line([(divider_x, card_y + 30), (divider_x, card_y + card_h - 30)], fill=DIVIDER_COLOR, width=1)
    
    # -------------------------------------------------------------------------
    # 3. LEFT ZONE: PURE TEXT & METRICS (X: 75 to 390 - ZERO OVERLAP WITH ROBOT)
    # -------------------------------------------------------------------------
    left_x = card_x + 35
    
    # Category Pill
    draw.rounded_rectangle((left_x, card_y + 40, left_x + 190, card_y + 68), radius=8, fill=st["badge_bg"], outline=st["badge_border"], width=1)
    draw.text((left_x + 14, card_y + 47), st["badge"], font=FONT_BADGE, fill=st["badge_txt"])
    
    # Main Hero Title
    draw.text((left_x, card_y + 90), st["title"], font=FONT_HERO, fill=TEXT_DARK)
    
    # Description lines
    draw.text((left_x, card_y + 138), st["desc_1"], font=FONT_DESC, fill=TEXT_MUTED)
    draw.text((left_x, card_y + 162), st["desc_2"], font=FONT_DESC, fill=TEXT_MUTED)
    
    # Highlight Pill at the bottom of the left zone
    hl_y = card_y + 240
    draw.rounded_rectangle((left_x, hl_y, left_x + 325, hl_y + 48), radius=10, fill=WHITE, outline=CARD_BORDER, width=1)
    draw.text((left_x + 14, hl_y + 17), st["highlight"], font=FONT_CARD_SUB, fill=TEXT_DARK)
    
    # Open Source tag
    draw.text((left_x, card_y + card_h - 45), "Código Aberto no GitHub: github.com/160f/jobhunter", font=FONT_FOOTER, fill=TEXT_LIGHT)
    
    # -------------------------------------------------------------------------
    # 4. RIGHT ZONE: ROBOT & VISUAL STAGE (X: 410 to 900 - DEDICATED STAGE)
    # -------------------------------------------------------------------------
    robot_x = divider_x + 95   # X = 515
    robot_y = card_y + 270     # Ground at Y = 330, Head at Y = 210, Antenna at Y = 185
    
    stage_x = divider_x + 195  # Objects strictly at X: 615 to 870
    
    if idx == 0:
        # STEP 1: Search light beam and clean floating pills
        beam_origin = draw_robot(draw, robot_x, robot_y, pose="search")
        bx, by = beam_origin
        
        # Soft warm light cone bounded to card right edge
        target_right = card_x + card_w - 25
        draw.polygon([(bx, by), (target_right, card_y + 110), (target_right, card_y + 330)], fill=(254, 252, 232))
        draw.line([(bx, by), (target_right, card_y + 110)], fill=(254, 240, 138), width=1)
        draw.line([(bx, by), (target_right, card_y + 330)], fill=(254, 240, 138), width=1)
        
        # Redraw robot over the light origin for sharp layering
        draw_robot(draw, robot_x, robot_y, pose="search")
        
        # 3 Floating Job Cards (strictly inside stage_x to target_right)
        pills = [
            ("Python Backend • Remoto", stage_x, card_y + 125, GREEN_TINT, GREEN_BORDER, GREEN_TEXT),
            ("AI Agent Dev • Global USD", stage_x - 10, card_y + 185, BLUE_TINT, BLUE_BORDER, BLUE_TEXT),
            ("Data Analyst • Home Office", stage_x + 5, card_y + 245, PURPLE_TINT, PURPLE_BORDER, PURPLE_TEXT)
        ]
        for p_txt, px, py, p_bg, p_brd, p_col in pills:
            draw.rounded_rectangle((px, py, px + 235, py + 42), radius=10, fill=WHITE, outline=p_brd, width=2)
            draw.text((px + 14, py + 14), p_txt, font=FONT_CARD_TITLE, fill=p_col)
            
    elif idx == 1:
        # STEP 2: Filter (Discard vs Approved cards strictly bounded)
        draw_robot(draw, robot_x, robot_y, pose="filter")
        
        # Discard Card
        draw.rounded_rectangle((stage_x, card_y + 130, stage_x + 245, card_y + 185), radius=12, fill=ROSE_TINT, outline=ROSE_BORDER, width=1)
        draw.text((stage_x + 16, card_y + 144), "✕ Descarte Automático", font=FONT_CARD_TITLE, fill=ROSE_TEXT)
        draw.text((stage_x + 16, card_y + 162), "Híbrido • Presencial • Exige Diploma", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        
        # Approved Card
        draw.rounded_rectangle((stage_x, card_y + 215, stage_x + 245, card_y + 270), radius=12, fill=GREEN_TINT, outline=GREEN_BORDER, width=2)
        draw.text((stage_x + 16, card_y + 229), "✔ Aprovada p/ Vaga", font=FONT_CARD_TITLE, fill=GREEN_TEXT)
        draw.text((stage_x + 16, card_y + 247), "100% Remoto • Aceita Brasil • PJ/CLT", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        
    elif idx == 2:
        # STEP 3: ATS Resume mockup
        draw_robot(draw, robot_x, robot_y, pose="cv")
        
        sheet_w, sheet_h = 235, 160
        draw.rounded_rectangle((stage_x + 5, card_y + 125, stage_x + 5 + sheet_w, card_y + 125 + sheet_h), radius=10, fill=WHITE, outline=CARD_BORDER, width=2)
        
        draw.text((stage_x + 20, card_y + 140), "CURRÍCULO ATS", font=FONT_BADGE, fill=TEXT_MUTED)
        draw.line([(stage_x + 20, card_y + 158), (stage_x + sheet_w - 5, card_y + 158)], fill=DIVIDER_COLOR, width=1)
        
        # Resume text lines
        draw.text((stage_x + 20, card_y + 170), "Python, APIs REST & Automação", font=FONT_CARD_SUB, fill=TEXT_DARK)
        draw.text((stage_x + 20, card_y + 190), "Agentes de IA e Análise de Dados", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        
        # ATS Stamp Badge
        draw.rounded_rectangle((stage_x + 20, card_y + 225, stage_x + 185, card_y + 265), radius=8, fill=GREEN_TINT, outline=GREEN_BORDER, width=1)
        draw.text((stage_x + 35, card_y + 236), "✔ ATS Score: 95%", font=FONT_CARD_TITLE, fill=GREEN_TEXT)
        
    elif idx == 3:
        # STEP 4: Apply (Flight trajectory and safe application card)
        draw_robot(draw, robot_x, robot_y, pose="apply")
        
        # Dotted trajectory
        dots = [(robot_x + 45, robot_y - 65), (robot_x + 85, robot_y - 80), (robot_x + 130, robot_y - 85), (robot_x + 175, robot_y - 75)]
        for dx, dy in dots:
            draw.ellipse((dx, dy, dx + 4, dy + 4), fill=CARD_BORDER)
            
        # Target Card
        draw.rounded_rectangle((stage_x, card_y + 145, stage_x + 245, card_y + 250), radius=14, fill=WHITE, outline=BLUE_BORDER, width=2)
        draw.text((stage_x + 18, card_y + 165), "Formulário Oficial", font=FONT_CARD_TITLE, fill=TEXT_DARK)
        draw.text((stage_x + 18, card_y + 188), "Currículo anexado com sucesso", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        draw.text((stage_x + 18, card_y + 215), "🔒 Pausa Ética em CAPTCHA / 2FA", font=FONT_BADGE, fill=BLUE_TEXT)
        
    elif idx == 4:
        # STEP 5: Celebrate & Interview Invitation Card
        draw_robot(draw, robot_x, robot_y, pose="celebrate")
        
        # Envelope Card
        draw.rounded_rectangle((stage_x - 10, card_y + 135, stage_x + 250, card_y + 265), radius=14, fill=YELLOW_TINT, outline=YELLOW_BORDER, width=2)
        draw.text((stage_x + 16, card_y + 155), "📬 RETORNO NO GMAIL", font=FONT_BADGE, fill=YELLOW_TEXT)
        draw.text((stage_x + 16, card_y + 178), "Convite de Entrevista! 🎉", font=FONT_STAGE_TITLE, fill=TEXT_DARK)
        draw.text((stage_x + 16, card_y + 212), "Identificado na auditoria diária das 18h", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        draw.text((stage_x + 16, card_y + 235), "Foco 100% na preparação técnica", font=FONT_BADGE, fill=GREEN_TEXT)
        
    # -------------------------------------------------------------------------
    # 5. BOTTOM NAVIGATION (Centered minimalist progress dots)
    # -------------------------------------------------------------------------
    dot_y = HEIGHT - 28
    start_dx = WIDTH // 2 - 50
    for d in range(len(STEPS)):
        dx = start_dx + d * 24
        if d == idx:
            # Active pill
            draw.rounded_rectangle((dx - 5, dot_y - 3, dx + 13, dot_y + 3), radius=3, fill=BLUE_TEXT)
        elif d < idx:
            # Past dot
            draw.ellipse((dx, dot_y - 3, dx + 6, dot_y + 3), fill=GREEN_TEXT)
        else:
            # Future dot
            draw.ellipse((dx, dot_y - 3, dx + 6, dot_y + 3), fill=CARD_BORDER)
            
    return im


def main():
    frames = []
    durations = []
    
    for i in range(len(STEPS)):
        frame = render_scene(i)
        frames.append(frame)
        
        if i == 4:
            durations.append(3800) # Celebrate: 3.8s
        elif i == 0:
            durations.append(3400) # Search beam: 3.4s
        else:
            durations.append(3000) # Other slides: 3.0s
            
    out_path = "jobhunter_aesthetic.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"GIF Estético corrigido com sucesso: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    main()
