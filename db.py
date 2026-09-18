"""
db.py — Conector Supabase | Central de Processos FFF
Nomes de colunas espelho exato da tabela 'processos' no Supabase.
"""

import json
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


# ── Vínculo entre auditoria e POP ─────────────────────────────────────────────

# Opções fixas de "documento de referência" quando a divergência não aponta pra um
# POP formal — mesma semântica do POPS_COMUNS do protótipo HTML.
POPS_COMUNS = [
    "GAP — processo crítico sem POP definido",
    "Além do POP — governança e maturidade",
]

# Macroprocessos plausíveis para cada frente de auditoria. O filtro é proposital-
# mente frouxo: serve só para encurtar a lista no seletor, e a UI sempre oferece
# "ver todos os POPs" — nenhum POP válido fica inacessível por causa dele.
FRENTE_MACROPROCESSOS = {
    "AÇO-AUD-01": ["Segurança de Alimentos e Qualidade"],
    "FRE-AUD-02": ["Operações de Loja e Atendimento", "Gestão de Riscos e Prevenção de Perdas"],
    "REC-AUD-03": ["Logística de Entrada", "Gestão de Riscos e Prevenção de Perdas"],
}

# Cada checklist avalia um POP-base — o checklist é a nota de cada passo desse POP.
# Aqui fica só o código do documento (coluna "Código_2"); nome e id vêm do banco, para
# não duplicar dado que já está cadastrado na aba Processos.
# O POP de operação do Açougue ainda não está cadastrado, então a frente fica sem
# base automática até que ele exista — aí passa a funcionar sozinha.
FRENTE_POP_BASE = {
    "AÇO-AUD-01": None,
    "FRE-AUD-02": "POP-3-OPL-3.25",
    "REC-AUD-03": "POP-2-LGE-2.1",
}


def _codigo_comparavel(valor) -> str:
    """Normaliza o código do POP para comparação (o banco tem 'POP -15-GPD-15.1')."""
    return re.sub(r'[\s-]', '', str(valor or '')).upper()


def pop_base_da_frente(df_processos: pd.DataFrame, tipo_checklist: str):
    """Registro do POP-base que o checklist avalia, ou None se não cadastrado."""
    codigo = FRENTE_POP_BASE.get(tipo_checklist)
    if not codigo or df_processos.empty or "codigo_2" not in df_processos.columns:
        return None

    alvo = _codigo_comparavel(codigo)
    for _, row in df_processos.iterrows():
        if _codigo_comparavel(row.get("codigo_2")) == alvo:
            return row
    return None

CRITICA_CAMPOS = {
    "texto": "",
    "codigo_item": "",
    "pop_id": None,
    "pop_nome": "",
    "pop_codigo_2": "",
    "ponto_pop": "",
    "confianca": None,
    # ── ciclo de vida da não conformidade (paridade com o HTML de referência) ──
    "status": "Aberta",
    "criticidade": "",
    "responsavel": "",
    "prazo": "",
    "acao_corretiva": "",
    "evidencia": "",
    "impacto_operacional": [],
}


def listar_processos_por_frente(df_processos: pd.DataFrame, tipo_checklist: str) -> pd.DataFrame:
    """POPs cujo macroprocesso é plausível para a frente auditada.

    DataFrame vazio (não erro) quando nada bate, para a UI cair no fallback de
    listar todos os processos.
    """
    macros = FRENTE_MACROPROCESSOS.get(tipo_checklist, [])
    if df_processos.empty or not macros or "macroprocesso" not in df_processos.columns:
        return pd.DataFrame()

    padrao = "|".join(re.escape(m) for m in macros)
    filtrado = df_processos[
        df_processos["macroprocesso"].astype(str).str.contains(padrao, case=False, na=False)
    ]
    return filtrado


def normalizar_critica(c) -> dict:
    """Devolve sempre o dict completo da não conformidade.

    Aceita as três formas que aparecem na prática: o dict já montado, a string
    simples das auditorias antigas e a string JSON — a coluna `criticas` é
    text[] no banco, então cada dict gravado volta serializado.
    """
    if isinstance(c, dict):
        return {**CRITICA_CAMPOS, **c}

    texto = str(c)
    if texto.lstrip().startswith("{"):
        try:
            dados = json.loads(texto)
            if isinstance(dados, dict):
                return {**CRITICA_CAMPOS, **dados}
        except (ValueError, TypeError):
            pass
    return {**CRITICA_CAMPOS, "texto": texto}


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


def buscar_auditoria_existente(loja: str, tipo: str, data: str):
    """Verifica se já existe uma auditoria para essa loja+frente+data. Retorna o
    registro (dict com id, total etc.) ou None. inserir_auditoria() sempre faz
    INSERT puro — sem essa checagem, salvar duas vezes a mesma loja/frente/data
    cria dois registros e as médias do Painel Geral/Rankings contam a auditoria
    em dobro."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/auditorias?loja=eq.{loja}&tipo=eq.{tipo}&data=eq.{data}&select=id,total",
        headers=HEADERS,
        timeout=20,
    )
    if not resp.ok:
        return None
    data_resp = resp.json()
    return data_resp[0] if data_resp else None


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
        # `criticas` é text[] no banco: serializa o dict aqui para não depender da
        # conversão implícita do Postgres (normalizar_critica desfaz na leitura).
        "criticas": [
            json.dumps(c, ensure_ascii=False) if isinstance(c, dict) else c
            for c in dados.get("criticas", [])
        ],
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


def atualizar_auditoria(auditoria_id: int, criticas: list) -> None:
    """Regrava o array `criticas` de uma auditoria já salva (PATCH parcial).

    Usado pela sub-aba de Não conformidades para editar status/responsável/
    prazo/ação corretiva de uma NC sem duplicar o registro da auditoria.
    """
    payload = {
        "criticas": [
            json.dumps(c, ensure_ascii=False) if isinstance(c, dict) else c
            for c in criticas
        ],
    }
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/auditorias?id=eq.{auditoria_id}",
        headers=HEADERS,
        json=payload,
        timeout=20,
    )
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)


def deletar_auditoria(auditoria_id: int) -> None:
    """Deleta uma auditoria pelo ID."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/auditorias?id=eq.{auditoria_id}",
        headers=HEADERS,
        timeout=20,
    )
    if not resp.ok:
        raise requests.HTTPError(f"{resp.status_code} — {resp.text[:300]}", response=resp)