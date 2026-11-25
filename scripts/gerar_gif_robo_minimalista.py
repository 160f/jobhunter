import os
import math
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1040
HEIGHT = 580

# Clean, modern typography
FONT_SUPER_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 24)
FONT_SUBTITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 21)
FONT_DESC = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 14)
FONT_BADGE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 11)
FONT_CARD_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
FONT_CARD_SUB = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 11)
FONT_CODE = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 12)
FONT_KPI = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 18)

# Minimalist Light Palette
BG_MAIN = (248, 250, 252)       # Soft slate-50
WHITE = (255, 255, 255)
BORDER_LIGHT = (226, 232, 240)  # Slate-200
BORDER_DARK = (203, 213, 225)   # Slate-300

TEXT_MAIN = (15, 23, 42)        # Slate-900 (deep charcoal)
TEXT_MUTED = (71, 85, 105)      # Slate-600
TEXT_LIGHT = (148, 163, 184)    # Slate-400

# Pastels & Accents
BLUE_BG = (238, 246, 255)
BLUE_BORDER = (186, 230, 253)
BLUE_TEXT = (2, 132, 199)

GREEN_BG = (240, 253, 244)
GREEN_BORDER = (187, 247, 208)
GREEN_TEXT = (22, 163, 74)

ORANGE_BG = (255, 247, 237)
ORANGE_BORDER = (254, 215, 170)
ORANGE_TEXT = (234, 88, 12)

PURPLE_BG = (250, 245, 255)
PURPLE_BORDER = (233, 213, 255)
PURPLE_TEXT = (147, 51, 234)

YELLOW_BG = (254, 252, 232)
YELLOW_BORDER = (254, 240, 138)
YELLOW_TEXT = (202, 138, 4)

# Robot Colors
ROBOT_BODY = (255, 255, 255)
ROBOT_OUTLINE = (100, 116, 139) # Slate-500
ROBOT_SCREEN = (15, 23, 42)     # Dark slate visor
ROBOT_EYE_CYAN = (56, 189, 248) # Glowing cyan
ROBOT_EYE_GREEN = (52, 211, 153)
ROBOT_JOINT = (203, 213, 225)


def draw_cute_robot(draw, x, y, pose="search", eye_color=ROBOT_EYE_CYAN):
    """
    Draws a cute, friendly minimalist robot centered horizontally around x.
    y is the top of the antenna.
    """
    # 1. Antenna
    draw.line([(x, y + 25), (x, y + 8)], fill=ROBOT_OUTLINE, width=3)
    draw.ellipse((x - 7, y, x + 7, y + 14), fill=eye_color, outline=ROBOT_OUTLINE, width=2)
    
    # 2. Head
    head_w, head_h = 76, 56
    head_x = x - head_w // 2
    head_y = y + 25
    draw.rounded_rectangle((head_x, head_y, head_x + head_w, head_y + head_h), radius=16, fill=ROBOT_BODY, outline=ROBOT_OUTLINE, width=2)
    
    # Ears
    draw.rounded_rectangle((head_x - 6, head_y + 18, head_x, head_y + 36), radius=3, fill=ROBOT_JOINT, outline=ROBOT_OUTLINE, width=1)
    draw.rounded_rectangle((head_x + head_w, head_y + 18, head_x + head_w + 6, head_y + 36), radius=3, fill=ROBOT_JOINT, outline=ROBOT_OUTLINE, width=1)
    
    # Screen / Visor
    screen_w, screen_h = 56, 36
    screen_x = x - screen_w // 2
    screen_y = head_y + 10
    draw.rounded_rectangle((screen_x, screen_y, screen_x + screen_w, screen_y + screen_h), radius=9, fill=ROBOT_SCREEN)
    
    # Eyes by pose
    if pose == "happy" or pose == "celebrate":
        # Happy arched eyes: ^ ^
        draw.line([(x - 18, screen_y + 20), (x - 12, screen_y + 14)], fill=ROBOT_EYE_GREEN, width=3)
        draw.line([(x - 12, screen_y + 14), (x - 6, screen_y + 20)], fill=ROBOT_EYE_GREEN, width=3)
        draw.line([(x + 6, screen_y + 20), (x + 12, screen_y + 14)], fill=ROBOT_EYE_GREEN, width=3)
        draw.line([(x + 12, screen_y + 14), (x + 18, screen_y + 20)], fill=ROBOT_EYE_GREEN, width=3)
    elif pose == "filter":
        # Scanning/analytical eyes: [o o]
        draw.ellipse((x - 18, screen_y + 13, x - 8, screen_y + 23), fill=ORANGE_TEXT)
        draw.ellipse((x + 8, screen_y + 13, x + 18, screen_y + 23), fill=ORANGE_TEXT)
    else:
        # Default cute round glowing eyes
        draw.ellipse((x - 17, screen_y + 13, x - 7, screen_y + 23), fill=eye_color)
        draw.ellipse((x + 7, screen_y + 13, x + 17, screen_y + 23), fill=eye_color)
        # Eye shine
        draw.ellipse((x - 15, screen_y + 15, x - 12, screen_y + 18), fill=WHITE)
        draw.ellipse((x + 9, screen_y + 15, x + 12, screen_y + 18), fill=WHITE)
        
    # 3. Neck
    draw.rectangle((x - 8, head_y + head_h, x + 8, head_y + head_h + 6), fill=ROBOT_JOINT, outline=ROBOT_OUTLINE, width=1)
    
    # 4. Body (Torso)
    body_w, body_h = 70, 72
    body_x = x - body_w // 2
    body_y = head_y + head_h + 6
    draw.rounded_rectangle((body_x, body_y, body_x + body_w, body_y + body_h), radius=14, fill=ROBOT_BODY, outline=ROBOT_OUTLINE, width=2)
    
    # Torso badge / heart / screen
    draw.rounded_rectangle((body_x + 14, body_y + 14, body_x + body_w - 14, body_y + 40), radius=6, fill=BLUE_BG, outline=BLUE_BORDER, width=1)
    # Mini blinking meter
    draw.line([(body_x + 20, body_y + 27), (body_x + 32, body_y + 27)], fill=eye_color, width=3)
    draw.line([(body_x + 36, body_y + 27), (body_x + 48, body_y + 27)], fill=GREEN_TEXT, width=3)
    
    # 5. Feet / Wheels
    foot_y = body_y + body_h
    draw.rounded_rectangle((x - 24, foot_y, x - 8, foot_y + 16), radius=5, fill=ROBOT_JOINT, outline=ROBOT_OUTLINE, width=1)
    draw.rounded_rectangle((x + 8, foot_y, x + 24, foot_y + 16), radius=5, fill=ROBOT_JOINT, outline=ROBOT_OUTLINE, width=1)
    
    # 6. Arms / Accessories by Pose
    if pose == "search":
        # Right arm holding a flashlight pointing forward-right
        draw.line([(body_x + body_w, body_y + 20), (body_x + body_w + 18, body_y + 36)], fill=ROBOT_OUTLINE, width=4)
        # Flashlight
        fl_x = body_x + body_w + 18
        fl_y = body_y + 34
        draw.rounded_rectangle((fl_x, fl_y - 8, fl_x + 20, fl_y + 8), radius=3, fill=(71, 85, 105), outline=ROBOT_OUTLINE, width=1)
        draw.ellipse((fl_x + 18, fl_y - 10, fl_x + 26, fl_y + 10), fill=YELLOW_BORDER, outline=ROBOT_OUTLINE, width=1)
        
        # Left arm relaxed
        draw.line([(body_x, body_y + 20), (body_x - 12, body_y + 40)], fill=ROBOT_OUTLINE, width=4)
        return (fl_x + 26, fl_y) # Light origin
        
    elif pose == "filter":
        # Left arm holding a sorting filter funnel / clipboard
        draw.line([(body_x, body_y + 20), (body_x - 20, body_y + 30)], fill=ROBOT_OUTLINE, width=4)
        draw.line([(body_x + body_w, body_y + 20), (body_x + body_w + 20, body_y + 28)], fill=ROBOT_OUTLINE, width=4)
        return (x, body_y)
        
    elif pose == "cv":
        # Arms holding a document and pen
        draw.line([(body_x - 2, body_y + 22), (body_x + 14, body_y + 46)], fill=ROBOT_OUTLINE, width=4)
        draw.line([(body_x + body_w + 2, body_y + 22), (body_x + body_w - 14, body_y + 46)], fill=ROBOT_OUTLINE, width=4)
        return (x, body_y)
        
    elif pose == "apply":
        # Launching paper airplane
        draw.line([(body_x, body_y + 20), (body_x - 12, body_y + 42)], fill=ROBOT_OUTLINE, width=4)
        draw.line([(body_x + body_w, body_y + 20), (body_x + body_w + 26, body_y + 6)], fill=ROBOT_OUTLINE, width=4)
        # Paper airplane at hand
        ap_x = body_x + body_w + 28
        ap_y = body_y + 4
        draw.polygon([(ap_x, ap_y), (ap_x + 26, ap_y - 8), (ap_x + 10, ap_y + 14)], fill=WHITE, outline=ROBOT_OUTLINE)
        draw.line([(ap_x, ap_y), (ap_x + 18, ap_y + 2)], fill=ROBOT_OUTLINE, width=1)
        return (ap_x, ap_y)
        
    elif pose == "happy" or pose == "celebrate":
        # Both arms raised in celebration! \o/
        draw.line([(body_x, body_y + 24), (body_x - 22, body_y - 4)], fill=ROBOT_OUTLINE, width=4)
        draw.line([(body_x + body_w, body_y + 24), (body_x + body_w + 22, body_y - 4)], fill=ROBOT_OUTLINE, width=4)
        return (x, body_y)
        
    return (x, y)


def draw_top_nav(draw, current_step):
    # Header bar
    draw.rectangle((0, 0, WIDTH, 65), fill=WHITE)
    draw.line((0, 65, WIDTH, 65), fill=BORDER_LIGHT, width=1)
    
    # Logo & Name
    draw.rounded_rectangle((28, 16, 175, 48), radius=8, fill=BLUE_BG, outline=BLUE_BORDER, width=1)
    draw.text((38, 24), "🤖 JOB HUNTER", font=FONT_BADGE, fill=BLUE_TEXT)
    draw.text((125, 24), "AI AGENT", font=FONT_BADGE, fill=GREEN_TEXT)
    
    draw.text((195, 18), "Como o Agente Autônomo Encontra seu Próximo Trabalho", font=FONT_SUPER_TITLE, fill=TEXT_MAIN)
    
    # Step pills at top right
    step_labels = ["1. Busca", "2. Filtra", "3. Adapta CV", "4. Aplica", "5. Entrevista"]
    start_px = WIDTH - 470
    for i, s_lbl in enumerate(step_labels):
        sx = start_px + i * 90
        is_active = (i == current_step)
        is_past = (i < current_step)
        
        bg = BLUE_BG if is_active else (GREEN_BG if is_past else WHITE)
        border = BLUE_BORDER if is_active else (GREEN_BORDER if is_past else BORDER_LIGHT)
        txt_col = BLUE_TEXT if is_active else (GREEN_TEXT if is_past else TEXT_LIGHT)
        
        draw.rounded_rectangle((sx, 20, sx + 82, 46), radius=13, fill=bg, outline=border, width=1)
        draw.text((sx + 10, 26), s_lbl, font=FONT_BADGE, fill=txt_col)


SCENES = [
    {
        "id": 0,
        "badge": "ETAPA 1 • PROCURA ATIVA",
        "badge_bg": BLUE_BG, "badge_border": BLUE_BORDER, "badge_txt": BLUE_TEXT,
        "title": "O Robô Varre as Melhores Vagas Remotas",
        "subtitle": "Monitora continuamente Greenhouse, Ashby, Himalayas e RemoteOK (+5.800 anúncios/dia)",
        "robot_pose": "search",
        "robot_x": 180, "robot_y": 200,
        "has_light": True
    },
    {
        "id": 1,
        "badge": "ETAPA 2 • FILTRO RÍGIDO",
        "badge_bg": ORANGE_BG, "badge_border": ORANGE_BORDER, "badge_txt": ORANGE_TEXT,
        "title": "Filtra e Descarta Falsos Positivos",
        "subtitle": "Elimina de imediato vagas híbridas, restritas a outros países ou com barreiras irreais",
        "robot_pose": "filter",
        "robot_x": 200, "robot_y": 200,
        "has_light": False
    },
    {
        "id": 2,
        "badge": "ETAPA 3 • CURRÍCULO ATS",
        "badge_bg": PURPLE_BG, "badge_border": PURPLE_BORDER, "badge_txt": PURPLE_TEXT,
        "title": "Cria o Currículo Perfeito em PDF (ATS)",
        "subtitle": "Reorganiza competências técnicas e alinha palavras-chave sem inventar nenhum fato",
        "robot_pose": "cv",
        "robot_x": 200, "robot_y": 200,
        "has_light": False
    },
    {
        "id": 3,
        "badge": "ETAPA 4 • CANDIDATURA SEGURA",
        "badge_bg": GREEN_BG, "badge_border": GREEN_BORDER, "badge_txt": GREEN_TEXT,
        "title": "Aplica com Controle e Segurança",
        "subtitle": "Modo automático ou aprovação prévia em 1 clique, com pausa ética em CAPTCHAs ou 2FA",
        "robot_pose": "apply",
        "robot_x": 200, "robot_y": 200,
        "has_light": False
    },
    {
        "id": 4,
        "badge": "ETAPA 5 • AUDITORIA NO GMAIL",
        "badge_bg": YELLOW_BG, "badge_border": YELLOW_BORDER, "badge_txt": YELLOW_TEXT,
        "title": "Audita Retornos e Conquista Entrevistas!",
        "subtitle": "Checagem diária às 18h via IA para capturar convites e atualizar o painel em tempo real",
        "robot_pose": "happy",
        "robot_x": 200, "robot_y": 200,
        "has_light": False
    }
]


def render_scene(scene_idx):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_MAIN)
    draw = ImageDraw.Draw(im)
    
    sc = SCENES[scene_idx]
    
    # 1. Top navigation
    draw_top_nav(draw, scene_idx)
    
    # 2. Main content container (Card clean)
    card_x, card_y, card_w, card_h = 30, 85, WIDTH - 60, 465
    draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=16, fill=WHITE, outline=BORDER_LIGHT, width=1)
    
    # Badge
    draw.rounded_rectangle((card_x + 30, card_y + 25, card_x + 225, card_y + 51), radius=7, fill=sc["badge_bg"], outline=sc["badge_border"], width=1)
    draw.text((card_x + 40, card_y + 31), sc["badge"], font=FONT_BADGE, fill=sc["badge_txt"])
    
    # Title & Subtitle
    draw.text((card_x + 30, card_y + 60), sc["title"], font=FONT_TITLE, fill=TEXT_MAIN)
    draw.text((card_x + 30, card_y + 90), sc["subtitle"], font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    # Left stage: Robot
    robot_x = card_x + 160
    robot_y = card_y + 140
    
    # Scene Specific Illustrations:
    if scene_idx == 0:
        # SCENE 1: SEARCH LIGHT BEAM & FLOATING JOBS
        light_orig = draw_cute_robot(draw, robot_x, robot_y, pose="search")
        lx, ly = light_orig
        
        # Draw translucent soft yellow/cyan cone of light
        beam_poly = [(lx, ly), (card_x + card_w - 50, card_y + 130), (card_x + card_w - 50, card_y + 390)]
        draw.polygon(beam_poly, fill=(254, 252, 232)) # Very soft warm beam
        draw.line([(lx, ly), (card_x + card_w - 50, card_y + 130)], fill=(254, 240, 138), width=2)
        draw.line([(lx, ly), (card_x + card_w - 50, card_y + 390)], fill=(254, 240, 138), width=2)
        
        # Re-draw robot over the light origin so it sits cleanly
        draw_cute_robot(draw, robot_x, robot_y, pose="search")
        
        # Floating Job Cards illuminated by the light
        jobs = [
            {"title": "Senior Python Backend Developer", "co": "TechCorp Global • Ashby API", "tag": "100% Remoto (Brasil)", "tag_col": GREEN_TEXT, "y": card_y + 150},
            {"title": "AI Agent & Evaluation Specialist", "co": "Innovate AI • Greenhouse API", "tag": "Salário em Dólar (USD)", "tag_col": BLUE_TEXT, "y": card_y + 230},
            {"title": "Data Analyst / Python Automation", "co": "FinTech Remote • RemoteOK", "tag": "Horário Flexível • PJ", "tag_col": PURPLE_TEXT, "y": card_y + 310}
        ]
        
        for j in jobs:
            jx = card_x + 440
            jy = j["y"]
            jw, jh = 460, 64
            # Illuminated card
            draw.rounded_rectangle((jx, jy, jx + jw, jy + jh), radius=10, fill=WHITE, outline=BLUE_BORDER, width=2)
            draw.text((jx + 16, jy + 14), j["title"], font=FONT_CARD_TITLE, fill=TEXT_MAIN)
            draw.text((jx + 16, jy + 34), j["co"], font=FONT_CARD_SUB, fill=TEXT_MUTED)
            # Tag pill
            draw.rounded_rectangle((jx + jw - 175, jy + 18, jx + jw - 15, jy + 44), radius=6, fill=GREEN_BG, outline=GREEN_BORDER, width=1)
            draw.text((jx + jw - 165, jy + 24), j["tag"], font=FONT_BADGE, fill=j["tag_col"])
            
    elif scene_idx == 1:
        # SCENE 2: FILTERING (DISCARD vs APPROVE)
        draw_cute_robot(draw, robot_x, robot_y, pose="filter")
        
        # Two columns on the right: Discarded (Red/Orange) vs Approved (Green)
        # Discard column
        dx, dy, dw, dh = card_x + 360, card_y + 150, 270, 230
        draw.rounded_rectangle((dx, dy, dx + dw, dy + dh), radius=12, fill=(255, 245, 245), outline=(254, 202, 202), width=1)
        draw.text((dx + 16, dy + 16), "❌ Descarte Automático", font=FONT_CARD_TITLE, fill=(220, 38, 38))
        draw.text((dx + 16, dy + 36), "Falsos positivos eliminados:", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        
        discards = [
            "• Híbrido / Presencial (SP/RJ)",
            "• Restrito a US / EU Citizens",
            "• Exige Bacharelado Obrigatório",
            "• Exige Inglês Nativo/Fluente"
        ]
        for idx_d, d_text in enumerate(discards):
            draw.text((dx + 16, dy + 68 + idx_d * 36), d_text, font=FONT_DESC, fill=(185, 28, 28))
            
        # Approved column
        ax, ay, aw, ah = card_x + 655, card_y + 150, 275, 230
        draw.rounded_rectangle((ax, ay, ax + aw, ay + ah), radius=12, fill=GREEN_BG, outline=GREEN_BORDER, width=2)
        draw.text((ax + 16, ay + 16), "✔ Aprovadas p/ Candidatura", font=FONT_CARD_TITLE, fill=GREEN_TEXT)
        draw.text((ax + 16, ay + 36), "100% aderentes ao perfil:", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        
        approves = [
            "✔ 100% Remoto (Home Office)",
            "✔ Residentes no Brasil Elegíveis",
            "✔ Avaliação por Experiência Real",
            "✔ Score de Aderência > 80%"
        ]
        for idx_a, a_text in enumerate(approves):
            draw.text((ax + 16, ay + 68 + idx_a * 36), a_text, font=FONT_DESC, fill=GREEN_TEXT)
            
    elif scene_idx == 2:
        # SCENE 3: RESUME GENERATION & ATS OPTIMIZATION
        draw_cute_robot(draw, robot_x, robot_y, pose="cv")
        
        # Realistic Clean Resume Sheet mockup on right
        rx, ry, rw, rh = card_x + 400, card_y + 140, 280, 260
        draw.rounded_rectangle((rx, ry, rx + rw, ry + rh), radius=8, fill=WHITE, outline=BORDER_DARK, width=2)
        
        # Resume header inside sheet
        draw.text((rx + 20, ry + 16), "CURRÍCULO PROFISSIONAL", font=FONT_BADGE, fill=TEXT_MUTED)
        draw.text((rx + 20, ry + 32), "Especialista em Python & IA", font=FONT_CARD_TITLE, fill=TEXT_MAIN)
        draw.line([(rx + 20, ry + 52), (rx + rw - 20, ry + 52)], fill=BORDER_LIGHT, width=1)
        
        # Resume content lines
        r_lines = [
            "Resumo: Automação, APIs REST e Agentes",
            "Competências: Python, FastAPI, Pandas, LLMs",
            "Experiência: Desenvolvimento de Soluções",
            "Projetos: Dashboards Quantitativos e Bots"
        ]
        for idx_r, r_t in enumerate(r_lines):
            draw.text((rx + 20, ry + 64 + idx_r * 28), r_t, font=FONT_CODE, fill=TEXT_MUTED)
            
        # ATS Stamp Badge
        stamp_x = rx + rw - 130
        stamp_y = ry + rh - 60
        draw.rounded_rectangle((stamp_x, stamp_y, stamp_x + 115, stamp_y + 44), radius=6, fill=GREEN_BG, outline=GREEN_TEXT, width=2)
        draw.text((stamp_x + 10, stamp_y + 8), "ATS APPROVED", font=FONT_BADGE, fill=GREEN_TEXT)
        draw.text((stamp_x + 18, stamp_y + 24), "Score: 92/100", font=FONT_BADGE, fill=GREEN_TEXT)
        
        # Explanatory card
        inf_x = card_x + 710
        draw.rounded_rectangle((inf_x, ry + 30, inf_x + 220, ry + 210), radius=12, fill=PURPLE_BG, outline=PURPLE_BORDER, width=1)
        draw.text((inf_x + 16, ry + 50), "Por que ATS?", font=FONT_CARD_TITLE, fill=PURPLE_TEXT)
        draw.text((inf_x + 16, ry + 78), "Robôs de triagem de RH\nexigem termos exatos\nda vaga.", font=FONT_DESC, fill=TEXT_MAIN)
        draw.text((inf_x + 16, ry + 140), "✔ Sem inventar fatos\n✔ PDF padronizado\n✔ Leitura imediata", font=FONT_DESC, fill=GREEN_TEXT)
        
    elif scene_idx == 3:
        # SCENE 4: SAFE SUBMISSION & ETHICAL HUMAN-IN-THE-LOOP
        draw_cute_robot(draw, robot_x, robot_y, pose="apply")
        
        # Flight path / dotted line for the paper airplane
        for dot_x in range(robot_x + 80, card_x + 480, 20):
            draw.ellipse((dot_x, card_y + 220, dot_x + 4, card_y + 224), fill=BORDER_DARK)
            
        # Submission status box
        sx, sy, sw, sh = card_x + 480, card_y + 150, 440, 230
        draw.rounded_rectangle((sx, sy, sx + sw, sy + sh), radius=12, fill=WHITE, outline=GREEN_BORDER, width=2)
        
        # Header of box
        draw.rounded_rectangle((sx + 16, sy + 16, sx + 220, sy + 44), radius=6, fill=GREEN_BG, outline=GREEN_BORDER, width=1)
        draw.text((sx + 26, sy + 22), "✔ Candidatura Realizada", font=FONT_BADGE, fill=GREEN_TEXT)
        
        draw.text((sx + 16, sy + 58), "Formulário oficial preenchido com sucesso", font=FONT_CARD_TITLE, fill=TEXT_MAIN)
        
        details = [
            "📄 Currículo PDF anexado exclusivamente para esta oportunidade",
            "🔒 Segurança Total: Pausa imediata se houver CAPTCHA ou 2FA",
            "📊 Status registrado em vagas.csv e candidaturas.csv",
            "⏱ Modo de Envio: Escolha entre Automático ou Aprovação Manual"
        ]
        for idx_dt, dt_text in enumerate(details):
            draw.text((sx + 16, sy + 90 + idx_dt * 30), dt_text, font=FONT_DESC, fill=TEXT_MUTED)
            
    elif scene_idx == 4:
        # SCENE 5: GMAIL AUDIT & CELEBRATION!
        draw_cute_robot(draw, robot_x, robot_y, pose="happy", eye_color=ROBOT_EYE_GREEN)
        
        # Golden envelope / interview invitation
        ix, iy, iw, ih = card_x + 390, card_y + 140, 400, 240
        draw.rounded_rectangle((ix, iy, ix + iw, iy + ih), radius=14, fill=YELLOW_BG, outline=YELLOW_BORDER, width=2)
        
        draw.rounded_rectangle((ix + 20, iy + 18, ix + 230, iy + 46), radius=6, fill=WHITE, outline=YELLOW_BORDER, width=1)
        draw.text((ix + 30, iy + 24), "📬 GMAIL • RETORNO DETECTADO", font=FONT_BADGE, fill=YELLOW_TEXT)
        
        draw.text((ix + 20, iy + 60), "Convite para Entrevista Técnica! 🎉", font=FONT_TITLE, fill=TEXT_MAIN)
        draw.text((ix + 20, iy + 92), "A inteligência artificial verificou seus e-mails às 18:00\ne identificou o avanço no processo seletivo.", font=FONT_SUBTITLE, fill=TEXT_MUTED)
        
        # KPI boxes inside celebration
        draw.rounded_rectangle((ix + 20, iy + 150, ix + 180, iy + 215), radius=8, fill=WHITE, outline=BORDER_LIGHT, width=1)
        draw.text((ix + 30, iy + 158), "Tempo Economizado", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        draw.text((ix + 30, iy + 178), "+20 horas/sem", font=FONT_KPI, fill=BLUE_TEXT)
        
        draw.rounded_rectangle((ix + 200, iy + 150, ix + 360, iy + 215), radius=8, fill=WHITE, outline=BORDER_LIGHT, width=1)
        draw.text((ix + 210, iy + 158), "Foco do Candidato", font=FONT_CARD_SUB, fill=TEXT_MUTED)
        draw.text((ix + 210, iy + 178), "100% Entrevistas", font=FONT_KPI, fill=GREEN_TEXT)
        
    # Bottom callout bar
    draw.rectangle((0, HEIGHT - 35, WIDTH, HEIGHT), fill=WHITE)
    draw.line((0, HEIGHT - 35, WIDTH, HEIGHT - 35), fill=BORDER_LIGHT, width=1)
    draw.text((35, HEIGHT - 26), "Job Hunter • Código Aberto no GitHub: https://github.com/160f/jobhunter", font=FONT_BADGE, fill=TEXT_MUTED)
    draw.text((WIDTH - 300, HEIGHT - 26), "Desenvolvido em Python + FastAPI + IA", font=FONT_BADGE, fill=BLUE_TEXT)
    
    return im


def main():
    frames = []
    durations = []
    
    for i in range(len(SCENES)):
        frame = render_scene(i)
        frames.append(frame)
        
        # Timing (in milliseconds)
        if i == 0:
            durations.append(3400) # Search light beam: 3.4s
        elif i == 4:
            durations.append(4000) # Final interview celebration: 4.0s
        else:
            durations.append(3000) # 3.0s each
            
    out_path = "jobhunter_robo_minimalista.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"GIF minimalista com robozinho gerado com sucesso: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    main()
