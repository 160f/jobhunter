"""Job Hunter v3 - coletor Greenhouse com triagem conservadora, sem IA.

- Não modifica vagas.csv nem candidaturas_acompanhamento.csv.
- Elimina especializações incompatíveis (CAD, engenharia não-TI, VFX, etc.).
- Elimina exigências obrigatórias de idiomas não dominados (candidato: PT nativo, ES intermediário, EN básico).
- Não categoriza apenas por menção acidental de Python/IA/suporte no corpo: exige aderência no título.
- Prioriza suporte técnico, infraestrutura, administração de sistemas, suporte remoto, Customer Support técnico, Python e avaliação de IA em português.
- Deduplica vagas equivalentes por empresa e cargo normalizado.
- Limita a 2 vagas por empresa e 2 por categoria quando houver alternativas qualificadas.
- O script não faz chamadas ao Gemini.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

BOARDS = ("rdstation", "quintoandar", "agency", "prolificacademicltd", "vtex", "ebanx")
WORKSPACE = Path(__file__).resolve().parent.parent
HISTORY = WORKSPACE / "vagas.csv"
OUTPUT = WORKSPACE / "job_hunter_pre_filtradas.json"
MAX_VAGAS = 5
PROFILE_PATH = Path(__file__).resolve().parent / "perfil_job_hunter.json"

# Prioridades estritas: experiência em TI (2002-2014) em suporte e infraestrutura,
# e pós-2014 em Python, automação e avaliação de IA em português.
CATEGORY_BONUS = {
    "Suporte Técnico N2/N3 / Aplicações": 35,
    "Infraestrutura / Servidores / Redes": 35,
    "Customer Support Técnico / SaaS": 25,
    "Python / Automação / Dados": 20,
    "AI Training / Evaluation": 18,
    "Customer Success / Onboarding": 12,
    "Customer Support / Atendimento": 10,
}

CATEGORIES = (
    ("Suporte Técnico N2/N3 / Aplicações", (
        r"\bit support\b", r"\btechnical support(?: (?:specialist|engineer|analyst))?\b",
        r"\bsupport engineer\b", r"\bapplication support\b", r"\bhelp[ -]?desk\b",
        r"\bservice desk\b", r"\bsuporte t[eé]cnico\b", r"\banalista de suporte\b",
        r"\bsuporte (?:n[123]|n[ií]vel [123])\b", r"\banalista de sustenta[cç][aã]o\b",
        r"\bsoporte t[eé]cnico\b", r"\bremote (?:it )?support\b",
        r"\btech support\b",
    )),
    ("Infraestrutura / Servidores / Redes", (
        r"\binfrastructure (?:analyst|engineer|specialist|support)\b", r"\bit infrastructure\b",
        r"\b(?:systems?|server|network) administrator\b", r"\bsysadmin\b",
        r"\b(?:windows|linux) administrator\b", r"\bit operations\b",
        r"\bnetwork (?:analyst|engineer|support)\b",
        r"\banalista de infraestrutura\b", r"\badministrador(?:a)? de (?:sistemas|servidores|redes)\b",
        r"\banalista de redes\b", r"\b(?:windows server|active directory|vmware|hyper[ -]?v)\b",
        r"\badministra[cç][aã]o de servidores\b",
    )),
    ("Customer Support Técnico / SaaS", (
        r"\bsaas support\b", r"\bproduct support\b", r"\btechnical customer support\b",
        r"\bcustomer support engineer\b", r"\bcustomer technical support\b",
        r"\bsaas support specialist\b", r"\bproduct support specialist\b",
        r"\bsoporte (?:de|al) producto\b", r"\bsuporte ao produto\b",
    )),
    ("Python / Automação / Dados", (
        r"\bpython\b", r"\bautomation (?:engineer|developer|specialist)\b",
        r"\bautomacao\b", r"\bautomatizacion\b", r"\bdata analyst\b",
        r"\banalista de dados\b", r"\banalista de datos\b",
        r"\bagent(?:ic)? (?:engineer|developer)\b", r"\bapi integration\b",
    )),
    ("AI Training / Evaluation", (
        r"\bai (?:trainer|evaluator|training|annotator|specialist)\b",
        r"\bllm (?:evaluator|trainer|annotator)\b", r"\bdata annotat",
        r"\bmodel evaluation\b", r"\bavaliador(?:a)? de (?:ia|inteligencia artificial)\b",
        r"\bevaluador(?:a)? de (?:ia|inteligencia artificial)\b",
    )),
    ("Customer Success / Onboarding", (
        r"\bcustomer success\b", r"\bcustomer onboarding\b",
        r"\bsucesso do cliente\b", r"\bimplantacao\b",
        r"\bimplementacion\b", r"\bonboarding specialist\b",
    )),
    ("Customer Support / Atendimento", (
        r"\bcustomer support\b", r"\bcustomer service\b",
        r"\batendimento ao cliente\b", r"\bsuporte ao cliente\b",
        r"\batencion al cliente\b", r"\bchat support\b",
        r"\bcustomer experience\b",
    )),
)

# Idiomas não dominados pelo candidato (domina apenas Português nativo, Espanhol intermediário, Inglês básico)
INCOMPATIBLE_LANGUAGES = (
    r"\b(japanese|japones|japonesa|nihongo)\b",
    r"\b(german|alemao|alema|deutsch)\b",
    r"\b(french|frances|francesa|francais)\b",
    r"\b(chinese|mandarin|mandarim|chines|chinesa)\b",
    r"\b(italian|italiano|italiana)\b",
    r"\b(russian|russo|russa)\b",
    r"\b(korean|coreano|coreana)\b",
    r"\b(arabic|arabe)\b",
    r"\b(dutch|holandes|holandesa|nederlands)\b",
    r"\b(swedish|sueco|sueca)\b",
    r"\b(polish|polones|polonesa)\b",
    r"\b(turkish|turco|turca)\b",
    r"\b(hindi|bengali|urdu|punjabi|tamil|telugu|marathi)\b",
    r"\b(czech|tcheco|danish|dinamarques|finnish|finlandes|hungarian|hungaro|norwegian|noruegues)\b",
    r"\b(hebrew|hebraico|indonesian|indonesio|tagalog|filipino|vietnamese|vietnamita|thai|tailandes)\b",
    r"\b(amharic|azerbaijani|belarusian|catalan|gujarati|haitian|icelandic|kazakh|latvian|lithuanian|macedonian|maori)\b",
    r"\b(kabuverdianu|kaqchikel|khmer|k'iche'|kinyarwanda|kyrgyz|fulah|galician|georgian|guarani|hausa|afrikaans|albanian|asturian)\b",
    r"\b(bilingual|trilingual|bilíngue|bilingue|trilíngue|trilingue)\b",
)

# Especializações incompatíveis com o perfil do candidato
INCOMPATIBLE_DOMAINS = (
    # Engenharia tradicional não-TI / CAD / Design / VFX / 3D / Áudio / Vídeo
    r"\b(electrical engineer(?:ing)?|engenharia el[eé]trica|engenheiro eletricista|engenheiro el[eé]trico)\b",
    r"\b(electronic(?:s)? engineer(?:ing)?|engenharia eletr[oô]nica|engenheiro eletr[oô]nico)\b",
    r"\b(civil engineer(?:ing)?|engenharia civil|engenheiro civil)\b",
    r"\b(mechanical engineer(?:ing)?|engenharia mec[aâ]nica|engenheiro mec[aâ]nico)\b",
    r"\b(chemical engineer(?:ing)?|engenharia qu[ií]mica|engenheiro qu[ií]mico)\b",
    r"\b(cad\b|autocad|solidworks|revit|bim\b)\b",
    r"\b(vfx\b|visual effects|3d artist|cgi\b|game artist|animat(?:or|ion)|3d model(?:ing)?)\b",
    r"\b(graphic designer|designer gr[aá]fico|art director|diretor de arte|illustrat(?:or|ion)|motion designer|video edit(?:or|ing)|audio edit(?:or|ing))\b",
    r"\b(voice actor|voice acting|ator de voz|locu[cç][aã]o|dublador|dublagem)\b",
    # Coleta de tarefas domésticas/vídeo físico/pesquisa de campo
    r"\b(video collection|photo collection|survey participants?|research participants?)\b",
    # Medicina / Saúde / Odonto / Farmácia / Enfermagem
    r"\b(ophthalmolog\w*|oftalmolog\w*|doctor|m[eé]dico\b|m[eé]dica\b|physician|surge(?:on|ry))\b",
    r"\b(nurse\b|nursing|enferm\w*|pharmac\w*|farmac\w*|biomed\w*|dentist\w*|odontol\w*)\b",
    r"\b(veterinar\w*|psicolog\w*|psycholog\w*|fisioterap\w*|therapist|nutrition\w*|nutricion\w*)\b",
    # Jurídico / Direito
    r"\b(lawyer\b|attorney\b|advogad\w*|jur[ií]dic\w*|paralegal|legal counsel|direito\b)\b",
    # Ciências puras não-computacionais / Matemática teórica pura
    r"\b(mathematics specialist|science specialist|chemistry|qu[ií]mic\w*|biolog\w*|geolog\w*|geospatial|detective|police|garment|fashion|culinary|chef\b)\b",
    # Contábil / Fiscal
    r"\b(tax analyst|contador\b|cont[aá]bil\w*|auditor fiscal|tribut[aá]r\w*)\b",
    # Vendas ativas / Prospecção comercial pura
    r"\b(sdr\b|bdr\b|inside sales\b|sales representative|vendedor\b|executivo de vendas|prospec[cç][aã]o comercial)\b",
    # Docência escolar
    r"\b(professor(?:a)? de (?:ensino|escola|ingl[eê]s|idiomas|matem[aá]tica|f[ií]sica)|teacher\b|pedagog\w*|docente\b)\b",
    # Liderança corporativa executiva
    r"\b(decision-makers?|leaders and decision-makers)\b",
)

INFRA_TECH_PATTERNS = (
    r"\bwindows server\b", r"\blinux\b", r"\bactive directory\b",
    r"\bvmware\b", r"\bhyper[ -]?v\b", r"\bsql server\b",
    r"\bfirewall", r"\bbackup", r"\bnetwork(?:ing)?\b",
    r"\bremote support\b", r"\bsuporte remoto\b",
)
UNCERTAIN_NEW_TECH = (
    (r"\bkubernetes\b", "Kubernetes"), (r"\bterraform\b", "Terraform"),
    (r"\baws\b", "AWS"), (r"\bazure\b", "Azure"),
    (r"\b(?:gcp|google cloud)\b", "Google Cloud"),
)


def load_profile(path: Path = PROFILE_PATH) -> dict:
    """Perfil declarativo, apenas dados profissionais autorizados pelo usuário."""
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("perfil_job_hunter.json deve conter um objeto JSON")
    return obj


def profile_notes_for_role(category: str, title: str, content: str) -> list[str]:
    warnings: list[str] = []
    if category in {"Suporte Técnico N2/N3 / Aplicações", "Infraestrutura / Servidores / Redes", "Customer Support Técnico / SaaS"}:
        warnings.append("Experiência formal em TI de 2002 a 2014; confirmar atualização prática nas versões e ferramentas atuais.")
    text = norm(title + " " + content)
    new_tools = [name for pat, name in UNCERTAIN_NEW_TECH if re.search(pat, text)]
    if new_tools:
        warnings.append("Verificar domínio comprovável de: " + ", ".join(new_tools) + ".")
    warnings.append("Confirmar no anúncio integral: elegibilidade Brasil, inglês mínimo, graduação, regime remoto e remuneração.")
    return warnings


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).lower().strip()


def normalize_base_title(title: str) -> str:
    """Remove sufixos regionais comuns para deduplicar requisições equivalentes."""
    t = norm(title)
    t = re.sub(r"\s*[-–(]\s*(?:br|brazil|brasil|remote|remoto|freelance|advisory|latam|sao paulo|sp|rj)[^)]*\)?$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def canonical_url(url: str) -> str:
    try:
        u = urllib.parse.urlsplit(url.strip())
        return f"{u.netloc.lower()}{u.path.rstrip('/').lower()}"
    except ValueError:
        return url.strip().lower().rstrip("/")


def existing_records(path: Path = HISTORY) -> tuple[set[str], set[tuple[str, str]]]:
    if not path.exists():
        return set(), set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        if "link_oficial" not in (rdr.fieldnames or []):
            raise ValueError("vagas.csv sem coluna 'link_oficial'; verifique o cabeçalho")
        urls = set()
        titles = set()
        for row in rdr:
            u = row.get("link_oficial", "").strip()
            if u:
                urls.add(canonical_url(u))
            emp = norm(row.get("empresa", ""))
            cargo = normalize_base_title(row.get("cargo", ""))
            if cargo:
                titles.add((emp, cargo))
        return urls, titles


def existing_urls(path: Path = HISTORY) -> set[str]:
    return existing_records(path)[0]


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        if tag in {"p", "li", "br", "div", "h1", "h2", "h3", "h4"}:
            self.parts.append(". ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag in {"p", "li", "div", "h1", "h2", "h3", "h4"}:
            self.parts.append(". ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def clean_html(markup) -> str:
    text = html.unescape(html.unescape(str(markup or "")))
    ext = TextExtractor()
    ext.feed(text)
    cleaned = html.unescape("".join(ext.parts))
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def check_eligibility(location: str, title: str, clean_content: str = "") -> tuple[str, str]:
    """Etapa 1: ELEGIBILIDADE eliminatória (modalidade, geografia, formação acadêmica, idiomas)."""
    loc = norm(location)
    ttl = norm(title)
    head = norm(clean_content[:350])
    full_text = norm(clean_content)

    # 1. Presencial ou híbrido
    if re.search(r"\b(hybrid|hibrid[ao]|on[- ]site|presencial|office[- ]based)\b", f"{loc} {ttl}"):
        return "INCOMPATIVEL", "Modalidade presencial/híbrida na localização oficial"

    # 2. Elegibilidade geográfica
    brasil = bool(re.search(r"\b(brasil|brazil|latam|latin america|americas|sao paulo|rio de janeiro|curitiba|belo horizonte|florianopolis)\b", f"{loc} {ttl} {head}"))
    if not brasil and bool(re.search(r"\bbr\b", f"{loc} {ttl}")):
        brasil = True

    remoto = bool(re.search(r"\b(remote|remoto|home[ -]?office|anywhere|worldwide|world wide)\b", f"{loc} {ttl}"))

    foreign_patterns = (
        r"\b(portugal|united states|usa|u\.s\.|us only|\bus\b|canada|united kingdom|uk only|\buk\b|"
        r"france|germany|deutschland|australia|\baus\b|austria|belgium|denmark|italy|italia|japan|japao|"
        r"mexico|netherlands|holanda|norway|spain|espanha|switzerland|suica|poland|sweden|new zealand|\bnz\b|"
        r"ireland|singapore|india|philippines|colombia|chile|argentina|luxembourg|"
        r"london|birmingham|boston|calgary|edmonton|frankfurt|hamburg|leeds|manchester|munich|new york|paris|san francisco|seattle|sydney|toronto|vancouver|berlin|melbourne|chicago|los angeles|austin|cape town)\b"
    )
    foreign = bool(re.search(foreign_patterns, f"{loc} {ttl} {head}"))

    if foreign and not brasil:
        return "INCOMPATIVEL", "Restrição geográfica para país/cidade estrangeira sem elegibilidade para o Brasil"

    # 3. Formação superior / Pós-graduação / PhD obrigatória
    degree_pat = r"(?:bachelor(?:'?s)?|master(?:'?s)?|phd|doctorate|pos[- ]graduacao|mestrado|doutorado|university degree|college degree|graduacao completa|ensino superior completo)"
    req_pat = r"(?:required|mandatory|must have|essential|obrigatori[oa]|obrigatorio|necessario|exigido|indispensavel|you must hold)"
    opt_pat = r"(?:not required|not mandatory|no degree required|nao exigid[oa]|nao obrigatori[oa]|dispensavel|optional|preferred|desirable|desejavel|diferencial|nice to have|plus|sem exigencia)"

    snippets = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\s*[•\u2022]\s*", full_text) if s.strip()]
    for s in snippets:
        if re.search(opt_pat, s):
            continue
        if re.search(degree_pat, s) and re.search(req_pat, s):
            return "INCOMPATIVEL", "Exigência eliminatória de formação superior/pós-graduação/PhD"

    # 4. Inglês fluente / avançado / intermediário obrigatório
    english = r"(?:english|ingles)"
    level = r"(?:intermediate|advanced|fluent|fluency|professional|b1|b2|c1|c2|intermediario|avancado|fluente)"
    for s in snippets:
        if re.search(opt_pat, s):
            continue
        if re.search(rf"\b{english}\b.{{0,45}}\b{level}\b|\b{level}\b.{{0,45}}\b{english}\b", s):
            if re.search(req_pat, s) or re.search(rf"\b(?:fluent|advanced|fluente|avancado)\b\s+\b{english}\b", s):
                return "INCOMPATIVEL", "Exigência de inglês acima do básico obrigatório"

    # 5. Avaliação de áudio/locução/comunicação em inglês sem menção expressa a português
    if re.search(r"\b(audio specialist|voice actor|voice acting|agentic audio)\b", ttl):
        if not re.search(r"\b(portuguese|portugues)\b", ttl):
            return "INCOMPATIVEL", "Avaliação de áudio/locução sem especificação de língua portuguesa (exige inglês fluente)"

    if brasil and remoto:
        return "POTENCIAL", "Brasil e remoto confirmados na localização/título"
    if brasil:
        return "PENDENTE", "Brasil informado, confirmação de modalidade remota pendente"
    if remoto:
        return "PENDENTE", "Remoto informado, elegibilidade brasileira pendente de confirmação no edital"
    return "INCOMPATIVEL", "Não consta modalidade remota nem Brasil"


def check_compatibility(title: str, clean_content: str = "") -> tuple[str, str]:
    """Etapa 2: COMPATIBILIDADE técnica (elimina especializações não comprovadas e categoriza)."""
    ttl = norm(title)
    body = norm(clean_content)
    full = f"{ttl} {body[:500]}"

    # Idiomas estrangeiros não dominados
    m_fluent = re.search(r"\bfluent in ([a-z ]+?)(?:\s*[-–(]|\s+project|\s+specialist|\s*$)", ttl)
    if m_fluent:
        lang = m_fluent.group(1).strip()
        if not re.search(r"\b(portuguese|portugues[ea]?)\b", lang):
            return "INCOMPATIVEL", f"Exige fluência em idioma não dominado ({lang})"

    m_speakers = re.search(r"^([a-z ]+?)\s*[-–]\s*fluent speakers", ttl)
    if m_speakers:
        lang = m_speakers.group(1).strip()
        if not re.search(r"\b(portuguese|portugues[ea]?)\b", lang):
            return "INCOMPATIVEL", f"Exige falante fluente de idioma não dominado ({lang})"

    m_ai_lang = re.search(r"^ai trainer\s*[-–]\s*(?:advanced\s+)?([a-z ]+?)(?:\s+fluency|\s*\(|\s*$)", ttl)
    if m_ai_lang:
        lang = m_ai_lang.group(1).strip()
        if not re.search(r"\b(portuguese|portugues[ea]?|brazilian)\b", lang):
            return "INCOMPATIVEL", f"Treinamento de IA em idioma não dominado ({lang})"

    foreign_langs = (
        r"\b(japanese|japones|german|alemao|french|frances|chinese|mandarin|mandarim|italian|italiano|"
        r"russian|russo|korean|coreano|arabic|arabe|dutch|holandes|swedish|sueco|polish|polones|"
        r"turkish|turco|hindi|bengali|tamil|czech|danish|finnish|hungarian|norwegian|hebrew|indonesian)\b"
    )
    if re.search(foreign_langs, ttl):
        return "INCOMPATIVEL", "Idioma estrangeiro não dominado exigido no cargo"

    # Espanhol linguístico avançado (candidato domina apenas nível intermediário)
    if re.search(r"\b(spanish|espanhol)\b", ttl):
        if re.search(r"\b(language specialist|linguist|phonetics|morphology|syntax|sociolinguistics|language data contributor)\b", full):
            return "INCOMPATIVEL", "Exige especialização linguística superior ao espanhol intermediário"

    # Tecnologias não comprovadas no perfil:
    # 1. Kubernetes / K8s (não presumir de Linux ou VMware)
    if re.search(r"\bkubernetes\b", ttl) or "k8s" in ttl:
        return "INCOMPATIVEL", "Exige especialização profissional em Kubernetes (não comprovada no perfil)"
    if "kubernetes" in body[:400] and re.search(r"\b(auditor|architect|specialist|devops engineer)\b", ttl):
        return "INCOMPATIVEL", "Atribuição central exige Kubernetes/DevOps avançado"

    # 2. Machine Learning / Deep Learning / PyTorch / TensorFlow (não presumir de Python)
    if re.search(r"\b(machine learning|ml ai task|deep learning|computer vision|nlp engineer|llm researcher)\b", ttl):
        return "INCOMPATIVEL", "Exige especialização aprofundada em Machine Learning/Deep Learning"

    # 3. Linguagens de programação não dominadas sem Python
    if re.search(r"\b(java|c\+\+|rust|golang|ruby|php|swift|kotlin|scala)\b", ttl) and not re.search(r"\bpython\b", ttl):
        return "INCOMPATIVEL", "Linguagem de programação não dominada exigida no cargo"

    # 4. Revisão de papers acadêmicos / Graphical abstract
    if re.search(r"\b(graphical abstract|scientific literature|scientific papers?)\b", full):
        return "INCOMPATIVEL", "Exige revisão de literatura acadêmica/papers científicos avançados"

    # Especializações alheias ao perfil
    for p in INCOMPATIBLE_DOMAINS:
        m_dom = re.search(p, ttl)
        if m_dom:
            return "INCOMPATIVEL", f"Especialização incompatível com o perfil ({m_dom.group(0)})"

    # Avaliação de IA: deve ser em Português ou em desenvolvimento técnico (Python/Software/Infraestrutura)
    is_ai_role = bool(re.search(r"\bai (?:trainer|evaluator|training|annotator|specialist)\b|\bllm (?:evaluator|trainer)\b", ttl))
    if is_ai_role:
        has_pt = bool(re.search(r"\b(portugues[ea]?|brazil|brasil|pt[- ]?br|paulistano|carioca)\b", ttl + " " + body))
        has_tech = bool(re.search(r"\b(python|coding|code|software|infrastructure|infraestrutura|developer|systems?|database|network|trace|workflows?)\b", ttl))
        if not has_pt and not has_tech:
            return "INCOMPATIVEL", "Treinamento de IA fora das especialidades do perfil (requer português ou stack técnica de TI)"

    # Categorização dentro das áreas prioritárias
    ranked = []
    for cat, patterns in CATEGORIES:
        in_title = sum(bool(re.search(pat, ttl)) for pat in patterns)
        in_body = sum(bool(re.search(pat, body)) for pat in patterns)
        bonus = CATEGORY_BONUS.get(cat, 0)
        if in_title:
            pt_ai = 15 if cat == "AI Training / Evaluation" and re.search(r"\b(portugues[ea]?|brazil|brasil|pt[- ]?br|paulistano|carioca)\b", ttl + " " + body) else 0
            ranked.append((100 + bonus + pt_ai + 15 * in_title + min(in_body, 5), cat))

    if not ranked:
        return "INCOMPATIVEL", "Título do cargo não corresponde a nenhuma das áreas prioritárias do perfil"

    best_score, best_cat = max(ranked, key=lambda x: x[0])
    return "COMPATIVEL", best_cat


def calculate_priority(category: str, title: str, clean_content: str, el_status: str) -> int:
    """Etapa 3: PRIORIDADE (calculada apenas para vagas aprovadas em Elegibilidade e Compatibilidade)."""
    score = 100 + CATEGORY_BONUS.get(category, 0)
    if category == "AI Training / Evaluation" and re.search(r"\b(portugues[ea]?|brazil|brasil|pt[- ]?br|paulistano|carioca)\b", norm(title + " " + clean_content)):
        score += 15
    if el_status == "POTENCIAL":
        score += 25
    score += tech_relevance_bonus(category, title + " " + clean_content)
    return score


def check_title_incompatibility(title: str) -> tuple[bool, str]:
    """Wrapper para compatibilidade de testes unitários legados."""
    status, reason = check_compatibility(title, "")
    return (status == "INCOMPATIVEL", reason)


def location_status(location: str, title: str, content_head: str = "") -> tuple[str, str]:
    """Wrapper para compatibilidade com testes unitários legados."""
    return check_eligibility(location, title, content_head)


def requirement_status(text: str) -> tuple[str, list[str]]:
    """Wrapper para compatibilidade com testes unitários legados."""
    text_norm = norm(text)
    snippets = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\s*[•\u2022]\s*", text_norm) if s.strip()]
    reasons: list[str] = []
    english = r"(?:english|ingles)"
    level = r"(?:intermediate|advanced|fluent|fluency|professional|b1|b2|c1|c2|intermediario|avancado|fluente)"
    degree = r"(?:bachelor(?:'?s)? degree|university degree|college degree|graduacao completa|ensino superior completo)"
    required = r"(?:required|mandatory|must have|essential|obrigatori[oa]|obrigatorio|necessario|exigido|indispensavel)"
    optional = r"(?:not required|not mandatory|no degree required|nao exigid[oa]|nao obrigatori[oa]|dispensavel|optional|preferred|desirable|desejavel|diferencial|nice to have|plus|sem exigencia)"
    foreign_lang = r"(?:japanese|japones|german|alemao|french|frances|chinese|mandarim|mandarin|italian|italiano|russian|russo|korean|coreano|arabic|arabe|dutch|holandes|tamil)"

    for sentence in snippets:
        if re.search(optional, sentence):
            continue
        if re.search(rf"\b{english}\b.{{0,45}}\b{level}\b|\b{level}\b.{{0,45}}\b{english}\b", sentence):
            if re.search(required, sentence) or re.search(rf"\b(?:fluent|advanced|fluente|avancado)\b\s+\b{english}\b", sentence):
                reasons.append("Possível inglês acima do básico obrigatório: " + sentence[:180])
        if re.search(rf"\b{foreign_lang}\b", sentence):
            if re.search(required, sentence) or re.search(rf"\b(?:fluent|advanced|fluente|avancado|native|nativo)\b", sentence):
                reasons.append("Exigência de idioma não dominado: " + sentence[:180])
        if re.search(degree, sentence) and re.search(required, sentence):
            reasons.append("Possível graduação obrigatória: " + sentence[:180])
    return ("INCOMPATIVEL", reasons) if reasons else ("PENDENTE", ["Requisitos eliminatórios não confirmados automaticamente"])


def categorize(title: str, content: str) -> tuple[str | None, int]:
    """Classifica cargo com base em padrões ponderados, exigindo compatibilidade de título."""
    t = norm(title)
    body = norm(content)
    ranked = []
    for cat, patterns in CATEGORIES:
        in_title = sum(bool(re.search(p, t)) for p in patterns)
        in_body = sum(bool(re.search(p, body)) for p in patterns)
        bonus = CATEGORY_BONUS.get(cat, 0)
        if in_title:
            pt_ai_bonus = 15 if cat == "AI Training / Evaluation" and re.search(r"\b(portugues[ea]?|brazil|brasil|pt[- ]?br|paulistano|carioca)\b", t + " " + body) else 0
            ranked.append((100 + bonus + pt_ai_bonus + 15 * in_title + min(in_body, 5), cat))
    return (max(ranked, key=lambda x: x[0])[1], max(ranked, key=lambda x: x[0])[0]) if ranked else (None, 0)


def tech_relevance_bonus(category: str, text: str) -> int:
    if category not in {"Suporte Técnico N2/N3 / Aplicações", "Infraestrutura / Servidores / Redes", "Customer Support Técnico / SaaS"}:
        return 0
    n = norm(text)
    return min(12, 3 * sum(bool(re.search(p, n)) for p in INFRA_TECH_PATTERNS))


def diversify_top(candidates: list[dict], limit: int = MAX_VAGAS, per_category: int = 2, per_company: int = 2) -> list[dict]:
    """Evita que um único quadro/empresa ou categoria domine todas as vagas.
    Aplica limite de 2 vagas por empresa e 2 por categoria quando houver alternativas."""
    ordered = sorted(candidates, key=lambda x: (x["prioridade_local"], x["updated_at"]), reverse=True)
    selected: list[dict] = []
    cat_counts: dict[str, int] = {}
    comp_counts: dict[str, int] = {}
    deferred: list[dict] = []

    for c in ordered:
        cat = c["categoria"]
        comp = c["empresa"]
        if cat_counts.get(cat, 0) >= per_category or comp_counts.get(comp, 0) >= per_company:
            deferred.append(c)
            continue
        selected.append(c)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        comp_counts[comp] = comp_counts.get(comp, 0) + 1
        if len(selected) == limit:
            return selected

    for c in deferred:
        if len(selected) >= limit:
            break
        selected.append(c)
    return selected


def useful_summary(text: str, title: str, max_chars: int = 1000) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\.\s+", text) if len(s.strip()) > 12]
    terms = ("requisit", "requirement", "qualific", "english", "ingles", "portugu", "spanish", "espan", "remote", "remot", "brazil", "brasil", "degree", "gradu", "salary", "salario", "compensation", "experience", "experiencia")
    chosen = [s for s in sentences if any(w in norm(s) for w in terms)]
    if not chosen:
        chosen = sentences[:7]
    out = f"Cargo: {title}. " + " ".join(chosen[:12])
    return out[:max_chars]


def fetch_json(url: str, timeout: int = 15):
    req = urllib.request.Request(url, headers={"User-Agent": "JobHunter/2.0 (public Greenhouse job boards)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def collect(boards=BOARDS, existing=None, fetch=fetch_json, max_vagas=MAX_VAGAS):
    if isinstance(existing, tuple):
        known_urls, known_titles = existing
    elif isinstance(existing, set):
        known_urls = existing
        known_titles = set()
    elif existing is None:
        known_urls, known_titles = existing_records()
    else:
        known_urls = set(existing)
        known_titles = set()

    seen_urls: set[str] = set()
    seen_titles: set[tuple[str, str]] = set()
    metrics = {
        "consultadas": 0, "duplicadas_no_csv": 0, "duplicadas_entre_fontes": 0,
        "incompativeis": 0, "incomp_elegibilidade": 0, "incomp_compatibilidade": 0,
        "sem_conteudo": 0, "sem_categoria": 0, "pendentes": 0, "potenciais": 0,
        "qualificadas": 0, "erros": []
    }
    candidates = []

    for board in boards:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
        try:
            data = fetch(url)
            jobs = data.get("jobs", [])
            if not isinstance(jobs, list):
                raise ValueError("campo 'jobs' não é lista")
        except (urllib.error.URLError, ValueError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            metrics["erros"].append(f"{board}: {type(exc).__name__}: {exc}")
            continue

        for job in jobs:
            metrics["consultadas"] += 1
            job_url = (job.get("absolute_url") or "").strip()
            if not job_url:
                metrics["sem_conteudo"] += 1
                continue
            canonical = canonical_url(job_url)
            if canonical in known_urls:
                metrics["duplicadas_no_csv"] += 1
                continue
            if canonical in seen_urls:
                metrics["duplicadas_entre_fontes"] += 1
                continue
            seen_urls.add(canonical)

            title = str(job.get("title") or "")
            norm_emp = norm(board)
            base_title = normalize_base_title(title)

            # Deduplicação de requisições equivalentes na mesma empresa
            if (norm_emp, base_title) in known_titles:
                metrics["duplicadas_no_csv"] += 1
                continue
            if (norm_emp, base_title) in seen_titles:
                metrics["duplicadas_entre_fontes"] += 1
                continue
            seen_titles.add((norm_emp, base_title))

            location = str((job.get("location") or {}).get("name") or "")
            content = clean_html(job.get("content") or "")

            # ETAPA 1: ELEGIBILIDADE (modalidade, geografia, formação acadêmica, idiomas)
            el_status, el_reason = check_eligibility(location, title, content)
            if el_status == "INCOMPATIVEL":
                metrics["incomp_elegibilidade"] += 1
                metrics["incompativeis"] += 1
                continue

            # ETAPA 2: COMPATIBILIDADE (elimina especializações alheias e categoriza por título)
            cp_status, cp_reason = check_compatibility(title, content)
            if cp_status == "INCOMPATIVEL":
                metrics["incomp_compatibilidade"] += 1
                metrics["incompativeis"] += 1
                continue

            cat = cp_reason

            # ETAPA 3: PRIORIDADE (calculada apenas após aprovação nas etapas 1 e 2)
            score = calculate_priority(cat, title, content, el_status)

            metrics["potenciais" if el_status == "POTENCIAL" else "pendentes"] += 1
            metrics["qualificadas"] += 1

            req_summary = useful_summary(content, title) if len(content) >= 50 else "Descrição insuficiente para avaliar requisitos."
            candidates.append({
                "empresa": board,
                "cargo": title,
                "localizacao_original": location,
                "link_oficial": job_url,
                "categoria": cat,
                "status_preliminar": "PENDENTE_VALIDACAO" if len(content) >= 50 else "PENDENTE_DADOS",
                "elegibilidade": el_reason,
                "requisitos": [el_reason],
                "prioridade_local": score,
                "resumo_requisitos": req_summary,
                "alertas_perfil": profile_notes_for_role(cat, title, content),
                "updated_at": job.get("updated_at") or "",
            })

    return diversify_top(candidates, limit=max_vagas, per_category=2, per_company=2), metrics, len(candidates)


def save_atomic_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".job_hunter_", suffix=".tmp", delete=False) as f:
        tmp = Path(f.name)
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(description="Busca e pré-filtragem do Job Hunter sem IA")
    parser.add_argument("--max", type=int, default=MAX_VAGAS, help="máximo de vagas para revisão")
    args = parser.parse_args()
    known_urls, known_titles = existing_records()
    selected, metrics, total = collect(existing=(known_urls, known_titles), max_vagas=max(1, min(args.max, 20)))
    profile = load_profile()
    payload = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "fonte": "Greenhouse",
        "perfil_para_avaliacao_ia": profile,
        "vagas_elegiveis_confirmadas": 0,
        "aviso": "Pré-filtragem NÃO comprova elegibilidade. Experiência profissional de TI ocorreu em 2002-2014; não presumir atuação contínua até hoje.",
        "conhecidas_csv": len(known_urls), "metricas": metrics,
        "candidatas_total": total, "vagas_para_revisao": selected,
    }
    save_atomic_json(OUTPUT, payload)
    print(f"Arquivos preservados: {HISTORY.name}. Pré-seleção: {OUTPUT}")
    print(f"Consultadas: {metrics['consultadas']} | conhecidas: {metrics['duplicadas_no_csv']} | incompatíveis: {metrics['incompativeis']} | pré-selecionadas: {len(selected)} | erros: {len(metrics['erros'])}")
    for i, v in enumerate(selected, 1):
        print(f"{i}. {v['cargo']} — {v['empresa']} [{v['status_preliminar']}] {v['link_oficial']}")
    for error in metrics["erros"]:
        print("ERRO:", error, file=sys.stderr)


if __name__ == "__main__":
    main()
