import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1060
HEIGHT = 640

# Fonts
FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)
FONT_SUBTITLE = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
FONT_HEADING = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 21)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
FONT_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 16)
FONT_BADGE = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 12)
FONT_CODE = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 14)
FONT_FLOW = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13)
FONT_FLOW_DESC = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 12)

# Colors
BG_DARK = (11, 15, 25)
PANEL_BG = (18, 25, 40)
CARD_BG = (23, 32, 51)
CARD_BORDER = (45, 62, 90)
CODE_BG = (12, 17, 28)
CODE_BORDER = (30, 42, 65)

COLOR_PRIMARY = (56, 189, 248)    # Sky blue
COLOR_SUCCESS = (16, 185, 129)    # Emerald green
COLOR_ACCENT = (129, 140, 248)    # Indigo
COLOR_WARNING = (245, 158, 11)   # Amber
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_DIM = (100, 116, 139)

STEPS = [
    {
        "num": 1,
        "title": "1. Clonar o Repositório do GitHub",
        "tag": "PASSO 1 • DOWNLOAD",
        "tag_color": COLOR_PRIMARY,
        "desc": [
            "Baixe o código-fonte limpo e estruturado diretamente do repositório.",
            "Contém o motor de busca, gerador de currículos e o painel web."
        ],
        "cmd_title": "Terminal (PowerShell / Bash) ou GitHub Desktop",
        "cmd": "git clone https://github.com/160f/jobhunter.git\ncd jobhunter",
        "tips": [
            "✔ Repositório público pronto para qualquer desenvolvedor.",
            "✔ Zero dependências pesadas ou APIs proprietárias obrigatórias."
        ],
        "flow_label": "1. Git Clone",
        "flow_sub": "Repositório GitHub"
    },
    {
        "num": 2,
        "title": "2. Ambiente & Dependências Python",
        "tag": "PASSO 2 • AMBIENTE",
        "tag_color": COLOR_ACCENT,
        "desc": [
            "Crie um ambiente virtual isolado para não misturar pacotes do sistema.",
            "Instale as bibliotecas essenciais para APIs, web e formatação de PDFs."
        ],
        "cmd_title": "Criação de venv & Instalação de requisitos",
        "cmd": "python -m venv venv\n.\\venv\\Scripts\\activate   # (No Linux/Mac: source venv/bin/activate)\npip install -r requirements.txt",
        "tips": [
            "✔ FastAPI + Uvicorn para o painel web responsivo.",
            "✔ Requests + Urllib para consultas assíncronas às APIs de vagas."
        ],
        "flow_label": "2. Ambiente Python",
        "flow_sub": "venv + requirements.txt"
    },
    {
        "num": 3,
        "title": "3. Arquivos Iniciais e Perfil do Candidato",
        "tag": "PASSO 3 • DADOS SEGUROS",
        "tag_color": COLOR_WARNING,
        "desc": [
            "Copie os modelos '.example' para gerar seus arquivos de dados locais.",
            "Preencha seu currículo real em 'perfil_cv_referencia.txt'."
        ],
        "cmd_title": "Cópia dos templates de exemplo",
        "cmd": "copy perfil_cv_referencia.example.txt perfil_cv_referencia.txt\ncopy config_painel.example.json config_painel.json\ncopy vagas.example.csv vagas.csv",
        "tips": [
            "🔒 100% SEGURO: Bloqueado no .gitignore (seus dados nunca sobem à nuvem).",
            "✔ Fonte única da verdade: currículos são gerados sem alucinações."
        ],
        "flow_label": "3. Perfil & Dados",
        "flow_sub": "Arquivos locais protegidos"
    },
    {
        "num": 4,
        "title": "4. Iniciar Painel & Configurar Visualmente",
        "tag": "PASSO 4 • INTERFACE WEB",
        "tag_color": COLOR_PRIMARY,
        "desc": [
            "Inicie o servidor local do painel interativo com apenas um comando.",
            "Acesse a aba 'Configurações' para ajustar tudo sem editar código ou JSON!"
        ],
        "cmd_title": "Executar Painel Web",
        "cmd": "python painel.py\n# Abra no navegador: http://localhost:8050",
        "tips": [
            "✔ Aba Configurações: selecione plataformas (Greenhouse, Ashby, Gupy...).",
            "✔ Defina cargos-alvo, regime CLT/PJ e horário da checagem diária."
        ],
        "flow_label": "4. Painel Web",
        "flow_sub": "http://localhost:8050"
    },
    {
        "num": 5,
        "title": "5. Execução: OpenBot + Gemini ou Standalone",
        "tag": "PASSO 5 • AUTOMAÇÃO INTELIGENTE",
        "tag_color": COLOR_SUCCESS,
        "desc": [
            "Escolha como operar: como agente autônomo com IA ou modo 100% autônomo local.",
            "Com OpenBot + Gemini, o agente audita e-mails e faz triagem semântica."
        ],
        "cmd_title": "Modo Agente no OpenBot ou Standalone",
        "cmd": "# Opção A (OpenBot): Criar Novo Agente -> Apontar pasta -> Modelo: Gemini\n# Opção B (Standalone): Disparar buscas direto pelos botões da aba Rotinas",
        "tips": [
            "✔ Rotinas diárias: 09h00 (Busca), 15h00 (Incremental) e 18h00 (E-mails).",
            "✔ Gemini conectado ao Gmail identifica convites e atualiza status no CSV."
        ],
        "flow_label": "5. IA & Execução",
        "flow_sub": "OpenBot Gemini / Standalone"
    },
    {
        "num": 6,
        "title": "Sistema Configurado & 100% Operacional!",
        "tag": "VISÃO GERAL • TUDO PRONTO",
        "tag_color": COLOR_SUCCESS,
        "desc": [
            "Parabéns! O Job Hunter está pronto para monitorar oportunidades remotas,",
            "filtrar vagas aderentes, gerar currículos em PDF e rastrear candidaturas."
        ],
        "cmd_title": "Ciclo Contínuo de Automação",
        "cmd": "1. Varredura Multi-API  ->  2. Triagem e Eliminação de Vagas Inválidas\n3. Geração de PDF sob medida  ->  4. Acompanhamento Diário via Painel/E-mail",
        "tips": [
            "✨ Projeto pronto para uso pessoal ou expansão com novas fontes de vagas.",
            "📊 Acompanhe tudo pelo Painel Web e pelas rotinas em segundo plano!"
        ],
        "flow_label": "Status Final",
        "flow_sub": "Operação Completa ✓"
    }
]

def draw_header(draw, active_step_idx):
    draw.rectangle((0, 0, WIDTH, 80), fill=(15, 21, 35))
    draw.line((0, 80, WIDTH, 80), fill=CARD_BORDER, width=1)
    
    # Logo / Badge
    draw.rounded_rectangle((28, 22, 160, 48), radius=6, fill=(30, 41, 59), outline=COLOR_PRIMARY, width=1)
    draw.text((38, 26), "JOB HUNTER", font=FONT_BADGE, fill=COLOR_PRIMARY)
    draw.text((122, 26), "v3.1", font=FONT_BADGE, fill=TEXT_MUTED)
    
    # Title
    draw.text((180, 18), "Fluxograma de Instalação & Configuração", font=FONT_TITLE, fill=TEXT_WHITE)
    draw.text((182, 50), "Do repositório GitHub ao agente autônomo com Gemini e painel web", font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    # Step counter pill
    step_num = min(active_step_idx + 1, 5)
    pill_text = f"ETAPA {step_num} DE 5" if active_step_idx < 5 else "CONCLUÍDO ✓"
    pill_color = COLOR_SUCCESS if active_step_idx >= 5 else COLOR_PRIMARY
    draw.rounded_rectangle((WIDTH - 170, 24, WIDTH - 30, 56), radius=16, fill=(20, 30, 48), outline=pill_color, width=1)
    draw.text((WIDTH - 152, 32), pill_text, font=FONT_BADGE, fill=pill_color)


def draw_left_card(draw, step, step_idx, fade_alpha=1.0):
    x, y, w, h = 30, 95, 640, 485
    
    # Main outer card
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=PANEL_BG, outline=CARD_BORDER, width=1)
    
    # Tag
    draw.rounded_rectangle((x + 20, y + 20, x + 200, y + 44), radius=6, fill=(24, 35, 54), outline=step["tag_color"], width=1)
    draw.text((x + 30, y + 25), step["tag"], font=FONT_BADGE, fill=step["tag_color"])
    
    # Step Title
    draw.text((x + 20, y + 54), step["title"], font=FONT_HEADING, fill=TEXT_WHITE)
    
    # Description lines
    cur_y = y + 92
    for line in step["desc"]:
        draw.text((x + 20, cur_y), line, font=FONT_BODY, fill=TEXT_MUTED)
        cur_y += 22
        
    # Code / Terminal Box
    cur_y += 10
    code_h = 160
    draw.rounded_rectangle((x + 20, cur_y, x + w - 20, cur_y + code_h), radius=8, fill=CODE_BG, outline=CODE_BORDER, width=1)
    
    # Code header bar
    draw.rectangle((x + 20, cur_y, x + w - 20, cur_y + 28), fill=(20, 27, 42))
    draw.ellipse((x + 32, cur_y + 9, x + 42, cur_y + 19), fill=(239, 68, 68))
    draw.ellipse((x + 48, cur_y + 9, x + 58, cur_y + 19), fill=(245, 158, 11))
    draw.ellipse((x + 64, cur_y + 9, x + 74, cur_y + 19), fill=(16, 185, 129))
    draw.text((x + 88, cur_y + 6), step["cmd_title"], font=FONT_BADGE, fill=TEXT_MUTED)
    
    # Code contents
    cmd_lines = step["cmd"].split("\n")
    code_y = cur_y + 38
    for cl in cmd_lines:
        prefix = "$ " if not cl.startswith("#") else ""
        col = COLOR_PRIMARY if not cl.startswith("#") else TEXT_DIM
        draw.text((x + 32, code_y), prefix + cl, font=FONT_CODE, fill=col)
        code_y += 24
        
    # Tips / Key items
    cur_y = cur_y + code_h + 16
    for tip in step["tips"]:
        col = COLOR_SUCCESS if ("✔" in tip or "✨" in tip or "🔒" in tip) else TEXT_MUTED
        draw.text((x + 24, cur_y), tip, font=FONT_BODY, fill=col)
        cur_y += 26


def draw_right_flowchart(draw, active_step_idx):
    x, y, w, h = 690, 95, 340, 485
    
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=PANEL_BG, outline=CARD_BORDER, width=1)
    draw.text((x + 20, y + 16), "ETAPAS DO FLUXO", font=FONT_BOLD, fill=TEXT_WHITE)
    draw.text((x + 20, y + 36), "Progresso da configuração", font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    start_y = y + 68
    node_h = 64
    gap = 14
    
    for i in range(5):
        ny = start_y + i * (node_h + gap)
        step_data = STEPS[i]
        
        is_done = (i < active_step_idx) or (active_step_idx == 5)
        is_current = (i == active_step_idx)
        
        if is_current:
            bg_col = (28, 42, 68)
            border_col = COLOR_PRIMARY
            border_w = 2
            icon_char = "▶"
            icon_color = COLOR_PRIMARY
            text_col = TEXT_WHITE
        elif is_done:
            bg_col = (20, 36, 32)
            border_col = COLOR_SUCCESS
            border_w = 1
            icon_char = "✓"
            icon_color = COLOR_SUCCESS
            text_col = TEXT_WHITE
        else:
            bg_col = (16, 22, 34)
            border_col = (35, 48, 70)
            border_w = 1
            icon_char = str(i + 1)
            icon_color = TEXT_DIM
            text_col = TEXT_MUTED
            
        if i > 0:
            line_y1 = ny - gap
            line_y2 = ny
            line_col = COLOR_SUCCESS if (i <= active_step_idx or active_step_idx == 5) else (35, 48, 70)
            draw.line((x + 40, line_y1, x + 40, line_y2), fill=line_col, width=2)
            
        draw.rounded_rectangle((x + 16, ny, x + w - 16, ny + node_h), radius=8, fill=bg_col, outline=border_col, width=border_w)
        circ_x = x + 40
        circ_y = ny + 32
        draw.ellipse((circ_x - 14, circ_y - 14, circ_x + 14, circ_y + 14), fill=(12, 18, 28), outline=border_col, width=1)
        draw.text((circ_x - 5, circ_y - 8), icon_char, font=FONT_FLOW, fill=icon_color)
        draw.text((x + 68, ny + 14), step_data["flow_label"], font=FONT_FLOW, fill=text_col)
        draw.text((x + 68, ny + 34), step_data["flow_sub"], font=FONT_FLOW_DESC, fill=TEXT_MUTED)


def draw_footer_progress(draw, progress_ratio, is_complete=False):
    y = 595
    draw.rectangle((0, y, WIDTH, HEIGHT), fill=(13, 18, 30))
    draw.line((0, y, WIDTH, y), fill=CARD_BORDER, width=1)
    
    bar_w = int((WIDTH - 60) * min(1.0, max(0.05, progress_ratio)))
    draw.rounded_rectangle((30, y + 16, WIDTH - 30, y + 26), radius=5, fill=(24, 32, 48))
    draw.rounded_rectangle((30, y + 16, 30 + bar_w, y + 26), radius=5, fill=COLOR_SUCCESS if is_complete else COLOR_PRIMARY)
    
    percent_str = f"Progresso: {int(progress_ratio * 100)}%"
    draw.text((32, y + 2), percent_str, font=FONT_BADGE, fill=COLOR_SUCCESS if is_complete else COLOR_PRIMARY)
    draw.text((WIDTH - 440, y + 2), "Dica: O painel em http://localhost:8050 permite configurar tudo sem editar JSON", font=FONT_BADGE, fill=TEXT_MUTED)


def render_frame(step_idx, progress_ratio=None):
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(im)
    
    if progress_ratio is None:
        progress_ratio = min(1.0, (step_idx + 1) / 5.0) if step_idx < 5 else 1.0
        
    is_complete = (step_idx >= 5)
    
    draw_header(draw, step_idx)
    draw_left_card(draw, STEPS[step_idx], step_idx)
    draw_right_flowchart(draw, step_idx)
    draw_footer_progress(draw, progress_ratio, is_complete)
    
    return im


def main():
    frames = []
    durations = []
    
    for i in range(len(STEPS)):
        base_ratio = min(1.0, (i + 1) / 5.0) if i < 5 else 1.0
        frame = render_frame(i, base_ratio)
        frames.append(frame)
        
        # Timing
        if i == len(STEPS) - 1:
            durations.append(3800) # Final summary frame: 3.8s
        elif i == 4:
            durations.append(3200) # Gemini frame: 3.2s
        else:
            durations.append(2800) # Regular frames: 2.8s
            
        # Add transition frame between steps
        if i < len(STEPS) - 1:
            next_ratio = min(1.0, (i + 1.5) / 5.0)
            mid_frame = render_frame(i, next_ratio)
            frames.append(mid_frame)
            durations.append(250) # Fast transition frame
            
    out_path = "fluxograma_instalacao.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"GIF animado gerado com sucesso: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    main()
