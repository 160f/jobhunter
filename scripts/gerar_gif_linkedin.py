import os
from PIL import Image, ImageDraw, ImageFont

# 16:9 widescreen format ideal for LinkedIn feed (1120 x 630)
WIDTH = 1120
HEIGHT = 630

# Load fonts
FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 25)
FONT_SUBTITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 14)
FONT_HEADING = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
FONT_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 15)
FONT_BADGE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 11)
FONT_CODE = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 13)
FONT_FLOW = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
FONT_FLOW_SUB = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 11)
FONT_BIG_KPI = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 28)

# Palette (Dark tech theme with vibrant accents)
BG_COLOR = (10, 14, 23)
HEADER_BG = (15, 21, 35)
CARD_BG = (19, 27, 44)
CARD_BORDER = (42, 58, 86)
BOX_BG = (13, 19, 32)
BOX_BORDER = (30, 44, 70)

COLOR_PRIMARY = (56, 189, 248)    # Cyan / Sky
COLOR_SUCCESS = (16, 185, 129)    # Emerald
COLOR_PURPLE = (168, 85, 247)     # Violet
COLOR_ORANGE = (249, 115, 22)     # Orange
COLOR_AMBER = (245, 158, 11)      # Amber

TEXT_MAIN = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_DIM = (100, 116, 139)

STEPS = [
    {
        "num": 1,
        "badge": "ETAPA 1 • PROCURA AUTOMÁTICA",
        "badge_color": COLOR_PRIMARY,
        "title": "Varredura Contínua em Múltiplas APIs",
        "subtitle": "Monitoramento inteligente em tempo real sem scraping intrusivo",
        "bullets": [
            "Conexão direta a APIs oficiais: Greenhouse, Ashby, Himalayas, RemoteOK e Jobicy.",
            "Varreduras agendadas (09h00 matinal e 15h00 incremental) para pegar vagas recém-abertas.",
            "Eliminação instantânea de duplicatas por identificador único de anúncio."
        ],
        "kpi_label": "Volume de Anúncios Monitorados",
        "kpi_val": "+5.800 vagas/dia",
        "box_title": "RADAR DE ENTRADA (APIs PÚBLICAS)",
        "box_lines": [
            "✔ Ashby API: Vagas internacionais remotas de alta tecnologia",
            "✔ Greenhouse API: Engenharia de software, dados e avaliação de IA",
            "✔ RemoteOK & Himalayas: Contratos globais em dólar (USD/EUR)"
        ],
        "step_icon": "1",
        "step_name": "Busca Multi-API",
        "step_desc": "Coleta contínua"
    },
    {
        "num": 2,
        "badge": "ETAPA 2 • PRÉ-FILTRAGEM ELIMINATÓRIA",
        "badge_color": COLOR_ORANGE,
        "title": "Filtros Rígidos contra Falsos Positivos",
        "subtitle": "Descarte automático de vagas inviáveis antes de gastar recursos",
        "bullets": [
            "100% Remoto Obrigatório: Qualquer menção a modelo híbrido/presencial é eliminada.",
            "Elegibilidade Geográfica: Descarta vagas restritas a residentes dos EUA, UE ou Canadá.",
            "Barreiras Realistas: Remove exigências de inglês fluente nativo e diplomas formais obrigatórios."
        ],
        "kpi_label": "Eficiência de Filtragem",
        "kpi_val": "98% descartadas",
        "box_title": "CRITÉRIOS DE ELIMINAÇÃO RÍGIDA",
        "box_lines": [
            "❌ Híbrido / Presencial / On-site  ->  DESCARTADA",
            "❌ Restrito a US/EU Citizen Only   ->  DESCARTADA",
            "❌ Exige Bacharelado Obrigatório   ->  DESCARTADA",
            "✔ 100% Remoto + Aceita Brasil     ->  APROVADA P/ TRIAGEM"
        ],
        "step_icon": "2",
        "step_name": "Filtros Rígidos",
        "step_desc": "Zero falsos positivos"
    },
    {
        "num": 3,
        "badge": "ETAPA 3 • TRIAGEM SEMÂNTICA & SCORE",
        "badge_color": COLOR_PURPLE,
        "title": "Avaliação de Aderência com IA (Score 0-100)",
        "subtitle": "Cruzamento profundo de requisitos mandatórios com o perfil real",
        "bullets": [
            "Fonte única da verdade: perfil de referência do candidato (zero alucinações).",
            "Cálculo objetivo de aderência técnica (Python, APIs, automação, IA, dados).",
            "Classificação automática: ALTA COMPATIBILIDADE, PENDENTE ou INCOMPATÍVEL."
        ],
        "kpi_label": "Precisão de Compatibilidade",
        "kpi_val": "Score 0 a 100",
        "box_title": "AVALIAÇÃO COGNITIVA DA VAGA",
        "box_lines": [
            "• Requisitos: Python backend, APIs REST, prompts com LLM",
            "• Histórico do Candidato: 100% alinhado às experiências práticas",
            "• Diagnóstico: ALTA ADERÊNCIA (Score: 88/100) -> Avançar p/ Currículo"
        ],
        "step_icon": "3",
        "step_name": "Triagem com IA",
        "step_desc": "Score de aderência"
    },
    {
        "num": 4,
        "badge": "ETAPA 4 • GERAÇÃO DE CURRÍCULO ATS",
        "badge_color": COLOR_PRIMARY,
        "title": "Currículo em PDF Customizado sob Medida",
        "subtitle": "Formatação perfeita para leitura automática por robôs de RH (ATS)",
        "bullets": [
            "Alinhamento terminológico com a oportunidade sem alterar nenhum fato real.",
            "Geração dinâmica em PDF no idioma exato da vaga (Português ou Inglês).",
            "Armazenamento seguro com versionamento rastreável por ID de oportunidade."
        ],
        "kpi_label": "Otimização para ATS",
        "kpi_val": "100% Leitura ATS",
        "box_title": "MOTOR DE GERAÇÃO DINÂMICA (PDF)",
        "box_lines": [
            "✔ Resumo profissional alinhado à stack da vaga",
            "✔ Competências reorganizadas para destacar palavras-chave essenciais",
            "✔ PDF padronizado gerado em milissegundos na pasta local"
        ],
        "step_icon": "4",
        "step_name": "Currículo ATS",
        "step_desc": "PDF personalizado"
    },
    {
        "num": 5,
        "badge": "ETAPA 5 • CANDIDATURA SEGURA & CONTROLE",
        "badge_color": COLOR_SUCCESS,
        "title": "Envio Inteligente com Segurança Ética",
        "subtitle": "Modo Automático ou Aprovação Manual com intervenção humana",
        "bullets": [
            "Modo Flexível: Usuário escolhe entre aprovação prévia em 1 clique ou envio autônomo.",
            "Pausa Ética Imediata: Interrompe e chama o usuário em CAPTCHAs, 2FA ou perguntas inéditas.",
            "Registro completo do ciclo de vida em banco de dados e planilhas de acompanhamento."
        ],
        "kpi_label": "Controle e Segurança",
        "kpi_val": "Human-in-the-Loop",
        "box_title": "POLÍTICA DE PROTEÇÃO AO CANDIDATO",
        "box_lines": [
            "✔ Anexo automático do currículo exclusivo gerado para a vaga",
            "🔒 NUNCA quebra regras de sites nem burla verificações de segurança",
            "✔ Status atualizado: NOVA -> ANALISADA -> ENVIADA"
        ],
        "step_icon": "5",
        "step_name": "Candidatura",
        "step_desc": "Envio ético e seguro"
    },
    {
        "num": 6,
        "badge": "ETAPA 6 • AUDITORIA DE RETORNOS & DASHBOARD",
        "badge_color": COLOR_AMBER,
        "title": "Auditoria de E-mails & Painel em Tempo Real",
        "subtitle": "Rastreamento diário de convites para entrevista e métricas de conversão",
        "bullets": [
            "Checagem diária às 18h00 no Gmail via IA para capturar convites e respostas.",
            "Painel web interativo (FastAPI): gráficos de funil, radar de vagas e controle de rotinas.",
            "Histórico completo mantido localmente sem expor dados pessoais à nuvem."
        ],
        "kpi_label": "Ciclo Fechado",
        "kpi_val": "Até a Entrevista",
        "box_title": "PAINEL WEB & ACOMPANHAMENTO DIÁRIO",
        "box_lines": [
            "📬 18:00 - IA audita Gmail por 'interview', 'processo seletivo' ou rejeições",
            "📊 Dashboard ao vivo em http://localhost:8050 com métricas e KPIs",
            "🎯 Resultado: Mais entrevistas agendadas com menor esforço repetitivo"
        ],
        "step_icon": "6",
        "step_name": "Acompanhamento",
        "step_desc": "Gmail + Dashboard"
    },
    {
        "num": 7,
        "badge": "VISÃO GERAL • ARQUITETURA COMPLETA",
        "badge_color": COLOR_SUCCESS,
        "title": "Job Hunter: Autonomia, Precisão e Ética",
        "subtitle": "A ponte inteligente entre o candidato e as melhores vagas remotas",
        "bullets": [
            "1. Busca Contínua  ->  2. Filtro Rígido  ->  3. IA Avalia Aderência",
            "4. Gera CV Sob Medida  ->  5. Aplica com Segurança  ->  6. Audita Retornos",
            "Projeto de código aberto com arquitetura modular: funciona com OpenBot ou Standalone!"
        ],
        "kpi_label": "Tempo Economizado",
        "kpi_val": "+20h por semana",
        "box_title": "PRONTO PARA USO & DISPONÍVEL NO GITHUB",
        "box_lines": [
            "⭐ GitHub: github.com/160f/jobhunter",
            "🚀 100% Python | Painel Web FastAPI | Integração com Gemini",
            "💼 Menos tempo preenchendo formulários, foco total nas entrevistas!"
        ],
        "step_icon": "✓",
        "step_name": "Pipeline Total",
        "step_desc": "Operação 100% pronta"
    }
]

def draw_header(draw, active_idx):
    # Header box
    draw.rectangle((0, 0, WIDTH, 75), fill=HEADER_BG)
    draw.line((0, 75, WIDTH, 75), fill=CARD_BORDER, width=1)
    
    # Brand Pill
    draw.rounded_rectangle((24, 18, 175, 48), radius=6, fill=(26, 36, 56), outline=COLOR_PRIMARY, width=1)
    draw.text((34, 22), "⚡ JOB HUNTER", font=FONT_BADGE, fill=COLOR_PRIMARY)
    draw.text((128, 22), "AI AGENT", font=FONT_BADGE, fill=COLOR_SUCCESS)
    
    # Title & subtitle
    draw.text((195, 14), "Como Funciona o Agente Autônomo de Vagas", font=FONT_TITLE, fill=TEXT_MAIN)
    draw.text((197, 46), "Do radar de oportunidades até o convite para entrevista • Pipeline 100% automatizado", font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    # Indicator pill
    step_str = f"PASSO {active_idx + 1} DE 6" if active_idx < 6 else "PIPELINE COMPLETO ✓"
    color = COLOR_SUCCESS if active_idx == 6 else COLOR_PRIMARY
    draw.rounded_rectangle((WIDTH - 195, 20, WIDTH - 25, 52), radius=16, fill=(22, 32, 50), outline=color, width=1)
    draw.text((WIDTH - 178, 28), step_str, font=FONT_BADGE, fill=color)


def draw_main_card(draw, step):
    x, y, w, h = 25, 90, 715, 480
    
    # Main outer card
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=CARD_BG, outline=CARD_BORDER, width=1)
    
    # Category Tag
    draw.rounded_rectangle((x + 20, y + 18, x + 235, y + 42), radius=6, fill=(25, 36, 56), outline=step["badge_color"], width=1)
    draw.text((x + 28, y + 23), step["badge"], font=FONT_BADGE, fill=step["badge_color"])
    
    # KPI callout box (Top right of card)
    kpi_w, kpi_h = 200, 56
    kpi_x = x + w - kpi_w - 20
    kpi_y = y + 16
    draw.rounded_rectangle((kpi_x, kpi_y, kpi_x + kpi_w, kpi_y + kpi_h), radius=8, fill=BOX_BG, outline=step["badge_color"], width=1)
    draw.text((kpi_x + 12, kpi_y + 8), step["kpi_label"], font=FONT_BADGE, fill=TEXT_MUTED)
    draw.text((kpi_x + 12, kpi_y + 24), step["kpi_val"], font=FONT_BIG_KPI, fill=step["badge_color"])
    
    # Main Title & Subtitle
    draw.text((x + 20, y + 54), step["title"], font=FONT_HEADING, fill=TEXT_MAIN)
    draw.text((x + 20, y + 84), step["subtitle"], font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    # Bullet points
    cur_y = y + 116
    for b in step["bullets"]:
        draw.text((x + 24, cur_y), "▸", font=FONT_BOLD, fill=step["badge_color"])
        draw.text((x + 42, cur_y), b, font=FONT_BODY, fill=TEXT_MAIN)
        cur_y += 26
        
    # Terminal / Demonstration Box
    cur_y += 12
    box_h = 160
    draw.rounded_rectangle((x + 20, cur_y, x + w - 20, cur_y + box_h), radius=8, fill=BOX_BG, outline=BOX_BORDER, width=1)
    
    # Box header
    draw.rectangle((x + 20, cur_y, x + w - 20, cur_y + 28), fill=(22, 30, 48))
    draw.ellipse((x + 32, cur_y + 9, x + 42, cur_y + 19), fill=(239, 68, 68))
    draw.ellipse((x + 48, cur_y + 9, x + 58, cur_y + 19), fill=(245, 158, 11))
    draw.ellipse((x + 64, cur_y + 9, x + 74, cur_y + 19), fill=(16, 185, 129))
    draw.text((x + 88, cur_y + 6), step["box_title"], font=FONT_BADGE, fill=TEXT_MUTED)
    
    # Lines inside box
    line_y = cur_y + 38
    for bl in step["box_lines"]:
        col = COLOR_PRIMARY if "✔" in bl else (COLOR_SUCCESS if "APROVADA" in bl or "Score" in bl or "GitHub" in bl else (COLOR_ORANGE if "❌" in bl else TEXT_MAIN))
        draw.text((x + 30, line_y), bl, font=FONT_CODE, fill=col)
        line_y += 26


def draw_side_pipeline(draw, active_idx):
    x, y, w, h = 760, 90, 335, 480
    
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((x + 18, y + 16), "PIPELINE EM EXECUÇÃO", font=FONT_BOLD, fill=TEXT_MAIN)
    draw.text((x + 18, y + 36), "Fluxo passo a passo do agente", font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    start_y = y + 64
    node_h = 56
    gap = 10
    
    for i in range(6):
        ny = start_y + i * (node_h + gap)
        step_meta = STEPS[i]
        
        is_done = (i < active_idx) or (active_idx == 6)
        is_current = (i == active_idx)
        
        if is_current:
            bg_col = (28, 44, 72)
            border_col = step_meta["badge_color"]
            border_w = 2
            icon_char = "▶"
            icon_color = step_meta["badge_color"]
            text_col = TEXT_MAIN
        elif is_done:
            bg_col = (18, 36, 32)
            border_col = COLOR_SUCCESS
            border_w = 1
            icon_char = "✓"
            icon_color = COLOR_SUCCESS
            text_col = TEXT_MAIN
        else:
            bg_col = (14, 20, 32)
            border_col = (36, 50, 72)
            border_w = 1
            icon_char = str(i + 1)
            icon_color = TEXT_DIM
            text_col = TEXT_MUTED
            
        # Connecting line
        if i > 0:
            line_y1 = ny - gap
            line_y2 = ny
            line_col = COLOR_SUCCESS if (i <= active_idx or active_idx == 6) else (36, 50, 72)
            draw.line((x + 36, line_y1, x + 36, line_y2), fill=line_col, width=2)
            
        # Box
        draw.rounded_rectangle((x + 14, ny, x + w - 14, ny + node_h), radius=8, fill=bg_col, outline=border_col, width=border_w)
        
        # Circle icon
        circ_x = x + 36
        circ_y = ny + 28
        draw.ellipse((circ_x - 13, circ_y - 13, circ_x + 13, circ_y + 13), fill=(10, 16, 26), outline=border_col, width=1)
        draw.text((circ_x - 5, circ_y - 8), icon_char, font=FONT_FLOW, fill=icon_color)
        
        # Text labels
        draw.text((x + 62, ny + 12), step_meta["step_name"], font=FONT_FLOW, fill=text_col)
        draw.text((x + 62, ny + 30), step_meta["step_desc"], font=FONT_FLOW_SUB, fill=TEXT_MUTED)


def draw_footer_progress(draw, active_idx):
    y = 585
    draw.rectangle((0, y, WIDTH, HEIGHT), fill=(12, 17, 28))
    draw.line((0, y, WIDTH, y), fill=CARD_BORDER, width=1)
    
    ratio = min(1.0, (active_idx + 1) / 6.0) if active_idx < 6 else 1.0
    bar_w = int((WIDTH - 50) * ratio)
    
    draw.rounded_rectangle((25, y + 18, WIDTH - 25, y + 27), radius=4, fill=(24, 32, 48))
    draw.rounded_rectangle((25, y + 18, 25 + bar_w, y + 27), radius=4, fill=COLOR_SUCCESS if active_idx == 6 else COLOR_PRIMARY)
    
    draw.text((28, y + 3), f"Status da Automação: {int(ratio * 100)}%", font=FONT_BADGE, fill=COLOR_SUCCESS if active_idx == 6 else COLOR_PRIMARY)
    draw.text((WIDTH - 420, y + 3), "Open Source no GitHub: https://github.com/160f/jobhunter", font=FONT_BADGE, fill=TEXT_MUTED)


def render_linkedin_frame(idx):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)
    
    draw_header(draw, idx)
    draw_main_card(draw, STEPS[idx])
    draw_side_pipeline(draw, idx)
    draw_footer_progress(draw, idx)
    
    return im


def main():
    frames = []
    durations = []
    
    for i in range(len(STEPS)):
        frame = render_linkedin_frame(i)
        frames.append(frame)
        
        # Timing optimized for LinkedIn readability
        if i == len(STEPS) - 1:
            durations.append(4200) # Finale slide: 4.2 seconds
        elif i in [2, 3, 4]:
            durations.append(3400) # Core AI, CV and Apply steps: 3.4 seconds
        else:
            durations.append(3000) # Search & filter steps: 3.0 seconds
            
    out_path = "jobhunter_linkedin_demo.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"GIF para LinkedIn gerado com sucesso: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    main()
