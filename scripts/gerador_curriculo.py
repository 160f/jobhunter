import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

class ResumePDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_auto_page_break(auto=True, margin=14)
        self.set_margins(16, 15, 16)
        
        # Carregar fontes TrueType do Windows para suporte UTF-8 pleno
        fonts_dir = r"C:\Windows\Fonts"
        self.add_font("Arial", "", os.path.join(fonts_dir, "arial.ttf"))
        self.add_font("Arial", "B", os.path.join(fonts_dir, "arialbd.ttf"))
        self.add_font("Arial", "I", os.path.join(fonts_dir, "ariali.ttf"))

    def header_title(self, name, headline, contact_items):
        self.set_font("Arial", "B", 18)
        self.set_text_color(15, 23, 42)
        self.cell(0, 8, name.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        if headline:
            self.set_font("Arial", "B", 11)
            self.set_text_color(37, 99, 235)
            self.cell(0, 6, headline, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
        self.set_font("Arial", "", 9)
        self.set_text_color(71, 85, 105)
        contact_str = "   |   ".join(contact_items)
        self.cell(0, 5, contact_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)
        
        # Linha horizontal sutil
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.4)
        self.line(self.get_x(), self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("Arial", "B", 10.5)
        self.set_text_color(15, 23, 42)
        self.cell(0, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.25)
        self.line(self.get_x(), self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def paragraph(self, text):
        self.set_font("Arial", "", 9.5)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 4.6, text)
        self.ln(2.5)

    def item_heading(self, role, company, period, location=""):
        self.set_font("Arial", "B", 9.5)
        self.set_text_color(15, 23, 42)
        self.cell(0, 4.8, f"{role} — {company}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.set_font("Arial", "I", 8.5)
        self.set_text_color(100, 116, 139)
        meta = period
        if location:
            meta += f" | {location}"
        self.cell(0, 4.2, meta, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def bullet(self, label, text):
        self.set_font("Arial", "B", 9)
        self.set_text_color(30, 41, 59)
        prefix = f"• {label}: " if label else "• "
        self.write(4.4, prefix)
        self.set_font("Arial", "", 9)
        self.set_text_color(51, 65, 85)
        self.write(4.4, text)
        self.ln(4.8)

def generate_custom_resume(data: dict, output_path: str):
    pdf = ResumePDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.header_title(
        name=data.get("name", "Seu Nome"),
        headline=data.get("headline", ""),
        contact_items=data.get("contacts", [
            "Sua Cidade, Estado, Brasil",
            "seu_email@exemplo.com",
            "+55 (XX) 99999-9999",
            "linkedin.com/in/seu-perfil"
        ])
    )
    
    # Seções
    sections = data.get("sections", [])
    for sec in sections:
        pdf.section_title(sec.get("title", ""))
        for p in sec.get("paragraphs", []):
            pdf.paragraph(p)
        for item in sec.get("items", []):
            pdf.item_heading(
                role=item.get("role", ""),
                company=item.get("company", ""),
                period=item.get("period", ""),
                location=item.get("location", "")
            )
            for b in item.get("bullets", []):
                pdf.bullet(b.get("label", ""), b.get("text", ""))
            pdf.ln(1.5)
        for b in sec.get("bullets", []):
            label = b.get("label", "")
            desc = b.get("text", "")
            pdf.bullet(label, desc)
        pdf.ln(2)
        
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    pdf.output(output_path)
    return output_path

if __name__ == "__main__":
    test_data = {
        "name": "Nome do Candidato",
        "headline": "Especialista em Automação, Python e Infraestrutura de TI",
        "contacts": [
            "Sua Cidade, Estado, Brasil",
            "seu_email@exemplo.com",
            "+55 (XX) 99999-9999",
            "linkedin.com/in/seu-perfil"
        ],
        "sections": [
            {
                "title": "Resumo Profissional",
                "paragraphs": [
                    "Profissional com trajetória sólida de 12 anos em Infraestrutura de TI e Suporte N2/N3 (2002–2014) e vivência contínua pós-2014 no mercado financeiro quantitativo, automações em Python, integração de APIs e engenharia de agentes de IA."
                ]
            },
            {
                "title": "Competências Principais",
                "bullets": [
                    {"label": "Linguagens & Automação", "text": "Python avançado, Scripts de automação, manipulação de dados, Playwright e Selenium."},
                    {"label": "APIs & Microsserviços", "text": "Integração REST, consumo assíncrono, autenticação e pipelines de dados."},
                    {"label": "Infraestrutura (2002–2014)", "text": "Windows Server, Linux, Active Directory, Redes, Virtualização VMware/Hyper-V e SQL Server."}
                ]
            }
        ]
    }
    out = generate_custom_resume(test_data, "curriculos/teste_geracao.pdf")
    print("Gerado com sucesso:", out)
