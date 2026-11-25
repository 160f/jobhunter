#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Job Hunter v3.1: tres canais independentes; nao faz candidaturas.

Sem dependencias externas. Os antigos scripts/CSVs nao sao modificados.
Fonte: APIs publicas Greenhouse, Himalayas, Remotive, RemoteOK, Arbeitnow.
Ashby e Lever opcionais por nomes de quadros validos, fornecidos no config.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # Instalar scripts na pasta do agente; v3 nao altera arquivos legados.
CONFIG = HERE / 'config_job_hunter_v3_1.json'
PREFIX = 'job_hunter_v3_1'
CHANNELS = ('EMPREGOS', 'IA', 'PESQUISAS')
OUT_SHORT = ROOT / (PREFIX + '_shortlist.json')
OUT_CSV = ROOT / (PREFIX + '_shortlist.csv')
OUT_BACKLOG = ROOT / (PREFIX + '_backlog.json')
OUT_REPORT = ROOT / (PREFIX + '_diagnostico.json')
OUT_STATE = ROOT / (PREFIX + '_estado.json')

# Regex para as FUNCOES profissionais; nao aceitar IA simplesmente por
# titulo conter "Freelance AI Trainer Project" em um cargo especializado.
EMPLOYMENT_PATTERNS = (
    ('Python e Automacao', re.compile(r'\bpython\b|\b(?:automation|automacao|automatizacao|rpa)\b|\b(?:api|integration|integracao)\s+(?:developer|engineer|specialist)\b', re.I)),
    ('Suporte e Infraestrutura', re.compile(r'\b(?:technical|it|application|customer)\s+support\b|\b(?:help\s?desk|service desk|linux administrator|windows administrator|systems? administrator|suporte tecnico|infraestrutura|analista de suporte|analista de redes|implantacao|onboarding)\b', re.I)),
    ('Dados e Quant', re.compile(r'\b(?:data analyst|data quality analyst|business intelligence|quantitative (?:analyst|researcher|trader)|quant (?:analyst|researcher|trader)|trading operations|analista de dados|cientista de dados)\b', re.I)),
)
GENERIC_ENGINEER = re.compile(r'\b(?:software|backend|front.?end|full.?stack)\s+(?:engineer|developer)\b|\bdesenvolvedor(?:a)?(?: de)? software\b', re.I)
STACK = re.compile(r'\bpython\b|\bfastapi\b|\bdjango\b|\bflask\b|\b(?:llm|langchain|agentic|ai agents|agentes? de ia)\b|\bapi integration\b', re.I)
AI_ROLES = re.compile(
    r'\b(?:ai|llm|artificial intelligence)\s+(?:trainer|evaluator|rater|annotator|reviewer|coding tasks?|coding evaluator|response reviewer)\b|'
    r'\b(?:coding|prompt|model)\s+(?:evaluator|reviewer|trainer|specialist)\b|'
    r'\b(?:data|text|audio|video|image)\s+(?:annotat\w*|label\w*|collection)\b|'
    r'\b(?:portuguese|spanish)\s+(?:linguist|evaluator|reviewer|annotator|language expert)\b|'
    r'\b(?:language alignment|content moderation|ai quality)\b|'
    r'\b[A-Za-zÀ-ÿ]+(?:\s+(?:Trilingual|Bilingual))?\s+Language\s+(?:Specialist|Expert|Evaluator|Trainer)\b', re.I)
AI_SUFFIX = re.compile(r'\s*[-–|]\s*(?:freelance\s+)?ai\s+trainer\s+project.*$', re.I)
STUDY = re.compile(r'\b(?:research participants?|paid (?:research|study)|user research study|research study|paid survey|market research (?:interview|participant)|paid interview|research interviews?)\b', re.I)
STUDY_RELEVANCE = re.compile(r'\b(?:finance|financial|capital markets?|trading|hedge fund|banking|investment|broker|it support|technical support|software|ai|technology|data|python|infrastructure|business intelligence|analyst|product manager|devops|system administrator|quant|automation|cybersecurity)\b', re.I)
SENIOR = re.compile(r'\b(?:senior|sr\.?|staff|principal|lead|director|head of|architect)\b', re.I)
UNSUPPORTED_TITLE_LANG = re.compile(
    r'\b(?:polish|french|german|japanese|korean|mandarin|chinese|arabic|italian|dutch|turkish|russian|thai|swedish|norwegian|finnish|greek|hebrew|hindi|vietnamese|czech|ukrainian)\b', re.I)
OTHER_PROFESSIONS = re.compile(
    r'\b(?:mathematics specialist|science specialist|garment manufacturing|electrical engineers?|aeronautical engineers?|mechanical engineers?|civil engineers?|medical doctor|physician|licensed attorney|lawyer|nurse|dentist|pharmacist|architecture specialist|3d modeling|cad expert|chemistry specialist|biology specialist)\b', re.I)
COLLECTION = re.compile(r'\b(?:audio|video|image|photo|speech)\s+(?:data\s+)?collection\b', re.I)
ENGLISH_MANDATORY = re.compile(
    r'\b(?:advanced|fluent|native|professional|excellent|strong)\s+(?:spoken\s+|written\s+)?english\b|'
    r'\benglish\s+(?:c1|c2|fluency|required|mandatory|at c1|at c2|proficiency required)\b|'
    r'\bingl[eê]s\s+(?:avancado|avan[cç]ado|fluente|obrigat[oó]rio)\b', re.I)
DEGREE_MANDATORY = re.compile(
    r'\b(?:bachelor(?:.s)? degree|university degree|college degree|gradua[cç][aã]o|ensino superior)\b.{0,65}\b(?:required|mandatory|must have|obrigat[oó]ri[oa]|exigid[oa])\b', re.I)
REMOTE = re.compile(r'\b(?:remote|remoto|remota|home\s?office|work from home|anywhere|worldwide|global|latam|latin america|brasil|brazil)\b', re.I)
ON_SITE = re.compile(r'\b(?:hybrid|hibrido|h[ií]brid[oa]|on.site|onsite|presencial|in.office)\b', re.I)
NO_BR_TITLE = re.compile(r'\b(?:portugal|spain|france|germany|poland|uk|united kingdom|united states|usa|canada|australia|south africa|mexico|argentina)\b', re.I)
BR = re.compile(r'\b(?:brasil|brazil|brazilian|latam|latin america|south america|worldwide|anywhere|global)\b', re.I)
NO_BR_EXPLICIT = re.compile(
    r'\b(?:must be|must reside|must live|need to be|required to be|only applicants|candidates must be)\s+' 
    r'.{0,40}\b(?:in|from)\s+(?:the\s+)?(?:united states|usa|us|canada|united kingdom|uk|europe|portugal|australia)\b|'
    r'\b(?:united states|usa|canada|united kingdom|uk|europe|portugal|australia)\s+(?:only|residents only)\b', re.I)


# Diferencia o idioma que a VAGA exige de idiomas citados em descricoes.
# A descoberta e ampla; a shortlist deve conter apenas requisitos plausiveis.
LANGUAGE_NAMED = re.compile(
    r'\b(?:asturian|galician|malay|polish|french|german|japanese|korean|mandarin|chinese|arabic|'
    r'italian|dutch|turkish|russian|thai|swedish|norwegian|finnish|greek|hebrew|hindi|'
    r'vietnamese|czech|ukrainian|romanian|hungarian|indonesian|filipino|tagalog|'
    r'english|spanish|portuguese|catalan|basque|persian|urdu|bengali|punjabi|swahili)\b', re.I)
LANGUAGE_PROFESSION = re.compile(
    r'\b(?P<lang>[A-Za-zÀ-ÿ]+)(?:\s+Trilingual|\s+Bilingual)?\s+'
    r'(?:Language\s+(?:Specialist|Expert|Evaluator|Trainer)|Linguist)\b', re.I)
LANGUAGE_FLUENT_IN = re.compile(r'\b(?:fluent|native|advanced|proficient)\s+in\s+(?P<lang>[A-Za-zÀ-ÿ]+)\b', re.I)
LANGUAGE_LEVEL = re.compile(
    r'\b(?:fluent|native|advanced)\s+(?P<lang>[A-Za-zÀ-ÿ]+)\s+(?:fluency|speaker|proficiency)\b|'
    r'\b(?P<lang2>[A-Za-zÀ-ÿ]+)\s+(?:fluency|speaker|proficiency)\b', re.I)
SPECIALIST_OUTSIDE_PROFILE = re.compile(
    r'\b(?:earth\s*(?:&|and)\s*environmental\s*sciences?|engineering\s+sciences?|'
    r'life\s+sciences?|audio\s+engineer|sound\s+engineer|ml\s+engineering|'
    r'\bSWE\b|supply\s+chain|medical\s+professionals?|clinical\s+research|'
    r'law\s+specialist|accounting\s+specialist|financial\s+auditor|mechanical\s+design|'
    r'civil\s+engineering|aerospace|aviation|aeronautical|robotics\s+engineer)\b', re.I)
STRONG_AI_ROLE = re.compile(
    r'\b(?:ai\s+coding\s+tasks?|coding\s+(?:evaluator|reviewer|trainer)|'
    r'(?:ai|llm)\s+(?:coding|response)\s+(?:evaluator|reviewer)|'
    r'(?:prompt\s+evaluator|prompt\s+engineer|agent\s+function\s+call|'
    r'function\s+calling|llm\s+agent|ai\s+evaluator|model\s+evaluator|'
    r'portuguese\s+ai\s+(?:evaluator|trainer|annotator)|'
    r'portuguese\s+(?:content|language)\s+(?:evaluator|reviewer)|'
    r'(?:video|audio|image|text|data)\s+(?:annotation|annotator|labeling)))\b', re.I)
STUDY_FOREIGN_TARGET = re.compile(
    r'\b(?:research\s+participants?|paid\s+(?:research|study)|research\s+study)\b'
    r'.{0,75}\b(?:united\s+kingdom|\buk\b|united\s+states|\busa\b|canada|'
    r'australia|portugal|germany|france)\b', re.I)


def classify_title_language(title, channel):
    """Retorna (alerta, gravidade) sem adivinhar fluencia a partir do texto geral.

    Gravidade hard: requisito de idioma objetivamente fora do perfil.
    risk: idioma/variante a ser confirmado com o anuncio.
    """
    if channel != 'IA':
        return None, None
    title = clean(title)
    chosen, strict = None, False
    hit = LANGUAGE_FLUENT_IN.search(title)
    if hit:
        chosen, strict = hit.group('lang'), True
    else:
        hit = LANGUAGE_LEVEL.search(title)
        if hit:
            chosen = hit.group('lang') or hit.group('lang2')
            strict = bool(re.search(r'\b(?:fluent|native|advanced)\b', hit.group(0), re.I))
        else:
            hit = LANGUAGE_PROFESSION.search(title)
            if hit:
                chosen = hit.group('lang')
                strict = bool(re.search(r'\b(?:trilingual|bilingual)\b', hit.group(0), re.I))
            else:
                hit = LANGUAGE_NAMED.search(title)
                if hit:
                    chosen = hit.group(0)
                    strict = bool(re.search(r'\b(?:advanced|fluent|native|proficient|trilingual|bilingual)\b', title, re.I))
    if not chosen:
        return None, None
    language = chosen.casefold()
    if language == 'portuguese':
        if re.search(r'\bportugal\b|\bpt[ _-]?pt\b', title, re.I):
            return 'Variante portuguesa de Portugal: dominio nao confirmado', 'risk'
        if strict and re.search(r'\b(?:trilingual|bilingual)\b', title, re.I):
            return 'Bilingue/trilingue: verificar outros idiomas exigidos', 'risk'
        return None, None
    if language == 'spanish':
        if strict:
            return 'Espanhol avancado/fluente/nativo exigido; nivel informado e intermediario', 'hard'
        return 'Espanhol exigido: verificar nivel requerido', 'risk'
    return 'Idioma requerido nao compativel com o perfil: ' + chosen, 'hard'


def ai_title_fit(title, channel):
    """Risco de especializacao e sinais positivos no titulo; descricao nao e diploma."""
    if channel != 'IA':
        return None, False
    t = clean(title)
    if OTHER_PROFESSIONS.search(t) or SPECIALIST_OUTSIDE_PROFILE.search(t):
        return 'Area profissional especializada nao comprovada: conferir formacao/experiencia', False
    return None, bool(STRONG_AI_ROLE.search(t))



def clean(value):
    if value is None:
        return ''
    if isinstance(value, dict):
        return ' '.join(clean(x) for x in value.values())
    if isinstance(value, list):
        return ' '.join(clean(x) for x in value)
    s = str(value)
    for _ in range(2):
        s = html.unescape(s)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', s)).strip()


def norm_url(url):
    url = (url or '').strip()
    u = urlsplit(url)
    if not u.netloc:
        return url.casefold().rstrip('/')
    tracking = {'fbclid', 'gclid', 'source', 'refid', 'trackingid', 'ref', 'utm_source', 'utm_medium', 'utm_campaign'}
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
         if k.casefold() not in tracking and not k.casefold().startswith('utm_')]
    return urlunsplit((u.scheme.casefold(), u.netloc.casefold(), u.path.rstrip('/'), urlencode(sorted(q)), ''))


def save_json(file, data):
    tmp = file.with_suffix(file.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(file)


def read_json(file, fallback):
    if not file.exists():
        return fallback
    try:
        return json.loads(file.read_text(encoding='utf-8-sig'))
    except Exception as exc:
        print(f'[AVISO] Nao foi possivel ler {file}: {exc}. Preservado.', file=sys.stderr)
        return fallback


def read_known_urls():
    found = set()
    csv_file = ROOT / 'vagas.csv'
    if not csv_file.exists():
        return found
    try:
        with csv_file.open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                u = norm_url(row.get('link_oficial') or '')
                if u:
                    found.add(u)
    except Exception as exc:
        print(f'[AVISO] Nao foi possivel ler vagas.csv: {exc}', file=sys.stderr)
    return found


def fetch(url, timeout=22):
    try:
        req = Request(url, headers={
            'User-Agent': 'JobHunterPersonalResearch/3.1 (+personal use; contact: no-contact)',
            'Accept': 'application/json',
        })
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8-sig')), None
    except HTTPError as exc:
        return None, f'HTTP {exc.code}'
    except URLError as exc:
        return None, f'REDE {exc.reason}'
    except Exception as exc:
        return None, f'{type(exc).__name__}: {exc}'


def base_job(**kwargs):
    result = {
        'empresa': '', 'cargo': '', 'descricao': '', 'localizacao': '',
        'link_oficial': '', 'link_fonte': '', 'fonte': '', 'data_publicacao': None,
        'remoto': None, 'regioes_permitidas': None, 'tz_restricoes': [],
        'tipo_contrato': '', 'remuneracao': '',
    }
    result.update(kwargs)
    result['cargo'] = clean(result['cargo'])
    result['empresa'] = clean(result['empresa'])
    result['descricao'] = clean(result['descricao'])
    result['localizacao'] = clean(result['localizacao'])
    return result


def gh_rows(data, slug):
    for row in data.get('jobs', []):
        location = row.get('location') or {}
        loc = location.get('name') if isinstance(location, dict) else location
        yield base_job(empresa=slug, cargo=row.get('title'), descricao=row.get('content'),
                       localizacao=loc, link_oficial=row.get('absolute_url') or '',
                       fonte='Greenhouse/' + slug, link_fonte=row.get('absolute_url') or '',
                       data_publicacao=row.get('updated_at'))


def him_rows(data, term):
    for row in data.get('jobs', []):
        reg = row.get('locationRestrictions')
        allowed = []
        if isinstance(reg, list):
            for x in reg:
                if isinstance(x, dict):
                    allowed.append((x.get('alpha2') or x.get('name') or '').upper())
                elif isinstance(x, str):
                    allowed.append(x.upper())
        guid = row.get('guid') or ''
        source_link = guid if guid.startswith('https://') else ('https://himalayas.app' + guid if guid.startswith('/') else '')
        salary = ' '.join(str(row.get(k) or '') for k in ('minSalary', 'maxSalary', 'currency', 'salaryPeriod')).strip()
        yield base_job(empresa=row.get('companyName'), cargo=row.get('title'),
                       descricao=row.get('description') or row.get('excerpt'),
                       localizacao=', '.join(allowed) if allowed else 'Worldwide / a confirmar',
                       link_oficial=row.get('applicationLink') or '', link_fonte=source_link,
                       fonte='Himalayas/' + term, data_publicacao=row.get('pubDate'), remoto=True,
                       regioes_permitidas=allowed if isinstance(reg, list) else None,
                       tz_restricoes=row.get('timezoneRestrictions') or [],
                       tipo_contrato=clean(row.get('employmentType')), remuneracao=salary)


def rem_rows(data):
    for row in data.get('jobs', []):
        yield base_job(empresa=row.get('company_name'), cargo=row.get('title'),
                       descricao=row.get('description'), localizacao=row.get('candidate_required_location'),
                       link_oficial=row.get('url'), link_fonte=row.get('url'), fonte='Remotive',
                       data_publicacao=row.get('publication_date'), remoto=True,
                       tipo_contrato=row.get('job_type'), remuneracao=row.get('salary'))


def remoteok_rows(data):
    if not isinstance(data, list):
        return
    for row in data:
        if not isinstance(row, dict) or not (row.get('position') or row.get('title')):
            continue  # A primeira entrada do feed e metadado.
        yield base_job(empresa=row.get('company'), cargo=row.get('position') or row.get('title'),
                       descricao=row.get('description'), localizacao=row.get('location'),
                       link_oficial=row.get('url') or row.get('apply_url'),
                       link_fonte=row.get('url'), fonte='RemoteOK',
                       data_publicacao=row.get('date'), remoto=True,
                       tipo_contrato='', remuneracao=row.get('salary') or '')


def arbeitnow_rows(data):
    for row in data.get('data', []):
        yield base_job(empresa=row.get('company_name'), cargo=row.get('title'),
                       descricao=row.get('description'), localizacao=row.get('location'),
                       link_oficial=row.get('url'), link_fonte=row.get('url'), fonte='Arbeitnow',
                       data_publicacao=row.get('created_at'), remoto=row.get('remote'),
                       tipo_contrato=' '.join(row.get('tags') or []))


def ashby_rows(data, slug):
    for row in data.get('jobs', []):
        if row.get('isListed') is False:
            continue
        summary = row.get('descriptionHtml') or row.get('descriptionPlain') or row.get('description')
        yield base_job(empresa=slug, cargo=row.get('title'), descricao=summary,
                       localizacao=clean(row.get('location')) + ' ' + clean(row.get('secondaryLocations')),
                       link_oficial=row.get('applyUrl') or row.get('jobUrl'),
                       link_fonte=row.get('jobUrl'), fonte='Ashby/' + slug,
                       data_publicacao=row.get('publishedAt'), remoto=row.get('isRemote'),
                       remuneracao=clean(row.get('compensation')))


def lever_rows(data, slug):
    if not isinstance(data, list):
        return
    for row in data:
        categories = row.get('categories') or {}
        if not isinstance(categories, dict):
            categories = {}
        loc = categories.get('location') or ''
        yield base_job(empresa=slug, cargo=row.get('text'),
                       descricao=row.get('descriptionPlain') or row.get('description') or row.get('lists'),
                       localizacao=loc, link_oficial=row.get('hostedUrl') or row.get('applyUrl'),
                       link_fonte=row.get('hostedUrl'), fonte='Lever/' + slug,
                       data_publicacao=row.get('createdAt'), remoto=bool(re.search(r'remote', clean(loc), re.I)))


class Collector:
    def __init__(self, config, get=None, sleep=None):
        self.config = config
        self.get = get or fetch
        self.sleep = sleep or time.sleep
        self.jobs = []
        self.diag = defaultdict(lambda: {'requisicoes': 0, 'sucessos': 0, 'erros': [], 'anuncios': 0})
        self.himalayas_rate_limited = False

    def add(self, source, url, parser):
        d = self.diag[source]
        d['requisicoes'] += 1
        data, err = self.get(url)
        if err:
            d['erros'].append(err)
            print(f'[FONTE COM ERRO] {source}: {err}')
            if source.startswith('Himalayas') and '429' in str(err):
                self.himalayas_rate_limited = True
            return
        try:
            got = list(parser(data))
            d['sucessos'] += 1
            d['anuncios'] += len(got)
            self.jobs.extend(got)
        except (TypeError, ValueError, AttributeError, KeyError) as exc:
            d['erros'].append('Resposta inesperada: ' + str(exc))
            print(f'[FONTE COM ERRO] {source}: esquema inesperado')

    def run(self):
        cfg = self.config['coleta']
        for board in cfg.get('greenhouse_boards', []):
            board = board.strip()
            self.add('Greenhouse/' + board,
                     'https://boards-api.greenhouse.io/v1/boards/' + board + '/jobs?content=true',
                     lambda d, b=board: gh_rows(d, b))
        # Cada q/canal e consultado diretamente, no lugar de depender de 1 pagina generica.
        first = True
        for channel, terms in cfg.get('himalayas_termos', {}).items():
            for term in terms:
                for page in range(1, max(1, int(cfg.get('himalayas_paginas_por_termo', 1))) + 1):
                    if self.himalayas_rate_limited:
                        break
                    if not first:
                        self.sleep(float(cfg.get('himalayas_pausa_segundos', 1.2)))
                    first = False
                    url = ('https://himalayas.app/jobs/api/search?' + urlencode({
                        'q': term, 'country': self.config['perfil'].get('pais', 'BR'), 'sort': 'recent', 'page': page}))
                    self.add(f'Himalayas/{channel}/{term}', url, lambda d, t=term: him_rows(d, t))
                if self.himalayas_rate_limited:
                    break
            if self.himalayas_rate_limited:
                break
        self.add('Remotive', 'https://remotive.com/api/remote-jobs?' + urlencode({
            'limit': int(cfg.get('remotive_limite', 500))}), rem_rows)
        if cfg.get('remoteok_ativo', True):
            self.add('RemoteOK', 'https://remoteok.com/api', remoteok_rows)
        for page in range(1, int(cfg.get('arbeitnow_paginas', 1)) + 1):
            self.add('Arbeitnow', 'https://www.arbeitnow.com/api/job-board-api?' + urlencode({'page': page}), arbeitnow_rows)
        for slug in cfg.get('ashby_boards', []):
            self.add('Ashby/' + slug, 'https://api.ashbyhq.com/posting-api/job-board/' + slug,
                     lambda d, s=slug: ashby_rows(d, s))
        for slug in cfg.get('lever_boards', []):
            self.add('Lever/' + slug, 'https://api.lever.co/v0/postings/' + slug + '?mode=json',
                     lambda d, s=slug: lever_rows(d, s))
        return self.jobs, dict(self.diag)


def job_channel(job):
    title = clean(job.get('cargo'))
    desc = clean(job.get('descricao'))
    # Pesquisa de usuarios na area de TI, bancos e trading, nao a vaga de "researcher".
    if STUDY.search(title):
        return ('PESQUISAS', 'Pesquisa paga / participacao') if STUDY_RELEVANCE.search(title) else (None, 'Pesquisa fora das areas de experiencia')
    # Se o titulo e de especialista, nao usar o sufixo de IA como prova de qualificacao.
    profession = AI_SUFFIX.sub('', title)
    if AI_ROLES.search(profession):
        return 'IA', 'Avaliacao/treinamento ou coleta de dados'
    for cat, pattern in EMPLOYMENT_PATTERNS:
        if pattern.search(profession):
            return 'EMPREGOS', cat
    if GENERIC_ENGINEER.search(profession) and STACK.search(desc[:5000]):
        return 'EMPREGOS', 'Engenharia generica: verificar stack real'
    return None, 'Cargo sem foco comprovado'


def geo_check(job):
    title, loc, desc = job['cargo'], clean(job['localizacao']), job['descricao'][:7000]
    if STUDY.search(title) and STUDY_FOREIGN_TARGET.search(title) and not BR.search(title):
        return 'INCOMPATIVEL', 'Pesquisa exige participantes de outro pais (titulo)'
    regs = job.get('regioes_permitidas')
    if isinstance(regs, list) and regs:
        values = {clean(x).upper() for x in regs}
        allow = {'BR', 'BRAZIL', 'BRASIL', 'LATAM', 'LATIN AMERICA', 'SOUTH AMERICA', 'WORLDWIDE', 'ANYWHERE', 'GLOBAL'}
        if values.isdisjoint(allow):
            return 'INCOMPATIVEL', 'API lista paises que nao incluem Brasil'
        return 'POTENCIAL', 'API informa abrangencia compativel; confirmar anuncio'
    # localizacao titulo em outro pais, sem Brasil ou mundo, e forte indicacao de restricao.
    if NO_BR_EXPLICIT.search(loc) or NO_BR_EXPLICIT.search(desc):
        return 'INCOMPATIVEL', 'Texto exige residencia em pais/regiao nao compativel'
    if (NO_BR_TITLE.search(title) and not BR.search(title)) or (
            NO_BR_TITLE.fullmatch(loc.strip()) and not BR.search(loc)):
        return 'REVISAR', 'Anuncio dirigido a outro pais; verificar contratacao no Brasil'
    if BR.search(loc) or BR.search(title):
        if job.get('remoto') is False or (ON_SITE.search(loc) and not REMOTE.search(loc)):
            return 'REVISAR', 'Modalidade remota nao demonstrada'
        return 'POTENCIAL', 'Referencia geografica compativel; validar texto completo'
    if job.get('remoto') is False:
        return 'REVISAR', 'Trabalho remoto nao confirmado'
    if job.get('remoto') is True or REMOTE.search(loc):
        return 'REVISAR', 'Remoto mas contratacao no Brasil nao confirmada'
    if REMOTE.search(desc):
        return 'REVISAR', 'Remoto na descricao; pais de contratacao a confirmar'
    return 'REVISAR', 'Remoto e Brasil ainda nao comprovados'


def qualify(job):
    channel, cat = job_channel(job)
    if not channel:
        return None, cat
    if not job.get('link_oficial'):
        return None, 'Sem link de candidatura'
    title, desc = job['cargo'], job['descricao']
    risks = []
    geo, geo_note = geo_check(job)
    if geo == 'INCOMPATIVEL':
        risks.append('Barreira geografica explicita')
    language_alert, language_severity = classify_title_language(title, channel)
    if language_alert:
        risks.append(language_alert)
    specialty_alert, strong_ai = ai_title_fit(title, channel)
    if specialty_alert:
        risks.append(specialty_alert)
    if OTHER_PROFESSIONS.search(title) and channel != 'IA':
        risks.append('Especialidade profissional nao comprovada no perfil')
    if channel == 'IA' and not strong_ai and not specialty_alert and not language_alert:
        risks.append('IA generica: comprovar aderencia das tarefas e experiencia')
    # Portugues-Portugal pode requerer variante PT-PT. Nao presumir elegibilidade.
    if re.search(r'\bportuguese\s*[-(]?\s*portugal\b|\bportuguese\s+language\s+specialist\s*\(portugal\)', title, re.I):
        risks.append('Exige portugues de Portugal: variante a confirmar')
    if ENGLISH_MANDATORY.search(desc) and not re.search(r'\benglish\s+(?:not required|optional|a plus)\b', desc, re.I):
        risks.append('Possivel ingles avancado obrigatorio')
    if DEGREE_MANDATORY.search(desc) and not re.search(r'\bdegree\s+(?:not required|preferred|a plus)\b', desc, re.I):
        risks.append('Possivel diploma universitario obrigatorio')
    if SENIOR.search(title):
        risks.append('Senioridade alta: requisitos a conferir')
    if cat.startswith('Engenharia generica'):
        risks.append('Verificar stack e anos de experiencia com software em producao')
    if COLLECTION.search(title):
        risks.append('Microtarefa/coleta: checar pagamento, consentimento e privacidade')
    if channel == 'PESQUISAS':
        risks.append('Pesquisa pontual: pagamento e paises elegiveis a confirmar')
    if not desc:
        risks.append('Descricao nao fornecida pela fonte')

    score = {'EMPREGOS': 40, 'IA': 42, 'PESQUISAS': 30}[channel]
    if cat in ('Python e Automacao', 'Suporte e Infraestrutura', 'Dados e Quant'):
        score += 12
    if geo == 'POTENCIAL':
        score += 12
    elif geo == 'REVISAR':
        score -= 8
    if re.search(r'\b(?:portuguese|brazil|brasil|brazilian)\b', title, re.I):
        score += 9
    if re.search(r'\b(?:spanish|espanhol)\b', title, re.I) and language_severity != 'hard':
        score += 3
    if 'Senioridade alta: requisitos a conferir' in risks:
        score -= 20
    if 'Especialidade profissional nao comprovada no perfil' in risks:
        score -= 40
    if specialty_alert:
        score -= 50
    if language_severity == 'hard':
        score -= 60
    elif language_severity == 'risk':
        score -= 18
    if 'IA generica: comprovar aderencia das tarefas e experiencia' in risks:
        score -= 16
    if 'Exige portugues de Portugal: variante a confirmar' in risks:
        score -= 15
    if 'Possivel ingles avancado obrigatorio' in risks:
        score -= 28
    if 'Possivel diploma universitario obrigatorio' in risks:
        score -= 25
    if 'Verificar stack e anos de experiencia com software em producao' in risks:
        score -= 14
    if COLLECTION.search(title):
        score -= 18
    if geo == 'INCOMPATIVEL':
        score -= 70
    if len(desc) < 80:
        score -= 8

    hard = {'Barreira geografica explicita'}
    unsupported = {'Especialidade profissional nao comprovada no perfil', 'Possivel ingles avancado obrigatorio', 'Possivel diploma universitario obrigatorio'}
    if language_severity == 'hard' or any(x in risks for x in hard):
        status = 'INCOMPATIVEL'
    elif specialty_alert or any(x in risks for x in unsupported):
        status = 'PENDENTE_RISCO_ALTO'
    else:
        status = 'POTENCIAL' if geo == 'POTENCIAL' else 'PENDENTE'
    priority = ('ALTA' if score >= 52 and status == 'POTENCIAL' and channel != 'PESQUISAS'
                else 'MEDIA' if score >= 32 and status in ('POTENCIAL', 'PENDENTE')
                else 'BAIXA')
    # IA generica nao pode ganhar ALTA so porque o titulo contem AI Trainer.
    if channel == 'IA' and not strong_ai and priority == 'ALTA':
        priority = 'MEDIA'
    # Pesquisa e renda pontual, entra como PENDENTE de elegibilidade sem ser confundida com emprego.
    if channel == 'PESQUISAS' and status in ('POTENCIAL', 'PENDENTE') and geo != 'INCOMPATIVEL':
        priority = 'MEDIA'
    # Retornar descricao completa para posterior verificacao manual/IA.
    desc_capped = desc[:20000]
    return {
        'canal': channel,
        'categoria': cat,
        'empresa': job['empresa'],
        'cargo': job['cargo'],
        'link_oficial': job['link_oficial'],
        'link_fonte': job.get('link_fonte') or job['link_oficial'],
        'fonte': job['fonte'],
        'localizacao': job['localizacao'],
        'remoto': job['remoto'],
        'tipo_contrato': job.get('tipo_contrato'),
        'remuneracao_anunciada': clean(job.get('remuneracao')),
        'data_publicacao': job.get('data_publicacao'),
        'status_elegibilidade': status,
        'situacao_geografica': geo,
        'motivo_geografia': geo_note,
        'prioridade': priority,
        'score': score,
        'alertas': risks,
        'descricao_completa': desc_capped,
        'descricao_truncada': len(desc) > 20000,
        'aderencia_ia_titulo': 'FORTE' if strong_ai else ('A_VERIFICAR' if channel == 'IA' else 'NAO_APLICAVEL'),
        'status_candidatura': 'NAO_ENVIADA',
        'nota': 'Triagem automatica preliminar. Aderencia nao e elegibilidade confirmada.'
    }, 'Candidato ao canal'


def title_family(item):
    t = clean(item['cargo']).casefold()
    t = AI_SUFFIX.sub('', t)
    t = re.sub(r'\s*\((?:remote|remoto)\)', '', t)
    t = re.sub(r'\b(?:remote|remoto|freelance)\b', '', t)
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


def shortlist_by_channel(candidates, cfg):
    all_lists = {}
    removed = Counter()
    for ch in CHANNELS:
        grouped = set()
        companies = Counter()
        filtered = [x for x in candidates if x['canal'] == ch
                    and x['prioridade'] in ('ALTA', 'MEDIA')]
        filtered.sort(key=lambda x: (0 if x['prioridade'] == 'ALTA' else 1,
                                     0 if x['status_elegibilidade'] == 'POTENCIAL' else 1,
                                     -x['score'], -int(x['novo']),
                                     x['empresa'].casefold(), x['cargo'].casefold()))
        selected = []
        for x in filtered:
            company = x['empresa'].casefold()
            family = (company, title_family(x))
            if family in grouped:
                removed[ch] += 1
                continue
            if companies[company] >= int(cfg['shortlist'].get('max_por_empresa_por_canal', 3)):
                continue
            selected.append(x)
            grouped.add(family)
            companies[company] += 1
            if len(selected) >= int(cfg['shortlist'][ch]):
                break
        all_lists[ch] = selected
    return all_lists, dict(removed)


def run_pipeline(rows, config, known, previous_seen=None):
    previous_seen = set(previous_seen or [])
    counts = Counter()
    dropped = Counter()
    unique = set()
    candidates = []
    seen_now = set()
    by_channel = defaultdict(Counter)
    for row in rows:
        counts['anuncios_recebidos'] += 1
        u = norm_url(row.get('link_oficial'))
        if not u:
            dropped['sem_link'] += 1
            continue
        if u in unique:
            dropped['duplicados_entre_fontes'] += 1
            continue
        unique.add(u)
        job, reason = qualify(row)
        if job is None:
            dropped[reason] += 1
            continue
        counts['em_foco'] += 1
        job['ja_no_vagas_csv'] = u in known
        job['novo'] = (u not in known and u not in previous_seen)
        seen_now.add(u)
        by_channel[job['canal']]['pretriadas'] += 1
        by_channel[job['canal']][job['status_elegibilidade']] += 1
        if job['novo']:
            by_channel[job['canal']]['novas'] += 1
        candidates.append(job)
    shortlists, groups_removed = shortlist_by_channel(
        [x for x in candidates if not x['ja_no_vagas_csv']], config)
    for ch, rows_selected in shortlists.items():
        by_channel[ch]['shortlist'] = len(rows_selected)
        by_channel[ch]['shortlist_novas'] = sum(x['novo'] for x in rows_selected)
    return candidates, shortlists, dict(counts), dict(dropped), dict(by_channel), groups_removed, seen_now


def write_csv(file, selected):
    cols = ['canal', 'empresa', 'cargo', 'prioridade', 'status_elegibilidade', 'situacao_geografica',
            'novo', 'score', 'remuneracao_anunciada', 'fonte', 'link_oficial', 'link_fonte', 'alertas']
    with file.open('w', encoding='utf-8-sig', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=cols, delimiter=';')
        wr.writeheader()
        for job in selected:
            wr.writerow({k: (' | '.join(job[k]) if k == 'alertas' else job.get(k, '')) for k in cols})


def execute(config, get=None, sleep=None, outdir=None, known_override=None, previous_seen=None):
    collector = Collector(config, get=get, sleep=sleep)
    rows, sources = collector.run()
    if sources and not any(x['sucessos'] for x in sources.values()):
        raise RuntimeError('Nenhuma fonte respondeu corretamente; saidas anteriores preservadas. Verificar rede/API.')
    known = read_known_urls() if known_override is None else known_override
    if previous_seen is None:
        # Na primeira execucao, ler o estado v3.0 SOMENTE para preservar o sinal de 'ja vista'.
        # Nunca sobrescreve o estado antigo. Se v3.1 ja tem estado, usa-o.
        legacy_state = ROOT / 'job_hunter_v3_estado.json'
        state_file = OUT_STATE if OUT_STATE.exists() else legacy_state
        state = read_json(state_file, {'versao': '3.1', 'urls_vistas': []})
        previous_seen = state.get('urls_vistas') or []
    backlog, shortlist, totals, dropped, by_channel, groups, seen_now = run_pipeline(
        rows, config, known, previous_seen)
    stamp = datetime.now(timezone.utc).isoformat()
    doc = {
        'gerado_em_utc': stamp, 'versao': '3.1',
        'nota': 'ALTA e prioridade de revisao, NAO confirmacao de elegibilidade. Candidaturas NAO enviadas.',
        'canais': {ch: {'quantidade': len(shortlist[ch]), 'oportunidades': shortlist[ch]} for ch in CHANNELS}}
    report = {
        'gerado_em_utc': stamp, 'versao': '3.1', 'resumo': totals,
        'descarte': dropped, 'canais': by_channel,
        'fontes': sources, 'repeticoes_shortlist': groups,
        'urls_ja_cadastradas': len(known),
        'alertas_mais_frequentes': dict(Counter(a for item in backlog for a in item['alertas']).most_common(20)),
        'canais_por_prioridade': {ch: dict(Counter(item['prioridade'] for item in backlog if item['canal'] == ch)) for ch in CHANNELS},
        'solicitacoes_com_erro': sum(len(x['erros']) for x in sources.values()),
        'observacao': 'Sem vagas novas nao quer dizer sem anuncios. Ver contadores de fonte, classificados e ja vistos.'
    }
    if outdir:
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        paths = [outdir / p.name for p in (OUT_SHORT, OUT_CSV, OUT_BACKLOG, OUT_REPORT, OUT_STATE)]
    else:
        paths = [OUT_SHORT, OUT_CSV, OUT_BACKLOG, OUT_REPORT, OUT_STATE]
    sh_file, csv_file, back_file, report_file, state_file = paths
    save_json(sh_file, doc)
    write_csv(csv_file, [r for ch in CHANNELS for r in shortlist[ch]])
    save_json(back_file, {'gerado_em_utc': stamp, 'versao': '3.1', 'oportunidades': backlog})
    save_json(report_file, report)
    save_json(state_file, {'versao': '3.1', 'atualizado_em_utc': stamp,
                           'urls_vistas': sorted(set(previous_seen) | seen_now)})
    return doc, report, paths


def main():
    p = argparse.ArgumentParser(description='Job Hunter v3.1 - 3 canais, nenhuma candidatura automatica')
    p.add_argument('--teste', action='store_true', help='Testes offline de regras; sem conexao nem gravacao')
    p.add_argument('--config', default=str(CONFIG), help='JSON de configuracao')
    args = p.parse_args()
    if args.teste:
        cases = [
            ('Python Developer', 'Remote Brazil', 'EMPREGOS'),
            ('IT Support Specialist', 'Remote - Brazil', 'EMPREGOS'),
            ('AI Coding Evaluator - Portuguese', 'Worldwide', 'IA'),
            ('IT Support Technician - Research Participants - United Kingdom', 'United Kingdom', 'PESQUISAS'),
            ('Mathematics Specialist - Freelance AI Trainer Project', 'Brazil', None),
            ('AI Trainer - Advanced Polish Fluency', 'Worldwide', 'IA'),
            ('Galician Trilingual Language Specialist - AI Trainer', 'Worldwide', 'IA'),
            ('AI Trainer (Life Sciences)', 'Brazil', 'IA'),
        ]
        for title, loc, expected in cases:
            job = base_job(cargo=title, localizacao=loc, empresa='Teste', remoto=True,
                           descricao='Remoto - brasileiro pode participar. Trabalho com Python e IA.',
                           link_oficial='https://example.com/test')
            ch, _ = job_channel(job)
            assert ch == expected, (title, ch, expected)
            obj, _ = qualify(job)
            print(f'OK: {title} => {ch or "FORA"}', (obj or {}).get('status_elegibilidade'))
        print('OK: regras offline')
        return
    config = read_json(Path(args.config), None)
    if not isinstance(config, dict) or not config.get('coleta') or not config.get('shortlist'):
        raise SystemExit('Erro: config_job_hunter_v3_1.json ausente ou invalido')
    try:
        doc, report, paths = execute(config)
    except RuntimeError as exc:
        raise SystemExit('[ERRO] ' + str(exc))
    print('\n===== JOB HUNTER v3 - TRES CANAIS =====')
    print('Anuncios recebidos:', report['resumo'].get('anuncios_recebidos', 0))
    print('Entraram no foco:', report['resumo'].get('em_foco', 0))
    print('Erros de API:', report['solicitacoes_com_erro'])
    for ch in CHANNELS:
        d = report['canais'].get(ch, {})
        print(f'\n[{ch}] pretriadas={d.get("pretriadas",0)} novas={d.get("novas",0)} '
              f'shortlist={d.get("shortlist",0)} shortlist_novas={d.get("shortlist_novas",0)}')
        for j in doc['canais'][ch]['oportunidades']:
            print(f'  - {j["prioridade"]} | {j["cargo"]} — {j["empresa"]} '
                  f'| {j["status_elegibilidade"]} | {j["fonte"]} | novo={j["novo"]}')
            print('    ' + j['link_oficial'])
    print('\nArquivos:')
    for path in paths:
        print(' ', path)
    print('NENHUMA candidatura enviada. vagas.csv e agendas atuais preservados.')


if __name__ == '__main__':
    main()
