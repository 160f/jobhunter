import csv
import html
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

BASE_DIR = Path(__file__).resolve().parent
AGENTS_MD_PATH = BASE_DIR / "AGENTS.md"
CONFIG_JSON_PATH = BASE_DIR / "config_painel.json"
PERFIL_CV_PATH = BASE_DIR / "perfil_cv_referencia.md"
PERFIL_CV_TXT_PATH = BASE_DIR / "perfil_cv_referencia.txt"
CANDIDATURAS_CSV = BASE_DIR / "candidaturas_acompanhamento.csv"
VAGAS_CSV = BASE_DIR / "vagas.csv"
CURRICULOS_DIR = BASE_DIR / "curriculos"
OPENBOT_DIR = BASE_DIR / ".openbot"

AGENTS_UNIVERSAL_PADRAO = """# Diretrizes de Comportamento do Agente (Processo Universal)

## 1. Fonte Única de Dados do Candidato
- Ler exclusivamente `perfil_cv_referencia.txt` (ou `perfil_cv_referencia.md`) para obter qualificações, experiências, formação, idiomas e competências do candidato.
- Jamais inventar, exagerar ou inferir experiências, cargos, empresas, datas, certificações, idiomas ou métricas ausentes no perfil do candidato.

## 2. Processo de Triagem e Validação de Vagas
- Analisar a descrição completa da oportunidade, status (aberta/fechada) e requisitos mandatórios.
- Cruzar os requisitos obrigatórios da vaga com as qualificações descritas em `perfil_cv_referencia.txt` e com as preferências operacionais configuradas no painel (modalidade, regime e cargos alvo).
- Classificar cada vaga em: `ALTA COMPATIBILIDADE`, `PENDENTE DE VALIDAÇÃO` ou `INCOMPATÍVEL`.
- Avançar para geração de currículo e candidatura apenas em vagas classificadas como `ALTA COMPATIBILIDADE`.

## 3. Processo de Geração de Currículo (PDF)
- Reorganizar resumo profissional e competências técnicas usando exclusivamente fatos do perfil do candidato, alinhando a terminologia à vaga para leitura por ATS.
- Gerar o PDF no idioma da vaga na pasta `curriculos/` com nome identificável, sem sobrescrever currículos anteriores.

## 4. Processo de Candidatura e Intervenção Humana
- Respeitar o modo de envio ativo (`Exige Aprovação` ou `Envio Automático`).
- Preencher o formulário na página oficial da vaga e anexar o PDF gerado para aquela oportunidade.
- Interromper imediatamente e solicitar intervenção humana em caso de CAPTCHA, verificação em duas etapas (2FA), perguntas inéditas sem resposta no perfil ou declarações legais não confirmadas.
- Registrar histórico, classificação e status atualizado em `vagas.csv` e `candidaturas_acompanhamento.csv`.

## 5. Rotina de Fim de Dia — Verificação de E-mail (Entrevistas e Rejeições)
- No final do dia (conforme horário configurado nas preferências operacionais), acessar a caixa de entrada do candidato e conferir os e-mails recebidos na data atual.
- Cruzar remetentes, assuntos e conteúdo com as empresas e vagas registradas em `candidaturas_acompanhamento.csv` e `vagas.csv`.
- Identificar retornos claros de **aprovação para entrevista** (convites, agendamento, próxima etapa ou teste técnico) e atualizar o status da vaga para `ENTREVISTA`, registrando data e resumo objetivo no campo de detalhes.
- Identificar retornos claros de **rejeição** (negativa ou encerramento do processo seletivo) e atualizar o status da vaga para `REJEITADA`, registrando data e resumo no campo de detalhes.
- Manter inalteradas as vagas sem retorno conclusivo; jamais responder e-mails ou confirmar horários de entrevista sem aprovação explícita do candidato.
- Interromper e solicitar intervenção humana caso o acesso ao e-mail exija login, 2FA ou apresente ambiguidade na classificação do retorno.
"""

PERFIL_CV_EXEMPLO = """# Perfil Profissional do Candidato (Preencha ou envie seu CV em PDF)

- Nome: [Seu Nome Completo]
- Localização / Fuso: [Cidade/Estado/País]
- Idiomas: [Seus idiomas e nível real]
- Formação: [Sua formação acadêmica]
- Experiências, Projetos e Competências:
  - [Descreva aqui apenas informações reais que o agente pode usar]
"""

CONFIG_PADRAO: Dict[str, Any] = {
    "plataformas": [
        {"nome": "Ashby", "nota": "Portais diretos de vagas"},
        {"nome": "Greenhouse", "nota": "Portais diretos de vagas"},
        {"nome": "Gupy", "nota": "Vagas no Brasil"},
        {"nome": "LinkedIn", "nota": "Buscas e candidaturas"},
    ],
    "vagas_buscadas": [
        {"cargo": "Desenvolvedor / Dados / Automação", "foco": "Palavras-chave e stack de interesse"},
    ],
    "modalidades": ["Remota"],
    "regimes": ["PJ", "CLT"],
    "modo_envio": "aprovacao",  # "aprovacao" | "automatico"
    "verificar_email_diario": True,
    "horario_email_diario": "18:00",
}

app = FastAPI(title="Job Hunter — OpenBot Dashboard")


def garantir_arquivos_iniciais() -> None:
    if not AGENTS_MD_PATH.exists():
        AGENTS_MD_PATH.write_text(AGENTS_UNIVERSAL_PADRAO.strip() + "\n", encoding="utf-8")
    if not PERFIL_CV_PATH.exists():
        PERFIL_CV_PATH.write_text(PERFIL_CV_EXEMPLO.strip() + "\n", encoding="utf-8")
    if not PERFIL_CV_TXT_PATH.exists():
        PERFIL_CV_TXT_PATH.write_text(ler_perfil_cv_bruto(), encoding="utf-8")


def ler_perfil_cv_bruto() -> str:
    if PERFIL_CV_PATH.exists():
        try:
            return PERFIL_CV_PATH.read_text(encoding="utf-8")
        except Exception:
            pass
    return PERFIL_CV_EXEMPLO.strip()


def ler_perfil_cv() -> str:
    garantir_arquivos_iniciais()
    try:
        return PERFIL_CV_PATH.read_text(encoding="utf-8")
    except Exception:
        return PERFIL_CV_EXEMPLO.strip()


def salvar_perfil_cv(texto: str) -> None:
    garantir_arquivos_iniciais()
    limpo = texto.strip() + "\n"
    shutil.copy2(PERFIL_CV_PATH, BASE_DIR / "perfil_cv_referencia.md.bak")
    if PERFIL_CV_TXT_PATH.exists():
        shutil.copy2(PERFIL_CV_TXT_PATH, BASE_DIR / "perfil_cv_referencia.txt.bak")
    PERFIL_CV_PATH.write_text(limpo, encoding="utf-8")
    PERFIL_CV_TXT_PATH.write_text(limpo, encoding="utf-8")


def limpar_texto_extraido(texto: str) -> str:
    linhas = [re.sub(r"[ \t]+", " ", ln).strip() for ln in texto.splitlines()]
    resultado: List[str] = []
    vazia_anterior = False
    for ln in linhas:
        if not ln:
            if not vazia_anterior and resultado:
                resultado.append("")
                vazia_anterior = True
        else:
            resultado.append(ln)
            vazia_anterior = False
    return "\n".join(resultado).strip()


def extrair_texto_pdf_bytes(pdf_bytes: bytes) -> Tuple[str, str]:
    tem_leitor = False

    try:
        from pypdf import PdfReader  # type: ignore

        tem_leitor = True
        reader = PdfReader(io.BytesIO(pdf_bytes))
        partes = [page.extract_text() or "" for page in reader.pages]
        texto = limpar_texto_extraido("\n\n".join(partes))
        if len(texto) >= 20:
            return texto, ""
    except ImportError:
        pass
    except Exception:
        pass

    try:
        import pdfplumber  # type: ignore

        tem_leitor = True
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            partes = [p.extract_text() or "" for p in pdf.pages]
        texto = limpar_texto_extraido("\n\n".join(partes))
        if len(texto) >= 20:
            return texto, ""
    except ImportError:
        pass
    except Exception:
        pass

    try:
        import fitz  # type: ignore

        tem_leitor = True
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        partes = [page.get_text("text") or "" for page in doc]
        texto = limpar_texto_extraido("\n\n".join(partes))
        if len(texto) >= 20:
            return texto, ""
    except ImportError:
        pass
    except Exception:
        pass

    if not tem_leitor:
        return "", "pdf_nolib"
    return "", "pdf_err"


def ler_config_painel() -> Dict[str, Any]:
    base = {
        "plataformas": [dict(x) for x in CONFIG_PADRAO["plataformas"]],
        "vagas_buscadas": [dict(x) for x in CONFIG_PADRAO["vagas_buscadas"]],
        "modalidades": list(CONFIG_PADRAO["modalidades"]),
        "regimes": list(CONFIG_PADRAO["regimes"]),
        "modo_envio": CONFIG_PADRAO["modo_envio"],
        "verificar_email_diario": CONFIG_PADRAO["verificar_email_diario"],
        "horario_email_diario": CONFIG_PADRAO["horario_email_diario"],
    }
    if CONFIG_JSON_PATH.exists():
        try:
            data = json.loads(CONFIG_JSON_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if isinstance(data.get("plataformas"), list):
                    base["plataformas"] = data["plataformas"]
                if isinstance(data.get("vagas_buscadas"), list):
                    base["vagas_buscadas"] = data["vagas_buscadas"]
                if isinstance(data.get("modalidades"), list):
                    base["modalidades"] = [str(m) for m in data["modalidades"] if m]
                if isinstance(data.get("regimes"), list):
                    base["regimes"] = [str(r) for r in data["regimes"] if r]
                if data.get("modo_envio") in ("aprovacao", "automatico"):
                    base["modo_envio"] = data["modo_envio"]
                if isinstance(data.get("verificar_email_diario"), bool):
                    base["verificar_email_diario"] = data["verificar_email_diario"]
                if isinstance(data.get("horario_email_diario"), str) and re.fullmatch(
                    r"\d{2}:\d{2}", data["horario_email_diario"].strip()
                ):
                    base["horario_email_diario"] = data["horario_email_diario"].strip()
        except Exception:
            pass
    return base


def sincronizar_config_no_agents(cfg: Dict[str, Any]) -> None:
    garantir_arquivos_iniciais()
    texto = AGENTS_MD_PATH.read_text(encoding="utf-8")

    plats = cfg.get("plataformas", [])
    linhas_plat = ["## Plataformas de Busca Ativas"]
    for p in plats:
        nome = str(p.get("nome", "")).strip()
        nota = str(p.get("nota", "")).strip()
        if nome:
            linhas_plat.append(f"- {nome}: {nota}" if nota else f"- {nome}")
    bloco_plat = "\n".join(linhas_plat)

    vagas_alvo = cfg.get("vagas_buscadas", [])
    mods = ", ".join(cfg.get("modalidades", [])) or "Remota"
    regs = ", ".join(cfg.get("regimes", [])) or "PJ"
    modo_txt = (
        "Exige aprovação humana antes do envio final"
        if cfg.get("modo_envio") == "aprovacao"
        else "Envio automático nas vagas elegíveis (respeitando pausas de bloqueio/CAPTCHA/2FA)"
    )
    email_ativo = bool(cfg.get("verificar_email_diario", True))
    horario_email = str(cfg.get("horario_email_diario", "18:00") or "18:00")
    email_txt = (
        f"Ativa no final do dia ({horario_email}) — conferir e-mails do dia para identificar rejeições ou aprovações para entrevista e atualizar status nos CSVs"
        if email_ativo
        else "Desativada"
    )

    linhas_pref = [
        "## Preferências Operacionais Ativas",
        f"- Modalidades aceitas: {mods}",
        f"- Regimes aceitos: {regs}",
        f"- Modo de envio: {modo_txt}",
        f"- Verificação diária de e-mail: {email_txt}",
        "- Cargos e frentes buscadas:",
    ]
    for v in vagas_alvo:
        cargo = str(v.get("cargo", "")).strip()
        foco = str(v.get("foco", "")).strip()
        if cargo:
            linhas_pref.append(f"  - {cargo} ({foco})" if foco else f"  - {cargo}")
    bloco_pref = "\n".join(linhas_pref)

    padrao_plat = re.compile(r"## Plataformas de Busca Ativas.*?(?=\n## |\Z)", re.DOTALL)
    if padrao_plat.search(texto):
        texto = padrao_plat.sub(bloco_plat, texto)
    else:
        texto = texto.rstrip() + "\n\n" + bloco_plat + "\n"

    padrao_pref = re.compile(r"## Preferências Operacionais Ativas.*?(?=\n## |\Z)", re.DOTALL)
    if padrao_pref.search(texto):
        texto = padrao_pref.sub(bloco_pref, texto)
    else:
        texto = texto.rstrip() + "\n\n" + bloco_pref + "\n"

    AGENTS_MD_PATH.write_text(texto, encoding="utf-8")


def salvar_config_painel(data: Dict[str, Any]) -> None:
    if CONFIG_JSON_PATH.exists():
        shutil.copy2(CONFIG_JSON_PATH, BASE_DIR / "config_painel.json.bak")
    CONFIG_JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if AGENTS_MD_PATH.exists():
        shutil.copy2(AGENTS_MD_PATH, BASE_DIR / "AGENTS.md.bak")
    sincronizar_config_no_agents(data)


def ler_csv_seguro(caminho: Path) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with caminho.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                linhas = []
                for row in reader:
                    limpa = {k: (v if v is not None else "") for k, v in row.items() if k is not None}
                    if any(str(v).strip() for v in limpa.values()):
                        linhas.append(limpa)
                return linhas
        except Exception:
            continue
    return []


def salvar_csv_atomico(caminho: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    """Grava CSV de forma segura (backup + arquivo temporário + replace) sem risco de zerar dados."""
    if caminho.exists():
        shutil.copy2(caminho, caminho.with_suffix(caminho.suffix + ".bak"))
    tmp_path = caminho.with_suffix(caminho.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            limpa = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(limpa)
    os.replace(tmp_path, caminho)


def ler_tabelas_openbot() -> List[Dict[str, Any]]:
    if not OPENBOT_DIR.exists():
        return []
    db_files = list(OPENBOT_DIR.glob("*.db")) + list(OPENBOT_DIR.glob("*.sqlite*"))
    if not db_files:
        return []

    resultados = []
    for db_path in db_files:
        try:
            uri = f"file:{db_path.as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                )
                tabelas = [r["name"] for r in cur.fetchall()]
                for t in tabelas:
                    cur.execute(f'SELECT COUNT(*) as total FROM "{t}"')
                    total = cur.fetchone()["total"]
                    cur.execute(f'SELECT * FROM "{t}" LIMIT 50')
                    linhas = [dict(r) for r in cur.fetchall()]
                    resultados.append(
                        {"db": db_path.name, "tabela": t, "total": total, "linhas": linhas}
                    )
        except Exception:
            continue
    return resultados


def formatar_data_hora_rotina(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "—"
    try:
        val = str(iso_str).strip()
        if "T" in val:
            clean = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean)
            return dt.strftime("%d/%m/%Y %H:%M")
        return val[:19]
    except Exception:
        return str(iso_str)[:19]


def ler_rotinas_openbot() -> Dict[str, Any]:
    db_path = Path(os.environ.get("APPDATA", "")) / "OpenBot" / "openbot.db"
    if not db_path.exists():
        db_path = Path.home() / "AppData" / "Roaming" / "OpenBot" / "openbot.db"

    rotinas = []
    runs = []
    if db_path.exists():
        try:
            uri = f"file:{db_path.as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=5.0) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                    SELECT r.routine_id, r.name, r.instruction, r.active, r.timezone, r.limit_policy, r.missed_policy,
                           t.schedule_json, t.next_run_at
                    FROM projection_agent_routines r
                    LEFT JOIN projection_routine_triggers t ON r.routine_id = t.routine_id
                    WHERE r.agent_id = 'agent-93c9d1f9-d7b6-421f-a70b-169559a3e5ed'
                    ORDER BY r.name
                """)
                rotinas = [dict(row) for row in cur.fetchall()]

                cur.execute("""
                    SELECT run_id, routine_name, run_kind, scheduled_for, status, error, created_at, missed_count
                    FROM projection_routine_runs
                    WHERE agent_id = 'agent-93c9d1f9-d7b6-421f-a70b-169559a3e5ed'
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
                runs = [dict(row) for row in cur.fetchall()]
        except Exception:
            pass

    if not rotinas:
        rotinas = [
            {
                "routine_id": "c36badf9-bc0f-4464-9793-9d86e09eeea1",
                "name": "Busca Diária de Oportunidades - Job Hunter",
                "instruction": "Varredura diária das 09h00 nas APIs públicas (Greenhouse, Himalayas, Remotive, RemoteOK, etc.) sem duplicatas.",
                "active": 1,
                "timezone": "America/Rio_Branco",
                "schedule_json": json.dumps({"kind": "daily", "time": "09:00"}),
                "next_run_at": "Diariamente às 09:00",
            },
            {
                "routine_id": "b61c290f-1bdf-48c5-9581-c0798ff7ab09",
                "name": "Busca Incremental de Oportunidades - Job Hunter",
                "instruction": "Varredura incremental das 15h00 nas APIs públicas para capturar novas vagas do dia.",
                "active": 1,
                "timezone": "America/Rio_Branco",
                "schedule_json": json.dumps({"kind": "daily", "time": "15:00"}),
                "next_run_at": "Diariamente às 15:00",
            },
        ]
    return {"rotinas": rotinas, "runs": runs}


def listar_curriculos() -> List[Dict[str, Any]]:
    if not CURRICULOS_DIR.exists():
        return []
    arquivos = []
    for pdf in sorted(CURRICULOS_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = pdf.stat()
        arquivos.append(
            {
                "nome": pdf.name,
                "tamanho_kb": round(stat.st_size / 1024, 1),
                "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            }
        )
    return arquivos


def extrair_url(texto: str) -> str:
    if not texto:
        return ""
    m = re.search(r"(https?://[^\s\)\]]+)", texto)
    return m.group(1) if m else ""


def extrair_nome_plataforma(texto: str) -> str:
    if not texto:
        return "Plataforma"
    limpo = re.sub(r"\(https?://[^\)]+\)", "", texto).strip()
    limpo = re.sub(r"https?://[^\s]+", "", limpo).strip()
    return limpo if limpo else "Link Oficial"


def encontrar_pdf_empresa(empresa: str, curriculos: List[Dict[str, Any]]) -> Optional[str]:
    if not empresa:
        return None
    slug = re.sub(r"[^a-z0-9]", "", empresa.lower())
    if not slug:
        return None
    for c in curriculos:
        nome_slug = re.sub(r"[^a-z0-9]", "", c["nome"].lower())
        if slug[:6] in nome_slug:
            return c["nome"]
    return None


def get_campo(row: Dict[str, str], *candidatos: str, excluir_id: bool = False) -> str:
    for k, v in row.items():
        if not k:
            continue
        k_norm = k.strip().lower()
        if excluir_id and ("id" in k_norm):
            continue
        for c in candidatos:
            if c in k_norm and v:
                return str(v).strip()
    return ""


def detectar_regiao_vaga(texto_completo: str) -> str:
    t = (texto_completo or "").lower()
    if any(k in t for k in ("brasil", "brazil", "portuguese", "pt-br", "br")):
        return "Brasil"
    if any(k in t for k in ("united states", "usa", "u.s.", "us remote", "new york", "san francisco", "california", "est / pst")):
        return "EUA"
    if any(k in t for k in ("europe", "europa", "uk", "united kingdom", "germany", "spain", "portugal", "bucareste", "bucharest", "cet")):
        return "Europa"
    if any(k in t for k in ("latam", "latin america", "américa latina", "mexico", "argentina", "colombia", "chile", "peru")):
        return "LATAM"
    if any(k in t for k in ("canada", "toronto", "vancouver")):
        return "Canadá"
    if "remote" in t or "remoto" in t:
        return "Global / Remoto"
    return "Brasil"


def eh_status_entrevista(status: str) -> bool:
    s = (status or "").lower()
    return "entrevista" in s or "interview" in s


def eh_status_rejeitada(status: str) -> bool:
    s = (status or "").lower()
    return "rejeit" in s or "rejected" in s or "recusad" in s


def eh_status_candidatada(status: str) -> bool:
    s = (status or "").lower()
    return (
        "enviada" in s
        or "aplicad" in s
        or eh_status_entrevista(s)
        or eh_status_rejeitada(s)
    )


def classificar_vaga_real(classif_raw: str, status_raw: str) -> str:
    c_low = (classif_raw or "").strip().lower()
    s_low = (status_raw or "").strip().lower()

    if eh_status_entrevista(s_low) or eh_status_rejeitada(s_low) or "enviada" in s_low or "aplicad" in s_low:
        return "ALTA COMPATIBILIDADE"

    combinado = f"{c_low} {s_low}"

    if any(k in combinado for k in ("incompat", "descart", "exclu")):
        return "INCOMPATÍVEL"

    if any(k in combinado for k in ("pendente", "aguard", "human", "captcha", "2fa")):
        return "PENDENTE DE VALIDAÇÃO"

    if any(k in c_low for k in ("alta", "compatível", "compativel", "elegível", "elegivel")):
        return "ALTA COMPATIBILIDADE"

    return "PENDENTE DE VALIDAÇÃO"


def consolidar_itens(
    vagas: List[Dict[str, str]],
    candidaturas: List[Dict[str, str]],
    curriculos: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    cand_por_id: Dict[str, Dict[str, str]] = {}
    cand_por_chave: Dict[str, Dict[str, str]] = {}

    for c in candidaturas:
        vid = get_campo(c, "id_vaga", "id vaga", "id")
        emp = get_campo(c, "empresa", excluir_id=True)
        cargo = get_campo(c, "cargo", "título", "titulo", "role", "position", excluir_id=True)
        if vid:
            cand_por_id[vid] = c
        if emp or cargo:
            cand_por_chave[f"{emp.lower()}|{cargo.lower()}"] = c

    itens: List[Dict[str, Any]] = []
    ids_usados = set()

    for idx, v in enumerate(vagas, start=1):
        vid = get_campo(v, "id_vaga", "id vaga", "id") or str(idx)
        emp = get_campo(v, "empresa", excluir_id=True) or "Empresa não informada"
        cargo = get_campo(v, "cargo", "título", "titulo", "role", "position", excluir_id=True) or "Cargo não informado"
        classif_raw = get_campo(
            v, "classificacao", "classificação", "compatibilidade", "decisao", "decisão", "triagem", "status", excluir_id=True
        )
        plat_raw = get_campo(v, "plataforma", "fonte", "origem", "url", "link", excluir_id=True)
        data_reg = get_campo(v, "data", "criado", "submiss", excluir_id=True)
        resumo = get_campo(v, "resumo", "descri", "requisito", "observ", "detalhe", "motivo", excluir_id=True)
        local_raw = get_campo(v, "local", "país", "pais", "região", "regiao", "modalidade", excluir_id=True)

        c = cand_por_id.get(vid) or cand_por_chave.get(f"{emp.lower()}|{cargo.lower()}")
        if c:
            ids_usados.add(id(c))
            status_etapa = get_campo(c, "status", "etapa", excluir_id=True) or "REGISTRADA"
            detalhes_etapa = get_campo(c, "detalhe", "observ", "motivo", excluir_id=True) or resumo
            plat_c = get_campo(c, "plataforma", "url", "link", excluir_id=True)
            if plat_c:
                plat_raw = plat_c
            data_c = get_campo(c, "data", "submiss", excluir_id=True)
            if data_c:
                data_reg = data_c
        else:
            status_etapa = get_campo(v, "status", "etapa", excluir_id=True) or "TRIADA"
            detalhes_etapa = resumo

        classif_real = classificar_vaga_real(classif_raw, status_etapa)
        url = extrair_url(plat_raw) or extrair_url(get_campo(v, "url", "link", excluir_id=True))
        plataforma = extrair_nome_plataforma(plat_raw)
        pdf_match = encontrar_pdf_empresa(emp, curriculos)
        regiao = detectar_regiao_vaga(f"{local_raw} {cargo} {detalhes_etapa} {plat_raw}")

        texto_geral = f"{classif_real} {status_etapa} {detalhes_etapa}".lower()
        precisa_humano = (
            classif_real != "INCOMPATÍVEL"
            and not eh_status_candidatada(status_etapa)
            and any(
                t in texto_geral
                for t in ("captcha", "2fa", "humana", "humano", "pendente", "interromp", "elegibilidade", "declara")
            )
        )

        itens.append(
            {
                "id": vid,
                "empresa": emp,
                "cargo": cargo,
                "classificacao": classif_real,
                "status": status_etapa,
                "detalhes": detalhes_etapa,
                "plataforma": plataforma,
                "url": url,
                "data": data_reg,
                "pdf": pdf_match,
                "regiao": regiao,
                "precisa_humano": precisa_humano,
            }
        )

    for c in candidaturas:
        if id(c) in ids_usados:
            continue
        vid = get_campo(c, "id_vaga", "id vaga", "id") or "-"
        emp = get_campo(c, "empresa", excluir_id=True) or "Empresa"
        cargo = get_campo(c, "cargo", "título", "titulo", "role", "position", excluir_id=True) or "Vaga"
        status_etapa = get_campo(c, "status", "etapa", excluir_id=True) or "ENVIADA"
        detalhes_etapa = get_campo(c, "detalhe", "observ", "motivo", excluir_id=True)
        plat_raw = get_campo(c, "plataforma", "url", "link", excluir_id=True)
        data_reg = get_campo(c, "data", "submiss", excluir_id=True)
        local_raw = get_campo(c, "local", "país", "pais", "região", "regiao", "modalidade", excluir_id=True)
        url = extrair_url(plat_raw)
        plataforma = extrair_nome_plataforma(plat_raw)
        pdf_match = encontrar_pdf_empresa(emp, curriculos)
        regiao = detectar_regiao_vaga(f"{local_raw} {cargo} {detalhes_etapa} {plat_raw}")

        classif_real = classificar_vaga_real("", status_etapa)
        texto_geral = f"{status_etapa} {detalhes_etapa}".lower()
        precisa_humano = (
            classif_real != "INCOMPATÍVEL"
            and not eh_status_candidatada(status_etapa)
            and any(
                t in texto_geral
                for t in ("captcha", "2fa", "humana", "humano", "pendente", "interromp", "elegibilidade", "declara")
            )
        )

        itens.append(
            {
                "id": vid,
                "empresa": emp,
                "cargo": cargo,
                "classificacao": classif_real,
                "status": status_etapa,
                "detalhes": detalhes_etapa,
                "plataforma": plataforma,
                "url": url,
                "data": data_reg,
                "pdf": pdf_match,
                "regiao": regiao,
                "precisa_humano": precisa_humano,
            }
        )

    return itens


def atualizar_status_vaga_csvs(vaga_id: str, novo_status: str, nota_detalhe: str) -> None:
    hoje = datetime.now().strftime("%d/%m/%Y")
    vagas_rows = ler_csv_seguro(VAGAS_CSV)
    vaga_origem: Optional[Dict[str, str]] = None

    if vagas_rows:
        vagas_fields = list(vagas_rows[0].keys())
        vaga_alterada = False
        for idx, vr in enumerate(vagas_rows, start=1):
            vid = get_campo(vr, "id_vaga", "id vaga", "id") or str(idx)
            if vid == vaga_id:
                vaga_origem = dict(vr)
                for k in vagas_fields:
                    kl = k.lower()
                    if "status" in kl or "etapa" in kl:
                        vr[k] = novo_status
                        vaga_alterada = True
                break
        if vaga_alterada:
            salvar_csv_atomico(VAGAS_CSV, vagas_fields, vagas_rows)

    cand_rows = ler_csv_seguro(CANDIDATURAS_CSV)
    if cand_rows:
        cand_fields = list(cand_rows[0].keys())
    else:
        cand_fields = ["ID_VAGA", "EMPRESA", "CARGO", "DATA_SUBMISSAO", "PLATAFORMA_ENVIO", "STATUS_ETAPA", "DETALHES_ETAPA"]

    atualizado = False
    for r in cand_rows:
        vid = get_campo(r, "id_vaga", "id vaga", "id")
        if vid == vaga_id:
            for k in cand_fields:
                kl = k.lower()
                if "status" in kl or "etapa" in kl:
                    r[k] = novo_status
                elif "data" in kl or "submiss" in kl:
                    if not r[k]:
                        r[k] = hoje
                elif "detalhe" in kl or "observ" in kl:
                    r[k] = nota_detalhe
            atualizado = True
            break

    if not atualizado:
        emp = get_campo(vaga_origem, "empresa", excluir_id=True) if vaga_origem else ""
        cargo = get_campo(vaga_origem, "cargo", "título", "titulo", "role", "position", excluir_id=True) if vaga_origem else ""
        plat = get_campo(vaga_origem, "plataforma", "fonte", "origem", "url", "link", excluir_id=True) if vaga_origem else ""
        nova_cand = {k: "" for k in cand_fields}
        for k in cand_fields:
            kl = k.lower()
            if "id" in kl:
                nova_cand[k] = vaga_id
            elif "empresa" in kl:
                nova_cand[k] = emp
            elif ("cargo" in kl or "titulo" in kl or "título" in kl) and "id" not in kl:
                nova_cand[k] = cargo
            elif "data" in kl or "submiss" in kl:
                nova_cand[k] = hoje
            elif "plataf" in kl or "envio" in kl or "url" in kl or "link" in kl:
                nova_cand[k] = plat
            elif "status" in kl or "etapa" in kl:
                nova_cand[k] = novo_status
            elif "detalhe" in kl or "observ" in kl:
                nova_cand[k] = nota_detalhe
        cand_rows.append(nova_cand)

    salvar_csv_atomico(CANDIDATURAS_CSV, cand_fields, cand_rows)


@app.get("/", response_class=HTMLResponse)
def dashboard(tab: str = "painel", saved: str = ""):
    garantir_arquivos_iniciais()
    vagas = ler_csv_seguro(VAGAS_CSV)
    candidaturas = ler_csv_seguro(CANDIDATURAS_CSV)
    curriculos = listar_curriculos()
    itens = consolidar_itens(vagas, candidaturas, curriculos)
    cfg = ler_config_painel()
    perfil_cv = ler_perfil_cv()

    plataformas_cfg: List[Dict[str, str]] = cfg.get("plataformas", [])
    vagas_buscadas_cfg: List[Dict[str, str]] = cfg.get("vagas_buscadas", [])
    modalidades_cfg: List[str] = cfg.get("modalidades", [])
    regimes_cfg: List[str] = cfg.get("regimes", [])
    modo_envio_cfg: str = cfg.get("modo_envio", "aprovacao")
    verificar_email_cfg: bool = bool(cfg.get("verificar_email_diario", True))
    horario_email_cfg: str = str(cfg.get("horario_email_diario", "18:00"))

    agents_texto = AGENTS_MD_PATH.read_text(encoding="utf-8") if AGENTS_MD_PATH.exists() else ""

    total_vagas = len(itens)
    total_enviadas = sum(1 for i in itens if eh_status_candidatada(i["status"]))
    total_entrevistas = sum(1 for i in itens if eh_status_entrevista(i["status"]))
    total_rejeitadas = sum(1 for i in itens if eh_status_rejeitada(i["status"]))
    total_alta = sum(1 for i in itens if i["classificacao"] == "ALTA COMPATIBILIDADE")
    total_incomp = sum(1 for i in itens if i["classificacao"] == "INCOMPATÍVEL")
    total_humano = sum(1 for i in itens if i["precisa_humano"])
    ultimo_pdf = curriculos[0]["nome"] if curriculos else "Nenhum PDF gerado ainda"

    aplicacoes_por_regiao: Dict[str, int] = {}
    for i in itens:
        if eh_status_candidatada(i["status"]):
            r = i.get("regiao") or "Brasil"
            aplicacoes_por_regiao[r] = aplicacoes_por_regiao.get(r, 0) + 1

    nomes_plat_cfg = [p.get("nome", "").strip() for p in plataformas_cfg if p.get("nome", "").strip()]
    nomes_plat_itens = [i["plataforma"] for i in itens if i["plataforma"] and i["plataforma"] != "Plataforma"]
    plataformas_filtro = list(dict.fromkeys(nomes_plat_cfg + nomes_plat_itens))

    toast_map = {
        "agents": "Diretrizes salvas em AGENTS.md (backup criado em AGENTS.md.bak).",
        "agents_reset": "AGENTS.md restaurado para o processo universal (incluindo verificação diária de e-mail; backup salvo em AGENTS.md.bak).",
        "perfil": "Perfil / CV do usuário salvo em perfil_cv_referencia.md e perfil_cv_referencia.txt.",
        "pdf_txt": "CV em PDF convertido para TXT (perfil_cv_referencia.txt) e sincronizado na base do perfil.",
        "pdf_nolib": "Biblioteca de leitura de PDF não instalada. Rode 'python -m pip install pypdf' no terminal e tente novamente.",
        "pdf_err": "Não foi possível extrair texto desse PDF (pode ser uma imagem escaneada). Tente outro PDF ou cole o texto manualmente.",
        "vaga": "Nova vaga adicionada ao fluxo do agente.",
        "status": "Status da candidatura atualizado para ENVIADA.",
        "status_entrevista": "Vaga marcada como ENTREVISTA.",
        "status_rejeitada": "Vaga marcada como REJEITADA.",
        "status_err": "Erro ao salvar status no CSV. Verifique se o arquivo não está aberto no Excel.",
        "plat_add": "Plataforma adicionada às buscas.",
        "plat_edit": "Plataforma atualizada.",
        "plat_del": "Plataforma removida das buscas.",
        "alvo_add": "Cargo/frente de busca adicionado.",
        "alvo_edit": "Cargo/frente de busca atualizado.",
        "alvo_del": "Cargo/frente de busca removido.",
        "pref": "Preferências operacionais e rotina de e-mail salvas e sincronizadas no AGENTS.md.",
        "rotina_busca": "Varredura diária disparada em segundo plano.",
        "rotina_inc": "Varredura incremental disparada em segundo plano.",
    }
    toast_cls = "toast toast-err" if saved in ("pdf_err", "pdf_nolib", "status_err") else "toast"
    toast_html = f'<div class="{toast_cls}">{html.escape(toast_map[saved])}</div>' if saved in toast_map else ""

    if tab == "configuracoes":
        linhas_plat = []
        for idx, p in enumerate(plataformas_cfg):
            nome_p = html.escape(str(p.get("nome", "")))
            nota_p = html.escape(str(p.get("nota", "")))
            linhas_plat.append(
                f"""
                <div class="list-edit-item">
                    <form method="post" action="/configuracoes/plataformas/alterar" class="inline-edit-form">
                        <input type="hidden" name="indice" value="{idx}">
                        <input type="text" name="nome" value="{nome_p}" required placeholder="Plataforma" class="inp-sm">
                        <input type="text" name="nota" value="{nota_p}" placeholder="Foco / observação" class="inp-lg">
                        <button type="submit" class="btn btn-soft">Salvar</button>
                    </form>
                    <form method="post" action="/configuracoes/plataformas/remover" class="inline-del-form">
                        <input type="hidden" name="indice" value="{idx}">
                        <button type="submit" class="btn btn-danger-soft">Remover</button>
                    </form>
                </div>
                """
            )

        linhas_alvos = []
        for idx, v in enumerate(vagas_buscadas_cfg):
            cargo_v = html.escape(str(v.get("cargo", "")))
            foco_v = html.escape(str(v.get("foco", "")))
            linhas_alvos.append(
                f"""
                <div class="list-edit-item">
                    <form method="post" action="/configuracoes/vagas-buscadas/alterar" class="inline-edit-form">
                        <input type="hidden" name="indice" value="{idx}">
                        <input type="text" name="cargo" value="{cargo_v}" required placeholder="Cargo ou palavra-chave" class="inp-sm">
                        <input type="text" name="foco" value="{foco_v}" placeholder="Stack / critério de busca" class="inp-lg">
                        <button type="submit" class="btn btn-soft">Salvar</button>
                    </form>
                    <form method="post" action="/configuracoes/vagas-buscadas/remover" class="inline-del-form">
                        <input type="hidden" name="indice" value="{idx}">
                        <button type="submit" class="btn btn-danger-soft">Remover</button>
                    </form>
                </div>
                """
            )

        def chk_mod(nome_m: str) -> str:
            checked = "checked" if nome_m in modalidades_cfg else ""
            return f'<label class="check-pill"><input type="checkbox" name="modalidades" value="{html.escape(nome_m)}" {checked}> {html.escape(nome_m)}</label>'

        def chk_reg(nome_r: str) -> str:
            checked = "checked" if nome_r in regimes_cfg else ""
            return f'<label class="check-pill"><input type="checkbox" name="regimes" value="{html.escape(nome_r)}" {checked}> {html.escape(nome_r)}</label>'

        sel_aprov = "checked" if modo_envio_cfg == "aprovacao" else ""
        sel_auto = "checked" if modo_envio_cfg == "automatico" else ""
        chk_email = "checked" if verificar_email_cfg else ""
        email_resumo_txt = f"Ativa às {html.escape(horario_email_cfg)}" if verificar_email_cfg else "Desativada"

        conteudo_principal = f"""
        <div class="config-grid">
            <div class="config-main">

                <div class="card">
                    <div class="card-head">
                        <div>
                            <h2>Perfil & CV do Candidato</h2>
                            <p class="muted">Envie um CV em PDF para converter em TXT e usar como base factual do candidato, ou edite diretamente abaixo.</p>
                        </div>
                        <span class="tag-mono">perfil_cv_referencia.txt</span>
                    </div>

                    <form method="post" action="/configuracoes/perfil/upload-pdf" enctype="multipart/form-data" class="pdf-upload-box">
                        <div class="pdf-upload-row">
                            <input type="file" name="arquivo_pdf" accept="application/pdf,.pdf" required class="inp-file">
                            <button type="submit" class="btn btn-primary">Converter PDF → TXT</button>
                        </div>
                        <div class="muted">Requer <code>pypdf</code> instalado (<code>python -m pip install pypdf</code>).</div>
                    </form>

                    <form method="post" action="/configuracoes/perfil/salvar">
                        <textarea name="cv_texto" rows="13" spellcheck="false">{html.escape(perfil_cv)}</textarea>
                        <div class="form-bar">
                            <span class="muted">Qualificações, formação, idiomas e experiências vivem exclusivamente aqui.</span>
                            <button type="submit" class="btn btn-soft">Salvar Texto do Perfil</button>
                        </div>
                    </form>
                </div>

                <div class="card">
                    <div class="card-head">
                        <div>
                            <h2>Vagas Buscadas (Cargos & Frentes)</h2>
                            <p class="muted">Adicione, altere ou remova os perfis de vaga que o agente deve buscar.</p>
                        </div>
                        <span class="tag-mono">{len(vagas_buscadas_cfg)} alvos</span>
                    </div>
                    <form method="post" action="/configuracoes/vagas-buscadas/adicionar" class="add-row-form">
                        <input type="text" name="cargo" required placeholder="Novo cargo ou tema (ex.: Backend Python, Dados)" class="inp-sm">
                        <input type="text" name="foco" placeholder="Foco ou palavras-chave (opcional)" class="inp-lg">
                        <button type="submit" class="btn btn-primary">+ Adicionar</button>
                    </form>
                    <div class="edit-list">
                        {''.join(linhas_alvos) if linhas_alvos else '<div class="empty">Nenhum cargo/frente cadastrado.</div>'}
                    </div>
                </div>

                <div class="card">
                    <div class="card-head">
                        <div>
                            <h2>Modalidade, Regime, Envio & Rotina de E-mail</h2>
                            <p class="muted">Defina trabalho Integral/Híbrida/Remota, CLT/PJ, aprovação prévia e conferência diária de retornos no e-mail.</p>
                        </div>
                        <span class="tag-mono">Execução</span>
                    </div>
                    <form method="post" action="/configuracoes/preferencias/salvar">
                        <div class="pref-block">
                            <div class="pref-label">Modalidade de Trabalho</div>
                            <div class="check-row">
                                {chk_mod("Integral")}
                                {chk_mod("Híbrida")}
                                {chk_mod("Remota")}
                            </div>
                        </div>

                        <div class="pref-block">
                            <div class="pref-label">Modelo de Contratação</div>
                            <div class="check-row">
                                {chk_reg("CLT")}
                                {chk_reg("PJ")}
                            </div>
                        </div>

                        <div class="pref-block">
                            <div class="pref-label">Envio de Candidatura</div>
                            <div class="radio-group">
                                <label class="radio-card">
                                    <input type="radio" name="modo_envio" value="aprovacao" {sel_aprov}>
                                    <div>
                                        <strong>Exige Aprovação</strong>
                                        <span>Prepara e aguarda confirmação antes de submeter.</span>
                                    </div>
                                </label>
                                <label class="radio-card">
                                    <input type="radio" name="modo_envio" value="automatico" {sel_auto}>
                                    <div>
                                        <strong>Envio Automático</strong>
                                        <span>Submete automaticamente nas vagas elegíveis (pausando em CAPTCHA/2FA/dúvidas).</span>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <div class="pref-block">
                            <div class="pref-label">Verificação de E-mail no Final do Dia</div>
                            <div class="email-routine-row">
                                <label class="check-pill">
                                    <input type="checkbox" name="verificar_email_diario" value="1" {chk_email}>
                                    Conferir e-mails do dia (entrevistas e rejeições)
                                </label>
                                <label class="time-pill">
                                    <span>Horário:</span>
                                    <input type="time" name="horario_email_diario" value="{html.escape(horario_email_cfg)}" class="inp-time">
                                </label>
                            </div>
                        </div>

                        <div class="form-bar">
                            <span class="muted">Sincroniza automaticamente no <code>AGENTS.md</code> ao salvar.</span>
                            <button type="submit" class="btn btn-primary">Salvar Preferências</button>
                        </div>
                    </form>
                </div>

                <div class="card">
                    <div class="card-head">
                        <div>
                            <h2>Plataformas de Busca</h2>
                            <p class="muted">Adicione, altere ou remova as fontes onde o agente realiza buscas e candidaturas.</p>
                        </div>
                        <span class="tag-mono">{len(plataformas_cfg)} ativas</span>
                    </div>

                    <form method="post" action="/configuracoes/plataformas/adicionar" class="add-row-form">
                        <input type="text" name="nome" required placeholder="Nova plataforma (ex.: Ashby, Greenhouse, Gupy)" class="inp-sm">
                        <input type="text" name="nota" placeholder="Observação ou filtro de busca (opcional)" class="inp-lg">
                        <button type="submit" class="btn btn-primary">+ Adicionar</button>
                    </form>

                    <div class="edit-list">
                        {''.join(linhas_plat) if linhas_plat else '<div class="empty">Nenhuma plataforma cadastrada.</div>'}
                    </div>
                </div>

                <div class="card">
                    <div class="card-head">
                        <div>
                            <h2>Diretrizes de Comportamento (AGENTS.md)</h2>
                            <p class="muted">Define apenas o processo de como o agente trabalha, sem qualificações pessoais embutidas.</p>
                        </div>
                        <div class="mid-actions">
                            <form method="post" action="/configuracoes/agents/reset-universal" style="margin:0;">
                                <button type="submit" class="btn btn-soft">Restaurar Padrão Universal</button>
                            </form>
                            <span class="tag-mono">AGENTS.md</span>
                        </div>
                    </div>
                    <form method="post" action="/configuracoes/salvar">
                        <textarea name="conteudo" rows="16" spellcheck="false">{html.escape(agents_texto)}</textarea>
                        <div class="form-bar">
                            <span class="muted">Backup automático em <code>AGENTS.md.bak</code> antes de gravar.</span>
                            <button type="submit" class="btn btn-primary">Salvar Diretrizes</button>
                        </div>
                    </form>
                </div>
            </div>

            <div class="config-side">
                <div class="card">
                    <h3>Resumo da Configuração Ativa</h3>
                    <ul class="clean-list">
                        <li><strong>Modalidades:</strong> {html.escape(', '.join(modalidades_cfg) or 'Remota')}</li>
                        <li><strong>Regimes:</strong> {html.escape(', '.join(regimes_cfg) or 'PJ')}</li>
                        <li><strong>Envio:</strong> {'Exige Aprovação' if modo_envio_cfg == 'aprovacao' else 'Automático'}</li>
                        <li><strong>Checagem de e-mail:</strong> {email_resumo_txt}</li>
                        <li><strong>Cargos alvo:</strong> {len(vagas_buscadas_cfg)} configurados</li>
                        <li><strong>Plataformas:</strong> {len(plataformas_cfg)} ativas</li>
                    </ul>
                </div>

                <div class="card">
                    <h3>Separação para Uso Público</h3>
                    <p class="muted">Como o projeto fica organizado para qualquer usuário:</p>
                    <ul class="clean-list">
                        <li><code>AGENTS.md</code>: apenas processo/comportamento.</li>
                        <li><code>perfil_cv_referencia.txt</code>: qualificações e CV.</li>
                        <li><code>config_painel.json</code>: alvos, regimes e envio.</li>
                    </ul>
                </div>
            </div>
        </div>
        """
    elif tab == "rotinas":
        dados_rotinas = ler_rotinas_openbot()
        rotinas_lista = dados_rotinas.get("rotinas", [])
        runs_lista = dados_rotinas.get("runs", [])

        total_rotinas_ativas = sum(1 for r in rotinas_lista if r.get("active"))
        if verificar_email_cfg:
            total_rotinas_ativas += 1

        ultima_exec = runs_lista[0] if runs_lista else {}
        status_ult = ultima_exec.get("status", "—")
        data_ult = formatar_data_hora_rotina(ultima_exec.get("created_at"))

        proximos_disparos = [r.get("next_run_at") for r in rotinas_lista if r.get("next_run_at")]
        proximo_txt = formatar_data_hora_rotina(proximos_disparos[0]) if proximos_disparos else "Conforme agendamento"

        cards_rotinas_html = []
        for r in rotinas_lista:
            r_name = html.escape(str(r.get("name", "Rotina")))
            r_active = bool(r.get("active", True))
            r_tz = html.escape(str(r.get("timezone", "America/Rio_Branco")))
            r_next = formatar_data_hora_rotina(r.get("next_run_at"))

            sched_str = "Horário agendado"
            try:
                sj = json.loads(r.get("schedule_json") or "{}")
                if sj.get("kind") == "daily":
                    sched_str = f"Diariamente às {sj.get('time', '00:00')} ({r_tz})"
            except Exception:
                sched_str = str(r.get("schedule_json") or "Diário")

            badge_ativo = '<span class="badge badge-ok">● Ativa</span>' if r_active else '<span class="badge badge-neutral">Inativa</span>'
            instr_raw = str(r.get("instruction", ""))
            instr_resumo = html.escape(instr_raw[:260] + ("..." if len(instr_raw) > 260 else ""))

            if "E-mail" in r_name or "Email" in r_name:
                form_action = "/configuracoes"
                btn_action = '<a href="/?tab=configuracoes" class="btn btn-soft">⚙ Ajustar nas Configurações</a>'
            elif "Diária" in r_name:
                btn_action = '<form method="post" action="/rotinas/executar-busca" style="margin: 0;"><button type="submit" class="btn btn-soft">▶ Disparar Busca Agora</button></form>'
            else:
                btn_action = '<form method="post" action="/rotinas/executar-incremental" style="margin: 0;"><button type="submit" class="btn btn-soft">▶ Disparar Incremental Agora</button></form>'

            cards_rotinas_html.append(
                f"""
                <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                            <h3 style="margin: 0; font-size: 1.05rem;">{r_name}</h3>
                            {badge_ativo}
                        </div>
                        <p class="muted" style="margin-bottom: 0.6rem; font-size: 0.88rem;"><strong>Frequência:</strong> {html.escape(sched_str)}</p>
                        <p class="muted" style="margin-bottom: 0.8rem; font-size: 0.85rem; line-height: 1.45;">{instr_resumo}</p>
                        <div style="font-size: 0.82rem; margin-bottom: 1rem; color: var(--text-soft);">
                            <div><strong>Próximo disparo:</strong> {html.escape(r_next)}</div>
                            <div><strong>Política de atraso:</strong> {html.escape(str(r.get('missed_policy', 'skip')))} (ignora execuções se o app estiver fechado)</div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; border-top: 1px solid var(--border); padding-top: 0.85rem;">
                        {btn_action}
                    </div>
                </div>
                """
            )

        tem_rotina_email = any("E-mail" in str(r.get("name", "")) or "Email" in str(r.get("name", "")) for r in rotinas_lista)
        if not tem_rotina_email:
            email_status_badge = '<span class="badge badge-ok">● Ativa</span>' if verificar_email_cfg else '<span class="badge badge-neutral">Inativa</span>'
            cards_rotinas_html.append(
                f"""
                <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                            <h3 style="margin: 0; font-size: 1.05rem;">Verificação Diária de E-mail (Entrevistas & Rejeições)</h3>
                            {email_status_badge}
                        </div>
                        <p class="muted" style="margin-bottom: 0.6rem; font-size: 0.88rem;"><strong>Frequência:</strong> Diariamente às {html.escape(horario_email_cfg)} (Fim do dia)</p>
                        <p class="muted" style="margin-bottom: 0.8rem; font-size: 0.85rem; line-height: 1.45;">
                            Varredura automática no encerramento do expediente para identificar mensagens de convocação para entrevista, testes técnicos ou avisos de encerramento/rejeição, mantendo o acompanhamento sincronizado.
                        </p>
                        <div style="font-size: 0.82rem; margin-bottom: 1rem; color: var(--text-soft);">
                            <div><strong>Ação automatizada:</strong> Atualiza <code>vagas.csv</code> e <code>candidaturas_acompanhamento.csv</code></div>
                            <div><strong>Modo de sincronização:</strong> Integrado às diretrizes do <code>AGENTS.md</code></div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; border-top: 1px solid var(--border); padding-top: 0.85rem;">
                        <a href="/?tab=configuracoes" class="btn btn-soft">⚙ Ajustar Horário nas Configurações</a>
                    </div>
                </div>
                """
            )

        cards_grid_html = "".join(cards_rotinas_html)

        # Ler diagnóstico da última execução do script Python de busca
        diag_path = BASE_DIR / "job_hunter_v3_1_diagnostico.json"
        diag_info = {}
        if diag_path.exists():
            try:
                diag_info = json.loads(diag_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        diag_data_txt = formatar_data_hora_rotina(diag_info.get("gerado_em_utc"))
        diag_recebidos = diag_info.get("resumo", {}).get("anuncios_recebidos", 0)
        diag_foco = diag_info.get("resumo", {}).get("em_foco", 0)
        diag_urls = diag_info.get("urls_ja_cadastradas", 0)
        novas_shortlist = 0
        for can in diag_info.get("canais", {}).values():
            if isinstance(can, dict):
                novas_shortlist += can.get("shortlist_novas", 0)

        card_diag_html = f"""
        <div class="card" style="margin-bottom: 2rem; background: var(--surface); border-left: 4px solid var(--green);">
            <div class="mid-head" style="margin-bottom: 0.6rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.05rem;">Diagnóstico da Última Varredura de APIs (Script Python Local)</h3>
                    <p class="muted" style="margin-top: 0.25rem;">Resultado técnico do último disparo das APIs em segundo plano (job_hunter_v3_1.py).</p>
                </div>
                <div class="mid-actions">
                    <span class="badge badge-ok">Executado em: {diag_data_txt}</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 0.85rem;">
                <div style="background: var(--surface-soft); padding: 0.75rem 1rem; border-radius: 8px;">
                    <div style="font-size: 0.72rem; color: var(--muted); font-weight: 700;">ANÚNCIOS CONSULTADOS</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--text);">{diag_recebidos:,}</div>
                </div>
                <div style="background: var(--surface-soft); padding: 0.75rem 1rem; border-radius: 8px;">
                    <div style="font-size: 0.72rem; color: var(--muted); font-weight: 700;">EM ESCOPO / FOCO</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--blue);">{diag_foco:,}</div>
                </div>
                <div style="background: var(--surface-soft); padding: 0.75rem 1rem; border-radius: 8px;">
                    <div style="font-size: 0.72rem; color: var(--muted); font-weight: 700;">NOVAS VAGAS NA RODADA</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--green);">{novas_shortlist}</div>
                </div>
                <div style="background: var(--surface-soft); padding: 0.75rem 1rem; border-radius: 8px;">
                    <div style="font-size: 0.72rem; color: var(--muted); font-weight: 700;">STATUS DA FILTRAGEM</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-soft); padding-top: 0.35rem;">Dedup ativa ({diag_urls} links)</div>
                </div>
            </div>
            <p style="font-size: 0.82rem; color: var(--muted); margin-top: 0.85rem; margin-bottom: 0; line-height: 1.45;">
                <em>Nota: Quando "Novas vagas na rodada" é 0, significa que o script consultou as APIs com sucesso, mas todas as oportunidades encontradas já haviam sido filtradas e registradas na rodada anterior, evitando repetições ou consumo indevido.</em>
            </p>
        </div>
        """

        linhas_tabela_runs = []
        for run in runs_lista:
            r_nome = html.escape(str(run.get("routine_name", "Rotina")))
            r_kind = "Agendada" if run.get("run_kind") == "scheduled" else "Manual"
            r_status = str(run.get("status", "unknown")).lower()
            r_dt = formatar_data_hora_rotina(run.get("created_at"))
            r_missed = run.get("missed_count")

            if r_status == "succeeded":
                badge_st = '<span class="badge badge-ok">Sucesso</span>'
                obs = "Execução concluída com êxito."
            elif r_status == "cancelled":
                badge_st = '<span class="badge badge-warn">Omitida / Cancelada</span>'
                obs = f"OpenBot fechado no horário previsto ({r_missed} ocorrência(s) pulada(s) conforme política skip)." if r_missed else "Cancelada antes do início."
            elif r_status == "failed":
                badge_st = '<span class="badge badge-danger">Falhou</span>'
                obs = html.escape(str(run.get("error") or "Erro na execução."))
            else:
                badge_st = f'<span class="badge badge-neutral">{html.escape(r_status)}</span>'
                obs = "Em andamento ou aguardando agente."

            linhas_tabela_runs.append(
                f"""
                <tr>
                    <td style="white-space: nowrap; font-weight: 500;">{r_dt}</td>
                    <td><strong>{r_nome}</strong></td>
                    <td style="white-space: nowrap;"><span class="badge badge-neutral">{r_kind}</span></td>
                    <td style="white-space: nowrap;">{badge_st}</td>
                    <td style="color: var(--text-soft); font-size: 0.82rem;">{obs}</td>
                </tr>
                """
            )

        tabela_runs_html = "".join(linhas_tabela_runs) if linhas_tabela_runs else "<tr><td colspan='5' class='muted' style='text-align:center; padding: 2rem;'>Nenhum histórico de execução registrado no OpenBot ainda.</td></tr>"

        conteudo_principal = f"""
        <div class="bento-top" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 1.5rem;">
            <div class="kpi-box">
                <div class="kpi-top">ROTINAS ATIVAS</div>
                <div class="kpi-sub">Monitoramento contínuo</div>
                <div class="kpi-num kpi-green">{total_rotinas_ativas}</div>
            </div>

            <div class="kpi-box">
                <div class="kpi-top">FUSO HORÁRIO</div>
                <div class="kpi-sub">Horário local de referência</div>
                <div class="kpi-num" style="font-size: 1.35rem; font-weight: 700; padding-top: 0.4rem;">Acre (UTC-5)</div>
            </div>

            <div class="kpi-box">
                <div class="kpi-top">ÚLTIMA EXECUÇÃO</div>
                <div class="kpi-sub">{html.escape(data_ult)}</div>
                <div class="kpi-num kpi-indigo" style="font-size: 1.4rem;">{html.escape(status_ult.capitalize())}</div>
            </div>

            <div class="kpi-box">
                <div class="kpi-top">PRÓXIMO DISPARO</div>
                <div class="kpi-sub">Agendamento no OpenBot</div>
                <div class="kpi-num kpi-purple" style="font-size: 1.25rem;">{html.escape(proximo_txt)}</div>
            </div>
        </div>

        <div style="margin-bottom: 2rem;">
            <div class="mid-head" style="margin-bottom: 1rem;">
                <div>
                    <h2 style="font-size: 1.3rem; margin: 0;">Rotinas Programadas & Automações</h2>
                    <p class="muted" style="margin-top: 0.25rem;">Varredura periódica de vagas, filtros objetivos sem consumo excessivo e auditoria de retornos por e-mail.</p>
                </div>
            </div>
            <div class="cards-grid">
                {cards_grid_html}
            </div>
        </div>

        {card_diag_html}

        <div class="card" style="margin-bottom: 2rem;">
            <div class="mid-head" style="margin-bottom: 1rem;">
                <div>
                    <h3 style="margin: 0;">Histórico Recente de Execuções (OpenBot Scheduler)</h3>
                    <p class="muted" style="margin-top: 0.25rem;">Auditoria das últimas execuções automáticas e manuais registradas pelo escalonador do OpenBot.</p>
                </div>
                <div class="mid-actions">
                    <a href="/?tab=rotinas" class="btn btn-soft">↻ Recarregar Histórico</a>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 160px;">Data / Hora</th>
                            <th>Rotina</th>
                            <th style="width: 100px;">Tipo</th>
                            <th style="width: 140px;">Status</th>
                            <th>Observação / Diagnóstico</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tabela_runs_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card" style="background: var(--surface-soft); border-left: 4px solid var(--blue);">
            <h4 style="margin-top: 0; color: var(--blue);">💡 Como funcionam as rotinas agendadas no OpenBot</h4>
            <p style="font-size: 0.88rem; line-height: 1.5; color: var(--text-soft); margin-bottom: 0.5rem;">
                As rotinas são disparadas nativamente pelo aplicativo local OpenBot conforme os agendamentos das <strong>09h00</strong> e <strong>15h00</strong>.
                Caso o computador esteja desligado ou o OpenBot esteja fechado na hora prevista, a política ativa é <code>skip</code> (para evitar acúmulo de buscas repetidas),
                retomando a busca no ciclo seguinte sem qualquer perda de vagas históricas.
            </p>
            <p style="font-size: 0.88rem; line-height: 1.5; color: var(--text-soft); margin-bottom: 0;">
                Você também pode acionar uma execução avulsa imediatamente a qualquer momento usando os botões <strong>Disparar Agora</strong> acima.
            </p>
        </div>
        """
    else:
        itens_json = json.dumps(itens, ensure_ascii=False)
        regioes_json = json.dumps(aplicacoes_por_regiao, ensure_ascii=False)
        pills_plataformas = "".join(
            f'<button type="button" class="radar-chip" onclick="filtrarPlataforma(\'{html.escape(p)}\')">{html.escape(p)} ↗</button>'
            for p in plataformas_filtro[:8]
        )
        alerta_topo = ""
        if total_humano > 0:
            alerta_topo = f"""
            <div class="human-banner" onclick="filtrarStatus('HUMANO')">
                <div>
                    <strong>Intervenção humana necessária em {total_humano} vaga(s)</strong>
                    <span>Clique para filtrar pendências de CAPTCHA, 2FA ou elegibilidade.</span>
                </div>
                <span class="banner-cta">Filtrar pendências →</span>
            </div>
            """

        qtd_inicial = min(10, total_vagas)
        modo_label = "Exige Aprovação" if modo_envio_cfg == "aprovacao" else "Envio Automático"
        frentes_resumo = ", ".join(v.get("cargo", "") for v in vagas_buscadas_cfg[:3] if v.get("cargo")) or "Cargos configurados"

        conteudo_principal = f"""
        {alerta_topo}

        <div class="bento-top">
            <div class="card bento-curriculos">
                <div class="mid-head">
                    <div>
                        <h3>Currículos & Perfil Base</h3>
                        <p class="muted">Último: {html.escape(ultimo_pdf)}</p>
                    </div>
                    <div class="mid-actions">
                        <a href="/?tab=configuracoes" class="btn btn-soft">Configurar ▾</a>
                    </div>
                </div>
                <div class="active-profile-pill">
                    <span>Alvos: {html.escape(frentes_resumo)} · {html.escape(modo_label)}</span>
                </div>
            </div>

            <div class="kpi-box bento-total">
                <div class="kpi-top">TOTAL DE VAGAS</div>
                <div class="kpi-sub">{html.escape(', '.join(modalidades_cfg) or 'Remota')} · {html.escape(', '.join(regimes_cfg) or 'PJ')}</div>
                <div class="kpi-num">{total_vagas}</div>
            </div>

            <div class="kpi-box bento-pdfs">
                <div class="kpi-top">CURRÍCULOS PDF</div>
                <div class="kpi-sub">Modo: {html.escape(modo_label)}</div>
                <div class="kpi-num kpi-indigo">{len(curriculos)}</div>
            </div>

            <div class="kpi-box bento-entrevistas">
                <div>
                    <div class="kpi-top">ENTREVISTAS</div>
                    <div class="kpi-sub">Avançaram no processo</div>
                    <div class="kpi-num kpi-purple" style="cursor:pointer;" onclick="filtrarStatus('ENTREVISTA')" title="Filtrar entrevistas">{total_entrevistas}</div>
                </div>
                <div class="kpi-split-footer">
                    <button type="button" class="kpi-mini-pill kpi-mini-purple" onclick="filtrarStatus('ENTREVISTA')">Entrevistas: {total_entrevistas}</button>
                    <button type="button" class="kpi-mini-pill kpi-mini-danger" onclick="filtrarStatus('REJEITADA')">Rejeitadas: {total_rejeitadas}</button>
                </div>
            </div>

            <div class="card bento-radar">
                <div class="radar-head">
                    <div>
                        <span class="radar-eyebrow">RADAR ATS & PLATAFORMAS</span>
                        <h3>Fontes de Busca</h3>
                    </div>
                    <button type="button" class="btn btn-soft" onclick="filtrarPlataforma('')">Todas Fontes</button>
                </div>
                <div class="radar-chips">
                    {pills_plataformas if pills_plataformas else '<span class="muted">Nenhuma fonte registrada ainda</span>'}
                </div>
            </div>

            <div class="kpi-box bento-candidatas">
                <div class="kpi-top">CANDIDATADAS</div>
                <div class="kpi-sub">{total_humano} pendente(s) / ação humana</div>
                <div class="kpi-num kpi-green">{total_enviadas}</div>
            </div>

            <div class="kpi-box bento-alta">
                <div class="kpi-top">ALTA COMPATIBILIDADE</div>
                <div class="kpi-sub">{total_incomp} incompatível(is) filtrada(s)</div>
                <div class="kpi-num kpi-blue">{total_alta}</div>
            </div>
        </div>

        <div class="main-split">
            <aside class="card map-card">
                <div class="map-head">
                    <div>
                        <h3>Mapa-Múndi de Aplicações</h3>
                        <p class="muted" id="mapStatusNote">Carregando cartografia mundial...</p>
                    </div>
                    <button type="button" class="btn btn-soft" onclick="filtrarRegiao('')">Limpar</button>
                </div>

                <div class="world-map-wrap">
                    <div id="worldMapMount" class="world-map-mount"></div>
                </div>

                <div id="regiaoResumoLista" class="region-summary"></div>
            </aside>

            <div class="main-col">
                <div class="filter-bar">
                    <input type="text" id="buscaInput" placeholder="Buscar cargo, empresa ou detalhe..." oninput="onFiltroAlterado()">
                    <select id="filtroClassif" onchange="onFiltroAlterado()">
                        <option value="">Classificação: Todas</option>
                        <option value="ALTA COMPATIBILIDADE">Alta Compatibilidade</option>
                        <option value="PENDENTE DE VALIDAÇÃO">Pendente de Validação</option>
                        <option value="INCOMPATÍVEL">Incompatível</option>
                    </select>
                    <select id="filtroStatus" onchange="onFiltroAlterado()">
                        <option value="">Status: Todos</option>
                        <option value="ENVIADA">Enviada</option>
                        <option value="ENTREVISTA">Entrevista</option>
                        <option value="REJEITADA">Rejeitada</option>
                        <option value="HUMANO">Ação Humana / Pendente</option>
                    </select>
                    <select id="filtroPlat" onchange="onFiltroAlterado()">
                        <option value="">Plataforma: Todas</option>
                        {''.join(f'<option value="{html.escape(p)}">{html.escape(p)}</option>' for p in plataformas_filtro)}
                    </select>
                </div>

                <div class="list-header">
                    <div>
                        <strong id="contadorVagas">Vagas ({qtd_inicial} de {total_vagas})</strong>
                        <span class="muted" id="subFiltroRegiao"> · Ordenadas das mais recentes</span>
                    </div>
                    <div class="view-toggle">
                        <button type="button" id="btnCards" class="toggle-btn active" onclick="mudarModo('cards')">Cards</button>
                        <button type="button" id="btnTabela" class="toggle-btn" onclick="mudarModo('tabela')">Tabela</button>
                    </div>
                </div>

                <div id="vagasContainer" class="cards-grid"></div>
                <div id="paginacaoBar" class="pagination-bar"></div>
            </div>
        </div>

        <script>
            const VAGAS_DATA = {itens_json};
            const APLICACOES_REGIAO = {regioes_json};
            const PAGE_SIZE = 10;
            let modoAtual = 'cards';
            let limiteAtual = PAGE_SIZE;
            let regiaoSelecionada = '';

            const LONLAT_REGIOES = {{
                'Brasil': [-51.9, -14.2],
                'EUA': [-98.5, 39.8],
                'Canadá': [-106.3, 56.1],
                'LATAM': [-99.1, 19.4],
                'Europa': [10.4, 51.1],
                'Global / Remoto': [104.2, 35.8]
            }};

            function renderizarListaRegioes() {{
                const resumoDiv = document.getElementById('regiaoResumoLista');
                if (!resumoDiv) return;
                const listaRegioes = Object.keys(LONLAT_REGIOES);
                resumoDiv.innerHTML = listaRegioes.map(r => {{
                    const apps = APLICACOES_REGIAO[r] || 0;
                    const activeCls = regiaoSelecionada === r ? 'reg-row-active' : '';
                    const badgeTxt = apps > 0 ? `${{apps}} aplicada(s)` : '0 aplicadas';
                    const badgeCls = apps > 0 ? 'reg-count-on' : 'reg-count-off';
                    return `
                        <button type="button" class="reg-row ${{activeCls}}" onclick="filtrarRegiao('${{r}}')">
                            <span>${{r}}</span>
                            <span class="reg-count ${{badgeCls}}">${{badgeTxt}}</span>
                        </button>
                    `;
                }}).join('');
            }}

            function carregarScript(src) {{
                return new Promise((resolve, reject) => {{
                    const s = document.createElement('script');
                    s.src = src;
                    s.onload = resolve;
                    s.onerror = reject;
                    document.head.appendChild(s);
                }});
            }}

            async function inicializarMapaGeografico() {{
                const mount = document.getElementById('worldMapMount');
                const note = document.getElementById('mapStatusNote');
                renderizarListaRegioes();

                try {{
                    await carregarScript('https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js');
                    await carregarScript('https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js');
                    const resp = await fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json');
                    const topo = await resp.json();
                    const countries = topojson.feature(topo, topo.objects.countries);

                    const width = 420;
                    const height = 225;
                    mount.innerHTML = '';

                    const svg = d3.select(mount)
                        .append('svg')
                        .attr('viewBox', `0 0 ${{width}} ${{height}}`)
                        .attr('class', 'geo-svg');

                    const projection = d3.geoNaturalEarth1()
                        .fitSize([width, height], countries);
                    const pathGen = d3.geoPath().projection(projection);

                    const ID_BRASIL = '076';
                    const ID_EUA = '840';
                    const ID_CANADA = '124';

                    svg.append('g')
                        .selectAll('path')
                        .data(countries.features)
                        .enter()
                        .append('path')
                        .attr('d', pathGen)
                        .attr('class', d => {{
                            const idStr = String(d.id || '').padStart(3, '0');
                            let reg = null;
                            if (idStr === ID_BRASIL) reg = 'Brasil';
                            else if (idStr === ID_EUA) reg = 'EUA';
                            else if (idStr === ID_CANADA) reg = 'Canadá';
                            const hasApp = reg && (APLICACOES_REGIAO[reg] || 0) > 0;
                            const isSel = reg && regiaoSelecionada === reg;
                            return `country-path ${{hasApp ? 'country-app' : ''}} ${{isSel ? 'country-sel' : ''}}`;
                        }})
                        .style('cursor', d => {{
                            const idStr = String(d.id || '').padStart(3, '0');
                            return (idStr === ID_BRASIL || idStr === ID_EUA || idStr === ID_CANADA) ? 'pointer' : 'default';
                        }})
                        .on('click', (_, d) => {{
                            const idStr = String(d.id || '').padStart(3, '0');
                            if (idStr === ID_BRASIL) filtrarRegiao('Brasil');
                            else if (idStr === ID_EUA) filtrarRegiao('EUA');
                            else if (idStr === ID_CANADA) filtrarRegiao('Canadá');
                        }});

                    for (const [reg, coords] of Object.entries(LONLAT_REGIOES)) {{
                        const qtd = APLICACOES_REGIAO[reg] || 0;
                        if (qtd <= 0) continue;
                        const pt = projection(coords);
                        if (!pt) continue;
                        const [cx, cy] = pt;
                        const txt = `${{reg}} (${{qtd}})`;
                        const wBox = Math.max(54, txt.length * 5.8 + 10);

                        const g = svg.append('g')
                            .attr('class', 'geo-pin')
                            .style('cursor', 'pointer')
                            .on('click', () => filtrarRegiao(reg));

                        g.append('circle').attr('cx', cx).attr('cy', cy).attr('r', 8).attr('class', 'geo-halo');
                        g.append('circle').attr('cx', cx).attr('cy', cy).attr('r', 3.8).attr('class', 'geo-dot');
                        g.append('rect')
                            .attr('x', cx - wBox / 2)
                            .attr('y', cy - 18)
                            .attr('width', wBox)
                            .attr('height', 12.5)
                            .attr('rx', 4)
                            .attr('class', 'geo-pill');
                        g.append('text')
                            .attr('x', cx)
                            .attr('y', cy - 9)
                            .attr('text-anchor', 'middle')
                            .attr('class', 'geo-label')
                            .text(txt);
                    }}

                    note.textContent = 'Projeção Natural Earth · Clique para filtrar.';
                }} catch (_) {{
                    const ativos = Object.entries(APLICACOES_REGIAO).filter(([, n]) => n > 0);
                    note.textContent = 'Modo offline (sem acesso a CDN cartográfico).';
                    mount.innerHTML = ativos.length
                        ? `<div class="offline-pins">${{ativos.map(([r, n]) => `<span class="offline-chip" onclick="filtrarRegiao('${{r}}')">● ${{r}}: ${{n}}</span>`).join('')}}</div>`
                        : '<div class="empty">Nenhuma aplicação registrada para sinalizar no mapa.</div>';
                }}
            }}

            function filtrarRegiao(reg) {{
                regiaoSelecionada = (regiaoSelecionada === reg) ? '' : reg;
                limiteAtual = PAGE_SIZE;
                inicializarMapaGeografico();
                renderizar();
            }}

            function parseDataOrdenacao(str) {{
                if (!str) return 0;
                const s = String(str).trim();
                let m = s.match(/^(\d{{4}})-(\d{{2}})-(\d{{2}})/);
                if (m) return new Date(`${{m[1]}}-${{m[2]}}-${{m[3]}}T00:00:00`).getTime() || 0;
                m = s.match(/^(\d{{2}})\/(\d{{2}})\/(\d{{4}})/);
                if (m) return new Date(`${{m[3]}}-${{m[2]}}-${{m[1]}}T00:00:00`).getTime() || 0;
                const t = Date.parse(s);
                return Number.isNaN(t) ? 0 : t;
            }}

            function ordenarMaisRecentes(lista) {{
                return [...lista].sort((a, b) => {{
                    const da = parseDataOrdenacao(a.data);
                    const db = parseDataOrdenacao(b.data);
                    if (db !== da) return db - da;
                    const na = parseInt(String(a.id).replace(/\D/g, ''), 10);
                    const nb = parseInt(String(b.id).replace(/\D/g, ''), 10);
                    if (!Number.isNaN(na) && !Number.isNaN(nb) && nb !== na) return nb - na;
                    return String(b.id).localeCompare(String(a.id));
                }});
            }}

            function onFiltroAlterado() {{
                limiteAtual = PAGE_SIZE;
                renderizar();
            }}

            function filtrarPlataforma(plat) {{
                document.getElementById('filtroPlat').value = plat;
                onFiltroAlterado();
            }}

            function filtrarStatus(st) {{
                const sel = document.getElementById('filtroStatus');
                sel.value = (sel.value === st) ? '' : st;
                onFiltroAlterado();
            }}

            function mudarModo(modo) {{
                modoAtual = modo;
                document.getElementById('btnCards').classList.toggle('active', modo === 'cards');
                document.getElementById('btnTabela').classList.toggle('active', modo === 'tabela');
                renderizar();
            }}

            function verMais() {{
                limiteAtual += PAGE_SIZE;
                renderizar();
            }}

            function mostrarTodas(total) {{
                limiteAtual = total;
                renderizar();
            }}

            function esc(str) {{
                if (!str) return '';
                return String(str)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;');
            }}

            function renderizar() {{
                const q = document.getElementById('buscaInput').value.toLowerCase().trim();
                const fClassif = document.getElementById('filtroClassif').value.toUpperCase();
                const fStatus = document.getElementById('filtroStatus').value.toUpperCase();
                const fPlat = document.getElementById('filtroPlat').value.toLowerCase();

                document.getElementById('subFiltroRegiao').textContent = regiaoSelecionada
                    ? ` · Região: ${{regiaoSelecionada}}`
                    : ' · Ordenadas das mais recentes';

                const filtradas = ordenarMaisRecentes(VAGAS_DATA.filter(v => {{
                    const stUp = (v.status || '').toUpperCase();
                    const texto = (v.empresa + ' ' + v.cargo + ' ' + v.detalhes + ' ' + v.plataforma + ' ' + (v.regiao || '')).toLowerCase();
                    if (q && !texto.includes(q)) return false;
                    if (regiaoSelecionada && (v.regiao || 'Brasil') !== regiaoSelecionada) return false;
                    if (fClassif && !v.classificacao.toUpperCase().includes(fClassif)) return false;
                    if (fPlat && !v.plataforma.toLowerCase().includes(fPlat)) return false;
                    if (fStatus === 'ENVIADA' && !stUp.includes('ENVIADA')) return false;
                    if (fStatus === 'ENTREVISTA' && !(stUp.includes('ENTREVISTA') || stUp.includes('INTERVIEW'))) return false;
                    if (fStatus === 'REJEITADA' && !(stUp.includes('REJEIT') || stUp.includes('REJECT') || stUp.includes('RECUSAD'))) return false;
                    if (fStatus === 'HUMANO' && !v.precisa_humano) return false;
                    return true;
                }}));

                const visiveis = filtradas.slice(0, limiteAtual);
                const restantes = filtradas.length - visiveis.length;

                document.getElementById('contadorVagas').textContent =
                    filtradas.length === 0
                        ? 'Vagas (0)'
                        : `Vagas (${{visiveis.length}} de ${{filtradas.length}})`;

                const container = document.getElementById('vagasContainer');
                const pagBar = document.getElementById('paginacaoBar');

                if (filtradas.length === 0) {{
                    container.className = '';
                    container.innerHTML = '<div class="card empty">Nenhuma vaga encontrada com os filtros selecionados.</div>';
                    pagBar.innerHTML = '';
                    return;
                }}

                if (restantes > 0) {{
                    const proximoLote = Math.min(PAGE_SIZE, restantes);
                    pagBar.innerHTML = `
                        <button type="button" class="btn-ver-mais" onclick="verMais()">+ Ver mais (${{proximoLote}} de ${{restantes}} restantes)</button>
                        <button type="button" class="btn-ver-todas" onclick="mostrarTodas(${{filtradas.length}})">Mostrar todas (${{filtradas.length}})</button>
                    `;
                }} else if (filtradas.length > PAGE_SIZE) {{
                    pagBar.innerHTML = `
                        <button type="button" class="btn-ver-todas" onclick="onFiltroAlterado()">Mostrar apenas as 10 mais recentes</button>
                    `;
                }} else {{
                    pagBar.innerHTML = '';
                }}

                if (modoAtual === 'tabela') {{
                    container.className = 'card table-container';
                    const rows = visiveis.map(v => {{
                        const stLow = (v.status || '').toLowerCase();
                        const isEntrevista = stLow.includes('entrevista') || stLow.includes('interview');
                        const isRejeitada = stLow.includes('rejeit') || stLow.includes('reject') || stLow.includes('recusad');
                        const isEnviada = stLow.includes('enviada') || stLow.includes('aplicad');
                        const isIncomp = v.classificacao === 'INCOMPATÍVEL';
                        const badgeClass = isEntrevista
                            ? 'badge-purple'
                            : (isRejeitada
                                ? 'badge-danger'
                                : (isEnviada
                                    ? 'badge-ok'
                                    : (v.precisa_humano ? 'badge-warn' : (isIncomp ? 'badge-danger' : 'badge-neutral'))));
                        const linkVaga = v.url ? `<a href="${{esc(v.url)}}" target="_blank" class="link-blue">Abrir ↗</a>` : '—';
                        const linkPdf = v.pdf ? `<a href="/curriculos/${{esc(v.pdf)}}" target="_blank" class="link-blue">PDF ↗</a>` : '—';
                        return `
                            <tr>
                                <td><strong>#${{esc(v.id)}}</strong></td>
                                <td><strong>${{esc(v.empresa)}}</strong></td>
                                <td>${{esc(v.cargo)}}</td>
                                <td>${{esc(v.regiao || 'Brasil')}}</td>
                                <td>${{esc(v.plataforma)}}</td>
                                <td><span class="badge ${{badgeClass}}">${{esc(v.status)}}</span></td>
                                <td class="td-detail">${{esc(v.detalhes || '—')}}</td>
                                <td>${{linkPdf}}</td>
                                <td>${{linkVaga}}</td>
                            </tr>
                        `;
                    }}).join('');

                    container.innerHTML = `
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th><th>Empresa</th><th>Cargo</th><th>Região</th><th>Fonte</th>
                                    <th>Status</th><th>Detalhes</th><th>Currículo</th><th>Link</th>
                                </tr>
                            </thead>
                            <tbody>${{rows}}</tbody>
                        </table>
                    `;
                    return;
                }}

                container.className = 'cards-grid';
                container.innerHTML = visiveis.map(v => {{
                    const stLow = (v.status || '').toLowerCase();
                    const isEntrevista = stLow.includes('entrevista') || stLow.includes('interview');
                    const isRejeitada = stLow.includes('rejeit') || stLow.includes('reject') || stLow.includes('recusad');
                    const isEnviada = stLow.includes('enviada') || stLow.includes('aplicad');
                    const isIncomp = v.classificacao === 'INCOMPATÍVEL';

                    const statusBadge = isEntrevista
                        ? `<span class="badge badge-purple">★ ${{esc(v.status)}}</span>`
                        : (isRejeitada
                            ? `<span class="badge badge-danger">✕ ${{esc(v.status)}}</span>`
                            : (isEnviada
                                ? `<span class="badge badge-ok">✓ ${{esc(v.status)}}</span>`
                                : (v.precisa_humano
                                    ? `<span class="badge badge-warn">⚠ ${{esc(v.status)}}</span>`
                                    : (isIncomp
                                        ? `<span class="badge badge-danger">${{esc(v.status)}}</span>`
                                        : `<span class="badge badge-neutral">${{esc(v.status)}}</span>`))));

                    const scoreTag = isEntrevista
                        ? '<span class="score-pill score-purple">Entrevista</span>'
                        : (isRejeitada
                            ? '<span class="score-pill score-danger">Rejeitada</span>'
                            : (isEnviada
                                ? '<span class="score-pill score-ok">Enviada</span>'
                                : (v.precisa_humano
                                    ? '<span class="score-pill score-warn">Atenção</span>'
                                    : (isIncomp
                                        ? '<span class="score-pill score-danger">Incompatível</span>'
                                        : '<span class="score-pill score-blue">Elegível</span>'))));

                    const btnLink = v.url
                        ? `<a href="${{esc(v.url)}}" target="_blank" class="btn-card btn-card-primary">Abrir Vaga ↗</a>`
                        : `<span class="btn-card btn-card-disabled">Sem URL</span>`;

                    const btnPdf = v.pdf
                        ? `<a href="/curriculos/${{esc(v.pdf)}}" target="_blank" class="btn-card btn-card-soft">Currículo PDF ↗</a>`
                        : '';

                    const btnConcluir = (!isEnviada && !isEntrevista && !isRejeitada && !isIncomp && v.id !== '-')
                        ? `<form method="post" action="/vagas/${{encodeURIComponent(v.id)}}/marcar-enviada" style="display:inline;">
                             <button type="submit" class="btn-card btn-card-green">✓ Marcar Enviada</button>
                           </form>`
                        : '';

                    const btnEntrevista = ((isEnviada || isRejeitada) && !isEntrevista && v.id !== '-')
                        ? `<form method="post" action="/vagas/${{encodeURIComponent(v.id)}}/atualizar-status" style="display:inline;">
                             <input type="hidden" name="novo_status" value="ENTREVISTA">
                             <button type="submit" class="btn-card btn-card-purple">★ Entrevista</button>
                           </form>`
                        : '';

                    const btnRejeitada = ((isEnviada || isEntrevista) && !isRejeitada && v.id !== '-')
                        ? `<form method="post" action="/vagas/${{encodeURIComponent(v.id)}}/atualizar-status" style="display:inline;">
                             <input type="hidden" name="novo_status" value="REJEITADA">
                             <button type="submit" class="btn-card btn-card-danger">✕ Rejeitada</button>
                           </form>`
                        : '';

                    return `
                        <article class="vaga-card ${{v.precisa_humano ? 'vaga-card-warn' : ''}}">
                            <div class="vaga-top">
                                <div class="vaga-tags">
                                    <span class="badge badge-neutral">#${{esc(v.id)}}</span>
                                    <span class="badge badge-plat">${{esc(v.plataforma)}}</span>
                                    ${{v.data ? `<span class="vaga-date">${{esc(v.data)}}</span>` : ''}}
                                </div>
                                ${{scoreTag}}
                            </div>
                            <h4 class="vaga-title">${{esc(v.cargo)}}</h4>
                            <div class="vaga-company">${{esc(v.empresa)}} · <span class="muted">${{esc(v.regiao || 'Brasil')}}</span></div>
                            <p class="vaga-desc">${{esc(v.detalhes || 'Sem observações adicionais registradas.')}}</p>
                            <div class="vaga-status-row">${{statusBadge}}</div>
                            <div class="vaga-actions">
                                ${{btnLink}}
                                ${{btnPdf}}
                                ${{btnConcluir}}
                                ${{btnEntrevista}}
                                ${{btnRejeitada}}
                            </div>
                        </article>
                    `;
                }}).join('');
            }}

            inicializarMapaGeografico();
            renderizar();
        </script>
        """

    def nav_btn(slug: str, label: str) -> str:
        ativo = "active" if tab == slug else ""
        return f'<a href="/?tab={slug}" class="top-btn {ativo}">{label}</a>'

    pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Job Hunter — OpenBot</title>
    <style>
        :root {{
            --bg: #f4f6f9;
            --surface: #ffffff;
            --surface-soft: #f8fafc;
            --border: #e5e7eb;
            --text: #111827;
            --text-soft: #4b5563;
            --muted: #6b7280;
            --blue: #2563eb;
            --blue-soft: #eff6ff;
            --green: #16a34a;
            --green-soft: #f0fdf4;
            --warn: #d97706;
            --warn-soft: #fffbeb;
            --danger: #dc2626;
            --danger-soft: #fef2f2;
            --danger-line: #fecaca;
            --purple: #7c3aed;
            --purple-soft: #f5f3ff;
            --purple-line: #ddd6fe;
        }}
        body.dark {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-soft: #162032;
            --border: #334155;
            --text: #f8fafc;
            --text-soft: #cbd5e1;
            --muted: #94a3b8;
            --blue-soft: rgba(37, 99, 235, 0.18);
            --green-soft: rgba(22, 163, 74, 0.18);
            --warn-soft: rgba(217, 119, 6, 0.18);
            --danger-soft: rgba(220, 38, 38, 0.2);
            --danger-line: rgba(248, 113, 113, 0.35);
            --purple-soft: rgba(124, 58, 237, 0.22);
            --purple-line: rgba(167, 139, 250, 0.35);
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }}
        .header {{
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 0.9rem 2rem;
        }}
        .header-inner {{
            max-width: 1420px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .brand-wrap {{ display: flex; align-items: center; gap: 0.85rem; }}
        .logo-badge {{
            width: 38px; height: 38px; border-radius: 10px;
            background: var(--blue); color: #fff; font-weight: 700; font-size: 0.9rem;
            display: flex; align-items: center; justify-content: center;
        }}
        .brand-title {{ display: flex; align-items: center; gap: 0.6rem; font-weight: 700; font-size: 1rem; }}
        .sync-pill {{
            font-size: 0.72rem; font-weight: 600; color: var(--green);
            background: var(--green-soft); padding: 0.18rem 0.55rem; border-radius: 999px;
        }}
        .brand-sub {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.1rem; }}
        .top-actions {{ display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }}
        .top-btn {{
            text-decoration: none; background: var(--surface); color: var(--text-soft);
            border: 1px solid var(--border); padding: 0.45rem 0.85rem; border-radius: 8px;
            font-size: 0.82rem; font-weight: 500; cursor: pointer;
        }}
        .top-btn:hover {{ background: var(--surface-soft); color: var(--text); }}
        .top-btn.active {{ background: var(--text); color: var(--surface); border-color: var(--text); }}
        .main {{ max-width: 1420px; margin: 1.5rem auto; padding: 0 2rem 3rem; }}
        .toast {{
            background: var(--green-soft); border: 1px solid rgba(22, 163, 74, 0.3);
            color: var(--green); padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.84rem; margin-bottom: 1.25rem;
        }}
        .toast-err {{
            background: var(--danger-soft); border-color: var(--danger-line); color: var(--danger);
        }}
        .human-banner {{
            background: var(--warn-soft); border: 1px solid rgba(217, 119, 6, 0.35); color: var(--warn);
            padding: 0.85rem 1.2rem; border-radius: 12px; margin-bottom: 1.25rem;
            display: flex; align-items: center; justify-content: space-between; cursor: pointer; font-size: 0.85rem;
        }}
        .human-banner span {{ display: block; opacity: 0.9; font-size: 0.8rem; }}
        .banner-cta {{ font-weight: 600; }}

        .bento-top {{
            display: grid;
            grid-template-columns: 1.45fr 1fr 1fr 1.05fr;
            grid-template-areas:
                "curriculos total pdfs entrevistas"
                "radar candidatas alta entrevistas";
            gap: 1rem;
            margin-bottom: 1.25rem;
        }}
        .bento-curriculos {{ grid-area: curriculos; }}
        .bento-total {{ grid-area: total; }}
        .bento-pdfs {{ grid-area: pdfs; }}
        .bento-entrevistas {{ grid-area: entrevistas; }}
        .bento-radar {{ grid-area: radar; }}
        .bento-candidatas {{ grid-area: candidatas; }}
        .bento-alta {{ grid-area: alta; }}

        .kpi-box {{
            background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
            padding: 1.1rem 1.35rem; display: flex; flex-direction: column; justify-content: space-between;
        }}
        .kpi-top {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; color: var(--text-soft); }}
        .kpi-sub {{ font-size: 0.75rem; color: var(--muted); margin-top: 0.15rem; }}
        .kpi-num {{ font-size: 1.75rem; font-weight: 700; margin-top: 0.5rem; letter-spacing: -0.03em; }}
        .kpi-green {{ color: var(--green); }}
        .kpi-blue {{ color: var(--blue); }}
        .kpi-indigo {{ color: #6366f1; }}
        .kpi-purple {{ color: var(--purple); }}

        .kpi-split-footer {{
            display: flex; flex-direction: column; gap: 0.45rem;
            margin-top: 1rem; padding-top: 0.85rem; border-top: 1px solid var(--border);
        }}
        .kpi-mini-pill {{
            width: 100%; text-align: left; font-size: 0.76rem; font-weight: 600;
            padding: 0.4rem 0.65rem; border-radius: 8px; cursor: pointer; border: 1px solid transparent;
        }}
        .kpi-mini-purple {{
            background: var(--purple-soft); color: var(--purple); border-color: var(--purple-line);
        }}
        .kpi-mini-danger {{
            background: var(--danger-soft); color: var(--danger); border-color: var(--danger-line);
        }}

        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.4rem; }}
        .mid-head {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem; }}
        h2, h3 {{ margin: 0; font-size: 0.98rem; font-weight: 700; }}
        .muted {{ color: var(--muted); font-size: 0.8rem; margin: 0.2rem 0 0; }}
        .mid-actions {{ display: flex; gap: 0.45rem; flex-wrap: wrap; align-items: center; }}
        .btn {{
            text-decoration: none; font-size: 0.78rem; font-weight: 600;
            padding: 0.42rem 0.75rem; border-radius: 8px; cursor: pointer;
            border: 1px solid var(--border); display: inline-block; white-space: nowrap;
        }}
        .btn-soft {{ background: var(--surface-soft); color: var(--text); }}
        .btn-soft:hover {{ background: var(--border); }}
        .btn-primary {{ background: var(--blue); color: #fff; border: none; padding: 0.48rem 1rem; }}
        .btn-outline {{ background: transparent; color: var(--blue); border-color: var(--border); }}
        .btn-danger-soft {{ background: var(--danger-soft); color: var(--danger); border-color: var(--danger-line); }}
        .active-profile-pill {{
            margin-top: 0.9rem; display: inline-block; background: var(--blue); color: #fff;
            font-size: 0.76rem; font-weight: 600; padding: 0.38rem 0.85rem; border-radius: 999px;
        }}
        .radar-head {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }}
        .radar-eyebrow {{
            font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; color: var(--blue);
            display: block; margin-bottom: 0.2rem;
        }}
        .radar-chips {{ margin-top: 0.85rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }}
        .radar-chip {{
            background: var(--surface-soft); border: 1px solid var(--border);
            color: var(--text-soft); font-size: 0.75rem; font-weight: 500; padding: 0.3rem 0.65rem;
            border-radius: 8px; cursor: pointer; transition: background-color 0.15s ease, color 0.15s ease;
        }}
        .radar-chip:hover {{ background: var(--blue-soft); color: var(--blue); border-color: var(--blue); }}

        .main-split {{
            display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 1.15rem; align-items: start;
        }}
        .map-card {{ position: sticky; top: 1rem; }}
        .map-head {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.85rem; }}
        .world-map-wrap {{
            border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
            background: #eef5fc;
        }}
        body.dark .world-map-wrap {{ background: #0f1c2e; }}
        .world-map-mount {{ width: 100%; min-height: 195px; display: flex; align-items: center; justify-content: center; }}
        .geo-svg {{ width: 100%; height: auto; display: block; }}
        .country-path {{
            fill: #d5dfec; stroke: #ffffff; stroke-width: 0.55; transition: fill 0.15s ease;
        }}
        body.dark .country-path {{ fill: #2c3a50; stroke: #152236; }}
        .country-path:hover {{ fill: #93c5fd; }}
        .country-app {{ fill: #4ade80; }}
        body.dark .country-app {{ fill: #15803d; }}
        .country-sel {{ fill: #2563eb; stroke: #1e3a8a; stroke-width: 0.9; }}
        .geo-halo {{ fill: rgba(22, 163, 74, 0.25); }}
        .geo-dot {{ fill: #16a34a; stroke: #ffffff; stroke-width: 1.3; }}
        .geo-pill {{ fill: rgba(15, 23, 42, 0.88); }}
        body.dark .geo-pill {{ fill: rgba(248, 250, 252, 0.94); }}
        .geo-label {{ font-size: 7.5px; font-weight: 700; fill: #ffffff; }}
        body.dark .geo-label {{ fill: #0f172a; }}
        .offline-pins {{ padding: 1rem; display: flex; flex-wrap: wrap; gap: 0.45rem; }}
        .offline-chip {{
            background: var(--green-soft); color: var(--green); font-size: 0.78rem; font-weight: 700;
            padding: 0.35rem 0.65rem; border-radius: 8px; cursor: pointer;
        }}

        .region-summary {{ margin-top: 0.85rem; display: flex; flex-direction: column; gap: 0.35rem; }}
        .reg-row {{
            width: 100%; display: flex; align-items: center; justify-content: space-between;
            padding: 0.44rem 0.7rem; border-radius: 8px; border: 1px solid var(--border);
            background: var(--surface-soft); color: var(--text); font-size: 0.78rem; cursor: pointer;
        }}
        .reg-row:hover {{ border-color: var(--blue); }}
        .reg-row-active {{ background: var(--blue-soft); border-color: var(--blue); font-weight: 600; }}
        .reg-count {{ font-size: 0.72rem; font-weight: 700; padding: 0.12rem 0.5rem; border-radius: 999px; }}
        .reg-count-on {{ background: var(--green-soft); color: var(--green); }}
        .reg-count-off {{ background: transparent; color: var(--muted); }}

        .filter-bar {{
            background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
            padding: 0.75rem; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 0.65rem; margin-bottom: 1.15rem;
        }}
        .filter-bar input, .filter-bar select {{
            width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--border);
            border-radius: 8px; background: var(--surface-soft); color: var(--text); font-size: 0.83rem;
        }}
        .list-header {{
            display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.9rem; font-size: 0.85rem;
        }}
        .view-toggle {{
            background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.18rem; display: flex; gap: 0.2rem;
        }}
        .toggle-btn {{
            border: none; background: transparent; color: var(--muted);
            font-size: 0.78rem; font-weight: 600; padding: 0.3rem 0.7rem; border-radius: 6px; cursor: pointer;
        }}
        .toggle-btn.active {{ background: var(--text); color: var(--surface); }}
        .cards-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
        .vaga-card {{
            background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
            padding: 1.2rem 1.35rem; display: flex; flex-direction: column; justify-content: space-between;
        }}
        .vaga-card-warn {{ border-left: 4px solid var(--warn); }}
        .vaga-top {{ display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.65rem; }}
        .vaga-tags {{ display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }}
        .vaga-date {{ font-size: 0.74rem; color: var(--muted); }}
        .badge {{ font-size: 0.7rem; font-weight: 600; padding: 0.18rem 0.55rem; border-radius: 6px; }}
        .badge-neutral {{ background: var(--surface-soft); color: var(--text-soft); border: 1px solid var(--border); }}
        .badge-plat {{ background: var(--blue-soft); color: var(--blue); }}
        .badge-ok {{ background: var(--green-soft); color: var(--green); }}
        .badge-warn {{ background: var(--warn-soft); color: var(--warn); }}
        .badge-danger {{ background: var(--danger-soft); color: var(--danger); border: 1px solid var(--danger-line); }}
        .badge-purple {{ background: var(--purple-soft); color: var(--purple); border: 1px solid var(--purple-line); }}
        .score-pill {{ font-size: 0.74rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 8px; }}
        .score-ok {{ background: var(--green-soft); color: var(--green); }}
        .score-warn {{ background: var(--warn-soft); color: var(--warn); }}
        .score-blue {{ background: var(--blue-soft); color: var(--blue); }}
        .score-danger {{ background: var(--danger-soft); color: var(--danger); border: 1px solid var(--danger-line); }}
        .score-purple {{ background: var(--purple-soft); color: var(--purple); border: 1px solid var(--purple-line); }}
        .vaga-title {{ margin: 0; font-size: 1rem; font-weight: 700; line-height: 1.35; }}
        .vaga-company {{ font-size: 0.82rem; font-weight: 600; color: var(--text-soft); margin-top: 0.2rem; }}
        .vaga-desc {{
            font-size: 0.82rem; color: var(--muted); line-height: 1.45; margin: 0.75rem 0;
            display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
        }}
        .vaga-status-row {{ margin-bottom: 0.85rem; }}
        .vaga-actions {{
            display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;
            padding-top: 0.75rem; border-top: 1px solid var(--border);
        }}
        .btn-card {{
            text-decoration: none; font-size: 0.78rem; font-weight: 600;
            padding: 0.42rem 0.8rem; border-radius: 8px; border: none; cursor: pointer;
        }}
        .btn-card-primary {{ background: var(--blue); color: #fff; }}
        .btn-card-soft {{ background: var(--surface-soft); color: var(--text); border: 1px solid var(--border); }}
        .btn-card-green {{ background: var(--green); color: #fff; }}
        .btn-card-purple {{ background: var(--purple-soft); color: var(--purple); border: 1px solid var(--purple-line); }}
        .btn-card-danger {{ background: var(--danger-soft); color: var(--danger); border: 1px solid var(--danger-line); }}
        .btn-card-disabled {{ background: var(--surface-soft); color: var(--muted); }}
        .pagination-bar {{
            margin-top: 1.25rem; display: flex; align-items: center; justify-content: center; gap: 0.65rem; flex-wrap: wrap;
        }}
        .btn-ver-mais {{
            background: var(--surface); color: var(--text); border: 1px solid var(--border);
            padding: 0.55rem 1.15rem; border-radius: 9px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
        }}
        .btn-ver-mais:hover {{ background: var(--surface-soft); }}
        .btn-ver-todas {{
            background: transparent; color: var(--muted); border: none;
            padding: 0.5rem 0.75rem; font-size: 0.78rem; font-weight: 600; cursor: pointer;
        }}
        .btn-ver-todas:hover {{ color: var(--text); text-decoration: underline; }}
        .table-container {{ overflow-x: auto; padding: 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.83rem; }}
        th, td {{ text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }}
        th {{ font-size: 0.72rem; text-transform: uppercase; color: var(--muted); background: var(--surface-soft); }}
        .td-detail {{ max-width: 300px; color: var(--text-soft); }}
        .link-blue {{ color: var(--blue); text-decoration: none; font-weight: 600; }}

        .config-grid {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 1.25rem; align-items: start; }}
        .config-main {{ display: flex; flex-direction: column; gap: 1.25rem; }}
        .config-side {{ display: flex; flex-direction: column; gap: 1rem; }}
        .card-head {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; gap: 1rem; }}
        .tag-mono {{
            font-family: monospace; font-size: 0.75rem; background: var(--surface-soft);
            padding: 0.25rem 0.55rem; border-radius: 6px; border: 1px solid var(--border); white-space: nowrap;
        }}
        .pdf-upload-box {{
            border: 1px dashed var(--border); border-radius: 10px; padding: 0.85rem 1rem;
            background: var(--surface-soft); margin-bottom: 1rem;
        }}
        .pdf-upload-row {{ display: flex; align-items: center; gap: 0.65rem; flex-wrap: wrap; }}
        .inp-file {{ flex: 1; min-width: 200px; font-size: 0.82rem; color: var(--text-soft); }}
        .add-row-form {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; }}
        .edit-list {{ display: flex; flex-direction: column; gap: 0.55rem; }}
        .list-edit-item {{
            display: flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.65rem;
            border: 1px solid var(--border); border-radius: 10px; background: var(--surface-soft);
        }}
        .inline-edit-form {{ display: flex; flex: 1; gap: 0.45rem; }}
        .inline-del-form {{ margin: 0; }}
        .inp-sm {{
            flex: 0.9; min-width: 140px; padding: 0.45rem 0.65rem; border: 1px solid var(--border);
            border-radius: 8px; background: var(--surface); color: var(--text); font-size: 0.82rem;
        }}
        .inp-lg {{
            flex: 1.4; padding: 0.45rem 0.65rem; border: 1px solid var(--border);
            border-radius: 8px; background: var(--surface); color: var(--text); font-size: 0.82rem;
        }}
        .pref-block {{ margin-bottom: 1.1rem; }}
        .pref-label {{ font-size: 0.82rem; font-weight: 700; margin-bottom: 0.45rem; }}
        .check-row {{ display: flex; flex-wrap: wrap; gap: 0.6rem; }}
        .check-pill {{
            display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.8rem;
            border: 1px solid var(--border); border-radius: 8px; background: var(--surface-soft);
            font-size: 0.82rem; font-weight: 600; cursor: pointer;
        }}
        .email-routine-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.6rem; }}
        .time-pill {{
            display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.35rem 0.7rem;
            border: 1px solid var(--border); border-radius: 8px; background: var(--surface-soft);
            font-size: 0.82rem; font-weight: 600;
        }}
        .inp-time {{
            border: 1px solid var(--border); border-radius: 6px; padding: 0.22rem 0.45rem;
            background: var(--surface); color: var(--text); font-size: 0.82rem;
        }}
        .radio-group {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }}
        .radio-card {{
            display: flex; align-items: flex-start; gap: 0.55rem; padding: 0.75rem 0.9rem;
            border: 1px solid var(--border); border-radius: 10px; background: var(--surface-soft); cursor: pointer;
        }}
        .radio-card strong {{ display: block; font-size: 0.84rem; }}
        .radio-card span {{ display: block; font-size: 0.76rem; color: var(--muted); margin-top: 0.15rem; }}

        textarea {{
            width: 100%; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.82rem; line-height: 1.55; padding: 0.9rem; border: 1px solid var(--border);
            border-radius: 10px; background: var(--surface-soft); color: var(--text);
        }}
        .form-bar {{ margin-top: 0.9rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; }}
        .clean-list {{ margin: 0.75rem 0 0; padding-left: 1.1rem; font-size: 0.83rem; color: var(--text-soft); line-height: 1.75; }}
        .empty {{ text-align: center; padding: 2rem; color: var(--muted); font-size: 0.85rem; }}

        @media (max-width: 1150px) {{
            .main-split, .config-grid, .bento-top {{
                grid-template-columns: 1fr !important;
                grid-template-areas: none !important;
            }}
            .bento-top > * {{ grid-area: auto !important; }}
            .map-card {{ position: static; }}
        }}
        @media (max-width: 900px) {{
            .cards-grid, .filter-bar, .radio-group, .add-row-form, .inline-edit-form {{
                grid-template-columns: 1fr !important; flex-direction: column;
            }}
            .main, .header {{ padding-left: 1rem; padding-right: 1rem; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <div class="brand-wrap">
                <div class="logo-badge">JH</div>
                <div>
                    <div class="brand-title">
                        Job Hunter — Painel & Candidaturas
                        <span class="sync-pill">● OpenBot</span>
                    </div>
                    <div class="brand-sub">Triagem & Candidaturas · Configurável por Usuário</div>
                </div>
            </div>
            <div class="top-actions">
                <button type="button" class="top-btn" onclick="toggleDark()">◐ Tema</button>
                <a href="/?tab={html.escape(tab)}" class="top-btn">↻ Atualizar</a>
                {nav_btn("painel", "Painel")}
                {nav_btn("rotinas", "⏱ Rotinas")}
                {nav_btn("configuracoes", "⚙ Configurações")}
            </div>
        </div>
    </header>

    <main class="main">
        {toast_html}
        {conteudo_principal}
    </main>

    <script>
        if (localStorage.getItem('jh_dark') === '1') document.body.classList.add('dark');
        function toggleDark() {{
            document.body.classList.toggle('dark');
            localStorage.setItem('jh_dark', document.body.classList.contains('dark') ? '1' : '0');
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=pagina)


@app.post("/rotinas/executar-busca")
def executar_busca_manual():
    script_path = BASE_DIR / "scripts" / "job_hunter_v3_1.py"
    if script_path.exists():
        subprocess.Popen([sys.executable, str(script_path)], cwd=str(BASE_DIR))
    return RedirectResponse(url="/?tab=rotinas&saved=rotina_busca", status_code=303)


@app.post("/rotinas/executar-incremental")
def executar_incremental_manual():
    script_path = BASE_DIR / "scripts" / "job_hunter_v3_1.py"
    if script_path.exists():
        subprocess.Popen([sys.executable, str(script_path)], cwd=str(BASE_DIR))
    return RedirectResponse(url="/?tab=rotinas&saved=rotina_inc", status_code=303)


@app.post("/configuracoes/agents/reset-universal")
def resetar_agents_universal():
    if AGENTS_MD_PATH.exists():
        shutil.copy2(AGENTS_MD_PATH, BASE_DIR / "AGENTS.md.bak")
    AGENTS_MD_PATH.write_text(AGENTS_UNIVERSAL_PADRAO.strip() + "\n", encoding="utf-8")
    sincronizar_config_no_agents(ler_config_painel())
    return RedirectResponse(url="/?tab=configuracoes&saved=agents_reset", status_code=303)


@app.post("/configuracoes/perfil/upload-pdf")
async def upload_perfil_pdf(arquivo_pdf: UploadFile = File(...)):
    garantir_arquivos_iniciais()
    conteudo_pdf = await arquivo_pdf.read()
    texto_extraido, erro = extrair_texto_pdf_bytes(conteudo_pdf)
    if erro or not texto_extraido:
        return RedirectResponse(url=f"/?tab=configuracoes&saved={erro or 'pdf_err'}", status_code=303)

    shutil.copy2(PERFIL_CV_PATH, BASE_DIR / "perfil_cv_referencia.md.bak")
    if PERFIL_CV_TXT_PATH.exists():
        shutil.copy2(PERFIL_CV_TXT_PATH, BASE_DIR / "perfil_cv_referencia.txt.bak")

    texto_final = texto_extraido.strip() + "\n"
    PERFIL_CV_TXT_PATH.write_text(texto_final, encoding="utf-8")
    PERFIL_CV_PATH.write_text(texto_final, encoding="utf-8")
    return RedirectResponse(url="/?tab=configuracoes&saved=pdf_txt", status_code=303)


@app.post("/configuracoes/perfil/salvar")
def salvar_perfil_rota(cv_texto: str = Form(...)):
    salvar_perfil_cv(cv_texto)
    return RedirectResponse(url="/?tab=configuracoes&saved=perfil", status_code=303)


@app.post("/configuracoes/vagas-buscadas/adicionar")
def adicionar_vaga_buscada(cargo: str = Form(...), foco: str = Form("")):
    cfg = ler_config_painel()
    if cargo.strip():
        cfg.setdefault("vagas_buscadas", []).append({"cargo": cargo.strip(), "foco": foco.strip()})
        salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=alvo_add", status_code=303)


@app.post("/configuracoes/vagas-buscadas/alterar")
def alterar_vaga_buscada(indice: int = Form(...), cargo: str = Form(...), foco: str = Form("")):
    cfg = ler_config_painel()
    alvos = cfg.get("vagas_buscadas", [])
    if 0 <= indice < len(alvos) and cargo.strip():
        alvos[indice] = {"cargo": cargo.strip(), "foco": foco.strip()}
        cfg["vagas_buscadas"] = alvos
        salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=alvo_edit", status_code=303)


@app.post("/configuracoes/vagas-buscadas/remover")
def remover_vaga_buscada(indice: int = Form(...)):
    cfg = ler_config_painel()
    alvos = cfg.get("vagas_buscadas", [])
    if 0 <= indice < len(alvos):
        alvos.pop(indice)
        cfg["vagas_buscadas"] = alvos
        salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=alvo_del", status_code=303)


@app.post("/configuracoes/preferencias/salvar")
def salvar_preferencias(
    modalidades: Optional[List[str]] = Form(None),
    regimes: Optional[List[str]] = Form(None),
    modo_envio: str = Form("aprovacao"),
    verificar_email_diario: Optional[str] = Form(None),
    horario_email_diario: str = Form("18:00"),
):
    cfg = ler_config_painel()
    cfg["modalidades"] = modalidades if modalidades else ["Remota"]
    cfg["regimes"] = regimes if regimes else ["PJ"]
    cfg["modo_envio"] = modo_envio if modo_envio in ("aprovacao", "automatico") else "aprovacao"
    cfg["verificar_email_diario"] = verificar_email_diario is not None
    horario_limpo = horario_email_diario.strip()
    cfg["horario_email_diario"] = horario_limpo if re.fullmatch(r"\d{2}:\d{2}", horario_limpo) else "18:00"
    salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=pref", status_code=303)


@app.post("/configuracoes/plataformas/adicionar")
def adicionar_plataforma(nome: str = Form(...), nota: str = Form("")):
    cfg = ler_config_painel()
    nome_limpo = nome.strip()
    if nome_limpo:
        cfg["plataformas"].append({"nome": nome_limpo, "nota": nota.strip()})
        salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=plat_add", status_code=303)


@app.post("/configuracoes/plataformas/alterar")
def alterar_plataforma(indice: int = Form(...), nome: str = Form(...), nota: str = Form("")):
    cfg = ler_config_painel()
    plataformas = cfg.get("plataformas", [])
    if 0 <= indice < len(plataformas) and nome.strip():
        plataformas[indice] = {"nome": nome.strip(), "nota": nota.strip()}
        cfg["plataformas"] = plataformas
        salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=plat_edit", status_code=303)


@app.post("/configuracoes/plataformas/remover")
def remover_plataforma(indice: int = Form(...)):
    cfg = ler_config_painel()
    plataformas = cfg.get("plataformas", [])
    if 0 <= indice < len(plataformas):
        plataformas.pop(indice)
        cfg["plataformas"] = plataformas
        salvar_config_painel(cfg)
    return RedirectResponse(url="/?tab=configuracoes&saved=plat_del", status_code=303)


@app.post("/configuracoes/salvar")
def salvar_configuracoes(conteudo: str = Form(...)):
    if AGENTS_MD_PATH.exists():
        shutil.copy2(AGENTS_MD_PATH, BASE_DIR / "AGENTS.md.bak")
    AGENTS_MD_PATH.write_text(conteudo, encoding="utf-8")
    return RedirectResponse(url="/?tab=configuracoes&saved=agents", status_code=303)


@app.post("/vagas/{vaga_id}/marcar-enviada")
def marcar_enviada(vaga_id: str):
    try:
        atualizar_status_vaga_csvs(
            vaga_id=vaga_id,
            novo_status="ENVIADA",
            nota_detalhe="Confirmada manualmente pelo usuário via painel.",
        )
        return RedirectResponse(url="/?tab=painel&saved=status", status_code=303)
    except Exception:
        return RedirectResponse(url="/?tab=painel&saved=status_err", status_code=303)


@app.post("/vagas/{vaga_id}/atualizar-status")
def atualizar_status_vaga(vaga_id: str, novo_status: str = Form(...)):
    try:
        st = novo_status.strip().upper()
        if st not in ("ENTREVISTA", "REJEITADA", "ENVIADA"):
            return RedirectResponse(url="/?tab=painel&saved=status_err", status_code=303)

        nota_map = {
            "ENTREVISTA": "Avançou para entrevista (atualizado via painel).",
            "REJEITADA": "Candidatura rejeitada (atualizado via painel).",
            "ENVIADA": "Confirmada manualmente pelo usuário via painel.",
        }
        saved_map = {
            "ENTREVISTA": "status_entrevista",
            "REJEITADA": "status_rejeitada",
            "ENVIADA": "status",
        }
        atualizar_status_vaga_csvs(vaga_id=vaga_id, novo_status=st, nota_detalhe=nota_map[st])
        return RedirectResponse(url=f"/?tab=painel&saved={saved_map[st]}", status_code=303)
    except Exception:
        return RedirectResponse(url="/?tab=painel&saved=status_err", status_code=303)


@app.get("/curriculos/{nome_arquivo}")
def abrir_curriculo(nome_arquivo: str):
    caminho = (CURRICULOS_DIR / nome_arquivo).resolve()
    if not str(caminho).startswith(str(CURRICULOS_DIR.resolve())) or not caminho.exists():
        raise HTTPException(status_code=404, detail="Currículo não encontrado.")
    return FileResponse(caminho, media_type="application/pdf")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("painel:app", host="127.0.0.1", port=8050, reload=False)
