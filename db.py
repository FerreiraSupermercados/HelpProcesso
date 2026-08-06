"""
db.py — Conector Supabase | Central de Processos FFF
Nomes de colunas espelho exato da tabela 'processos' no Supabase.
"""

import requests
import streamlit as st
import pandas as pd
import re

SUPABASE_URL: str = st.secrets["SUPABASE_URL"]
SUPABASE_KEY: str = st.secrets["SUPABASE_ANON_KEY"]
TABLE = "processos"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# ── Colunas exatas da tabela no Supabase ──────────────────────────────────────
# chave interna (usada no código) → nome real da coluna no banco
COL = {
    "tipo_documento":   "Tipo de documento",
    "nivel_atual":      "Nível atual",
    "macroprocesso":    "Macroprocessos",
    "codigo":           "Código",
    "processo":         "Processos",
    "codigo_1":         "Código_1",
    "sigla":            "Sigla",
    "status":           "Status",
    "criticidade":      "Níve de Criticidade",   # nome exato com typo do banco
    "tipo_criterio":    "Tipo de critério",
    "ultima_revisao":   "Ultima Revisão",
    "link_documento":   "Link Documento",
    "sigla_1":          "Sigla_1",
    "codigo_2":         "Código_2",
    "tipo_atividade":   "Tipo de atividade",
    "revisado_gestor":  "Revisado pelo Gestor",
    "observacoes":      "Observações",
    "objetivo":         "Objetivo Estratégico",
}

# Colunas que aparecem na tabela principal (na ordem desejada)
COLS_TABELA = [
    "tipo_documento", "macroprocesso", "codigo",
    "processo", "codigo_1", "sigla", "status",
    "criticidade", "tipo_criterio", "tipo_atividade",
]

# Rótulos exibidos no cabeçalho da tabela
LABELS = {
    "tipo_documento":  "Tipo de Documento",
    "objetivo":        "Objetivo Estratégico",
    "macroprocesso":   "Macroprocesso",
    "codigo":          "Código",
    "processo":        "Processo",
    "codigo_1":        "Cód. Processo",
    "sigla":           "Sigla",
    "status":          "Status",
    "criticidade":     "Criticidade",
    "tipo_criterio":   "Tipo de Critério",
    "ultima_revisao":  "Última Revisão",
    "tipo_atividade":  "Tipo de Atividade",
    "nivel_atual":     "Nível Atual",
}

STATUS_OPTS      = ["Ativo", "Em Atualização", "Pendente"]
CRITICIDADE_OPTS = ["Alta", "Moderada", "Leve"]


# ── Helpers de URL do Drive ───────────────────────────────────────────────────

def _extract_drive_id(url: str) -> str:
    """
    Extrai o ID do arquivo a partir de qualquer formato comum de URL do Google Drive:
      - https://drive.google.com/file/d/FILE_ID/view?usp=sharing
      - https://drive.google.com/file/d/FILE_ID/view
      - https://drive.google.com/open?id=FILE_ID
      - https://drive.google.com/uc?id=FILE_ID
      - https://docs.google.com/document/d/FILE_ID/edit
    """
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",    # formato padrão /file/d/ID
        r"/d/([a-zA-Z0-9_-]{20,})",      # /d/ID (docs, sheets…) — mín. 20 chars para não capturar segmentos curtos
        r"[?&]id=([a-zA-Z0-9_-]+)",      # ?id=ID ou &id=ID (open, uc…)
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return ""


def drive_preview(url: str) -> str:
    """Converte qualquer URL do Drive para o formato de pré-visualização embutida."""
    if not url or not url.strip():
        return ""
    url = url.strip()
    if "/preview" in url:
        return url.split("?")[0]          # remove query params de links já em /preview
    file_id = _extract_drive_id(url)
    if file_id:
        return f"https://drive.google.com/file/d/{file_id}/preview"
    return url if url.startswith("http") else ""


def drive_direct(url: str) -> str:
    """Converte qualquer URL do Drive para o formato de link direto /view."""
    if not url or not url.strip():
        return ""
    url = url.strip()
    file_id = _extract_drive_id(url)
    if file_id:
        return f"https://drive.google.com/file/d/{file_id}/view"
    # Não é um link do Drive — retorna como está se for uma URL válida
    return url if url.startswith("http") else ""


# ── CRUD ──────────────────────────────────────────────────────────────────────

def _ep(params: str = "") -> str:
    return f"{SUPABASE_URL}/rest/v1/{TABLE}{params}"


def listar_processos() -> pd.DataFrame:
    """
    Busca todos os processos. Usa select explícito com os nomes reais das colunas
    para evitar erro 400 no order com colunas de nome composto.
    """
    # Monta select explícito com todos os campos
    select_cols = ",".join(
        f'"{v}"' for v in list(COL.values()) + ["id", "criado_em", "atualizado_em"]
    )
    # Order com aspas para colunas com espaço/maiúscula
    order = f'"Macroprocessos".asc,"Processos".asc'

    resp = requests.get(
        _ep(f'?select={select_cols}&order={order}&limit=2000'),
        headers=HEADERS,
        timeout=20,
    )
    if not resp.ok:
        raise requests.HTTPError(
            f"{resp.status_code} — {resp.text[:300]}", response=resp
        )

    data = resp.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Renomeia colunas do banco → chaves internas para o app usar normalmente
    # Renomeia colunas do banco → chaves internas para o app usar normalmente
    inv = {v: k for k, v in COL.items()}
    df = df.rename(columns=inv)

    # ✅ Converte campos de texto para string, evitando NaN/float em .strip()
    cols_texto = [c for c in df.columns if c not in ("id", "criado_em", "atualizado_em")]
    df[cols_texto] = df[cols_texto].fillna("").astype(str)

    # Colunas de link processadas
    if "link_documento" in df.columns:
        df["link_preview"] = df["link_documento"].apply(drive_preview)
        df["link_direto"]  = df["link_documento"].apply(drive_direct)

    return df
#def payload para banco e coluna de link processadas para atualizar chaves internas

def _payload_para_banco(dados: dict) -> dict:
    """Converte dict com chaves internas → nomes reais das colunas do banco."""
    return {COL[k]: v for k, v in dados.items() if k in COL}


def inserir_processo(dados: dict) -> dict:
    payload = _payload_para_banco(dados)
    resp = requests.post(_ep(), headers=HEADERS, json=payload, timeout=20)
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)
    return resp.json()


def atualizar_processo(processo_id: int, dados: dict) -> dict:
    payload = _payload_para_banco(dados)
    resp = requests.patch(
        _ep(f"?id=eq.{processo_id}"),
        headers=HEADERS, json=payload, timeout=20,
    )
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)
    return resp.json()


def deletar_processo(processo_id: int) -> None:
    resp = requests.delete(_ep(f"?id=eq.{processo_id}"), headers=HEADERS, timeout=20)
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)


# ── Filtros ───────────────────────────────────────────────────────────────────

def filter_opts(df: pd.DataFrame, col_key: str) -> list:
    """col_key = chave interna (ex: 'macroprocesso')"""
    if df.empty or col_key not in df.columns:
        return ["Todos"]
    vals = sorted({str(v).strip() for v in df[col_key].dropna() if str(v).strip()})
    return ["Todos"] + vals
# ── LGPD ─────────────────────────────────────────────────────────────────────

def usuario_aceitou_lgpd(usuario: str) -> bool:
    """Verifica se o usuário já aceitou os termos."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/aceites_lgpd?usuario=eq.{usuario}&select=id&limit=1",
        headers=HEADERS,
        timeout=10,
    )
    if not resp.ok:
        return False
    return len(resp.json()) > 0


def registrar_aceite_lgpd(usuario: str) -> None:
    """Registra o aceite do usuário na tabela aceites_lgpd."""
    payload = {"usuario": usuario}
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/aceites_lgpd",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )
    if not resp.ok:
        raise requests.HTTPError(
            f"{resp.status_code} — {resp.text[:300]}", response=resp
        )

        
# ── AUDITORIAS ─────────────
def listar_auditorias(loja: str = None, tipo: str = None) -> pd.DataFrame:
    """Busca todas as auditorias do Supabase."""
    # Monta a query
    params = "?select=*&order=data.desc"
    if loja:
        params += f"&loja=eq.{loja}"
    if tipo:
        params += f"&tipo=eq.{tipo}"
    
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/auditorias{params}",
        headers=HEADERS,
        timeout=20,
    )
    if not resp.ok:
        print(f"Erro ao buscar auditorias: {resp.status_code} — {resp.text[:200]}")
        return pd.DataFrame()
    
    data = resp.json()
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Converte topicos de JSON para lista
    if "topicos" in df.columns:
        df["topicos"] = df["topicos"].apply(lambda x: x if isinstance(x, list) else [])
    
    # Converte criticas de JSON para lista
    if "criticas" in df.columns:
        df["criticas"] = df["criticas"].apply(lambda x: x if isinstance(x, list) else [])
    
    return df


def inserir_auditoria(dados: dict) -> dict:
    """Insere uma nova auditoria no Supabase."""
    # Prepara o payload
    payload = {
        "loja": dados.get("loja"),
        "data": dados.get("data"),
        "tipo": dados.get("tipo"),
        "avaliador": dados.get("avaliador", "Auditor Controladoria"),
        "topicos": dados.get("topicos", []),
        "total": dados.get("total", 0),
        "criticas": dados.get("criticas", [])
    }
    
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/auditorias",
        headers=HEADERS,
        json=payload,
        timeout=20,
    )
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)
    return resp.json()


def deletar_auditoria(auditoria_id: int) -> None:
    """Deleta uma auditoria pelo ID."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/auditorias?id=eq.{auditoria_id}",
        headers=HEADERS,
        timeout=20,
    )
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)