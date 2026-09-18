"""
app.py — Central de Processos e Riscos | Ferreira Supermercados
Banco: Supabase | PDFs: Google Drive (público via link)
"""
import pdfplumber
import re
import io
import math
import requests
from datetime import timedelta
import streamlit as st
import pandas as pd
import base64, os
import textwrap
import html as html_lib
import numpy as np
from db import (
    listar_processos, inserir_processo, atualizar_processo, deletar_processo,
    filter_opts, drive_preview, drive_direct,
    COLS_TABELA, LABELS, COL, STATUS_OPTS, CRITICIDADE_OPTS,
    usuario_aceitou_lgpd, registrar_aceite_lgpd,
    listar_auditorias, inserir_auditoria, deletar_auditoria, atualizar_auditoria,
    listar_processos_por_frente, normalizar_critica, pop_base_da_frente,
    buscar_auditoria_existente, CRITICA_CAMPOS,
)


def _img_b64(path: str) -> str:
    """Carrega imagem local como base64 para uso em HTML."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"

_LOGO_HEADER  = _img_b64("LOGO.png")
_LOGO_SIDEBAR = _img_b64("LOGO2.png")

st.set_page_config(
    page_title="Central de Processos | FFF",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Nunito:wght@400;500;600;700;800&family=Barlow+Semi+Condensed:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --vd:#0a3d1f; --vm:#115c2e; --vc:#1a8040; --vmt:#e6f4ec;
    --am:#f8c10a; --amd:#d4a200; --aml:#fff8d6;
    --cr:#f5f9f6; --tx:#0d2a16; --mu:#4d7a5e; --bd:#b8ddc7; --wh:#ffffff;
    --shadow: 0 4px 24px rgba(10,61,31,.10);
}
html,body,[class*="css"]{font-family:'Nunito',sans-serif;color:var(--tx);}
.stApp{background:var(--cr);}
.block-container{padding:0 1.5rem 3rem!important;}

/* ── Custom Streamlit Tabs ── */
div[data-baseweb="tab-list"] {
    background-color: #f4fbf6 !important;
    border-bottom: 2px solid #b8ddc7 !important;
    padding: 0 10px !important;
    border-radius: 12px 12px 0 0 !important;
    gap: 6px !important;
}

button[role="tab"] {
    font-family: 'Barlow Semi Condensed', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #728177 !important;
    background-color: transparent !important;
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 16px !important;
    transition: all 0.15s ease-in-out !important;
}

button[role="tab"]:hover {
    color: #12331C !important;
    background-color: rgba(46,158,55,.05) !important;
}

button[role="tab"][aria-selected="true"] {
    color: #12331C !important;
    background-color: #ffffff !important;
    border-bottom: 4px solid #f8c10a !important;
    font-weight: 700 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"]{background:linear-gradient(180deg,var(--vd) 0%,#072812 100%)!important;border-right:4px solid var(--am);}
[data-testid="stSidebar"] *{color:#cce8d8!important;}
[data-testid="stSidebar"] label{color:var(--am)!important;font-size:.67rem!important;font-weight:700!important;letter-spacing:.12em!important;text-transform:uppercase!important;}
[data-testid="stSidebar"] [data-baseweb="select"]>div{background:rgba(255,255,255,.06)!important;border-color:rgba(248,193,10,.22)!important;border-radius:8px!important;}
[data-testid="stSidebar"] input{background:rgba(255,255,255,.06)!important;border-color:rgba(248,193,10,.22)!important;border-radius:8px!important;}
[data-testid="stSidebar"] .stButton>button{background:rgba(248,193,10,.12)!important;border:1.5px solid rgba(248,193,10,.35)!important;color:var(--am)!important;border-radius:9px!important;font-weight:700!important;font-size:.82rem!important;transition:all .2s!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:var(--am)!important;color:var(--vd)!important;}

/* ── Login ── */
.login-card{background:var(--wh);border-radius:20px;padding:2.8rem 2.5rem 2.2rem;box-shadow:0 20px 60px rgba(10,61,31,.14);border:1px solid var(--bd);text-align:center;margin-top:3rem;}
.login-badge{display:inline-block;background:var(--vd);color:var(--am)!important;font-family:'Oswald',sans-serif;font-size:2.5rem;font-weight:700;letter-spacing:.12em;padding:.3rem 1rem;border-radius:10px;border:2.5px solid var(--am);margin-bottom:.5rem;}
.login-title{font-family:'Oswald',sans-serif;font-size:1.15rem;color:var(--vd);margin:.4rem 0 .1rem;font-weight:600;}
.login-sub{font-size:.72rem;color:var(--mu);letter-spacing:.1em;text-transform:uppercase;margin-bottom:.3rem;}
.login-line{height:2px;background:linear-gradient(90deg,transparent,var(--am),transparent);margin:1.3rem 0;border:none;opacity:.7;}

/* ── Header ── */
.fff-header{background:linear-gradient(100deg,var(--vd) 0%,var(--vm) 55%,#1d6e3a 100%);padding:.9rem 2rem;margin:0 -1.5rem 1.5rem -1.5rem;border-bottom:4px solid var(--am);display:flex;align-items:center;gap:1.2rem;box-shadow:0 5px 28px rgba(0,0,0,.22);}
.fff-logo-img{height:52px;width:auto;object-fit:contain;filter:drop-shadow(0 2px 8px rgba(0,0,0,.3));}
.fff-badge{font-family:'Oswald',sans-serif;font-size:2rem;font-weight:700;color:var(--am);border:2.5px solid var(--am);padding:.15rem .65rem;border-radius:7px;letter-spacing:.12em;line-height:1;flex-shrink:0;}
.header-text h1{font-family:'Oswald',sans-serif;font-size:1.25rem;font-weight:600;color:#e0f0e8;margin:0;letter-spacing:.04em;}
.header-text p{font-size:.68rem;color:var(--am);margin:.1rem 0 0;letter-spacing:.16em;text-transform:uppercase;opacity:.9;}

/* ── Métricas ── */
.metric-card{background:var(--wh);border-radius:12px;padding:.85rem 1rem;border:1px solid var(--bd);border-left:3px solid var(--vm);box-shadow:0 1px 2px rgba(18,51,28,.06),0 4px 16px rgba(18,51,28,.05);}
.metric-num{font-family:'Barlow Semi Condensed',sans-serif;font-size:2.2rem;font-weight:700;color:var(--vd);line-height:1;margin-bottom:.2rem;}
.metric-lbl{font-size:.72rem;font-weight:700;color:var(--mu);text-transform:uppercase;letter-spacing:.06em;}
.mc-ativo{border-left-color:#0d6632;} .mc-ativo .metric-num{color:#0d6632;}
.mc-atualiz{border-left-color:#944f00;} .mc-atualiz .metric-num{color:#944f00;}
.mc-pendente{border-left-color:#7a1515;} .mc-pendente .metric-num{color:#7a1515;}

/* ── Sidebar elementos ── */
.sb-section{font-size:.62rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--am);padding:.9rem 0 .3rem;display:block;border-top:1px solid rgba(248,193,10,.1);margin-top:.4rem;}
.sb-logo-wrap{padding:1.2rem 1rem .9rem;text-align:center;border-bottom:1px solid rgba(248,193,10,.12);margin-bottom:.4rem;}
.sb-logo-img{max-width:140px;max-height:70px;width:auto;height:auto;object-fit:contain;filter:brightness(1.05) drop-shadow(0 2px 6px rgba(0,0,0,.35));}
.sb-fff{font-family:'Oswald',sans-serif;font-size:2rem;font-weight:700;color:var(--am)!important;border:2px solid var(--am);display:inline-block;padding:.15rem .7rem;border-radius:7px;letter-spacing:.1em;line-height:1.1;}
.sb-sub{display:block;font-size:.6rem;color:rgba(204,232,216,.45)!important;letter-spacing:.14em;text-transform:uppercase;margin-top:.45rem;}
.sb-user{background:rgba(248,193,10,.07);border:1px solid rgba(248,193,10,.18);border-radius:9px;padding:.4rem .8rem;margin-bottom:.5rem;display:flex;align-items:center;gap:.4rem;font-size:.77rem;}
.sb-admin{background:var(--am);color:var(--vd)!important;font-size:.58rem;font-weight:800;padding:2px 8px;border-radius:20px;margin-left:auto;text-transform:uppercase;letter-spacing:.05em;}

/* ── Tabela ── */
.table-wrap{background:var(--wh);border-radius:16px;border:1px solid var(--bd);box-shadow:var(--shadow);overflow:hidden;}
.table-toolbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;padding:.85rem 1.4rem;background:linear-gradient(90deg,var(--vmt),var(--wh));border-bottom:2px solid var(--bd);}
.results-pill{background:var(--vd);color:var(--am);padding:.3rem .95rem;border-radius:20px;font-size:.75rem;font-weight:800;letter-spacing:.04em;}
.table-scroll{overflow-x:auto;max-height:56vh;overflow-y:auto;}
table.fff-table{width:100%;border-collapse:collapse;font-size:.8rem;}
table.fff-table thead tr{background:var(--vd);position:sticky;top:0;z-index:2;}
table.fff-table thead th{color:#9ecfb2;font-weight:700;font-size:.66rem;letter-spacing:.09em;text-transform:uppercase;padding:.8rem 1rem;text-align:left;border-bottom:3px solid var(--am);white-space:nowrap;}
table.fff-table thead th.c-doc{color:var(--am);text-align:center;min-width:130px;}
table.fff-table tbody tr{border-bottom:1px solid #e8f3ec;transition:background .12s;}
table.fff-table tbody tr:hover{background:#eaf7ef;}
table.fff-table tbody tr:nth-child(even){background:#f4fbf6;}
table.fff-table tbody tr:nth-child(even):hover{background:#e2f4e8;}
table.fff-table tbody td{padding:.65rem 1rem;color:var(--tx);vertical-align:middle;white-space:nowrap;max-width:220px;overflow:hidden;text-overflow:ellipsis;}
table.fff-table tbody td.c-doc{text-align:center;white-space:nowrap;}

/* ── Badges ── */
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.65rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;}
.b-ativo{background:#d4f0e0;color:#0d6632;border:1px solid #8ecfaa;}
.b-atualiz{background:#fef3d0;color:#7a4f00;border:1px solid #f0d070;}
.b-pendente{background:#fce8e8;color:#7a1515;border:1px solid #f0aaaa;}
.b-default{background:#e8ecea;color:#3d5a47;border:1px solid #c0d4c8;}

/* ── Criticidade ── */
.crit{display:inline-flex;align-items:center;gap:5px;font-size:.79rem;font-weight:600;}
.cdot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.c-alta .cdot{background:#e63030;box-shadow:0 0 5px #e6303088;}
.c-media .cdot{background:#e67e22;box-shadow:0 0 5px #e67e2288;}
.c-leve .cdot{background:#22a356;box-shadow:0 0 5px #22a35688;}

/* ── Botão PDF ── */
.pdf-btn{display:inline-flex;align-items:center;gap:5px;background:var(--vd);color:var(--am)!important;border:2px solid rgba(248,193,10,.45);padding:5px 13px;border-radius:8px;font-size:.72rem;font-weight:800;text-decoration:none!important;letter-spacing:.03em;transition:all .18s;white-space:nowrap;}
.pdf-btn:hover{background:var(--am);color:var(--vd)!important;border-color:var(--am);transform:scale(1.05);box-shadow:0 4px 14px rgba(248,193,10,.4);}
.no-link{color:#bbb;font-size:.8rem;}

/* ── Viewer ── */
.pdf-viewer-wrap{background:var(--wh);border-radius:16px;border:3px solid var(--am);overflow:hidden;box-shadow:0 10px 44px rgba(0,0,0,.16);margin-top:1rem;}
.pdf-viewer-bar{background:var(--vd);padding:.65rem 1.2rem;display:flex;align-items:center;justify-content:space-between;border-bottom:3px solid var(--am);}
.pdf-viewer-bar span{color:#e0f0e8;font-weight:700;font-size:.9rem;}

/* ── Admin ── */
.admin-header{background:linear-gradient(135deg,#081e10,#0d3a1c);border:1.5px solid var(--am);border-radius:12px;padding:1rem 1.4rem;margin-bottom:1rem;display:flex;align-items:center;gap:.8rem;}
.admin-title{color:var(--am);font-weight:700;font-size:1rem;font-family:'Oswald',sans-serif;letter-spacing:.04em;}
.admin-sub{color:rgba(255,255,255,.4);font-size:.71rem;margin-top:.1rem;}

/* ── Misc ── */
.gold-line{border:none;height:2px;background:linear-gradient(90deg,transparent,var(--am),transparent);margin:1.1rem 0;opacity:.55;}
.footer{text-align:center;padding:1.3rem;margin-top:2rem;border-top:1px solid var(--bd);color:var(--mu);font-size:.7rem;letter-spacing:.06em;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--vmt);}
::-webkit-scrollbar-thumb{background:var(--vc);border-radius:3px;}
/* ── Modal LGPD ── */
.lgpd-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:center;justify-content:center;}
.lgpd-card{background:var(--wh);border-radius:18px;padding:2.2rem 2rem 1.8rem;max-width:520px;width:90%;border:3px solid var(--am);box-shadow:0 20px 60px rgba(0,0,0,.35);}
.lgpd-icon{font-size:2.4rem;text-align:center;margin-bottom:.5rem;}
.lgpd-title{font-family:'Oswald',sans-serif;font-size:1.3rem;color:var(--vd);text-align:center;font-weight:700;margin-bottom:.3rem;}
.lgpd-sub{font-size:.72rem;color:var(--mu);text-align:center;letter-spacing:.1em;text-transform:uppercase;margin-bottom:1.1rem;}
.lgpd-body{background:var(--vmt);border:1px solid var(--bd);border-radius:10px;padding:1rem 1.2rem;font-size:.82rem;color:var(--tx);line-height:1.7;margin-bottom:1.2rem;}
.lgpd-body strong{color:var(--vd);}
</style>
""", unsafe_allow_html=True)


def check_credentials(u, p):
    return st.secrets.get("users", {}).get(u) == p

def is_admin(u):
    return u in st.secrets.get("admins", [])

def _session_token(u: str) -> str:
    """Token determinístico p/ manter o login após F5, sem expor a senha na URL."""
    import hashlib
    segredo = st.secrets.get("session_secret", "fff-central-processos")
    senha = st.secrets.get("users", {}).get(u, "")
    return hashlib.sha256(f"{u}:{senha}:{segredo}".encode()).hexdigest()[:32]

def restaurar_sessao():
    """Reidrata auth/admin a partir do token salvo na URL (sobrevive a F5)."""
    if st.session_state.get("auth"):
        return
    qp = st.query_params
    u, tok = qp.get("u"), qp.get("s")
    if u and tok and st.secrets.get("users", {}).get(u) is not None:
        if tok == _session_token(u):
            st.session_state.update(auth=True, username=u, admin=is_admin(u))

@st.dialog("Termo de Ciência — LGPD", width="large")
def lgpd_modal():
    st.markdown("""
    <div style="text-align:center;margin-bottom:.5rem;">
        <span style="font-size:.72rem;color:#4d7a5e;letter-spacing:.1em;text-transform:uppercase;">
            Grupo Ferreira · Acesso a Dados Sensíveis
        </span>
    </div>
    <div style="background:#e6f4ec;border:1px solid #b8ddc7;border-radius:10px;
                padding:1rem 1.2rem;font-size:.85rem;color:#0d2a16;line-height:1.8;margin-bottom:1.2rem;">
        Ao acessar este sistema, você declara estar ciente de que:<br><br>
        • As informações aqui disponíveis são <strong>confidenciais e de uso interno</strong> do Grupo Ferreira.<br>
        • O acesso é <strong>individual e intransferível</strong>, sendo vedado o compartilhamento de credenciais.<br>
        • Os dados estão protegidos pela <strong>Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018)</strong>.<br>
        • O uso indevido ou compartilhamento não autorizado pode implicar em <strong>responsabilidade civil e criminal</strong>.<br>
        • Seu aceite será <strong>registrado com data e hora</strong> para fins de auditoria.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Aceitar e Entrar", use_container_width=True, type="primary"):
            try:
                registrar_aceite_lgpd(_user)
                st.session_state["lgpd_ok"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao registrar aceite: {e}")
    with col2:
        if st.button("Recusar e Sair", use_container_width=True):
            for k in ["auth", "username", "admin", "lgpd_ok"]:
                st.session_state.pop(k, None)
            st.rerun()


def lgpd_gate():
    if st.session_state.get("lgpd_ok"):
        return True

    if usuario_aceitou_lgpd(_user):
        st.session_state["lgpd_ok"] = True
        return True


    lgpd_modal()
    return False
def login_screen():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        _logo_login = (
            f'<img src="{_LOGO_HEADER}" style="max-height:100px;width:auto;'
            f'object-fit:contain;margin-bottom:.6rem;" alt="Ferreira Supermercados">'
            if _LOGO_HEADER else '<div class="login-badge">FFF</div>'
        )
        st.markdown(f"""
        <div class="login-card">
            {_logo_login}
            <div class="login-title">Central de Processos e Riscos</div>
            <div class="login-sub">Ferreira Supermercados</div>
            <hr class="login-line">
        </div>""", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            u = st.text_input("Usuário", placeholder="seu.usuario")
            p = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("Entrar →", use_container_width=True)
        if entrar:
            u = u.strip()
            if check_credentials(u, p):
                st.session_state.update(auth=True, username=u, admin=is_admin(u))
                st.query_params.update(u=u, s=_session_token(u))
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

restaurar_sessao()

if not st.session_state.get("auth"):
    login_screen()
    st.stop()

_user  = st.session_state["username"]
_admin = st.session_state.get("admin", False)


if not lgpd_gate():
    st.stop()


def badge_status(v):
    s = v.upper()
    c = "b-ativo" if "ATIVO" in s else "b-atualiz" if "ATUALIZA" in s else "b-pendente" if "PENDENTE" in s else "b-default"
    return f'<span class="badge {c}">{v}</span>'

def badge_crit(v):
    c = v.lower()
    cls = "c-alta"  if any(x in c for x in ["alta","crítica","critica"]) else \
          "c-media" if any(x in c for x in ["modera","média","media"])   else \
          "c-leve"  if any(x in c for x in ["leve","baixa"])             else ""
    return f'<span class="crit {cls}"><span class="cdot"></span>{v}</span>' if cls else v

def apply_filter(df, col, val):
    if val and val != "Todos" and col in df.columns:
        return df[df[col].astype(str).str.strip() == val.strip()]
    return df

@st.cache_data(ttl=60, show_spinner=False)
def load():
    return listar_processos()


with st.sidebar:
    ab = '<span class="sb-admin">Admin</span>' if _admin else ""
    _logo_s_tag = f'<img src="{_LOGO_SIDEBAR}" class="sb-logo-img" alt="Ferreira Supermercados">' if _LOGO_SIDEBAR else '<div class="sb-fff">FFF</div>'
    st.markdown(f"""
    <div class="sb-logo-wrap">
        {_logo_s_tag}
        <span class="sb-sub">Central de Processos e Riscos</span>
    </div>
    <div class="sb-user"><span>👤</span><span>{_user}</span>{ab}</div>
    """, unsafe_allow_html=True)

    if st.button("Sair", use_container_width=True):
        [st.session_state.pop(k, None) for k in ["auth","username","admin"]]
        st.query_params.clear()
        st.cache_data.clear(); st.rerun()

    with st.spinner("Carregando..."):
        try:
            df_raw = load()
        except Exception as e:
            st.error(f"Erro no banco:\n{e}"); st.stop()

    if df_raw.empty:
        st.warning("Nenhum processo cadastrado ainda.")

    st.markdown('<span class="sb-section">🔍 Filtros</span>', unsafe_allow_html=True)
    #f_obj   = st.selectbox("Objetivo Estratégico", filter_opts(df_raw, "objetivo"))
    f_mac   = st.selectbox("Macroprocesso",         filter_opts(df_raw, "macroprocesso"))
    f_proc  = st.selectbox("Processo",              filter_opts(df_raw, "processo"))
    f_stat  = st.selectbox("Status",                filter_opts(df_raw, "status"))
    f_crit  = st.selectbox("Criticidade",           filter_opts(df_raw, "criticidade"))
    f_tdoc  = st.selectbox("Tipo de Documento",     filter_opts(df_raw, "tipo_documento"))
    f_tativ = st.selectbox("Tipo de Atividade",     filter_opts(df_raw, "tipo_atividade"))
    f_tcrit = st.selectbox("Tipo de Critério",      filter_opts(df_raw, "tipo_criterio"))

    st.markdown('<span class="sb-section">🔎 Busca livre</span>', unsafe_allow_html=True)
    f_busca = st.text_input("Buscar", placeholder="Nome, sigla, código...", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear(); st.rerun()

df = df_raw.copy() if not df_raw.empty else pd.DataFrame()
if not df.empty:
    for col, val in [
        ("macroprocesso", f_mac), ("processo", f_proc),
        ("status", f_stat), ("criticidade", f_crit), ("tipo_documento", f_tdoc),
        ("tipo_atividade", f_tativ), ("tipo_criterio", f_tcrit),
    ]:
        df = apply_filter(df, col, val)

    if f_busca.strip():
        skip = {"id","link_documento","link_preview","link_direto","criado_em","atualizado_em"}
        tc = [c for c in df.columns if c not in skip]
        mask = df[tc].apply(
            lambda c: c.astype(str).str.contains(f_busca.strip(), case=False, na=False)
        ).any(axis=1)
        df = df[mask]


_logo_h_tag = f'<img src="{_LOGO_HEADER}" class="fff-logo-img" alt="Ferreira Supermercados">' if _LOGO_HEADER else '<div class="fff-badge">FFF</div>'
st.markdown(f"""
<div class="fff-header">
    {_logo_h_tag}
    <div class="header-text">
        <h1>Central de Processos e Riscos</h1>
        <p>Ferreira Supermercados · Repositório Corporativo</p>
    </div>
</div>""", unsafe_allow_html=True)

tab_labels = ["Processos"]
if _admin:
    tab_labels += ["Novo Processo", "Gerenciar"]
tab_labels += ["Auditoria"] 
tabs = st.tabs(tab_labels)
audit_tab_index = 3 if _admin else 1

with tabs[0]:
    total = len(df_raw)
    def cnt(kw):
        return int(df_raw["status"].astype(str).str.upper().str.contains(kw, na=False).sum()) \
               if not df_raw.empty and "status" in df_raw.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    for cw, num, lbl, cls in [
        (c1, total,            "Total",          ""),
        (c2, cnt("ATIVO"),     "Ativos",         " mc-ativo"),
        (c3, cnt("ATUALIZA"),  "Em Atualização", " mc-atualiz"),
        (c4, cnt("PENDENTE"),  "Pendentes",      " mc-pendente"),
    ]:
        with cw:
            st.markdown(
                f'<div class="metric-card{cls}">'
                f'<div class="metric-num">{num}</div>'
                f'<div class="metric-lbl">{lbl}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<hr class="gold-line">', unsafe_allow_html=True)

    # ── Tabela ──
    # Exibe apenas as colunas que realmente existem no df
    cols_visiveis = [c for c in COLS_TABELA if c in df_raw.columns]
    n_filt = len(df)

    st.markdown(f"""
    <div class="table-wrap">
      <div class="table-toolbar">
        <span class="results-pill">{n_filt} processo(s)</span>
        <span style="font-size:.72rem;color:var(--mu);">{total} total · filtre pela barra lateral</span>
      </div>""", unsafe_allow_html=True)

    if df.empty:
        st.markdown("</div>", unsafe_allow_html=True)
        st.info("Nenhum processo encontrado com os filtros aplicados.")
    else:
        th = "".join(f"<th>{LABELS.get(c, c)}</th>" for c in cols_visiveis)
        th += '<th class="c-doc">Documento</th>'

        tbody = ""
        for _, row in df.iterrows():
            tds = ""
            for col in cols_visiveis:
                val = str(row.get(col, "")).strip()
                if col == "status":
                    val = badge_status(val)
                elif col == "criticidade":
                    val = badge_crit(val)
                tds += f"<td>{val}</td>"

            url_d = str(row.get("link_direto", "")).strip()
            doc_cell = (
                f'<a class="pdf-btn" href="{url_d}" target="_blank" rel="noopener">📄 Abrir PDF</a>'
                if url_d.startswith("http") else '<span class="no-link">—</span>'
            )
            tds += f'<td class="c-doc">{doc_cell}</td>'
            tbody += f"<tr>{tds}</tr>"

        st.markdown(f"""
          <div class="table-scroll">
            <table class="fff-table">
              <thead><tr>{th}</tr></thead>
              <tbody>{tbody}</tbody>
            </table>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Visualizador online de PDF ──
    st.markdown("<br>", unsafe_allow_html=True)
    if not df.empty and "link_direto" in df.columns:
        df_pdf = df[df["link_direto"].astype(str).str.startswith("http")]
        if not df_pdf.empty:
            with st.expander("🔍 Visualizar PDF online", expanded=False):
                st.caption("Selecione um processo para ver o documento sem sair da página.")
                opcoes = {
                    f"[{str(r.get('sigla','') or '—')}]  {str(r.get('processo',''))}": r
                    for _, r in df_pdf.iterrows()
                }
                sel = st.selectbox(
                    "Processo:", ["— selecione —"] + list(opcoes.keys()),
                    label_visibility="collapsed"
                )
                if sel != "— selecione —":
                    row_s   = opcoes[sel]
                    preview = str(row_s.get("link_preview","")).strip()
                    direto  = str(row_s.get("link_direto","")).strip()
                    nome    = str(row_s.get("processo","Documento")).strip()

                    st.markdown(f"""
                    <div class="pdf-viewer-wrap">
                      <div class="pdf-viewer-bar">
                        <span>📄 {nome}</span>
                        <a class="pdf-btn" href="{direto}" target="_blank">↗ Abrir em nova aba</a>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    if preview:
                        st.components.v1.iframe(preview, height=720, scrolling=True)
                    else:
                        st.warning("Pré-visualização indisponível. Use o botão abaixo.")
                        st.markdown(
                            f'<a class="pdf-btn" href="{direto}" target="_blank">📄 Abrir PDF</a>',
                            unsafe_allow_html=True
                        )

# ════════════ ABA 2 — NOVO PROCESSO (admin) ═══════════════════════════════════
if _admin:
    with tabs[1]:
        st.markdown("""
        <div class="admin-header">
            <span style="font-size:1.4rem;"></span>
            <div><div class="admin-title">Cadastrar Novo Processo</div>
            <div class="admin-sub">Preencha os campos e salve no banco de dados.</div></div>
        </div>""", unsafe_allow_html=True)

        with st.form("form_novo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n_td  = st.text_input("Tipo de Documento")
                n_obj = st.text_input("Objetivo Estratégico")
                n_mac = st.text_input("Macroprocesso")
                n_cod = st.text_input("Código do Macroprocesso")
                n_pr  = st.text_input("Processo *")
                n_cp  = st.text_input("Código do Processo")
                n_tativ = st.text_input("Tipo de Atividade")
            with c2:
                n_sig  = st.text_input("Sigla")
                n_sig1 = st.text_input("Sigla_1 (se houver)")
                n_cod2 = st.text_input("Código_2 (se houver)")
                n_st   = st.selectbox("Status", STATUS_OPTS)
                n_cr   = st.selectbox("Criticidade", CRITICIDADE_OPTS)
                n_tc   = st.text_input("Tipo de Critério")
                n_ur   = st.text_input("Última Revisão", placeholder="dd/mm/aaaa")
                n_niv  = st.text_input("Nível Atual")
            n_lk  = st.text_input(
                "Link do PDF (Google Drive)",
                placeholder="https://drive.google.com/file/d/...",
                help="Configure o arquivo como 'Qualquer pessoa com o link pode visualizar'"
            )
            n_rev = st.text_input("Revisado pelo Gestor")
            n_obs = st.text_area("Observações", height=80)

            st.caption("O PDF deve estar no Drive com permissão 'Qualquer pessoa com o link pode visualizar'.")

            if st.form_submit_button("Salvar Processo", use_container_width=True):
                if not n_pr.strip():
                    st.error("O campo 'Processo' é obrigatório.")
                else:
                    try:
                        inserir_processo({
                            "tipo_documento": n_td.strip(),
                            "objetivo":       n_obj.strip(),
                            "macroprocesso":  n_mac.strip(),
                            "codigo":         n_cod.strip(),
                            "processo":       n_pr.strip(),
                            "codigo_1":       n_cp.strip(),
                            "sigla":          n_sig.strip(),
                            "sigla_1":        n_sig1.strip(),
                            "codigo_2":       n_cod2.strip(),
                            "status":         n_st,
                            "criticidade":    n_cr,
                            "tipo_criterio":  n_tc.strip(),
                            "ultima_revisao": n_ur.strip(),
                            "nivel_atual":    n_niv.strip(),
                            "link_documento": n_lk.strip(),
                            "tipo_atividade": n_tativ.strip(),
                            "revisado_gestor":n_rev.strip(),
                            "observacoes":    n_obs.strip(),
                        })
                        st.success(f"✅ '{n_pr}' cadastrado com sucesso!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# ════════════ ABA 3 — GERENCIAR (admin) ═══════════════════════════════════════
if _admin:
    with tabs[2]:
        st.markdown("""
        <div class="admin-header">
            <span style="font-size:1.4rem;"></span>
            <div><div class="admin-title">Gerenciar Processos</div>
            <div class="admin-sub">Edite campos ou remova processos existentes.</div></div>
        </div>""", unsafe_allow_html=True)

        if df_raw.empty:
            st.info("Nenhum processo cadastrado.")
        else:
            opcoes_g = {
                f"[{str(r.get('sigla','—'))}]  {str(r.get('processo',''))}  —  {str(r.get('status',''))}": r
                for _, r in df_raw.iterrows()
            }
            sel_g = st.selectbox("Selecione o processo:", list(opcoes_g.keys()))
            re_   = opcoes_g[sel_g]
            st.markdown('<hr class="gold-line">', unsafe_allow_html=True)

            def v(f): return str(re_.get(f, "") or "")
            def si(opts, f):
                val = v(f)
                return opts.index(val) if val in opts else 0

            with st.form("form_edit"):
                st.markdown(f"**Editando:** `{v('processo')}`")
                c1, c2 = st.columns(2)
                with c1:
                    e_td   = st.text_input("Tipo de Documento",    value=v("tipo_documento"))
                    e_obj  = st.text_input("Objetivo Estratégico", value=v("objetivo"))
                    e_mac  = st.text_input("Macroprocesso",         value=v("macroprocesso"))
                    e_cod  = st.text_input("Código do Macro",       value=v("codigo"))
                    e_pr   = st.text_input("Processo",              value=v("processo"))
                    e_cp   = st.text_input("Código do Processo",    value=v("codigo_1"))
                    e_tativ = st.text_input("Tipo de Atividade",    value=v("tipo_atividade"))
                with c2:
                    e_sig  = st.text_input("Sigla",           value=v("sigla"))
                    e_sig1 = st.text_input("Sigla_1",         value=v("sigla_1"))
                    e_cod2 = st.text_input("Código_2",        value=v("codigo_2"))
                    e_st   = st.selectbox("Status",           STATUS_OPTS,      index=si(STATUS_OPTS,      "status"))
                    e_cr   = st.selectbox("Criticidade",      CRITICIDADE_OPTS, index=si(CRITICIDADE_OPTS, "criticidade"))
                    e_tc   = st.text_input("Tipo de Critério",value=v("tipo_criterio"))
                    e_ur   = st.text_input("Última Revisão",  value=v("ultima_revisao"))
                    e_niv  = st.text_input("Nível Atual",     value=v("nivel_atual"))
                e_lk  = st.text_input("Link do PDF", value=v("link_documento"))
                e_rev = st.text_input("Revisado pelo Gestor", value=v("revisado_gestor"))
                e_obs = st.text_area("Observações", value=v("observacoes"), height=80)

                cs, cd = st.columns([3, 1])
                with cs: save   = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with cd: delete = st.form_submit_button("🗑️ Excluir",           use_container_width=True)

            if save:
                try:
                    atualizar_processo(int(re_["id"]), {
                        "tipo_documento": e_td.strip(),  "objetivo":       e_obj.strip(),
                        "macroprocesso":  e_mac.strip(), "codigo":         e_cod.strip(),
                        "processo":       e_pr.strip(),  "codigo_1":       e_cp.strip(),
                        "sigla":          e_sig.strip(), "sigla_1":        e_sig1.strip(),
                        "codigo_2":       e_cod2.strip(),"status":         e_st,
                        "criticidade":    e_cr,          "tipo_criterio":  e_tc.strip(),
                        "ultima_revisao": e_ur.strip(),  "nivel_atual":    e_niv.strip(),
                        "link_documento": e_lk.strip(),  "tipo_atividade": e_tativ.strip(),
                        "revisado_gestor":e_rev.strip(), "observacoes":    e_obs.strip(),
                    })
                    st.success("✅ Atualizado com sucesso!")
                    st.cache_data.clear(); st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

            if delete:
                try:
                    deletar_processo(int(re_["id"]))
                    st.success("Processo removido.")
                    st.cache_data.clear(); st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
                    

# ════════════ ABA 4 — AUDITORIA (COM KPIs E GRÁFICOS DO HTML) ═══════════════
with tabs[audit_tab_index]:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    :root{
      --verde:#2E9E37;--verde-esc:#1E7A2A;--verde-tinta:#12331C;--amarelo:#F2C300;
      --exc:#1E7A2A;--bom:#5FB65B;--aten:#E8B23A;--risco:#E67E22;--crit:#D64545;
      --papel:#F4F7F3;--branco:#FFFFFF;--borda:#DDE6DC;--texto:#2A3A2E;--suave:#728177;
      --sombra:0 1px 2px rgba(18,51,28,.06),0 4px 16px rgba(18,51,28,.05);
      --disp:'Barlow Semi Condensed',system-ui,sans-serif;--corpo:'Inter',system-ui,sans-serif;
    }
    .aud-card{background:var(--branco);border:1px solid var(--borda);border-radius:12px;padding:18px;box-shadow:var(--sombra);margin-bottom:14px}
    .aud-card h3{font-family:var(--disp);font-size:16px;font-weight:600;color:var(--texto);letter-spacing:.3px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between}
    .aud-kpi .rot{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--suave);font-weight:600}
    .aud-kpi .num{font-family:var(--disp);font-size:40px;font-weight:700;line-height:1;margin:8px 0 2px;color:var(--verde-tinta)}
    .aud-kpi .pe{font-size:12px;color:var(--suave);margin-bottom:2px}
    .aud-kpi .faixa{height:4px;border-radius:3px;margin-top:12px;background:var(--papel);overflow:hidden}
    .aud-kpi .faixa i{display:block;height:100%}
    .aud-selo{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.3px;color:#fff}
    .aud-barra{display:flex;align-items:center;gap:10px;padding:6px 0}
    .aud-barra .nome{min-width:130px;max-width:46%;font-size:12.5px;font-weight:500;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .aud-barra .trilho{flex:1;height:22px;background:var(--papel);border-radius:5px;overflow:hidden;position:relative}
    .aud-barra .trilho i{display:block;height:100%;border-radius:5px;transition:width .6s cubic-bezier(.2,.7,.2,1)}
    .aud-barra .val{width:52px;text-align:right;font-family:var(--disp);font-weight:700;font-size:15px}
    .aud-heat table{width:100%;border-collapse:collapse;font-size:13px}
    .aud-heat th{text-align:left;font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--suave);font-weight:600;padding:9px 10px;border-bottom:1px solid var(--borda)}
    .aud-heat td{padding:10px;border-bottom:1px solid #eef3ee;vertical-align:middle}
    .aud-heat tr:hover td{background:#fafcf9}
    .aud-cel{width:74px;height:38px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;color:#fff;border-radius:5px;margin:2px}
    .aud-degrau{display:flex;align-items:center;gap:14px;padding:12px 16px;border-radius:10px;border:1px solid var(--borda);background:#fff;position:relative;margin-bottom:6px}
    .aud-degrau.atual{box-shadow:0 0 0 2px var(--verde);border-color:var(--verde)}
    .aud-degrau .nn{font-family:var(--disp);font-weight:700;font-size:30px;width:40px;text-align:center;line-height:1}
    .aud-degrau .info b{font-size:14px}
    .aud-degrau .info .fx{font-size:11px;color:var(--suave)}
    .aud-degrau .info p{font-size:12px;color:var(--texto);margin-top:2px}
    .aud-degrau .tag-atual{position:absolute;right:14px;top:14px;font-size:11px;font-weight:700;color:var(--verde-esc);background:#eafaec;padding:3px 10px;border-radius:20px}
    .aud-aviso{background:#fff8e6;border:1px solid #f0dca0;border-left:4px solid var(--amarelo);border-radius:8px;padding:11px 14px;font-size:13px;margin:12px 0;display:flex;gap:10px}
    .aud-aviso.grave{background:#fdeeee;border-color:#eebcbc;border-left-color:var(--crit)}
    .aud-aviso.ok{background:#effaf0;border-color:#bfe6c2;border-left-color:var(--exc)}
    .aud-anel{position:relative;width:96px;height:96px;flex-shrink:0}
    .aud-anel .txt{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
    .aud-anel .txt b{font-family:var(--disp);font-size:26px;font-weight:700;line-height:1;color:var(--verde-tinta)}
    .aud-anel .txt small{font-size:9px;letter-spacing:.5px;text-transform:uppercase;color:var(--suave)}
    .aud-tema{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #eef3ee}
    .aud-tema .tt{flex:1}
    .aud-tema .tt b{font-size:13.5px}
    .aud-tema .tt .lj{font-size:11.5px;color:var(--suave);margin-top:2px}
    .aud-tema .cnt{font-family:var(--disp);font-weight:700;font-size:26px;line-height:1;width:44px;text-align:center}
    .aud-tema .cnt small{display:block;font-size:9px;letter-spacing:.5px;color:var(--suave);text-transform:uppercase;font-weight:600}
    .aud-insight{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #eef3ee;font-size:13.5px}
    .aud-insight .mk{font-size:18px;flex-shrink:0;line-height:1.2}
    .aud-cod{font-family:var(--disp);font-weight:700;color:var(--verde-esc);font-size:15px}

    /* ── Cabeçalho de seção (padrão .cab do HTML de referência) ── */
    .aud-cab{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:10px;
        padding-bottom:12px;border-bottom:1px solid var(--borda)}
    .aud-cab h1{font-family:var(--disp);font-weight:700;font-size:26px;color:var(--texto);line-height:1.15;letter-spacing:.2px;margin:0}
    .aud-cab h1 .ic{margin-right:8px}
    .aud-cab .desc{color:var(--suave);font-size:13px;margin-top:6px;max-width:660px}

    /* ── Tag genérica (chip de contexto) ── */
    .aud-tag{display:inline-block;padding:1px 8px;border-radius:5px;font-size:11px;font-weight:600;
        border:1px solid var(--borda);background:var(--papel);color:var(--suave)}

    /* ── Vínculo com POP ── */
    .pop-vinculo{font-size:12px;color:var(--verde-esc);background:rgba(46,158,55,.10);
        border:1px solid rgba(46,158,55,.30);border-radius:6px;padding:3px 9px;display:inline-block;font-weight:600}
    .pop-vinculo.faltando{background:rgba(214,69,69,.12);border-color:rgba(214,69,69,.40);color:var(--crit)}

    /* ── Análise por loja — paridade visual com o HTML de referência v2 ── */
    .aud-v2-card{background:var(--branco);border:1px solid var(--borda);border-radius:12px;
        padding:18px;box-shadow:var(--sombra);margin-bottom:14px}
    .aud-v2-card h3{font-family:var(--disp);font-size:16px;font-weight:600;color:var(--texto);
        letter-spacing:.3px;margin:0 0 14px;display:flex;align-items:center;justify-content:space-between;
        gap:10px;flex-wrap:wrap}
    .aud-v2-card h3 .leve{font-size:11.5px;color:var(--suave);font-weight:500;font-family:var(--corpo);letter-spacing:0}
    .aud-v2-topo{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding-bottom:16px;
        border-bottom:1px solid var(--borda);margin-bottom:18px}
    .aud-v2-anel{position:relative;width:104px;height:104px;flex-shrink:0}
    .aud-v2-anel .txt{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
    .aud-v2-anel .txt b{font-family:var(--disp);font-size:28px;font-weight:700;line-height:1;color:var(--texto)}
    .aud-v2-anel .txt small{font-size:9px;color:var(--suave)}
    .aud-v2-titulo{font-family:var(--disp);font-size:24px;font-weight:700;color:var(--texto);line-height:1.1}
    .aud-v2-cod{font-family:var(--disp);font-weight:700;color:var(--verde-esc);font-size:21px}
    .aud-v2-muted{color:var(--suave);font-size:13px;margin-top:3px}
    .aud-v2-score{font-family:var(--disp);font-weight:700;font-size:16px}
    .aud-v2-frentes{min-width:210px;text-align:right}
    .aud-v2-frentes-label{font-size:11.5px;color:var(--suave);font-weight:600;margin-bottom:6px}
    .aud-v2-selo{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;
        letter-spacing:.3px;color:#fff;white-space:nowrap}
    .aud-v2-blocos{display:grid;gap:10px}
    .aud-v2-barra{display:flex;align-items:center;gap:10px;padding:6px 0}
    .aud-v2-barra .nome{width:158px;font-size:12.5px;font-weight:500;flex-shrink:0;white-space:nowrap;
        overflow:hidden;text-overflow:ellipsis}
    .aud-v2-trilho{flex:1;height:22px;background:var(--papel);border-radius:5px;position:relative}
    .aud-v2-trilho .preenche{display:block;height:100%;border-radius:5px}
    .aud-v2-trilho .marcador{position:absolute;top:-4px;width:2px;height:30px;background:#5b6a5e;border-radius:2px}
    .aud-v2-trilho .marcador::after{content:'';position:absolute;top:-4px;left:-3px;width:8px;height:8px;border-radius:50%;background:#5b6a5e}
    .aud-v2-barra .val{width:56px;text-align:right;font-family:var(--disp);font-weight:700;font-size:15px}
    .aud-v2-legenda{display:flex;gap:14px;flex-wrap:wrap;font-size:11.5px;color:var(--suave);margin-top:14px}
    .aud-v2-legenda i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:middle}
    .aud-v2-aviso{background:#fff8e6;border:1px solid #f0dca0;border-left:4px solid var(--amarelo);
        border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:12px;display:flex;gap:10px}
    .aud-v2-aviso.grave{background:#fdeeee;border-color:#eebcbc;border-left-color:var(--crit)}
    .aud-v2-aviso.bom{background:#effaf0;border-color:#bfe6c2;border-left-color:var(--exc)}
    .aud-v2-aviso .mk{font-size:18px;flex-shrink:0;line-height:1.2}
    .aud-v2-table-wrap{overflow-x:auto}
    .aud-v2-table{width:100%;border-collapse:collapse;font-size:13px}
    .aud-v2-table th{text-align:left;font-size:11px;color:var(--suave);font-weight:600;padding:6px 8px;
        border-bottom:1px solid var(--borda)}
    .aud-v2-table td{padding:6px 8px;border-bottom:1px solid var(--borda);vertical-align:top}
    .aud-v2-table td:nth-child(2)>div{display:block;max-width:100%;white-space:nowrap;overflow:hidden;
        text-overflow:ellipsis;line-height:1.35;margin-top:3px}
    .aud-v2-table tr:hover td{background:#f7fbf7}
    .aud-v2-tag{display:inline-block;padding:1px 8px;border-radius:5px;font-size:11px;font-weight:600;
        border:1px solid var(--borda);background:var(--papel);color:var(--suave);white-space:nowrap}
    .aud-v2-status{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;color:#fff;white-space:nowrap}
    .aud-v2-empty{text-align:center;padding:26px 20px;color:var(--suave);font-size:13px}
    .aud-v2-evolucao{margin-top:16px}
    .aud-v2-evolucao svg{width:100%;height:auto;display:block}
    .aud-v2-evolucao-legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:6px}
    .aud-v2-evolucao-legend span{font-size:12px;margin-right:14px}
    .aud-v2-detalhe{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #eef3ee}
    /* ── Não conformidades — cartões do HTML de referência v2 ── */
    .aud-nc-card{background:var(--branco);border:1px solid var(--borda);border-radius:10px;
        padding:14px;margin-bottom:10px;box-shadow:var(--sombra)}
    .aud-nc-topo{display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap;margin-bottom:8px}
    .aud-nc-ref{font-family:var(--disp);font-weight:700;font-size:17px;color:var(--verde-esc);letter-spacing:.3px}
    .aud-nc-pop{font-size:12px;color:var(--verde-esc);background:#effaf0;border:1px solid #bfe6c2;
        border-radius:6px;padding:3px 9px;display:inline-block}
    .aud-nc-pop.faltando{background:#fdeeee;border-color:#eebcbc;color:var(--crit)}
    .aud-nc-corpo{font-size:13px}
    .aud-nc-linha{display:flex;gap:6px;margin-top:5px;font-size:12.5px;line-height:1.35}
    .aud-nc-linha b{color:var(--texto);font-weight:600;flex-shrink:0}
    .aud-nc-rodape{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:11px;
        padding-top:10px;border-top:1px dashed var(--borda)}
    .aud-nc-filtros{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
    .aud-nc-filtros .aud-nc-contagem{font-size:12.5px;color:var(--suave);margin-left:2px}
    @media (max-width: 900px){.aud-nc-filtros{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media (max-width: 760px){
        .aud-v2-frentes{width:100%;text-align:left}
        .aud-v2-barra .nome{width:116px}
    }
    </style>
    """, unsafe_allow_html=True)

    def cab_html(titulo: str, desc: str = "", icone: str = "") -> str:
        """Cabeçalho de seção padronizado (replica o bloco .cab do HTML de
        referência) — usar no topo de cada sub-aba de Auditoria no lugar de
        st.markdown("### ...") + st.caption(...) soltos."""
        ic = f'<span class="ic">{icone}</span>' if icone else ''
        desc_html = f'<div class="desc">{desc}</div>' if desc else ''
        return (
            f'<div class="aud-cab"><div><h1>{ic}{titulo}</h1>{desc_html}</div></div>'
        )

    def data_br(valor) -> str:
        """Converte uma data/timestamp ISO ('AAAA-MM-DD' ou com hora) para DD/MM/AAAA.
        Usado em toda exportação/exibição de data na aba Auditoria — o público é
        brasileiro, então nenhuma data crua em formato americano deve chegar à tela."""
        s = str(valor or '').strip()
        if not s or s.lower() == 'none':
            return ''
        s = s[:10]  # descarta hora/timezone se vier junto ('AAAA-MM-DDTHH:MM:SS')
        partes = s.split('-')
        if len(partes) == 3 and len(partes[0]) == 4:
            ano, mes, dia = partes
            return f"{dia}/{mes}/{ano}"
        return s

    def df_para_csv_br(df: pd.DataFrame, colunas_data: list = None) -> bytes:
        """Gera CSV pronto para abrir no Excel brasileiro: separador ';', datas em
        DD/MM/AAAA e BOM UTF-8 (sem o BOM o Excel do Windows lê acentos como lixo,
        ex.: 'não' vira 'nÃ£o')."""
        df = df.copy()
        for col in (colunas_data or []):
            if col in df.columns:
                df[col] = df[col].apply(data_br)
        return df.to_csv(index=False, sep=';').encode('utf-8-sig')

    # ── Configurações ──
    LOJAS = [
        ['01','Irmã Dulce'], ['02','Lourival Parente'], ['03','Porto Alegre'],
        ['04','Água Mineral'], ['06','Renascença'], ['07','Parque Piauí'],
        ['08','São Joaquim'], ['09','Mocambinho'], ['10','Morada do Sol'],
        ['11','Dirceu'], ['12','Centro'], ['14','Água Branca'],
        ['16','Empório Leste'], ['17','Cristo Rei'], ['18','Empório M.C'],
        ['19','Guadalupe'], ['22','Noé Mendes'], ['23','Kennedy'],
        ['24','Demerval Lobão'], ['25','José de Freitas'], ['26','Pio IX']
    ]
    
    CHECKLISTS = {
        'AÇO-AUD-01': {'nome': 'Açougue', 'cor': '#B0442E', 'slots': [
            'Aderência ao processo', 'Maturidade operacional', 
            'Conhecimento e disseminação', 'Eficiência / performance', 'Estrutura / gaps'
        ]},
        'FRE-AUD-02': {'nome': 'Frente de Loja', 'cor': '#2E6BB0', 'slots': [
            'Aderência ao processo', 'Maturidade operacional', 
            'Conhecimento e disseminação', 'Eficiência / performance', 'Gaps e processos não mapeados'
        ]},
        'REC-AUD-03': {'nome': 'Recebimento', 'cor': '#7A4EB0', 'slots': [
            'Aderência ao processo', 'Maturidade operacional', 
            'Conhecimento e disseminação', 'Eficiência / performance', 'Gaps e processos não mapeados'
        ]},
        'ATA-AUD-04': {'nome': 'Atacado', 'cor': '#C08A1E', 'slots': [
            'Aderência ao processo', 'Maturidade operacional',
            'Conhecimento e disseminação', 'Eficiência / performance', 'Gaps e processos não mapeados'
        ]}
    }
    
    POSSIVEL = [35, 20, 15, 15, 15]
    SLOTS_CURTOS = ['Aderência', 'Maturidade', 'Conhecimento', 'Eficiência', 'Gaps/Estrut.']
    LETRAS_BLOCO = ['A', 'B', 'C', 'D', 'E']

    def _codigo_frente_flexivel(nome: str) -> str:
        """Gera um identificador estável para uma frente/setor novo."""
        import unicodedata
        base = unicodedata.normalize('NFKD', str(nome or ''))
        base = base.encode('ascii', 'ignore').decode().upper()
        slug = re.sub(r'[^A-Z0-9]+', '-', base).strip('-') or 'SEM-NOME'
        return f'EXT-AUD-{slug[:48].rstrip("-")}'

    def _registrar_checklist_flexivel(nome: str, codigo: str = None, slots: list = None) -> str:
        """Registra uma frente nova só na Auditoria, sem alterar Processos."""
        nome_limpo = re.sub(r'\s+', ' ', str(nome or '')).strip()
        codigo = codigo or _codigo_frente_flexivel(nome_limpo)
        nomes_slots = [
            str(slot).strip() if str(slot or '').strip() else SLOTS_CURTOS[i]
            for i, slot in enumerate((slots or [])[:5])
        ]
        nomes_slots += SLOTS_CURTOS[len(nomes_slots):]
        CHECKLISTS.setdefault(codigo, {
            'nome': nome_limpo or codigo,
            'cor': '#728177',
            'slots': nomes_slots[:5],
        })
        return codigo
    
    # Régua oficial da Auditoria — deve permanecer idêntica à do HTML v2.
    # A nota dos itens do checklist é outra régua: itens com nível <= 3 são
    # pontos críticos elegíveis para NC. Não misturar as duas regras.
    FAIXAS_AUDITORIA = [
        {'min': 90, 'rot': 'Referência',         'risco': 'Mínimo',  'prio': 'Expansão — disseminar o modelo para outras unidades', 'hex': '#1E7A2A'},
        {'min': 76, 'rot': 'Avançado',           'risco': 'Mínimo',  'prio': 'Excelência — benchmark interno e mentoria',            'hex': '#5FB65B'},
        {'min': 61, 'rot': 'Adequado',           'risco': 'Baixo',   'prio': 'Melhoria contínua — revisão mensal dos gaps',          'hex': '#E8B23A'},
        {'min': 41, 'rot': 'Em Desenvolvimento', 'risco': 'Médio',   'prio': 'Prioritária — plano de ação em 60 dias',               'hex': '#E67E22'},
        {'min': 21, 'rot': 'Insuficiente',       'risco': 'Alto',    'prio': 'Urgente — plano estrutural em até 30 dias',            'hex': '#D64545'},
        {'min': 0,  'rot': 'Crítico',            'risco': 'Crítico', 'prio': 'Imediata — intervenção emergencial',                   'hex': '#8E2020'},
    ]

    def faixa(nota):
        try:
            valor = float(nota)
        except (TypeError, ValueError):
            valor = 0.0
        for item in FAIXAS_AUDITORIA:
            if valor >= item['min']:
                return {'rot': item['rot'], 'cor': item['hex'], 'hex': item['hex'],
                        'risco': item['risco'], 'prio': item['prio'], 'min': item['min']}
        item = FAIXAS_AUDITORIA[-1]
        return {'rot': item['rot'], 'cor': item['hex'], 'hex': item['hex'],
                'risco': item['risco'], 'prio': item['prio'], 'min': item['min']}

    def faixa_intervalo(indice: int) -> str:
        item = FAIXAS_AUDITORIA[indice]
        limite_superior = 100 if indice == 0 else FAIXAS_AUDITORIA[indice - 1]['min'] - 1
        return f"{item['min']}–{limite_superior}"

    def legenda_faixa_html() -> str:
        """Legenda da régua de classificação (mesmos cortes de faixa()), para repetir em toda aba que exiba a cor/rótulo de uma nota."""
        html = '<div style="display:flex;gap:20px;flex-wrap:wrap;font-size:0.85rem;color:#728177;margin-top:16px;padding-top:12px;border-top:1px solid #EEF3EE;">'
        for indice, item in enumerate(FAIXAS_AUDITORIA):
            fx = faixa(item['min'])
            html += (
                '<span style="display:flex;align-items:center;gap:6px;">'
                f'<span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:{fx["cor"]};"></span>'
                f'{fx["rot"]} ({faixa_intervalo(indice)})</span>'
            )
        html += '</div>'
        return html

    def nivel_maturidade(nota):
        if nota >= 90: return 5
        if nota >= 80: return 4
        if nota >= 70: return 3
        if nota >= 60: return 2
        return 1
    
    NIVEIS = {
        1: {'rot': 'Inicial', 'fx': '< 60', 'hex': '#D64545', 'desc': 'Práticas ausentes ou informais.'},
        2: {'rot': 'Em estruturação', 'fx': '60–69', 'hex': '#E67E22', 'desc': 'Iniciativas isoladas.'},
        3: {'rot': 'Padronizado', 'fx': '70–79', 'hex': '#E8B23A', 'desc': 'Processo implementado, com desvios.'},
        4: {'rot': 'Gerenciado', 'fx': '80–89', 'hex': '#5FB65B', 'desc': 'Execução consistente.'},
        5: {'rot': 'Excelência', 'fx': '90–100', 'hex': '#1E7A2A', 'desc': 'Monitorado e em evolução.'}
    }
    
    # ── PONTO DO POP CITADO NO ITEM DO CHECKLIST ──
    # O POP em si é um só por checklist (ver FRENTE_POP_BASE em db.py) — o que varia
    # de item para item é o ponto interno avaliado. Os padrões abaixo extraem esse
    # ponto do enunciado ("ANEXO 113", "Seção VII", "p.14-15", "etapa 1 do POP").
    PADROES_PONTO_POP = [
        re.compile(r'ANEXO\s+[IVXLC]+\b|ANEXO\s+\d+', re.IGNORECASE),
        re.compile(r'Se[çc][ãa]o\s+[IVXLC]+\b', re.IGNORECASE),
        re.compile(r'etapas?\s+\d+(?:\s*[-–a]\s*\d+)?\s+do\s+POP', re.IGNORECASE),
        re.compile(r'POP\s+(?:de\s+|do\s+|da\s+)?[A-ZÀ-Ú][\wÀ-ú]*(?:\s+[a-zà-úA-ZÀ-Ú][\wÀ-ú]*){0,2}'),
        re.compile(r'\bp\.\s*\d+(?:\s*-\s*\d+)?', re.IGNORECASE),
    ]

    def detectar_pontos_pop(texto: str) -> list:
        """Trechos do item que apontam o ponto do POP, na ordem em que aparecem."""
        achados, vistos = [], set()
        for padrao in PADROES_PONTO_POP:
            for m in padrao.finditer(texto or ''):
                trecho = re.sub(r'\s+', ' ', m.group()).strip()
                chave = trecho.lower()
                if trecho and chave not in vistos:
                    vistos.add(chave)
                    achados.append(trecho)
        return achados

    def _baixar_pdf_pop(link_documento: str) -> bytes:
        """Obtém o PDF do POP por arquivo local, URL direta ou Google Drive.

        O importador nunca trata o nome do arquivo como se fosse conteúdo lido:
        quando o PDF não pode ser baixado, devolvemos bytes vazios para a UI
        bloquear o salvamento e pedir a correção do vínculo no cadastro do POP.
        """
        link = str(link_documento or '').strip()
        if not link:
            return b''
        if os.path.isfile(link):
            try:
                with open(link, 'rb') as arquivo:
                    return arquivo.read()
            except OSError:
                return b''

        urls = []
        file_id = None
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', link) or re.search(r'[?&]id=([a-zA-Z0-9_-]+)', link)
        if match:
            file_id = match.group(1)
            urls.append(f'https://drive.google.com/uc?export=download&id={file_id}')
        if re.match(r'^https?://', link, re.IGNORECASE):
            urls.append(link)
        if not urls:
            return b''

        try:
            sessao = requests.Session()
            cabecalho = {'User-Agent': 'Mozilla/5.0'}
            for url in urls:
                resposta = sessao.get(url, headers=cabecalho, timeout=30)
                if not resposta.ok:
                    continue
                conteudo = resposta.content
                if conteudo.startswith(b'%PDF'):
                    return conteudo

                # Arquivos grandes do Drive podem exigir uma confirmação em HTML.
                confirm = re.search(r'name="confirm" value="([^"]+)"', resposta.text or '')
                if not confirm:
                    confirm = re.search(r'[?&]confirm=([0-9A-Za-z_-]+)', resposta.text or '')
                if confirm and file_id:
                    url_confirmado = f'https://drive.google.com/uc?export=download&confirm={confirm.group(1)}&id={file_id}'
                    resposta_confirmada = sessao.get(url_confirmado, headers=cabecalho, timeout=30)
                    if resposta_confirmada.ok and resposta_confirmada.content.startswith(b'%PDF'):
                        return resposta_confirmada.content
        except requests.RequestException:
            return b''
        return b''

    @st.cache_data(ttl=3600, show_spinner=False)
    def _texto_pop_por_pagina(link_documento: str) -> list:
        """Baixa o PDF do POP e devolve o texto extraído de cada página."""
        conteudo = _baixar_pdf_pop(link_documento)
        if not conteudo:
            return []
        try:
            with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
                return [page.extract_text() or '' for page in pdf.pages]
        except Exception:
            return []

    # Títulos de seção dos POPs vêm em numeração romana e caixa alta
    # ("IV. PROCEDIMENTO", "VII. TABELA DE REFERÊNCIA"), o que permite citar o
    # ponto do POP como o auditor cita: seção + página, não só a página.
    PADRAO_SECAO_POP = re.compile(r'\b([IVXLC]{1,5})\.\s+([A-ZÀ-Ú][A-ZÀ-Ú\s/,\-()]{4,55})')

    # Seções que descrevem o documento, não a regra a cumprir: citar uma delas
    # como ponto divergente não ajuda o gestor a corrigir nada.
    SECOES_POP_IGNORADAS = ('dicion', 'objetivo', 'controle de altera', 'perguntas frequentes', 'faq')

    def _secao_da_pagina(texto_pagina: str) -> str:
        """Último título de seção normativa declarado na página ('IV. PROCEDIMENTO')."""
        for romano, titulo in reversed(PADRAO_SECAO_POP.findall(texto_pagina or '')):
            titulo = re.sub(r'\s+', ' ', titulo).strip()
            # O título vem grudado no começo da tabela seguinte; corta no
            # primeiro rótulo de coluna para não arrastar o cabeçalho inteiro.
            titulo = re.split(r'\s+(?:TIPO|TERMO|ATEN[ÇC][ÃA]O|SITUA[ÇC]|P$)', titulo)[0].strip()
            palavras = titulo.split()
            if len(palavras) > 6:
                titulo = ' '.join(palavras[:6])
            if not titulo:
                continue
            if any(t in titulo.lower() for t in SECOES_POP_IGNORADAS):
                continue
            return f'Seção {romano}. {titulo}'
        return ''

    def sugerir_ponto_pop_por_contexto(texto_item: str, link_documento: str) -> str:
        """Localiza evidência literal no POP para orientar a não conformidade."""
        paginas = _texto_pop_por_pagina(link_documento)
        if not paginas:
            return ''
        evidencia = _trecho_literal_no_pop(texto_item, paginas)
        pagina = evidencia.get('pagina') or 0
        return _localizacao_pop(paginas, pagina) if pagina else ''

    def _normalizar_texto_pop(texto: str) -> str:
        import unicodedata
        base = unicodedata.normalize('NFD', str(texto or ''))
        return re.sub(r'[^a-z0-9]+', ' ', base.encode('ascii', 'ignore').decode().lower()).strip()

    def _localizacao_pop(paginas: list, numero_pagina: int) -> str:
        if not numero_pagina or not paginas:
            return ''
        secao = ''
        for i in range(numero_pagina - 1, -1, -1):
            secao = _secao_da_pagina(paginas[i])
            if secao:
                break
        return f'{secao} (p.{numero_pagina})' if secao else f'p.{numero_pagina}'

    _TERMOS_GENERICOS_POP = {
        'a', 'ao', 'aos', 'as', 'com', 'como', 'da', 'das', 'de', 'do', 'dos',
        'e', 'em', 'entre', 'essa', 'esse', 'esta', 'este', 'foi', 'ha', 'na',
        'nas', 'no', 'nos', 'num', 'numa', 'o', 'os', 'ou', 'para', 'pela',
        'pelas', 'pelo', 'pelos', 'por', 'que', 'se', 'sem', 'ser', 'sua',
        'suas', 'seu', 'seus', 'tem', 'um', 'uma', 'umas', 'uns',
    }

    def _trecho_literal_no_pop(descricao: str, paginas: list) -> dict:
        """Retorna somente evidência textual contínua existente no PDF.

        Não há busca fuzzy, similaridade ou aproximação por palavras isoladas.
        O trecho precisa aparecer na mesma ordem e de forma contínua no texto
        extraído do POP; caso contrário, o item permanece para revisão manual.
        """
        tokens_item = _normalizar_texto_pop(descricao).split()
        textos_norm = [_normalizar_texto_pop(pagina) for pagina in paginas]
        textos_com_delimitadores = [f' {texto} ' for texto in textos_norm]

        # Primeiro prioriza a pergunta completa, que é a evidência mais forte.
        pergunta_norm = ' '.join(tokens_item)
        if pergunta_norm and len(pergunta_norm) >= 24:
            for numero, texto in enumerate(textos_com_delimitadores, start=1):
                if f' {pergunta_norm} ' in texto:
                    return {
                        'status': 'Pergunta inteira encontrada no POP',
                        'confianca': 'Alta', 'pontuacao': 100,
                        'pagina': numero, 'evidencia': pergunta_norm,
                    }

        referencias = detectar_pontos_pop(descricao)
        referencias_encontradas = []
        for referencia in referencias:
            ref_norm = _normalizar_texto_pop(referencia)
            if len(ref_norm.split()) < 2:
                continue
            for numero, texto in enumerate(textos_com_delimitadores, start=1):
                if f' {ref_norm} ' in texto:
                    referencias_encontradas.append(referencia)
                    return {
                        'status': 'Referência exata encontrada no POP',
                        'confianca': 'Alta', 'pontuacao': 100,
                        'pagina': numero, 'evidencia': referencia,
                        'referencias_encontradas': referencias_encontradas,
                    }

        # Checklist e POP podem usar uma frase operacional idêntica dentro de
        # perguntas maiores. Isso é aceito apenas como trecho literal contínuo,
        # com pelo menos 4 palavras e 3 termos substantivos, nunca por palavras
        # soltas ou por pontuação de similaridade.
        max_tokens = min(12, len(tokens_item))
        for tamanho in range(max_tokens, 3, -1):
            for inicio in range(len(tokens_item) - tamanho + 1):
                trecho = tokens_item[inicio:inicio + tamanho]
                substantivos = [
                    token for token in trecho
                    if len(token) >= 4 and token not in _TERMOS_GENERICOS_POP
                    and not token.isdigit()
                ]
                if len(substantivos) < 3:
                    continue
                trecho_norm = ' '.join(trecho)
                for numero, texto in enumerate(textos_com_delimitadores, start=1):
                    if f' {trecho_norm} ' in texto:
                        return {
                            'status': 'Trecho literal localizado no POP',
                            'confianca': 'Revisão manual', 'pontuacao': 75,
                            'pagina': numero, 'evidencia': trecho_norm,
                            'referencias_encontradas': referencias_encontradas,
                        }

        return {
            'status': 'Sem trecho literal suficiente no POP',
            'confianca': 'Revisão manual', 'pontuacao': 0,
            'pagina': 0, 'evidencia': '',
            'referencias_encontradas': referencias_encontradas,
        }

    def _referencia_associada_ao_checklist(item: dict) -> str:
        """Referencia automática segura quando a pergunta é uma paráfrase.

        O texto não é apresentado como uma etapa inventada do POP. A referência
        deixa explícito que veio do item/bloco do checklist associado ao POP
        escolhido na importação.
        """
        codigo = str(item.get('codigo') or '').strip()
        bloco = codigo.split('.', 1)[0] if codigo else ''
        bloco_por_numero = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E'}
        bloco_letra = bloco_por_numero.get(bloco)
        if bloco_letra in {'B', 'D'}:
            return f'Bloco {bloco_letra} — governança e maturidade do checklist'
        if bloco_letra == 'E':
            return 'Bloco E — gap identificado no checklist'
        return f'Item {codigo or "do checklist"} — critério associado ao POP'

    def confrontar_item_com_pop(item: dict, paginas: list) -> dict:
        """Compara um item do checklist com o texto extraído do POP.

        A correspondência usa somente evidência literal do PDF: pergunta
        inteira, referência explícita ou trecho contínuo da pergunta. Não há
        aproximação semântica, palavras soltas ou inferência de página.
        """
        descricao = str(item.get('descricao') or '')
        if not paginas:
            return {
                'status': 'POP não verificável', 'confianca': 'Não verificado',
                'pontuacao': 0, 'referencia': 'Revisão obrigatória: PDF do POP não foi lido.',
                'pagina': '', 'evidencia': '', 'termos_comuns': [], 'referencias_encontradas': [],
            }

        evidencia = _trecho_literal_no_pop(descricao, paginas)
        pagina = evidencia.get('pagina') or 0
        status = evidencia['status']

        # O checklist é uma avaliação criada manualmente a partir do POP. O
        # vínculo explícito do documento selecionado é, portanto, a associação
        # válida para auditar o item; a busca literal abaixo é evidência
        # complementar, não uma barreira para salvar a auditoria.
        if status == 'Sem trecho literal suficiente no POP':
            status = 'POP associado ao checklist'
            referencia = _referencia_associada_ao_checklist(item)
            evidencia_textual = ''
            confianca = 'Vínculo explícito'
        else:
            referencia = _localizacao_pop(paginas, pagina) if pagina else 'Revisão manual: nenhum trecho literal localizado.'
            evidencia_textual = evidencia.get('evidencia', '')
            confianca = evidencia['confianca']

        return {
            'status': status,
            'confianca': confianca,
            'pontuacao': evidencia['pontuacao'],
            'referencia': referencia,
            'pagina': pagina,
            'evidencia': evidencia_textual,
            'termos_comuns': [],
            'referencias_encontradas': evidencia.get('referencias_encontradas', []),
        }

    def _pops_com_pdf(df_processos: pd.DataFrame) -> list:
        """Lista POPs cadastrados com vínculo de arquivo/URL para a importação."""
        if df_processos is None or df_processos.empty:
            return []
        resultado = []
        vistos = set()
        for _, row in df_processos.iterrows():
            link = str(row.get('link_documento') or '').strip()
            nome = str(row.get('processo') or '').strip()
            codigo = str(row.get('codigo_2') or '').strip()
            link_utilizavel = bool(re.match(r'^https?://', link, re.IGNORECASE) or os.path.isfile(link))
            if not link or not nome or not link_utilizavel:
                continue
            chave = (str(row.get('id') or ''), codigo, nome, link)
            if chave in vistos:
                continue
            vistos.add(chave)
            resultado.append({
                'id': row.get('id'), 'codigo': codigo, 'nome': nome,
                'link': link, 'rotulo': f'{codigo} — {nome}' if codigo else nome,
            })
        return resultado

    # ══════════════════════════════════════════════════════════════════════
    # AUDITORIA AUTOMÁTICA — preenche a NC inteira por regra, sem digitação
    # ══════════════════════════════════════════════════════════════════════
    # Responsável NÃO é derivado por regra: quem resolve cada NC depende da
    # loja específica e de quem trabalha nela (definido pelo assistente de
    # processos que preenche o checklist), não do bloco ou do tema do item.
    # O mesmo vale para o prazo. Ambos ficam em branco para preenchimento
    # manual na conferência.

    # Ação corretiva por tipo de achado. A primeira entrada cujo termo aparecer
    # no enunciado define a ação, então a ordem importa: o que identifica o
    # objeto da exigência ("POP afixado", "quadro de metas") vem antes do que
    # identifica só o cenário ("câmara", "piso"), senão uma frase sobre afixar
    # POPs na câmara viraria manutenção de equipamento.
    ACOES_POR_TEMA = [
        (('pop', 'anexo', 'procediment', 'plastificad'),
         'Imprimir, plastificar e afixar os POPs e anexos vigentes nos pontos de uso.'),
        (('quadro', 'painel', 'painéi', 'painei', 'gestão à vista', 'gestao a vista', 'metas'),
         'Instalar e manter o quadro de gestão à vista com metas, resultados e anexos do processo.'),
        (('trein', 'recicla', 'capacita', 'integra'),
         'Programar o treinamento/reciclagem com registro de participação e avaliação de eficácia.'),
        (('plano de ação', 'plano de acao', 'tratativa', 'causa raiz', '5 porqu'),
         'Elaborar plano de ação formal com responsável, prazo e status por desvio.'),
        (('indicador', 'kpi', 'monitorad', 'percentual de', '% de'),
         'Definir o indicador, publicar a apuração mensal e acompanhar em reunião de resultados.'),
        (('reuni', 'alinhamento', 'pauta'),
         'Instituir a reunião com periodicidade definida, pauta registrada e lista de presença.'),
        (('conferência cega', 'conferencia cega', 'bipagem', 'coletor', 'canhoto',
          'nota fiscal', 'nf-e', 'pré-conferência', 'pre-conferencia'),
         'Cumprir a rotina do POP na conferência e bloquear o avanço sem a etapa concluída.'),
        (('cancelament', 'devoluç', 'devoluc', 'divergênc', 'divergenc', 'avaria',
          'quebra', 'perda', 'invent'),
         'Apurar as ocorrências por responsável, analisar a causa e tratar os desvios recorrentes.'),
        (('epi', 'higieniz', 'lavat', 'sabonete', 'álcool', 'alcool', 'fardament', 'uniform'),
         'Repor os itens de higiene/EPI e incluir a verificação na rotina diária do setor.'),
        (('praga', 'mofo', 'infiltra', 'dedetiza'),
         'Acionar dedetização/manutenção corretiva e vedar os pontos de entrada identificados.'),
        (('temperatura', 'refrigera', 'frigorif', 'aferid', 'termômetr', 'termometr'),
         'Corrigir o equipamento, registrar a temperatura por turno e tratar desvios na hora.'),
        (('ralo', 'drenagem', 'sifão', 'sifao', 'piso', 'parede', 'teto', 'bancada',
          'ferrugem', 'inox', 'ilha', 'câmara', 'camara', 'conservad', 'danific'),
         'Abrir ordem de manutenção para recuperar a estrutura e incluir no plano preventivo.'),
        (('afixad', 'afixar', 'impress', 'visívei', 'visivei', 'mural', 'cartaz', 'catálogo', 'catalogo'),
         'Imprimir e afixar o material exigido em todos os pontos de uso.'),
        ((), 'Regularizar o item conforme o POP de referência e registrar a evidência da correção.'),
    ]

    # Impacto operacional inferido pelo tema do item (vocabulário do HTML v2).
    IMPACTOS_POR_TEMA = [
        (('praga', 'mofo', 'infiltra', 'epi', 'higieniza', 'temperatura', 'validade',
          'contamina', 'refrigera'), ['Segurança', 'Operacional']),
        (('custo', 'divergência de custo', 'divergencia de custo', 'financeir', 'kpi',
          'indicador', 'perda', 'avaria', 'cancelament', 'invent'), ['Financeiro', 'Operacional']),
        (('atendiment', 'cliente', 'fila', 'caixa'), ['Operacional', 'Cliente']),
        ((), ['Operacional']),
    ]

    def _bloco_do_item(codigo_item: str) -> str:
        """Letra do bloco a partir do código do item ('2.4' -> 'B')."""
        prefixo = str(codigo_item or '').split('.', 1)[0]
        if prefixo.isdigit():
            idx = int(prefixo) - 1
            if 0 <= idx < len(LETRAS_BLOCO):
                return LETRAS_BLOCO[idx]
        return ''

    def _casar_tema(texto: str, tabela):
        """Primeiro valor da tabela cujo termo aparece no texto (última entrada = padrão)."""
        alvo = (texto or '').lower()
        for termos, valor in tabela:
            if not termos:
                return valor
            if any(t in alvo for t in termos):
                return valor
        return None

    def _criticidade_item(item: dict) -> str:
        """Régua do HTML v2: notas 0–2 alta, nota 3 média."""
        nivel = item.get('nivel')
        if nivel is not None:
            if int(nivel) <= 2:
                return 'Alta'
            if int(nivel) <= 3:
                return 'Média'
            return 'Baixa'
        pct = float(item.get('pct') or 0)
        return 'Alta' if pct <= 40 else ('Média' if pct <= 60 else 'Baixa')

    def auditar_item_automaticamente(item: dict, tipo_checklist: str,
                                     data_auditoria, pop_nome: str = '',
                                     pop_link: str = '') -> dict:
        """Monta a não conformidade completa de um item reprovado, sem digitação.

        Deriva criticidade da nota, ação corretiva e impacto do tema do
        enunciado, e o ponto do POP do próprio texto do item (ou do conteúdo
        do POP, por contexto). Responsável e prazo não são atribuídos por
        regra — dependem da loja e de quem trabalha nela, então ficam em
        branco para quem está revisando a auditoria preencher.
        """
        pct = float(item.get('pct') or 0)
        descricao = item.get('descricao') or ''
        codigo = item.get('codigo') or ''

        criticidade = _criticidade_item(item)

        pontos = detectar_pontos_pop(descricao)
        ponto_pop = ' · '.join(pontos[:3])
        if not ponto_pop and pop_link:
            ponto_pop = sugerir_ponto_pop_por_contexto(descricao, pop_link)

        nivel_str = f" | Nível {item['nivel']}: {item['nivel_txt']}" if item.get('nivel') is not None else ''
        obs_str = f" | Obs: {item['observacao']}" if item.get('observacao') else ''

        return {
            'texto': (
                f"{codigo} — {item.get('descricao_curta', descricao)} "
                f"({item.get('obtido', 0):.2f}/{item.get('possivel', 0):.2f} → {pct:.1f}%)"
                f"{nivel_str}{obs_str}"
            ),
            'codigo_item': codigo,
            'ponto_pop': ponto_pop,
            'status': 'Aberta',
            'criticidade': criticidade,
            'responsavel': '',
            'prazo': '',
            'acao_corretiva': _casar_tema(descricao, ACOES_POR_TEMA),
            'evidencia': item.get('observacao') or 'Constatado durante a auditoria de maturidade operacional.',
            'impacto_operacional': _casar_tema(descricao, IMPACTOS_POR_TEMA),
        }

    # ── DADOS REAIS DO SUPABASE ──
    @st.cache_data(ttl=5, show_spinner=False)  # <-- TTL de 5 segundos
    def carregar_dados_exemplo():
        """Carrega auditorias do Supabase"""
        try:
            df = listar_auditorias()
            if df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar auditorias: {e}")
            return pd.DataFrame()

    df_auditorias = carregar_dados_exemplo()

    # Auditorias importadas podem trazer frentes novas. Recria o rótulo a partir
    # do identificador salvo para que filtros, histórico e exportações não fiquem
    # presos às quatro frentes originais.
    if not df_auditorias.empty and 'tipo' in df_auditorias.columns:
        for tipo_salvo in df_auditorias['tipo'].dropna().astype(str).unique():
            if tipo_salvo not in CHECKLISTS and tipo_salvo.startswith('EXT-AUD-'):
                nome_salvo = tipo_salvo.removeprefix('EXT-AUD-').replace('-', ' ').title()
                _registrar_checklist_flexivel(nome_salvo, codigo=tipo_salvo)

    def vencida(nc: dict) -> bool:
        """True se a NC tem prazo definido, ainda não foi concluída e o prazo já passou."""
        from datetime import datetime as _dt
        prazo = (nc.get('prazo') or '').strip()
        if not prazo or nc.get('status') in {'Concluída', 'Cancelada'}:
            return False
        return prazo < _dt.now().strftime('%Y-%m-%d')

    def todas_ncs(df: pd.DataFrame) -> list:
        """Achata as auditorias em uma lista de NCs (uma entrada por crítica),
        cada uma carregando o contexto da auditoria de origem (id, loja, tipo, data)
        para permitir filtros, agregações e edição (via atualizar_auditoria)."""
        ncs = []
        if df.empty or 'criticas' not in df.columns:
            return ncs
        for _, row in df.iterrows():
            criticas = row.get('criticas')
            if not isinstance(criticas, list):
                continue
            for idx, c in enumerate(criticas):
                nc = normalizar_critica(c)
                nc['_auditoria_id'] = row.get('id')
                nc['_idx'] = idx
                nc['_loja'] = row.get('loja')
                nc['_tipo'] = row.get('tipo')
                nc['_data'] = row.get('data')
                ncs.append(nc)
        return ncs

    def _aud_csv_json(valor) -> str:
        import json as _json
        return _json.dumps(valor, ensure_ascii=False, default=str)

    def _aud_csv_num(valor):
        try:
            return float(str(valor).replace(',', '.').replace('%', '').strip())
        except (TypeError, ValueError):
            return ''

    def _aud_csv_faixa(score: float) -> tuple:
        """Classificação e risco na mesma régua usada em todo o dashboard (faixa())."""
        f = faixa(score)
        return f['rot'], f['risco']

    def _aud_csv_item_info(nc: dict) -> tuple:
        """Extrai código, descrição curta e nota sem perder o texto original."""
        texto = _aud_txt(nc.get('texto'))
        codigo = _aud_txt(nc.get('codigo_item')) or '—'
        if codigo == '—':
            encontrado = re.match(r'^\s*([0-9]+(?:\.[0-9]+)+)\s*[—-]\s*(.*)$', texto)
            if encontrado:
                codigo, texto = encontrado.group(1), encontrado.group(2)
        descricao = re.split(r'\s+\([0-9]+[.,][0-9]+/', texto, maxsplit=1)[0].strip()
        if codigo != '—':
            descricao = re.sub(r'^' + re.escape(codigo) + r'\s*[—-]\s*', '', descricao).strip()
        nota_encontrada = re.search(r'(?:→|->|>)\s*([0-9]+[.,]?[0-9]*)\s*%', texto)
        nota = _aud_csv_num(nota_encontrada.group(1)) if nota_encontrada else ''
        bloco_num = codigo.split('.', 1)[0] if codigo[:1].isdigit() else ''
        bloco_idx = int(bloco_num) - 1 if bloco_num.isdigit() else -1
        bloco = LETRAS_BLOCO[bloco_idx] if 0 <= bloco_idx < len(LETRAS_BLOCO) else '—'
        return codigo, descricao, nota, bloco

    def auditorias_para_exportacao(frame: pd.DataFrame) -> pd.DataFrame:
        """CSV completo de auditorias: campos da auditoria + tópicos e NCs."""
        rows = []
        for _, row in frame.iterrows():
            topicos = row.get('topicos') if isinstance(row.get('topicos'), list) else []
            criticas = row.get('criticas') if isinstance(row.get('criticas'), list) else []
            score = _aud_csv_num(row.get('total'))
            classificacao, risco = _aud_csv_faixa(score if score != '' else 0)
            item = {
                'ID Auditoria': row.get('id', ''),
                'Loja_Cod': row.get('loja', ''),
                'Loja_Nome': dict(LOJAS).get(str(row.get('loja')), dict(LOJAS).get(row.get('loja'), '')),
                'Frente_Cod': row.get('tipo', ''),
                'Frente': CHECKLISTS.get(row.get('tipo'), {}).get('nome', row.get('tipo', '')),
                'Data': data_br(row.get('data')),
                'Auditor': row.get('avaliador', ''),
                'Gerente': row.get('gerente', ''),
                'Turno': row.get('turno', ''),
                'Relatório': row.get('relatorio', ''),
            }
            for i, letra in enumerate(LETRAS_BLOCO):
                topico = topicos[i] if i < len(topicos) and isinstance(topicos[i], dict) else {}
                item[f'Bloco_{letra}_Nome'] = topico.get('nome', SLOTS_CURTOS[i])
                item[f'Bloco_{letra}_Possível'] = topico.get('possivel', POSSIVEL[i])
                item[f'Bloco_{letra}_Pct'] = _aud_csv_num(topico.get('pct', ''))
            item.update({
                'Score_Ponderado': score,
                'Classificação': classificacao,
                'Risco': risco,
                'Nível': nivel_maturidade(score if score != '' else 0),
                'Score_Anterior': row.get('scoreAnterior', ''),
                'Próxima_Auditoria': data_br(row.get('proxima')),
                'NCs_Total': len(criticas),
                'NCs_Abertas': sum((normalizar_critica(c).get('status') or 'Aberta') in {'Aberta', 'Em andamento'} for c in criticas),
                'Observação': row.get('obs', row.get('observacao', '')),
                'Tópicos_JSON': _aud_csv_json(topicos),
                'NCs_JSON': _aud_csv_json(criticas),
                'Criado_em': data_br(row.get('criado_em')),
                'Atualizado_em': data_br(row.get('atualizado_em')),
            })
            rows.append(item)
        return pd.DataFrame(rows)

    def ncs_para_exportacao(ncs: list) -> pd.DataFrame:
        """CSV completo de NCs, uma linha por não conformidade."""
        colunas = [
            'ID Auditoria', 'Loja_Cod', 'Loja_Nome', 'Frente_Cod', 'Frente',
            'Data_Auditoria', 'Item_Checklist', 'Item_Descricao', 'POP_Codigo',
            'POP_Documento', 'POP_Ponto_Divergente', 'Descricao_Divergencia',
            'Evidencia', 'Nota', 'Origem', 'Bloco', 'Criticidade', 'Impacto',
            'Responsavel', 'Prazo', 'Status', 'Dias_Em_Aberto',
            'Acao_Corretiva', 'Data_Registro', 'Critica_JSON',
        ]
        rows = []
        for nc_bruta in ncs:
            nc = normalizar_critica(nc_bruta)
            codigo, descricao, nota, bloco = _aud_csv_item_info(nc)
            loja = nc.get('_loja', '')
            tipo = nc.get('_tipo', '')
            status = nc.get('status') or 'Aberta'
            pop_nome = _aud_txt(nc.get('pop_nome'))
            prazo = data_br(nc.get('prazo'))
            data_auditoria = data_br(nc.get('_data'))
            data_inicio = pd.to_datetime(nc.get('_data'), errors='coerce')
            dias_aberto = ''
            if status in {'Aberta', 'Em andamento'} and not pd.isna(data_inicio):
                dias_aberto = max(0, (pd.Timestamp.now().normalize() - data_inicio.normalize()).days)
            impacto = nc.get('impacto_operacional') or []
            if isinstance(impacto, str):
                impacto = [impacto]
            rows.append({
                'ID Auditoria': nc.get('_auditoria_id', ''),
                'Loja_Cod': loja,
                'Loja_Nome': dict(LOJAS).get(str(loja), dict(LOJAS).get(loja, '')),
                'Frente_Cod': tipo,
                'Frente': CHECKLISTS.get(tipo, {}).get('nome', tipo),
                'Data_Auditoria': data_auditoria,
                'Item_Checklist': codigo,
                'Item_Descricao': descricao,
                'POP_Codigo': nc.get('pop_codigo_2', ''),
                'POP_Documento': pop_nome,
                'POP_Ponto_Divergente': nc.get('ponto_pop', ''),
                'Descricao_Divergencia': nc.get('texto', ''),
                'Evidencia': nc.get('evidencia', ''),
                'Nota': nota,
                'Origem': 'POP Ferreira' if pop_nome else 'Sem rastreio',
                'Bloco': bloco,
                'Criticidade': nc.get('criticidade', ''),
                'Impacto': ' / '.join(str(x) for x in impacto),
                'Responsavel': nc.get('responsavel', ''),
                'Prazo': prazo,
                'Status': status,
                'Dias_Em_Aberto': dias_aberto,
                'Acao_Corretiva': nc.get('acao_corretiva', ''),
                'Data_Registro': data_auditoria,
                'Critica_JSON': _aud_csv_json(nc),
            })
        return pd.DataFrame(rows, columns=colunas)

    def calcular_metricas(df):
        """Calcula todas as métricas do painel"""
        # ── VERIFICA SE O DATAFRAME ESTÁ VAZIO ──
        if df.empty:
            return {
                'total': 0,
                'lojas': 0,
                'nota_media': 0,
                'total_criticas': 0,
                'nota_rede': 0,
                'ativos': 0,
                'atualizacao': 0,
                'pendentes': 0
            }
        
        # ── VERIFICA SE AS COLUNAS EXISTEM ──
        colunas_necessarias = ['loja', 'total', 'criticas', 'data', 'tipo']
        for col in colunas_necessarias:
            if col not in df.columns:
                return {
                    'total': len(df),
                    'lojas': 0,
                    'nota_media': 0,
                    'total_criticas': 0,
                    'nota_rede': 0,
                    'ativos': 0,
                    'atualizacao': 0,
                    'pendentes': 0
                }
        
        total = len(df)
        lojas = df['loja'].nunique()
        nota_media = df['total'].mean()
        total_criticas = df['criticas'].apply(len).sum()
        
        # Última auditoria por loja (para ranking)
        ultimas = df.sort_values('data').groupby('loja').last().reset_index()
        nota_rede = ultimas['total'].mean()
        
        # Contagem por status (simulado)
        ativos = len(df[df['total'] >= 80])
        atualizacao = len(df[(df['total'] >= 70) & (df['total'] < 80)])
        pendentes = len(df[df['total'] < 70])
        
        return {
            'total': total,
            'lojas': lojas,
            'nota_media': nota_media,
            'total_criticas': total_criticas,
            'nota_rede': nota_rede,
            'ativos': ativos,
            'atualizacao': atualizacao,
            'pendentes': pendentes
        }
        
    def calcular_rankings(df):
        """Calcula rankings por loja e por frente"""
        # Última auditoria por loja
        ultimas = df.sort_values('data').groupby('loja').last().reset_index()
        
        # Ranking geral
        ranking_loja = ultimas.groupby('loja')['total'].mean().sort_values(ascending=False)
        
        # Ranking por frente
        ranking_frente = {}
        for tipo in df['tipo'].unique():
            df_tipo = df[df['tipo'] == tipo]
            ranking_frente[tipo] = df_tipo.groupby('loja')['total'].mean().sort_values(ascending=False)
        
        return ranking_loja, ranking_frente
    
    # ── SUB-ABAS (ordem conforme a navegação do HTML de referência v2) ──
    sub_tabs = st.tabs([
        "▩ Painel geral",
        "≡ Rankings",
        "▦ Mapa de risco",
        "◎ Análise por loja",
        "✕ Não conformidades",
        "☰ Histórico",
        "⭳ Importar PDF",
        "＋ Lançar manual",
        "⛁ Dados & exportação"
    ])
    
       # ═══════════════════════════════════════════════════════════════════
    # A referência v2 troca de subaba ao clicar em "Abrir detalhamento das NCs".
    # Como st.tabs não expõe uma seleção programática, o clique nativo abaixo
    # grava o destino na URL e este pequeno componente aciona a subaba no DOM.
    if st.query_params.get("auditoria_subtab") == "ncs":
        st.components.v1.html(
            """
            <script>
            (function abrirSubabaNCs(){
              try {
                const listas = Array.from(window.parent.document.querySelectorAll('div[data-baseweb="tab-list"]'));
                const listaAuditoria = listas[listas.length - 1];
                const botoes = listaAuditoria ? listaAuditoria.querySelectorAll('button[role="tab"]') : [];
                if (botoes.length > 4) { botoes[4].click(); return; }
              } catch (e) {}
              setTimeout(abrirSubabaNCs, 120);
            })();
            </script>
            """,
            height=1,
            scrolling=False,
        )
        st.query_params.pop("auditoria_subtab", None)

    # SUB-ABA 1 - PAINEL GERAL (COM KPIs DO HTML)
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[0]:
        st.markdown(cab_html(
            "Painel geral da rede",
            "Consolidação das auditorias internas de Açougue, Frente de Loja, Recebimento e Atacado.",
            "▩",
        ), unsafe_allow_html=True)
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            # ── KPIs ──
            metricas = calcular_metricas(df_auditorias)
            ncs_rede = todas_ncs(df_auditorias)
            ncs_abertas = [n for n in ncs_rede if (n.get('status') or 'Aberta') in {'Aberta', 'Em andamento'}]
            ncs_vencidas = [n for n in ncs_abertas if vencida(n)]
            ncs_sem_pop = [n for n in ncs_abertas if not (n.get('pop_nome') or '').strip()]

            if ncs_sem_pop:
                origem_sem_pop = {}
                for n in ncs_sem_pop:
                    chave = (n.get('_loja') or '?', n.get('_tipo') or '?')
                    origem_sem_pop[chave] = origem_sem_pop.get(chave, 0) + 1
                detalhe_origem = ' · '.join(
                    f"{loja} {CHECKLISTS.get(tipo, {}).get('nome', tipo)} ({qtd})"
                    for (loja, tipo), qtd in sorted(origem_sem_pop.items(), key=lambda x: -x[1])
                )
                st.markdown(f"""
                <div style="background:#fdeeee;border:1px solid #eebcbc;border-left:4px solid #D64545;
                    border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:14px;display:flex;gap:10px;">
                    <span>⚑</span>
                    <div><b>{len(ncs_sem_pop)} não conformidade(s) sem rastreio ao POP.</b>
                    Toda NC deveria indicar o documento e o ponto exato do POP divergente.
                    Veja a aba <b>Não conformidades</b> para regularizar.
                    <div style="margin-top:4px;color:#728177;font-size:12px">{detalhe_origem}</div></div>
                </div>
                """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                f = faixa(metricas['nota_rede'])
                st.markdown(f"""
                <div class="aud-card aud-kpi">
                    <div class="rot">Nota média da rede</div>
                    <div class="num">{metricas['nota_rede']:.2f}</div>
                    <div class="pe"><span class="aud-selo" style="background:{f['cor']}">{f['rot']}</span></div>
                    <div class="faixa"><i style="width:{min(100, metricas['nota_rede'])}%;background:{f['cor']}"></i></div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                pct_lojas = 100 * metricas['lojas'] / max(1, len(LOJAS))
                st.markdown(f"""
                <div class="aud-card aud-kpi">
                    <div class="rot">Lojas auditadas</div>
                    <div class="num">{metricas['lojas']} <small style="font-size:16px;color:#728177;font-family:Inter,sans-serif">de {len(LOJAS)}</small></div>
                    <div class="pe">{len(df_auditorias)} auditorias no histórico</div>
                    <div class="faixa"><i style="width:{pct_lojas:.1f}%;background:#2E9E37"></i></div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                cor_ab = '#D64545' if ncs_abertas else '#1E7A2A'
                pct_ab = 100 if ncs_abertas else 100
                st.markdown(f"""
                <div class="aud-card aud-kpi">
                    <div class="rot">Não conformidades em aberto</div>
                    <div class="num">{len(ncs_abertas)}</div>
                    <div class="pe">{len(ncs_vencidas)} com prazo vencido</div>
                    <div class="faixa"><i style="width:{pct_ab}%;background:{cor_ab}"></i></div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                cor_sp = '#D64545' if ncs_sem_pop else '#1E7A2A'
                st.markdown(f"""
                <div class="aud-card aud-kpi">
                    <div class="rot">NCs sem rastreio ao POP</div>
                    <div class="num">{len(ncs_sem_pop)}</div>
                    <div class="pe">{'Regularizar a referência' if ncs_sem_pop else 'Todas rastreadas'}</div>
                    <div class="faixa"><i style="width:100%;background:{cor_sp}"></i></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── RANKING DAS LOJAS E DESEMPENHO POR PROCESSO (2 colunas) ──
            col_rank, col_proc = st.columns(2)

            ranking_loja, _ = calcular_rankings(df_auditorias)
            frentes_por_loja = df_auditorias.groupby('loja')['tipo'].nunique().to_dict()
            n_frentes_total = len(CHECKLISTS)

            with col_rank:
                st.markdown('<div class="aud-card"><h3>Ranking das lojas <span style="font-size:11px;color:#728177;font-weight:500">média das frentes</span></h3>', unsafe_allow_html=True)
                html_rank = ""
                for loja, nota in ranking_loja.items():
                    f = faixa(nota)
                    nome_loja = dict(LOJAS).get(loja, loja)
                    n_frentes = frentes_por_loja.get(loja, 0)
                    sufixo_cob = f" ({n_frentes}/{n_frentes_total})" if n_frentes < n_frentes_total else ""
                    texto_nome = f"{loja} — {nome_loja}{sufixo_cob}"
                    html_rank += f"""<div class="aud-barra">
                        <div class="nome" title="{texto_nome}"><span class="aud-cod" style="font-size:12px">{loja}</span> {nome_loja}{sufixo_cob}</div>
                        <div class="trilho"><i style="width:{min(100,nota)}%;background:{f['cor']}"></i></div>
                        <div class="val" style="color:{f['cor']}">{nota:.2f}</div>
                    </div>"""
                st.markdown(html_rank + '</div>', unsafe_allow_html=True)

            with col_proc:
                notas_tipo = df_auditorias.groupby('tipo')['total'].mean()
                topicos_medias = []
                for i, nome in enumerate(SLOTS_CURTOS):
                    pcts_t = []
                    for _, row in df_auditorias.iterrows():
                        if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                            pcts_t.append(row['topicos'][i].get('pct', 0))
                    if pcts_t:
                        topicos_medias.append({
                            'topico': nome, 'media': sum(pcts_t)/len(pcts_t),
                            'peso': POSSIVEL[i], 'letra': LETRAS_BLOCO[i],
                        })

                st.markdown('<div class="aud-card"><h3>Score por frente</h3>', unsafe_allow_html=True)
                html_proc = ""
                for tipo, nota in notas_tipo.items():
                    f = faixa(nota)
                    nome = CHECKLISTS[tipo]['nome']
                    html_proc += f"""<div class="aud-barra">
                        <div class="nome">{nome}</div>
                        <div class="trilho"><i style="width:{min(100,nota)}%;background:{f['cor']}"></i></div>
                        <div class="val" style="color:{f['cor']}">{nota:.2f}</div>
                    </div>"""
                st.markdown(html_proc + '</div>', unsafe_allow_html=True)

            st.markdown('<div class="aud-card"><h3>Score por bloco do checklist <span style="font-size:11px;color:#728177;font-weight:500">rede — última auditoria de cada loja</span></h3>', unsafe_allow_html=True)
            html_blocos = ""
            for item in topicos_medias:
                f = faixa(item['media'])
                html_blocos += f"""<div class="aud-barra">
                    <div class="nome" title="{item['letra']}. {item['topico']} (peso {item['peso']}%)">{item['letra']}. {item['topico']} <span style="color:#728177;font-weight:400">(peso {item['peso']}%)</span></div>
                    <div class="trilho"><i style="width:{min(100,item['media'])}%;background:{f['cor']}"></i></div>
                    <div class="val" style="color:{f['cor']}">{item['media']:.2f}</div>
                </div>"""
            st.markdown(html_blocos + '</div>', unsafe_allow_html=True)

            # ── LEGENDA DA CLASSIFICAÇÃO ──
            st.markdown(legenda_faixa_html(), unsafe_allow_html=True)

            # ── GAPS RECORRENTES NA REDE (PARETO) ──
            st.markdown('<div class="aud-card" style="margin-top:16px"><h3>Gaps recorrentes na rede <span style="font-size:11px;color:#728177;font-weight:500">não conformidades agrupadas pelos itens do checklist</span></h3>', unsafe_allow_html=True)
            grupos = {}
            for n in ncs_abertas:
                chave = (n.get('codigo_item') or '').strip() or (n.get('texto') or '')[:80] or 'Item não informado'
                if chave not in grupos:
                    grupos[chave] = {
                        'n': 0, 'lojas': set(), 'tipos': set(), 'pops': set(),
                        'texto': n.get('texto') or chave,
                    }
                grupos[chave]['n'] += 1
                grupos[chave]['lojas'].add(n.get('_loja'))
                grupos[chave]['tipos'].add(n.get('_tipo'))
                grupos[chave]['pops'].add(n.get('pop_nome') or '—')

            if not grupos:
                st.markdown('<div style="text-align:center;padding:26px;color:#728177">Nenhuma não conformidade em aberto.</div></div>', unsafe_allow_html=True)
            else:
                top = sorted(grupos.items(), key=lambda kv: -kv[1]['n'])[:8]
                max_n = top[0][1]['n']
                linhas = ""
                for chave, g in top:
                    frentes_txt = ', '.join(CHECKLISTS.get(t, {}).get('nome', t) for t in g['tipos'])
                    pops_txt = ' · '.join(p for p in g['pops'] if p and p != '—') or '—'
                    lojas_ordenadas = sorted(g['lojas'])
                    max_lojas_visiveis = 4
                    lojas_txt = ' '.join(
                        f'<span class="aud-cod" style="font-size:12px">{l}</span>'
                        for l in lojas_ordenadas[:max_lojas_visiveis]
                    )
                    if len(lojas_ordenadas) > max_lojas_visiveis:
                        restante = lojas_ordenadas[max_lojas_visiveis:]
                        lojas_txt += (
                            f' <span class="aud-cod" style="font-size:12px;color:#728177" '
                            f'title="{", ".join(restante)}">+{len(restante)}</span>'
                        )
                    largura = 100 * g['n'] / max_n
                    texto_gap = g['texto'] if len(g['texto']) <= 90 else g['texto'][:89].rstrip() + '…'
                    linhas += f"""<tr>
                        <td style="font-weight:500" title="{g['texto']}">{texto_gap}</td>
                        <td><span class="aud-tag">{frentes_txt}</span></td>
                        <td style="font-size:12px;color:#728177">{pops_txt}</td>
                        <td style="text-align:center">{lojas_txt}</td>
                        <td><div style="display:flex;align-items:center;gap:8px">
                            <div style="flex:1;height:18px;background:#F4F7F3;border-radius:5px;overflow:hidden">
                            <span style="display:block;height:100%;width:{largura}%;background:#D64545"></span></div>
                            <span style="font-family:'Barlow Semi Condensed',sans-serif;font-weight:700">{g['n']}</span></div></td>
                    </tr>"""
                st.markdown(f"""
                <table style="width:100%;border-collapse:collapse;font-size:13px">
                <thead><tr>
                    <th style="text-align:left;padding:9px 10px;border-bottom:1px solid #DDE6DC;font-size:11.5px;color:#728177">Item do checklist</th>
                    <th style="text-align:left;padding:9px 10px;border-bottom:1px solid #DDE6DC;font-size:11.5px;color:#728177">Frente</th>
                    <th style="text-align:left;padding:9px 10px;border-bottom:1px solid #DDE6DC;font-size:11.5px;color:#728177">Documento de referência</th>
                    <th style="text-align:center;padding:9px 10px;border-bottom:1px solid #DDE6DC;font-size:11.5px;color:#728177">Lojas</th>
                    <th style="text-align:left;padding:9px 10px;border-bottom:1px solid #DDE6DC;font-size:11.5px;color:#728177;width:160px">Ocorrências</th>
                </tr></thead>
                <tbody>{linhas}</tbody></table>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── EXPORTAR ──
            csv_data = df_para_csv_br(auditorias_para_exportacao(df_auditorias))
            st.download_button("📊 Exportar CSV", data=csv_data,
                file_name=f"auditorias_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True, key="export_csv_painel_geral")

        # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 2 - RANKINGS
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[1]:
        st.markdown(cab_html(
            "Rankings",
            "Classificações pela auditoria mais recente de cada loja/frente.",
            "≡",
        ), unsafe_allow_html=True)
        
        if df_auditorias.empty:
            st.info(" Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            # ── CÁLCULOS ──
            ranking_loja, ranking_frente = calcular_rankings(df_auditorias)
            
            # Tópicos mais frágeis
            topicos_medias = []
            for i, nome in enumerate(SLOTS_CURTOS):
                pcts = []
                for _, row in df_auditorias.iterrows():
                    if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                        pcts.append(row['topicos'][i].get('pct', 0))
                if pcts:
                    topicos_medias.append({
                        'topico': nome, 'media': sum(pcts)/len(pcts),
                        'peso': POSSIVEL[i], 'letra': LETRAS_BLOCO[i],
                    })
            
            # ═══════════════════════════════════════════════════════════
            # LINHA 1: Ranking geral + Tópicos frágeis
            # ═══════════════════════════════════════════════════════════
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Ranking geral das lojas**")

                if not ranking_loja.empty:
                    frentes_por_loja_rk = df_auditorias.groupby('loja')['tipo'].nunique().to_dict()
                    n_frentes_total_rk = len(CHECKLISTS)
                    tem_cobertura_parcial = any(
                        frentes_por_loja_rk.get(loja, 0) < n_frentes_total_rk for loja in ranking_loja.index
                    )

                    html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem;'>"
                    html += "<thead><tr style='background:#0a3d1f;'>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:left;font-size:0.7rem;text-transform:uppercase;'>#</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:left;font-size:0.7rem;text-transform:uppercase;'>Loja</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:center;font-size:0.7rem;text-transform:uppercase;'>Cobertura</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:center;font-size:0.7rem;text-transform:uppercase;'>Nota</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:center;font-size:0.7rem;text-transform:uppercase;'>Faixa</th>"
                    html += "</tr></thead><tbody>"

                    for i, (loja, nota) in enumerate(ranking_loja.items(), 1):
                        f = faixa(nota)
                        nome_loja = dict(LOJAS).get(loja, loja)
                        cor = f['cor']
                        rot = f['rot']
                        n_frentes_loja = frentes_por_loja_rk.get(loja, 0)
                        parcial = n_frentes_loja < n_frentes_total_rk
                        cor_cob = '#D64545' if parcial else '#728177'
                        bg_cob = '#fdeeee' if parcial else '#F4F7F3'

                        html += "<tr style='border-bottom:1px solid #e8f3ec;'>"
                        html += "<td style='padding:0.65rem 0.8rem;font-weight:700;color:#1E7A2A;'>" + str(i) + "</td>"
                        html += "<td style='padding:0.65rem 0.8rem;font-weight:600;'><span style='font-weight:700;color:#1E7A2A;'>" + loja + "</span> " + nome_loja + "</td>"
                        html += f"<td style='padding:0.65rem 0.8rem;text-align:center;'><span style='background:{bg_cob};color:{cor_cob};padding:2px 9px;border-radius:5px;font-size:0.7rem;font-weight:700;'>{n_frentes_loja}/{n_frentes_total_rk}</span></td>"
                        html += "<td style='padding:0.65rem 0.8rem;text-align:center;font-weight:700;font-size:0.95rem;color:" + cor + ";'>" + f"{nota:.2f}" + "</td>"
                        html += "<td style='padding:0.65rem 0.8rem;text-align:center;'><span style='background:" + cor + ";color:white;padding:2px 10px;border-radius:20px;font-size:0.65rem;font-weight:700;'>" + rot + "</span></td>"
                        html += "</tr>"

                    html += "</tbody></table>"
                    st.markdown(html, unsafe_allow_html=True)
                    if tem_cobertura_parcial:
                        st.caption("ⓘ Unidades com cobertura parcial não são diretamente comparáveis às demais.")
                else:
                    st.info("Nenhuma loja auditada.")
            
            with col2:
                st.markdown("**Blocos mais frágeis da rede** <span style='font-size:11px;color:#728177;font-weight:400'>onde a rede mais perde score</span>", unsafe_allow_html=True)

                topicos_ordenados = sorted(topicos_medias, key=lambda x: x['media'])

                html = ""
                for item in topicos_ordenados:
                    f = faixa(item['media'])
                    cor = f['cor']
                    media_str = f"{item['media']:.2f}"
                    media_pct = f"{item['media']:.2f}"

                    html += "<div style='display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #EEF3EE;'>"
                    html += "<div style='width:150px;font-size:0.85rem;font-weight:600;color:#0d2a16;'>" + f"{item['letra']}. {item['topico']}" + f" <span style='color:#728177;font-weight:400'>(peso {item['peso']}%)</span></div>"
                    html += "<div style='flex:1;height:24px;background:#F4F7F3;border-radius:6px;overflow:hidden;'>"
                    html += "<div style='height:100%;width:" + media_pct + "%;background:" + cor + ";border-radius:6px;'></div>"
                    html += "</div>"
                    html += "<div style='width:50px;text-align:right;font-weight:700;font-size:0.9rem;color:" + cor + ";'>" + media_str + "</div>"
                    html += "</div>"

                st.markdown(html, unsafe_allow_html=True)
                bloco_mais_pesado = max(topicos_medias, key=lambda x: x['peso']) if topicos_medias else None
                if bloco_mais_pesado:
                    st.markdown(f"""
                    <div style="background:#fff8e6;border:1px solid #f0dca0;border-left:4px solid #F2C300;
                        border-radius:8px;padding:11px 14px;font-size:13px;margin-top:16px;display:flex;gap:10px;">
                        <span>ⓘ</span><div><b>{bloco_mais_pesado['letra']}. {bloco_mais_pesado['topico']}</b> é o bloco de maior peso ({bloco_mais_pesado['peso']}% da nota) — cada ponto perdido nele pesa mais no score final do que nos demais blocos.</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ═══════════════════════════════════════════════════════════
            # LINHA 2: Rankings por frente — grade dinâmica (2 por linha,
            # cresce em novas linhas conforme frentes são adicionadas em
            # CHECKLISTS, sem quebrar o layout)
            # ═══════════════════════════════════════════════════════════
            frentes_lista = list(CHECKLISTS.items())
            for linha_inicio in range(0, len(frentes_lista), 2):
                cols_linha = st.columns(2)
                for col, (tipo_key, info) in zip(cols_linha, frentes_lista[linha_inicio:linha_inicio + 2]):
                    titulo = info['nome']
                    cor_badge = info['cor']
                    with col:
                        html = "<div style='background:" + cor_badge + "15;border:1px solid " + cor_badge + ";border-radius:8px;padding:12px 16px;margin-bottom:16px;'>"
                        html += "<span style='background:" + cor_badge + ";color:white;padding:3px 12px;border-radius:15px;font-size:0.7rem;font-weight:700;text-transform:uppercase;'>" + titulo + "</span>"
                        html += "</div>"

                        df_tipo = df_auditorias[df_auditorias['tipo'] == tipo_key]

                        if not df_tipo.empty:
                            ultimas_tipo = df_tipo.sort_values('data').groupby('loja').last().reset_index()
                            rank_tipo = ultimas_tipo.groupby('loja')['total'].mean().sort_values(ascending=False)

                            for i, (loja, nota) in enumerate(rank_tipo.items(), 1):
                                f = faixa(nota)
                                cor = f['cor']
                                nota_str = f"{nota:.2f}"
                                nome_loja = dict(LOJAS).get(loja, loja)

                                html += "<div style='display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #EEF3EE;'>"
                                html += "<span style='font-weight:600;color:#728177;width:20px;'>" + str(i) + ".</span>"
                                html += "<span style='font-weight:700;font-size:0.85rem;color:#0d2a16;flex:1;'>" + loja + " " + nome_loja + "</span>"
                                html += "<span style='font-weight:700;font-size:0.9rem;color:" + cor + ";'>" + nota_str + "</span>"
                                html += "</div>"
                        else:
                            html += "<div style='text-align:center;padding:20px;color:#728177;font-size:0.85rem;'>Nenhuma auditoria desta frente.</div>"

                        st.markdown(html, unsafe_allow_html=True)

            # ── LEGENDA DA CLASSIFICAÇÃO ──
            st.markdown(legenda_faixa_html(), unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 3 - MAPA DE RISCO (HEATMAP)
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[2]:
        st.markdown(cab_html(
            "Mapa de risco",
            "Resumo dos tópicos da auditoria mais recente.",
            "▦",
        ), unsafe_allow_html=True)
        
        # ─ VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            
            opcoes_heatmap = {
                f"{CHECKLISTS.get(codigo, {'nome': codigo})['nome']} — {codigo}": codigo
                for codigo in (
                    [codigo for codigo in CHECKLISTS
                     if codigo in set(df_auditorias['tipo'].astype(str).tolist())]
                    + sorted(
                        set(df_auditorias['tipo'].astype(str).tolist()) - set(CHECKLISTS)
                    )
                )
            }
            if st.session_state.get("heatmap_tipo") not in opcoes_heatmap:
                st.session_state.pop("heatmap_tipo", None)
            tipo_heatmap_rotulo = st.selectbox(
                "Selecione a Frente",
                list(opcoes_heatmap),
                key="heatmap_tipo"
            )
            tipo_heatmap = opcoes_heatmap[tipo_heatmap_rotulo]
            
            df_heat = df_auditorias[df_auditorias['tipo'] == tipo_heatmap]
            
            if df_heat.empty:
                st.info(f"Nenhuma auditoria de {CHECKLISTS[tipo_heatmap]['nome']} foi registrada. "
                        "Use a aba 'Importar PDF' ou 'Lançar Manual' para registrar a primeira.")
            else:
                # Última auditoria por loja
                df_heat = df_heat.sort_values('data').groupby('loja').last().reset_index()
                
                # ── FUNÇÃO PARA COR DO TEXTO ──
                def cor_nota(nota):
                    return faixa(nota)['hex']
                
                # Constrói a tabela HTML
                html_table = """
                <style>
                .heatmap-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.8rem;
                }
                .heatmap-table thead tr {
                    background: #0a3d1f;
                    position: sticky;
                    top: 0;
                    z-index: 2;
                }
                .heatmap-table thead th {
                    color: #9ecfb2;
                    font-weight: 700;
                    font-size: 0.66rem;
                    letter-spacing: 0.09em;
                    text-transform: uppercase;
                    padding: 0.8rem 0.8rem;
                    text-align: center;
                    border-bottom: 3px solid #f8c10a;
                    white-space: nowrap;
                }
                .heatmap-table thead th:first-child {
                    text-align: left;
                    min-width: 180px;
                }
                .heatmap-table tbody tr {
                    border-bottom: 1px solid #e8f3ec;
                    transition: background 0.12s;
                }
                .heatmap-table tbody tr:hover {
                    background: #eaf7ef;
                }
                .heatmap-table tbody tr:nth-child(even) {
                    background: #f4fbf6;
                }
                .heatmap-table tbody tr:nth-child(even):hover {
                    background: #e2f4e8;
                }
                .heatmap-table tbody td {
                    padding: 0.65rem 0.8rem;
                    color: #0d2a16;
                    vertical-align: middle;
                    white-space: nowrap;
                    font-size: 0.8rem;
                    text-align: center;
                    font-weight: 600;
                }
                .heatmap-table tbody td:first-child {
                    text-align: left;
                    font-weight: 700;
                    color: #0a3d1f;
                }
                .nota-num {
                    font-family: 'Barlow Semi Condensed', sans-serif;
                    font-weight: 700;
                    font-size: 0.95rem;
                }
                </style>
                <div style="overflow-x:auto;max-height:56vh;overflow-y:auto;border:1px solid #DDE6DC;border-radius:12px;">
                <table class="heatmap-table">
                    <thead>
                        <tr>
                            <th>Loja</th>
                """ + "".join(
                    f"<th>{LETRAS_BLOCO[i]}. {nome}<br><span style='font-weight:400;color:#9aa89c'>{POSSIVEL[i]}%</span></th>"
                    for i, nome in enumerate(SLOTS_CURTOS)
                ) + """
                            <th>Nota</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for _, row in df_heat.iterrows():
                    loja_str = f"{row['loja']} - {dict(LOJAS).get(row['loja'], '')}"
                    
                    # Tópicos - cores apenas no texto dos números
                    topicos_html = ""
                    if isinstance(row['topicos'], list):
                        for i in range(5):
                            pct = row['topicos'][i].get('pct', 0) if i < len(row['topicos']) else 0
                            cor = cor_nota(pct)
                            topicos_html += f'<td style="color:{cor};font-weight:700;">{pct:.2f}</td>'
                    else:
                        for _ in range(5):
                            topicos_html += '<td>—</td>'
                    
                    # Nota Total - cor no texto
                    nota = row['total']
                    cor = cor_nota(nota)
                    nota_html = f'<td><span class="nota-num" style="color:{cor}">{nota:.2f}</span></td>'
                    
                    html_table += f"""
                        <tr>
                            <td>{loja_str}</td>
                            {topicos_html}
                            {nota_html}
                        </tr>
                    """
                
                html_table += """
                    </tbody>
                </table>
                </div>
                """
                
                # ── RENDERIZA O HTML COM components ──
                # Altura proporcional ao nº de linhas (cabeçalho de 2 linhas + linhas de
                # dado), com piso alto o bastante para nunca cortar linhas visíveis mesmo
                # com poucas lojas na tabela.
                altura_heat = min(700, max(220, 130 + 56 * len(df_heat)))
                st.components.v1.html(html_table, height=altura_heat, scrolling=True)

                st.caption(f"{len(df_heat)} loja(s) auditada(s) · Exibindo a última auditoria de cada loja")
                
                # ── LEGENDA (gerada a partir de faixa(), sem duplicar valores) ──
                st.markdown(legenda_faixa_html(), unsafe_allow_html=True)
                
                # ── EXPORTAR E ATUALIZAR ──
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    csv_heat = df_para_csv_br(auditorias_para_exportacao(df_heat))
                    st.download_button(
                        " Exportar Mapa de Risco CSV",
                        data=csv_heat,
                        file_name=f"mapa_risco_{tipo_heatmap}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    if st.button("🔄 Atualizar Mapa", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
                    
                    
    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 4 - ANÁLISE POR LOJA
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[3]:
        def _aud_render(markup: str) -> None:
            """Renderiza HTML sem deixar a indentação virar bloco de código Markdown."""
            # O Markdown considera linhas com quatro espaços como código. Como os
            # cards são montados com f-strings aninhadas, o recuo pode voltar depois
            # do primeiro elemento; removemos o recuo de cada linha antes de enviar.
            html_limpo = textwrap.dedent(str(markup)).strip()
            html_limpo = "\n".join(linha.lstrip() for linha in html_limpo.splitlines())
            st.markdown(html_limpo, unsafe_allow_html=True)

        def _aud_latest(frame: pd.DataFrame) -> pd.DataFrame:
            """Último ciclo de cada loja/frente, mesma base do HTML v2."""
            if frame.empty:
                return frame.copy()
            work = frame.copy()
            work['_aud_ordem'] = work['data'].astype(str)
            return (
                work.sort_values('_aud_ordem')
                    .drop_duplicates(['loja', 'tipo'], keep='last')
                    .drop(columns=['_aud_ordem'])
            )

        def _aud_pct(row, index: int) -> float:
            topicos = row.get('topicos', [])
            if isinstance(topicos, list) and len(topicos) > index and isinstance(topicos[index], dict):
                try:
                    return float(topicos[index].get('pct', 0) or 0)
                except (TypeError, ValueError):
                    return 0.0
            return 0.0

        def _aud_faixa_v2(nota: float) -> dict:
            """Régua única do dashboard (mesma de faixa()), com risco e prioridade de atuação."""
            f = faixa(nota)
            return {'rot': f['rot'], 'risco': f['risco'], 'prio': f['prio'], 'cor': f['hex']}

        def _aud_txt(value) -> str:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return ''
            return str(value).strip()

        def _aud_num(value, default: float = 0.0) -> float:
            numero = pd.to_numeric(value, errors='coerce')
            return default if pd.isna(numero) else float(numero)

        st.markdown(cab_html(
            "Análise por loja",
            "Consolidação das frentes auditadas na unidade, comparada com a média da rede na mesma base de cálculo.",
        ), unsafe_allow_html=True)
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            lojas_analise = sorted(df_auditorias['loja'].astype(str).unique().tolist())
            opcoes_loja = {
                f"{loja} — {dict(LOJAS).get(loja, loja)}": loja
                for loja in lojas_analise
            }
            col_filtro, _ = st.columns([1.2, 2.8])
            with col_filtro:
                loja_rotulo = st.selectbox(
                    "Loja",
                    list(opcoes_loja),
                    key="aud_v2_loja",
                )
            loja_selecionada = opcoes_loja[loja_rotulo]
            
            df_loja = df_auditorias[df_auditorias['loja'].astype(str) == str(loja_selecionada)]
            
            if df_loja.empty:
                st.warning(f"Nenhuma auditoria para a loja {loja_selecionada}")
            else:
                # ── Base de cálculo do v2: último ciclo de cada loja/frente ──
                df_ultimas_rede = _aud_latest(df_auditorias)
                df_ultimas_loja = df_ultimas_rede[df_ultimas_rede['loja'].astype(str) == str(loja_selecionada)]
                if df_ultimas_loja.empty:
                    st.warning(f"Nenhuma auditoria para a loja {loja_selecionada}")
                    st.stop()

                media_loja = pd.to_numeric(df_ultimas_loja['total'], errors='coerce').dropna()
                media_rede = pd.to_numeric(df_ultimas_rede['total'], errors='coerce').dropna()
                nota_loja = float(media_loja.mean()) if not media_loja.empty else 0.0
                nota_rede = float(media_rede.mean()) if not media_rede.empty else 0.0
                f_loja = _aud_faixa_v2(nota_loja)
                ultima_data = sorted(df_ultimas_loja['data'].astype(str).tolist())[-1] if not df_ultimas_loja.empty else ''
                ultima_formatada = data_br(ultima_data)

                loja_medias = [
                    float(np.mean([_aud_pct(row, i) for _, row in df_ultimas_loja.iterrows()]))
                    if len(df_ultimas_loja) else 0.0
                    for i in range(len(SLOTS_CURTOS))
                ]
                rede_medias = [
                    float(np.mean([_aud_pct(row, i) for _, row in df_ultimas_rede.iterrows()]))
                    if len(df_ultimas_rede) else 0.0
                    for i in range(len(SLOTS_CURTOS))
                ]

                # ── CARD CENTRAL: estrutura e detalhes da referência v2 ──
                loja_nome_html = html_lib.escape(str(dict(LOJAS).get(loja_selecionada, loja_selecionada)))
                loja_codigo_html = html_lib.escape(str(loja_selecionada))
                circ = 2 * 3.14159 * 42
                progresso = max(0.0, min(100.0, nota_loja))
                linhas_frentes = []
                ult_por_tipo = {str(row['tipo']): row for _, row in df_ultimas_loja.iterrows()}
                for tipo, config in CHECKLISTS.items():
                    nome_frente = html_lib.escape(str(config['nome']))
                    if tipo in ult_por_tipo:
                        nota_frente = _aud_num(ult_por_tipo[tipo].get('total', 0))
                        faixa_frente = _aud_faixa_v2(nota_frente)
                        linhas_frentes.append(
                            f'<div style="display:flex;gap:8px;align-items:center;justify-content:flex-end;margin-bottom:4px">'
                            f'<span class="aud-v2-selo" style="background:{config["cor"]}">{nome_frente}</span>'
                            f'<span class="aud-v2-score" style="color:{faixa_frente["cor"]}">{nota_frente:.2f}</span></div>'
                        )
                    else:
                        linhas_frentes.append(
                            f'<div style="display:flex;gap:8px;align-items:center;justify-content:flex-end;margin-bottom:4px;opacity:.45">'
                            f'<span class="aud-v2-selo" style="background:{config["cor"]}">{nome_frente}</span>'
                            f'<span class="aud-v2-score" style="color:var(--suave)">—</span></div>'
                        )

                linhas_blocos = []
                for i, nome in enumerate(SLOTS_CURTOS):
                    val_loja = loja_medias[i]
                    val_rede = rede_medias[i]
                    f_item = _aud_faixa_v2(val_loja)
                    cor_item = f_item['cor']
                    pct_loja = max(0.0, min(100.0, val_loja))
                    pct_rede = max(0.0, min(100.0, val_rede))
                    nome_bloco = html_lib.escape(str(nome))
                    linhas_blocos.append(
                        f'<div class="aud-v2-barra"><div class="nome" title="{LETRAS_BLOCO[i]}. {nome_bloco}">{LETRAS_BLOCO[i]}. {nome_bloco}</div>'
                        f'<div class="aud-v2-trilho"><span class="preenche" style="width:{pct_loja:.2f}%;background:{cor_item}"></span>'
                        f'<span class="marcador" style="left:{pct_rede:.2f}%" title="rede {val_rede:.1f}"></span></div>'
                        f'<div class="val" style="color:{cor_item}">{val_loja:.2f}</div></div>'
                    )

                html_card = (
                    f'<div class="aud-v2-card"><div class="aud-v2-topo">'
                    f'<div class="aud-v2-anel"><svg width="104" height="104" viewBox="0 0 104 104" aria-label="Nota da loja {nota_loja:.2f}">'
                    f'<circle cx="52" cy="52" r="42" fill="none" stroke="#F4F7F3" stroke-width="9"/>'
                    f'<circle cx="52" cy="52" r="42" fill="none" stroke="{f_loja["cor"]}" stroke-width="9" stroke-dasharray="{circ * progresso / 100:.2f} {circ * (1 - progresso / 100):.2f}" stroke-linecap="round" transform="rotate(-90 52 52)"/>'
                    f'<text x="52" y="52" text-anchor="middle" dy=".35em" font-size="22" font-weight="700" fill="#2A3A2E">{nota_loja:.1f}</text></svg></div>'
                    f'<div style="flex:1;min-width:220px"><div class="aud-v2-titulo"><span class="aud-v2-cod">{loja_codigo_html}</span> {loja_nome_html}</div>'
                    f'<div class="aud-v2-muted">{len(df_ultimas_loja)} de {len(CHECKLISTS)} frentes auditadas · última em {ultima_formatada}</div>'
                    f'<div style="margin-top:10px"><span class="aud-v2-selo" style="background:{f_loja["cor"]}">{f_loja["rot"]}</span><span style="font-size:13px;color:var(--suave);margin-left:6px">rede: {nota_rede:.2f}</span></div>'
                    f'<div style="margin-top:8px;font-size:12.5px;color:var(--suave)">Risco {f_loja["risco"].lower()} — {f_loja["prio"]}</div></div>'
                    f'<div class="aud-v2-frentes"><div class="aud-v2-frentes-label">Score por frente</div>{"".join(linhas_frentes)}</div></div>'
                    f'<h3>Blocos do checklist — loja e rede</h3><div class="aud-v2-blocos">{"".join(linhas_blocos)}</div>'
                    f'<div class="aud-v2-legenda"><span><i style="background:#5b6a5e;border-radius:50%"></i>marcador = média da rede no bloco</span></div></div>'
                )
                _aud_render(html_card)

                # ── LEITURA DA UNIDADE + SITUAÇÃO DAS NCs (lado a lado, como no v2) ──
                if loja_medias:
                    i_melhor = loja_medias.index(max(loja_medias))
                    i_pior = loja_medias.index(min(loja_medias))
                    melhor_nome = SLOTS_CURTOS[i_melhor]
                    melhor_valor = loja_medias[i_melhor]
                    pior_nome = SLOTS_CURTOS[i_pior]
                    pior_valor = loja_medias[i_pior]
                else:
                    melhor_nome = "—"
                    melhor_valor = 0
                    pior_nome = "—"
                    pior_valor = 0

                delta_rede = nota_loja - nota_rede
                comparacao = (
                    f"Unidade acima da média da rede em {delta_rede:.2f} pontos."
                    if delta_rede >= 0 else
                    f"Unidade {abs(delta_rede):.2f} pontos abaixo da média da rede — priorizar no plano de acompanhamento."
                )
                cor_comparacao = "#1E7A2A" if nota_loja >= nota_rede else "#E67E22"

                letra_melhor = LETRAS_BLOCO[i_melhor] if loja_medias else ''
                letra_pior = LETRAS_BLOCO[i_pior] if loja_medias else ''
                faixa_melhor = _aud_faixa_v2(melhor_valor)['rot'].lower() if loja_medias else ''
                faixa_pior = _aud_faixa_v2(pior_valor)['rot'].lower() if loja_medias else ''

                observacoes_loja = []
                for _, row in df_ultimas_loja.iterrows():
                    observacao = _aud_txt(row.get('obs') or row.get('observacao') or row.get('observacoes'))
                    if observacao:
                        nome_frente = html_lib.escape(str(CHECKLISTS.get(row.get('tipo'), {}).get('nome', row.get('tipo', 'Frente'))))
                        observacoes_loja.append(
                            f'<div class="aud-v2-aviso"><span class="mk">✎</span><div><b>{nome_frente}:</b> {html_lib.escape(observacao)}</div></div>'
                        )

                leitura_html = f'''
                    <div class="aud-v2-card"><h3>Leitura da unidade</h3>
                        <div class="aud-v2-aviso bom"><span class="mk">▲</span><div><b>Maior fortaleza:</b> bloco {letra_melhor} — {html_lib.escape(str(melhor_nome))} ({melhor_valor:.2f}), faixa {faixa_melhor}.</div></div>
                        <div class="aud-v2-aviso grave"><span class="mk">▼</span><div><b>Prioridade de ação:</b> bloco {letra_pior} — {html_lib.escape(str(pior_nome))} ({pior_valor:.2f}), faixa {faixa_pior}. {_aud_faixa_v2(pior_valor)['prio']}</div></div>
                        <div class="aud-v2-aviso {'bom' if nota_loja >= nota_rede else ''}" style="{'background:#effaf0;border-color:#bfe6c2' if nota_loja >= nota_rede else ''}">
                            <span class="mk">{'✓' if nota_loja >= nota_rede else '≈'}</span><div>{comparacao}</div>
                        </div>
                        {''.join(observacoes_loja)}
                    </div>
                '''

                ncs_loja_todas = [n for n in todas_ncs(df_loja)]
                ncs_loja_abertas = [n for n in ncs_loja_todas if (n.get('status') or 'Aberta') in {'Aberta', 'Em andamento'}]
                limite_ncs_resumo = 4
                ncs_loja_resumo = ncs_loja_todas[:limite_ncs_resumo]

                col_leitura, col_ncs = st.columns(2)

                with col_leitura:
                    _aud_render(leitura_html)

                # ── NÃO CONFORMIDADES ──
                with col_ncs:
                    linhas_nc_html = []
                    status_cores = {'Aberta': '#D64545', 'Em andamento': '#E8B23A', 'Concluída': '#1E7A2A', 'Cancelada': '#9aa89c'}
                    for nc in ncs_loja_resumo:
                        codigo = _aud_txt(nc.get('codigo_item')) or '—'
                        texto_completo = _aud_txt(nc.get('texto')) or 'Descrição não informada.'
                        if codigo == '—':
                            codigo_extraido = re.match(r'^\s*([0-9]+(?:\.[0-9]+)+)\s*[—-]\s*(.*)$', texto_completo)
                            if codigo_extraido:
                                codigo = codigo_extraido.group(1)
                                texto_completo = codigo_extraido.group(2)
                        bloco = html_lib.escape(codigo[:1] if codigo != '—' else '—')
                        codigo_html = html_lib.escape(codigo)
                        descricao_base = texto_completo.split('?', 1)[0].strip()
                        descricao = html_lib.escape(
                            descricao_base if len(descricao_base) <= 100 else descricao_base[:97].rstrip() + '…'
                        )
                        descricao_completa_html = html_lib.escape(texto_completo)
                        status = _aud_txt(nc.get('status')) or 'Aberta'
                        status_html = html_lib.escape(status)
                        prazo = data_br(nc.get('prazo')) or '—'
                        vencido = bool(nc.get('prazo')) and vencida(nc) and status in {'Aberta', 'Em andamento'}
                        prazo_html = f'<span class="aud-v2-tag" style="color:#D64545;border-color:#eebcbc;background:#fdeeee">⚠ {html_lib.escape(prazo)}</span>' if vencido else f'<span class="aud-v2-tag">{html_lib.escape(prazo)}</span>'
                        linhas_nc_html.append(
                            f'<tr><td><span class="aud-v2-tag">{bloco}</span></td>'
                            f'<td><b>{codigo_html}</b><div title="{descricao_completa_html}" style="font-size:12px;color:var(--suave)">{descricao}</div></td>'
                            f'<td><span class="aud-v2-status" style="background:{status_cores.get(status, "#999")}">{status_html}</span></td>'
                            f'<td style="white-space:nowrap">{prazo_html}</td></tr>'
                        )

                    if linhas_nc_html:
                        nc_rows_html = ''.join(linhas_nc_html)
                        aviso_limite_ncs = (
                            f'<div style="margin-top:10px;color:var(--suave);font-size:12px">'
                            f'Mostrando {len(ncs_loja_resumo)} de {len(ncs_loja_todas)} não conformidade(s). '
                            'Use o detalhamento para consultar a lista completa.</div>'
                            if len(ncs_loja_todas) > len(ncs_loja_resumo) else ''
                        )
                        nc_body = f'''
                            <div class="aud-v2-table-wrap"><table class="aud-v2-table">
                                <thead><tr><th>Bloco</th><th>Item</th><th>Status</th><th>Prazo</th></tr></thead>
                                <tbody>{nc_rows_html}</tbody>
                            </table></div>
                            {aviso_limite_ncs}
                        '''
                    else:
                        nc_body = '<div class="aud-v2-empty">Nenhuma não conformidade registrada nesta unidade.</div>'
                    nc_html = f'''
                        <div class="aud-v2-card"><h3>Situação das não conformidades <span class="leve">{len(ncs_loja_abertas)} em aberto de {len(ncs_loja_todas)}</span></h3>
                            {nc_body}
                        </div>
                    '''
                    _aud_render(nc_html)
                    if ncs_loja_todas and st.button(
                        "Abrir detalhamento das NCs",
                        key=f"aud_abrir_ncs_{loja_selecionada}",
                    ):
                        st.session_state["nc_v2_loja"] = (
                            f"{loja_selecionada} — {dict(LOJAS).get(loja_selecionada, loja_selecionada)}"
                        )
                        st.session_state["nc_v2_status"] = "Em aberto"
                        st.query_params["auditoria_subtab"] = "ncs"
                        st.rerun()

                # ── EVOLUÇÃO ENTRE CICLOS — SVG responsivo, como no HTML v2 ──
                df_evolucao = df_loja.copy()
                df_evolucao['_data_str'] = df_evolucao['data'].astype(str).str[:10]
                df_evolucao = (
                    df_evolucao.sort_values(['_data_str', 'tipo'])
                               .drop_duplicates(['_data_str', 'tipo'], keep='last')
                )
                datas_evolucao = sorted(df_evolucao['_data_str'].dropna().unique().tolist())

                if len(datas_evolucao) < 2:
                    _aud_render('''
                        <div class="aud-v2-card aud-v2-evolucao">
                            <h3>Evolução entre ciclos</h3>
                            <div class="aud-v2-empty">Há apenas um ciclo de auditoria nesta unidade. A série aparece quando o próximo ciclo for registrado.</div>
                        </div>
                    ''')
                else:
                    series = {}
                    valores_grafico = []
                    for tipo, config in CHECKLISTS.items():
                        pontos = []
                        for data_ciclo in datas_evolucao:
                            registros = df_evolucao[(df_evolucao['_data_str'] == data_ciclo) & (df_evolucao['tipo'] == tipo)]
                            if registros.empty:
                                pontos.append(None)
                            else:
                                nota_ciclo = pd.to_numeric(registros.iloc[0].get('total'), errors='coerce')
                                if pd.isna(nota_ciclo):
                                    pontos.append(None)
                                else:
                                    valor_ciclo = float(nota_ciclo)
                                    pontos.append(valor_ciclo)
                                    valores_grafico.append(valor_ciclo)
                        if any(p is not None for p in pontos):
                            series[tipo] = pontos

                    if valores_grafico:
                        menor = min(valores_grafico)
                        maior = max(valores_grafico)
                        limite_baixo = max(0, int(np.floor((menor - 6) / 10) * 10))
                        limite_alto = min(100, int(np.ceil((maior + 6) / 10) * 10))
                        if limite_alto - limite_baixo < 20:
                            limite_alto = min(100, limite_baixo + 20)
                        if limite_alto == limite_baixo:
                            limite_alto = min(100, limite_baixo + 20)

                        largura_svg, altura_svg = 760, 250
                        margem = {'l': 44, 'r': 16, 't': 16, 'b': 36}
                        largura_interna = largura_svg - margem['l'] - margem['r']
                        altura_interna = altura_svg - margem['t'] - margem['b']

                        def _svg_x(index):
                            return margem['l'] + (largura_interna / 2 if len(datas_evolucao) == 1 else largura_interna * index / (len(datas_evolucao) - 1))

                        def _svg_y(value):
                            return margem['t'] + altura_interna * (1 - (value - limite_baixo) / (limite_alto - limite_baixo))

                        ticks_svg = sorted(set(int(round(limite_baixo + (limite_alto - limite_baixo) * j / 5)) for j in range(6)))
                        grade_svg = ''.join(
                            f'<line x1="{margem["l"]}" x2="{largura_svg - margem["r"]}" y1="{_svg_y(tick):.2f}" y2="{_svg_y(tick):.2f}" stroke="#DDE6DC"/>'
                            f'<text x="{margem["l"] - 8}" y="{_svg_y(tick) + 3:.2f}" text-anchor="end" font-size="10" fill="#9aa89c">{tick}</text>'
                            for tick in ticks_svg
                        )
                        linhas_svg = []
                        legendas_svg = []
                        for tipo, pontos in series.items():
                            config = CHECKLISTS[tipo]
                            coordenadas = [(_svg_x(i), _svg_y(valor)) for i, valor in enumerate(pontos) if valor is not None]
                            if coordenadas:
                                caminho = ' '.join(f"{'M' if i == 0 else 'L'}{x:.2f} {y:.2f}" for i, (x, y) in enumerate(coordenadas))
                                linhas_svg.append(
                                    f'<path d="{caminho}" fill="none" stroke="{config["cor"]}" stroke-width="2.5"/>'
                                    + ''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.5" fill="{config["cor"]}"/>' for x, y in coordenadas)
                                )
                                legendas_svg.append(f'<span><i style="display:inline-block;width:12px;height:3px;background:{config["cor"]};vertical-align:middle;margin-right:5px"></i>{html_lib.escape(str(config["nome"]))}</span>')
                        rotulos_x = ''.join(
                            f'<text x="{_svg_x(i):.2f}" y="{altura_svg - 12}" text-anchor="middle" font-size="10.5" fill="#728177">{html_lib.escape(data_br(data_ciclo))}</text>'
                            for i, data_ciclo in enumerate(datas_evolucao)
                        )
                        detalhes_evolucao = []
                        for _, row in df_evolucao.sort_values(['_data_str', 'tipo'], ascending=[False, True]).iterrows():
                            tipo = row.get('tipo')
                            nota = pd.to_numeric(row.get('total'), errors='coerce')
                            if pd.isna(nota):
                                continue
                            config = CHECKLISTS.get(tipo, {'nome': tipo, 'cor': '#728177'})
                            detalhes_evolucao.append(
                                f'<div class="aud-v2-detalhe"><span style="font-weight:600;font-size:13px;color:var(--suave)">{html_lib.escape(data_br(row.get("_data_str")))}</span>'
                                f'<span class="aud-v2-selo" style="background:{config["cor"]};font-size:10px">{html_lib.escape(str(config["nome"]))}</span>'
                                f'<span style="margin-left:auto;font-weight:700;color:{_aud_faixa_v2(float(nota))["cor"]}">{float(nota):.2f}%</span></div>'
                            )

                        linhas_svg_html = ''.join(linhas_svg)
                        rotulos_x_html = rotulos_x
                        legendas_svg_html = ''.join(legendas_svg)
                        detalhes_evolucao_html = ''.join(detalhes_evolucao)
                        evolucao_html = f'''
                            <div class="aud-v2-card aud-v2-evolucao">
                                <h3>Evolução entre ciclos</h3>
                                <svg viewBox="0 0 {largura_svg} {altura_svg}" role="img" aria-label="Evolução das notas por frente">{grade_svg}{linhas_svg_html}{rotulos_x_html}</svg>
                                <div class="aud-v2-evolucao-legend">{legendas_svg_html}</div>
                                <div style="margin-top:16px;padding-top:10px;border-top:1px solid #EEF3EE;font-size:12px;color:var(--suave)">Detalhamento por auditoria</div>
                                {detalhes_evolucao_html}
                            </div>
                        '''
                        _aud_render(evolucao_html)
                    else:
                        _aud_render('''
                            <div class="aud-v2-card aud-v2-evolucao">
                                <h3>Evolução entre ciclos</h3>
                                <div class="aud-v2-empty">Não há notas numéricas suficientes para montar a série histórica.</div>
                            </div>
                        ''')

                # ── LEGENDA DA CLASSIFICAÇÃO ──
                st.markdown(legenda_faixa_html(), unsafe_allow_html=True)
    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 5 - NÃO CONFORMIDADES
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[4]:
        st.markdown(cab_html(
            "Não conformidades",
            "Cada divergência é registrada com o item do checklist, o POP, o ponto de referência e a ação corretiva.",
            "✕",
        ), unsafe_allow_html=True)

        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            ncs_all = todas_ncs(df_auditorias)

            if not ncs_all:
                st.info("Nenhuma não conformidade registrada ainda.")
            else:
                from datetime import datetime

                ncs_abertas_all = [n for n in ncs_all if (n.get('status') or 'Aberta') in {'Aberta', 'Em andamento'}]
                ncs_vencidas_all = [n for n in ncs_abertas_all if vencida(n)]
                ncs_alta_all = [n for n in ncs_abertas_all if n.get('criticidade') == 'Alta']
                ncs_sem_pop_all = [n for n in ncs_abertas_all if not (n.get('pop_nome') or '').strip()]

                # ── KPIs ──
                k1, k2, k3, k4 = st.columns(4)
                for col, rot, num, cor_kpi in [
                    (k1, 'Em aberto', len(ncs_abertas_all), '#D64545' if ncs_abertas_all else '#1E7A2A'),
                    (k2, 'Prazo vencido', len(ncs_vencidas_all), '#D64545' if ncs_vencidas_all else '#1E7A2A'),
                    (k3, 'Criticidade alta', len(ncs_alta_all), '#D64545' if ncs_alta_all else '#1E7A2A'),
                    (k4, 'Sem rastreio ao POP', len(ncs_sem_pop_all), '#D64545' if ncs_sem_pop_all else '#1E7A2A'),
                ]:
                    with col:
                        st.markdown(f"""
                        <div class="aud-card aud-kpi">
                            <div class="rot">{rot}</div>
                            <div class="num">{num}</div>
                            <div class="faixa"><i style="width:100%;background:{cor_kpi}"></i></div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── FILTROS NO PADRÃO DO HTML V2 ──
                fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.0, 1.35, 1.15, 1.15, 1.05, 1.25])
                with fc1:
                    f_status = st.selectbox(
                        "Status", ["Em aberto", "Prazo vencido", "Concluídas", "Todas"],
                        key="nc_v2_status",
                    )
                with fc2:
                    lojas_nc_map = {"Todas as lojas": "Todas"}
                    lojas_nc_map.update({
                        f"{loja} — {dict(LOJAS).get(loja, loja)}": loja
                        for loja in sorted({n['_loja'] for n in ncs_all if n.get('_loja')})
                    })
                    f_loja_rotulo = st.selectbox("Loja", list(lojas_nc_map), key="nc_v2_loja")
                    f_loja = lojas_nc_map[f_loja_rotulo]
                with fc3:
                    tipos_nc_presentes = {
                        _aud_txt(n.get('_tipo')) for n in ncs_all if _aud_txt(n.get('_tipo'))
                    }
                    tipos_nc_ordenados = (
                        [codigo for codigo in CHECKLISTS if codigo in tipos_nc_presentes]
                        + sorted(tipos_nc_presentes - set(CHECKLISTS))
                    )
                    tipos_nc_map = {"Todas as frentes": "Todas"}
                    tipos_nc_map.update({
                        f"{CHECKLISTS.get(codigo, {'nome': codigo})['nome']} — {codigo}": codigo
                        for codigo in tipos_nc_ordenados
                    })
                    if st.session_state.get("nc_v2_tipo") not in tipos_nc_map:
                        st.session_state.pop("nc_v2_tipo", None)
                    f_tipo_rotulo = st.selectbox("Frente", list(tipos_nc_map), key="nc_v2_tipo")
                    f_tipo = tipos_nc_map[f_tipo_rotulo]
                with fc4:
                    blocos_nc_map = {"Todos os blocos": "Todas"}
                    blocos_nc_map.update({f"{letra}. {nome}": letra for letra, nome in zip(LETRAS_BLOCO, SLOTS_CURTOS)})
                    f_bloco_rotulo = st.selectbox("Bloco", list(blocos_nc_map), key="nc_v2_bloco")
                    f_bloco = blocos_nc_map[f_bloco_rotulo]
                with fc5:
                    f_crit = st.selectbox("Criticidade", ["Toda criticidade", "Alta", "Média", "Baixa"], key="nc_v2_crit")
                with fc6:
                    f_pop = st.selectbox("Rastreio ao POP", ["Rastreio: todos", "Sem referência ao POP"], key="nc_v2_pop")

                ncs_filtradas = ncs_all
                if f_status == "Em aberto":
                    ncs_filtradas = [n for n in ncs_filtradas if (n.get('status') or 'Aberta') in {'Aberta', 'Em andamento'}]
                elif f_status == "Prazo vencido":
                    ncs_filtradas = [n for n in ncs_filtradas if vencida(n)]
                elif f_status == "Concluídas":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('status') == 'Concluída']
                if f_loja != "Todas":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('_loja') == f_loja]
                if f_tipo != "Todas":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('_tipo') == f_tipo]
                if f_bloco != "Todas":
                    ncs_filtradas = [
                        n for n in ncs_filtradas
                        if _aud_txt(n.get('codigo_item')).split('.', 1)[0] == str(LETRAS_BLOCO.index(f_bloco) + 1)
                    ]
                if f_crit != "Toda criticidade":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('criticidade') == f_crit]
                if f_pop == "Sem referência ao POP":
                    ncs_filtradas = [n for n in ncs_filtradas if not (n.get('pop_nome') or '').strip()]
                crit_ordem = {'Alta': 0, 'Média': 1, 'Baixa': 2}
                ncs_filtradas = sorted(ncs_filtradas, key=lambda n: str(n.get('_data') or ''), reverse=True)
                ncs_filtradas = sorted(ncs_filtradas, key=lambda n: crit_ordem.get(n.get('criticidade'), 9))

                st.markdown(
                    f'<div class="aud-nc-filtros"><span class="aud-nc-contagem">{len(ncs_filtradas)} registro(s)</span></div>',
                    unsafe_allow_html=True,
                )

                # ── EXPORTAR CSV DAS NCs FILTRADAS ──
                if ncs_filtradas:
                    df_export_nc = ncs_para_exportacao(ncs_filtradas)
                    st.download_button(
                        "📊 Exportar NCs filtradas (CSV)",
                        data=df_para_csv_br(df_export_nc),
                        file_name=f"nao_conformidades_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv", key="export_csv_ncs",
                    )

                @st.dialog("Atualizar não conformidade", width="medium")
                def _aud_nc_modal(nc_modal):
                    """Editor da NC em modal, sem expandir o card ou a página."""
                    status_atual = _aud_txt(nc_modal.get('status')) or 'Aberta'
                    status_opcoes = ['Aberta', 'Em andamento', 'Concluída', 'Cancelada']
                    prazo_atual = None
                    if nc_modal.get('prazo'):
                        try:
                            prazo_atual = datetime.strptime(nc_modal['prazo'], '%Y-%m-%d')
                        except Exception:
                            prazo_atual = None
                    st.caption(
                        f"{CHECKLISTS.get(nc_modal.get('_tipo'), {}).get('nome', nc_modal.get('_tipo'))} · "
                        f"Loja {nc_modal.get('_loja')} · Item {nc_modal.get('codigo_item') or '—'}"
                    )
                    crit_opcoes = ['Alta', 'Média', 'Baixa']
                    crit_atual = _aud_txt(nc_modal.get('criticidade')) or 'Média'
                    mcrit, mstatus = st.columns(2)
                    with mcrit:
                        nova_criticidade = st.selectbox(
                            "Criticidade", crit_opcoes,
                            index=crit_opcoes.index(crit_atual) if crit_atual in crit_opcoes else 1,
                            key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_crit",
                        )
                    with mstatus:
                        novo_status = st.selectbox(
                            "Status", status_opcoes,
                            index=status_opcoes.index(status_atual) if status_atual in status_opcoes else 0,
                            key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_status",
                        )

                    m1, m2 = st.columns(2)
                    with m1:
                        novo_resp = st.text_input(
                            "Responsável", value=nc_modal.get('responsavel', ''),
                            key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_resp",
                        )
                    with m2:
                        novo_prazo = st.date_input(
                            "Prazo", value=prazo_atual, format="DD/MM/YYYY",
                            key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_prazo",
                        )
                    nova_acao = st.text_area(
                        "Ação corretiva", value=nc_modal.get('acao_corretiva', ''), height=110,
                        key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_acao",
                    )
                    cancelar, salvar = st.columns(2)
                    with cancelar:
                        if st.button("Cancelar", use_container_width=True,
                                     key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_cancel"):
                            st.rerun()
                    with salvar:
                        salvar_modal = st.button(
                            "Salvar alteração", type="primary", use_container_width=True,
                            key=f"modal_{nc_modal['_auditoria_id']}_{nc_modal['_idx']}_save",
                        )
                    if salvar_modal:
                        aud_id = int(nc_modal['_auditoria_id'])
                        row_aud = df_auditorias[df_auditorias['id'] == aud_id]
                        if row_aud.empty:
                            st.error("Auditoria de origem não encontrada.")
                        else:
                            criticas_originais = row_aud.iloc[0]['criticas']
                            criticas_norm = [normalizar_critica(c) for c in criticas_originais]
                            idx_nc = nc_modal['_idx']
                            if idx_nc < len(criticas_norm):
                                criticas_norm[idx_nc]['status'] = novo_status
                                criticas_norm[idx_nc]['criticidade'] = nova_criticidade
                                criticas_norm[idx_nc]['responsavel'] = novo_resp.strip()
                                criticas_norm[idx_nc]['prazo'] = novo_prazo.strftime('%Y-%m-%d') if novo_prazo else ''
                                criticas_norm[idx_nc]['acao_corretiva'] = nova_acao.strip()
                                try:
                                    atualizar_auditoria(aud_id, criticas_norm)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {e}")

                # ── CARTÕES DETALHADOS NO PADRÃO DO HTML V2 ──
                for i, nc in enumerate(ncs_filtradas):
                    frente_nome = CHECKLISTS.get(nc.get('_tipo'), {}).get('nome', nc.get('_tipo'))
                    atrasada = vencida(nc)
                    cor_crit = {'Alta': '#D64545', 'Média': '#E8B23A', 'Baixa': '#728177'}.get(nc.get('criticidade'), '#728177')
                    nome_loja_nc = dict(LOJAS).get(nc.get('_loja'), '')
                    texto_nc = _aud_txt(nc.get('texto')) or 'Item não informado.'
                    codigo_item = _aud_txt(nc.get('codigo_item')) or '—'
                    if codigo_item == '—':
                        codigo_extraido = re.match(r'^\s*([0-9]+(?:\.[0-9]+)+)\s*[—-]\s*(.*)$', texto_nc)
                        if codigo_extraido:
                            codigo_item, texto_nc = codigo_extraido.group(1), codigo_extraido.group(2)
                    descricao_item = re.split(r'\s+\([0-9]+[.,][0-9]+/', texto_nc, maxsplit=1)[0].strip()
                    if codigo_item != '—':
                        descricao_item = re.sub(r'^' + re.escape(codigo_item) + r'\s*[—-]\s*', '', descricao_item).strip()
                    if '?' in descricao_item:
                        descricao_item = descricao_item.split('?', 1)[0].strip() + '?'
                    pct_match = re.search(r'(?:→|->|>)\s*([0-9]+[.,]?[0-9]*)\s*%', texto_nc)
                    nota_nc = pct_match.group(1).replace(',', '.') if pct_match else '—'
                    bloco_num = codigo_item.split('.', 1)[0] if codigo_item[:1].isdigit() else ''
                    bloco_idx = int(bloco_num) - 1 if bloco_num.isdigit() else -1
                    bloco_letra = LETRAS_BLOCO[bloco_idx] if 0 <= bloco_idx < len(LETRAS_BLOCO) else '—'
                    bloco_nome = SLOTS_CURTOS[bloco_idx] if 0 <= bloco_idx < len(SLOTS_CURTOS) else 'Bloco não informado'
                    pop_nome = _aud_txt(nc.get('pop_nome'))
                    pop_txt = pop_nome or 'POP de referência não informado'
                    pop_codigo = _aud_txt(nc.get('pop_codigo_2'))
                    if pop_codigo:
                        pop_txt = f"{pop_codigo} — {pop_txt}"
                    pop_ok = bool(pop_nome and _aud_txt(nc.get('ponto_pop')))
                    status = _aud_txt(nc.get('status')) or 'Aberta'
                    status_cor = {'Aberta': '#D64545', 'Em andamento': '#E8B23A', 'Concluída': '#1E7A2A', 'Cancelada': '#9aa89c'}.get(status, '#999')
                    impacto = nc.get('impacto_operacional') or []
                    if isinstance(impacto, str):
                        impacto = [impacto]
                    impacto_html = ''.join(f'<span class="aud-tag">{html_lib.escape(str(item))}</span>' for item in impacto)
                    resp = _aud_txt(nc.get('responsavel'))
                    resp_html = f'<span class="aud-tag">Resp.: {html_lib.escape(resp)}</span>' if resp else ''
                    prazo = data_br(nc.get('prazo'))
                    prazo_html = f'<span class="aud-tag{" alerta" if atrasada else ""}">Prazo {html_lib.escape(prazo)}</span>' if prazo else ''
                    vencido_html = '<span class="aud-tag alerta">prazo vencido</span>' if atrasada else ''
                    pop_class = 'aud-nc-pop' if pop_ok else 'aud-nc-pop faltando'
                    card_html = (
                        f'<div class="aud-nc-card"><div class="aud-nc-topo">'
                        f'<span class="aud-nc-ref">{html_lib.escape(codigo_item)}</span>'
                        f'<span class="aud-v2-selo" style="background:{CHECKLISTS.get(nc.get("_tipo"), {}).get("cor", "#728177")}">{html_lib.escape(str(frente_nome))}</span>'
                        f'<span class="aud-tag">Bloco {bloco_letra} · {html_lib.escape(str(bloco_nome))}</span>'
                        f'<span class="aud-tag">Nota {html_lib.escape(str(nota_nc))}</span>'
                        f'<span style="margin-left:auto;display:flex;gap:6px;align-items:center">'
                        f'<span class="aud-v2-status" style="background:{status_cor}">{html_lib.escape(status)}</span>{vencido_html}</span></div>'
                        f'<div style="font-weight:600;font-size:13.5px;margin-bottom:6px">{html_lib.escape(descricao_item or "Item não informado.")}</div>'
                        f'<div style="margin-bottom:8px"><span class="{pop_class}">{html_lib.escape(pop_txt)}</span></div>'
                        f'<div class="aud-nc-corpo">'
                        f'<div class="aud-nc-linha"><b>Ponto do POP:</b><span>{html_lib.escape(_aud_txt(nc.get("ponto_pop")) or "— não informado")}</span></div>'
                        f'<div class="aud-nc-linha"><b>Divergência:</b><span>{html_lib.escape(descricao_item or "Não informada.")}</span></div>'
                        f'<div class="aud-nc-linha"><b>Evidência:</b><span>{html_lib.escape(_aud_txt(nc.get("evidencia")) or "Não informada.")}</span></div>'
                        f'<div class="aud-nc-linha"><b>Ação corretiva:</b><span>{html_lib.escape(_aud_txt(nc.get("acao_corretiva")) or "Não informada.")}</span></div></div>'
                        f'<div class="aud-nc-rodape"><span class="aud-v2-selo" style="background:{cor_crit}">Criticidade {html_lib.escape(_aud_txt(nc.get("criticidade")) or "—")}</span>'
                        f'{impacto_html}<span class="aud-tag">{html_lib.escape("POP Ferreira" if pop_nome else "Sem rastreio")}</span>{resp_html}{prazo_html}'
                        f'<span class="aud-tag"><span class="aud-cod" style="font-size:12px">{html_lib.escape(str(nc.get("_loja") or "—"))}</span> {html_lib.escape(str(nome_loja_nc))} · {html_lib.escape(data_br(nc.get("_data")))}</span></div></div>'
                    )
                    _aud_render(card_html)

                    key_base = f"ncedit_{nc['_auditoria_id']}_{nc['_idx']}"
                    _, acao_nc = st.columns([5.8, 1.2])
                    with acao_nc:
                        if st.button("Alterar status", key=f"{key_base}_open", use_container_width=True):
                            _aud_nc_modal(nc)

                    # Mantém o trecho antigo no arquivo apenas como referência;
                    # o editor ativo é o modal acima.
                    if False:
                        ce1, ce2, ce3 = st.columns(3)
                        with ce1:
                            novo_status = st.selectbox(
                                "Status", ['Aberta', 'Em andamento', 'Concluída'],
                                index=['Aberta', 'Em andamento', 'Concluída', 'Cancelada'].index(status) if status in ['Aberta', 'Em andamento', 'Concluída', 'Cancelada'] else 0,
                                key=f"{key_base}_status",
                            )
                        with ce2:
                            novo_resp = st.text_input("Responsável", value=nc.get('responsavel', ''), key=f"{key_base}_resp")
                        with ce3:
                            prazo_atual = None
                            if nc.get('prazo'):
                                try:
                                    prazo_atual = datetime.strptime(nc['prazo'], '%Y-%m-%d')
                                except Exception:
                                    prazo_atual = None
                            novo_prazo = st.date_input("Prazo", value=prazo_atual, format="DD/MM/YYYY", key=f"{key_base}_prazo")
                        nova_acao = st.text_area("Ação corretiva", value=nc.get('acao_corretiva', ''), key=f"{key_base}_acao", height=70)
                        if st.button("💾 Salvar alterações", key=f"{key_base}_save"):
                            aud_id = int(nc['_auditoria_id'])
                            row_aud = df_auditorias[df_auditorias['id'] == aud_id]
                            if row_aud.empty:
                                st.error("Auditoria de origem não encontrada.")
                            else:
                                criticas_originais = row_aud.iloc[0]['criticas']
                                criticas_norm = [normalizar_critica(c) for c in criticas_originais]
                                idx_nc = nc['_idx']
                                if idx_nc < len(criticas_norm):
                                    criticas_norm[idx_nc]['status'] = novo_status
                                    criticas_norm[idx_nc]['responsavel'] = novo_resp.strip()
                                    criticas_norm[idx_nc]['prazo'] = novo_prazo.strftime('%Y-%m-%d') if novo_prazo else ''
                                    criticas_norm[idx_nc]['acao_corretiva'] = nova_acao.strip()
                                    try:
                                        atualizar_auditoria(aud_id, criticas_norm)
                                        st.success("Não conformidade atualizada.")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar: {e}")

                # O bloco legado abaixo fica desativado: os cartões acima já
                # exibem o conteúdo completo e mantêm a edição no expander.
                for i, nc in enumerate([]):
                    frente_nome = CHECKLISTS.get(nc.get('_tipo'), {}).get('nome', nc.get('_tipo'))
                    atrasada = vencida(nc)
                    cor_crit = {'Alta': '#D64545', 'Média': '#E8B23A', 'Baixa': '#728177'}.get(nc.get('criticidade'), '#728177')
                    nome_loja_nc = dict(LOJAS).get(nc.get('_loja'), '')
                    texto_nc = nc.get('texto') or ''
                    texto_curto = texto_nc if len(texto_nc) <= 70 else texto_nc[:69].rstrip() + '…'
                    titulo = f"[{nc.get('_loja')} — {nome_loja_nc}] {frente_nome} · {nc.get('codigo_item') or '—'} — {texto_curto}"
                    if atrasada:
                        titulo = "⚠ " + titulo

                    with st.expander(titulo, expanded=False):
                        st.markdown(f"**Frente:** {frente_nome} · **Loja:** {nc.get('_loja')} — {nome_loja_nc} · **Data da auditoria:** {data_br(nc.get('_data'))}")
                        st.markdown(nc.get('texto') or '')
                        pop_txt = nc.get('pop_nome') or '— sem vínculo —'
                        if nc.get('pop_codigo_2'):
                            pop_txt = f"{nc['pop_codigo_2']} — {pop_txt}"
                        if nc.get('ponto_pop'):
                            pop_txt += f" ({nc['ponto_pop']})"
                        st.caption(f"POP: {pop_txt}")

                        key_base = f"ncedit_{nc['_auditoria_id']}_{nc['_idx']}"
                        ce1, ce2, ce3 = st.columns(3)
                        with ce1:
                            novo_status = st.selectbox(
                                "Status", ['Aberta', 'Em andamento', 'Concluída'],
                                index=['Aberta', 'Em andamento', 'Concluída'].index(nc.get('status') or 'Aberta'),
                                key=f"{key_base}_status",
                            )
                        with ce2:
                            novo_resp = st.text_input("Responsável", value=nc.get('responsavel', ''), key=f"{key_base}_resp")
                        with ce3:
                            prazo_atual = None
                            if nc.get('prazo'):
                                try:
                                    prazo_atual = datetime.strptime(nc['prazo'], '%Y-%m-%d')
                                except Exception:
                                    prazo_atual = None
                            novo_prazo = st.date_input("Prazo", value=prazo_atual, format="DD/MM/YYYY", key=f"{key_base}_prazo")
                        nova_acao = st.text_area("Ação corretiva", value=nc.get('acao_corretiva', ''), key=f"{key_base}_acao", height=70)

                        if st.button("💾 Salvar alterações", key=f"{key_base}_save"):
                            aud_id = int(nc['_auditoria_id'])
                            row_aud = df_auditorias[df_auditorias['id'] == aud_id]
                            if row_aud.empty:
                                st.error("Auditoria de origem não encontrada.")
                            else:
                                criticas_originais = row_aud.iloc[0]['criticas']
                                criticas_norm = [normalizar_critica(c) for c in criticas_originais]
                                idx_nc = nc['_idx']
                                if idx_nc < len(criticas_norm):
                                    criticas_norm[idx_nc]['status'] = novo_status
                                    criticas_norm[idx_nc]['responsavel'] = novo_resp.strip()
                                    criticas_norm[idx_nc]['prazo'] = novo_prazo.strftime('%Y-%m-%d') if novo_prazo else ''
                                    criticas_norm[idx_nc]['acao_corretiva'] = nova_acao.strip()
                                    try:
                                        atualizar_auditoria(aud_id, criticas_norm)
                                        st.success("Não conformidade atualizada.")
                                        st.cache_data.clear()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 6 - HISTÓRICO
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[5]:
        st.markdown(cab_html(
            "Histórico de auditorias",
            "Todas as auditorias registradas.",
            "☰",
        ), unsafe_allow_html=True)
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            from datetime import datetime
            
            col1, col2 = st.columns(2)
            with col1:
                lojas_hist_map = {"Todas": "Todas"}
                lojas_hist_map.update({
                    f"{loja} — {dict(LOJAS).get(loja, loja)}": loja
                    for loja in sorted(df_auditorias['loja'].astype(str).unique().tolist())
                })
                loja_filtro_hist_rotulo = st.selectbox(
                    "Filtrar por Loja", list(lojas_hist_map), key="hist_loja_final"
                )
                loja_filtro_hist = lojas_hist_map[loja_filtro_hist_rotulo]
            with col2:
                tipo_filtro_hist = st.selectbox(
                    "Filtrar por Frente",
                    ["Todas"] + df_auditorias['tipo'].unique().tolist(),
                    key="hist_tipo_final"
                )
            
            df_hist = df_auditorias.copy()
            if loja_filtro_hist != "Todas":
                df_hist = df_hist[df_hist['loja'].astype(str) == str(loja_filtro_hist)]
            if tipo_filtro_hist != "Todas":
                df_hist = df_hist[df_hist['tipo'] == tipo_filtro_hist]
            
            # ── CRIA TABELA ESTILIZADA ──
            if not df_hist.empty:
                # Mapeamento de cores por tipo
                classes_tipo = {
                    'AÇO-AUD-01': 'badge-acougue',
                    'FRE-AUD-02': 'badge-frente',
                    'REC-AUD-03': 'badge-recebimento',
                    'ATA-AUD-04': 'badge-atacado',
                }
                cores_tipo = {
                    codigo: (config.get('nome', codigo), classes_tipo.get(codigo, 'badge-custom'))
                    for codigo, config in CHECKLISTS.items()
                }
                
                # Função para badge de nota
                def badge_nota(nota):
                    f = faixa(nota)
                    return f'<span class="badge-status" style="background:{f["hex"]};color:white">{f["rot"]}</span>'
                
                # Função para cor da nota
                def cor_nota(nota):
                    return faixa(nota)['hex']

                
                # Constrói a tabela HTML
                html_table = """
                <style>
                .historico-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.8rem;
                }
                .historico-table thead tr {
                    background: #0a3d1f;
                    position: sticky;
                    top: 0;
                    z-index: 2;
                }
                .historico-table thead th {
                    color: #9ecfb2;
                    font-weight: 700;
                    font-size: 0.66rem;
                    letter-spacing: 0.09em;
                    text-transform: uppercase;
                    padding: 0.8rem 0.8rem;
                    text-align: left;
                    border-bottom: 3px solid #f8c10a;
                    white-space: nowrap;
                }
                .historico-table thead th.center {
                    text-align: center;
                }
                .historico-table tbody tr {
                    border-bottom: 1px solid #e8f3ec;
                    transition: background 0.12s;
                }
                .historico-table tbody tr:hover {
                    background: #eaf7ef;
                }
                .historico-table tbody tr:nth-child(even) {
                    background: #f4fbf6;
                }
                .historico-table tbody tr:nth-child(even):hover {
                    background: #e2f4e8;
                }
                .historico-table tbody td {
                    padding: 0.65rem 0.8rem;
                    color: #0d2a16;
                    vertical-align: middle;
                    white-space: nowrap;
                    font-size: 0.8rem;
                }
                .historico-table tbody td.center {
                    text-align: center;
                }
                .badge-tipo {
                    display: inline-block;
                    padding: 2px 10px;
                    border-radius: 20px;
                    font-size: 0.6rem;
                    font-weight: 800;
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                    color: white;
                }
                .badge-acougue { background: #B0442E; }
                .badge-frente { background: #2E6BB0; }
                .badge-recebimento { background: #7A4EB0; }
                .badge-atacado { background: #C08A1E; }
                .badge-custom { background: #728177; }
                
                .badge-status {
                    display: inline-block;
                    padding: 2px 10px;
                    border-radius: 20px;
                    font-size: 0.6rem;
                    font-weight: 800;
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                }
                .badge-excelente { background: #1E7A2A; color: white; }
                .badge-bom { background: #5FB65B; color: white; }
                .badge-atencao { background: #E8B23A; color: #12331C; }
                .badge-risco { background: #E67E22; color: white; }
                .badge-critico { background: #D64545; color: white; }
                
                .nota-num {
                    font-family: 'Barlow Semi Condensed', sans-serif;
                    font-weight: 700;
                    font-size: 0.95rem;
                }
                .codigo-tipo {
                    font-size: 0.7rem;
                    color: #728177;
                    font-family: monospace;
                }
                </style>
                <div style="overflow-x:auto;max-height:56vh;overflow-y:auto;border:1px solid #DDE6DC;border-radius:12px;">
                <table class="historico-table">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Loja</th>
                            <th>Frente</th>
                            <th>Auditor</th>
                            <th class="center">A</th>
                            <th class="center">B</th>
                            <th class="center">C</th>
                            <th class="center">D</th>
                            <th class="center">E</th>
                            <th class="center">Score</th>
                            <th>Classificação</th>
                            <th class="center">NC</th>
                            <th class="center">Sem POP</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for _, row in df_hist.iterrows():
                    # Data
                    data_obj = pd.to_datetime(row['data'])
                    data_str = data_obj.strftime('%d/%m/%Y')
                    
                    # Loja
                    loja_str = f"{row['loja']} - {dict(LOJAS).get(row['loja'], '')}"
                    
                    # Frente e badge
                    tipo_info = cores_tipo.get(row['tipo'], ('', ''))
                    frente_nome = tipo_info[0]
                    badge_class = tipo_info[1]
                    frente_html = f'<span class="badge-tipo {badge_class}">{frente_nome}</span>' if badge_class else row['tipo']
                    
                    # Auditor
                    auditor_html = f'<td>{row.get("avaliador", "") or "—"}</td>'

                    # Não conformidades
                    criticas_linha = row['criticas'] if isinstance(row.get('criticas'), list) else []
                    criticas_norm_linha = [normalizar_critica(c) for c in criticas_linha]
                    n_ncs_linha = len(criticas_norm_linha)
                    if n_ncs_linha:
                        nc_html = f'<td class="center"><span class="badge-status badge-risco">{n_ncs_linha}</span></td>'
                    else:
                        nc_html = '<td class="center">—</td>'

                    # Não conformidades sem POP vinculado
                    n_sem_pop_linha = sum(1 for nc in criticas_norm_linha if not (nc.get('pop_nome') or '').strip())
                    if n_sem_pop_linha:
                        sem_pop_html = f'<td class="center"><span class="badge-status badge-critico" title="Não conformidades sem POP de referência vinculado">{n_sem_pop_linha}</span></td>'
                    else:
                        sem_pop_html = '<td class="center">—</td>'

                    # Tópicos
                    topicos_html = ""
                    if isinstance(row['topicos'], list):
                        for i in range(5):
                            pct = row['topicos'][i].get('pct', 0) if i < len(row['topicos']) else 0
                            cor = cor_nota(pct)
                            topicos_html += f'<td class="center" style="font-weight:600;color:{cor}">{pct:.2f}</td>'
                    else:
                        for _ in range(5):
                            topicos_html += '<td class="center">—</td>'
                    
                    # Nota
                    nota = row['total']
                    cor = cor_nota(nota)
                    nota_html = f'<td class="center"><span class="nota-num" style="color:{cor}">{nota:.2f}</span></td>'

                    # Classificação (mesma régua do Painel geral / Rankings)
                    f_class = faixa(nota)
                    classificacao_html = f'<td><span class="badge-status" style="background:{f_class["hex"]};color:white">{f_class["rot"]}</span></td>'

                    html_table += f"""
                        <tr>
                            <td>{data_str}</td>
                            <td>{loja_str}</td>
                            <td>{frente_html}</td>
                            {auditor_html}
                            {topicos_html}
                            {nota_html}
                            {classificacao_html}
                            {nc_html}
                            {sem_pop_html}
                        </tr>
                    """
                
                html_table += """
                    </tbody>
                </table>
                </div>
                """
                
                # ── RENDERIZA O HTML COM components ──
                # Piso alto o bastante para nunca cortar linhas visíveis mesmo com
                # poucos registros na tabela.
                altura_hist = min(700, max(220, 110 + 56 * len(df_hist)))
                st.components.v1.html(html_table, height=altura_hist, scrolling=True)

                st.caption(f"{len(df_hist)} registro(s) · {df_hist['loja'].nunique()} lojas auditadas")

                # ── LEGENDA DA CLASSIFICAÇÃO ──
                st.markdown(legenda_faixa_html(), unsafe_allow_html=True)

                # ── EXPORTAR HISTÓRICO ──
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    csv_hist = df_para_csv_br(auditorias_para_exportacao(df_hist))
                    st.download_button(
                        "📊 Exportar Histórico CSV",
                        data=csv_hist,
                        file_name=f"historico_auditorias_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    if st.button("🔄 Atualizar Histórico", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("Nenhum registro com os filtros selecionados.")

    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 7 - IMPORTAR PDF
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[6]:
        # ── CSS para file uploader, labels em negrito e espaçamento ajustado ──
        st.markdown("""
        <style>
        /* File Uploader - esconde TUDO e centraliza o texto */
        [data-testid="stFileUploaderDropzone"] {
            position: relative !important;
            border: 2px dashed #b8ddc7 !important;
            border-radius: 10px !important;
            background: #f4fbf6 !important;
            cursor: pointer !important;
            padding: 30px 20px !important;
            margin: 8px 0 !important;
            min-height: 100px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
        }
        [data-testid="stFileUploaderDropzone"] > * { display: none !important; }
        [data-testid="stFileUploaderDropzone"]::before {
            content: "Clique para selecionar o arquivo";
            display: block !important; width: 100% !important;
            text-align: center !important; color: #0d2a16 !important;
            font-size: 1rem !important; font-weight: 600 !important; margin-bottom: 8px !important;
        }
        [data-testid="stFileUploaderDropzone"]::after {
            content: "Limite de 200MB por arquivo • PDF";
            display: block !important; width: 100% !important;
            text-align: center !important; color: #728177 !important; font-size: 0.8rem !important;
        }
        [data-testid="stFileUploaderDropzone"]:hover { border-color: #1a8040 !important; background: #eaf7ef !important; }
        [data-testid="stFileUploaderDropzone"] [data-testid], [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] svg,
        [data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderFileName"],
        [data-testid="stFileUploaderSharedFileCard"], [data-testid="stFileUploaderFileDetails"],
        [data-testid="stFileUploaderFileMessage"], [data-testid="stFileUploaderFileSize"],
        [data-testid="stFileUploaderFileIcon"] { display: none !important; }

        /* ── LADO ESQUERDO: Loja, Frente, Data, Auditor (Espaçamento colado) ── */
        .label-destaque {
            font-size: 0.85rem !important;
            font-weight: 800 !important;
            color: #0d2a16 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: -40px !important;
            display: block !important;
        }
        
        /* ─ LADO DIREITO: Título "Resumo dos Tópicos" (Sem margem negativa) ── */
        .label-topicos {
            font-size: 0.85rem !important;
            font-weight: 800 !important;
            color: #0d2a16 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 0 !important;
            display: block !important;
        }

        /* ── LADO DIREITO: Puxa os inputs numéricos para cima dos nomes ─ */
        [data-testid="stNumberInput"] label {
            margin-bottom: 5px !important;
            padding-bottom: 0 !important;
        }

        /* Textarea maior */
        .stTextArea textarea { min-height: 240px !important; max-height: 400px !important; }
        
        /* Botão verde escuro */
        .stButton button {
            background-color: #0d6632 !important; color: white !important; border-color: #0d6632 !important;
        }
        .stButton button:hover {
            background-color: #0a4f27 !important; color: white !important; border-color: #0a4f27 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── ESCALA OFICIAL DE NÍVEIS 0-5 ──
        NIVEIS_ITEM = {
            0: 'Prática completamente ausente. Risco operacional imediato.',
            1: 'Existe alguma iniciativa sem formalização. Alta variabilidade.',
            2: 'Processo executado de forma incompleta e inconsistente.',
            3: 'Processo implementado com desvios frequentes.',
            4: 'Executado de forma consistente com falhas mínimas e sob controle.',
            5: 'Excelência, monitorado, sustentado e em evolução contínua.'
        }
        
        # ── Inicializa o estado do uploader ──
        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0
        
        # ── Função para extrair dados do PDF ──
        def extrair_dados_pdf(conteudo_pdf):
            import re
            
            dados = {
                'loja': '', 
                'data': '', 
                'hora': '', 
                'nota_total': 0.0,
                'tipo_detectado': '',
                'frente_nome': '',
                'topicos': [0.0, 0.0, 0.0, 0.0, 0.0],
                'topicos_possivel': [0.0, 0.0, 0.0, 0.0, 0.0],
                'topicos_obtido': [0.0, 0.0, 0.0, 0.0, 0.0],
                'topicos_nomes': ['', '', '', '', ''],
                'itens': [], 
                'criticas': [], 
                'observacoes': []
            }
            
            titulo_pdf = conteudo_pdf[:500].upper()
            
            if 'AÇOUGUE' in titulo_pdf:
                dados['tipo_detectado'] = 'AÇO-AUD-01'
            elif 'FRENTE DE LOJA' in titulo_pdf or 'FRENTEDELOJA' in titulo_pdf:
                dados['tipo_detectado'] = 'FRE-AUD-02'
            elif 'RECEBIMENTO' in titulo_pdf:
                dados['tipo_detectado'] = 'REC-AUD-03'
            elif 'ATACADO' in titulo_pdf:
                dados['tipo_detectado'] = 'ATA-AUD-04'
            else:
                dados['tipo_detectado'] = ''

            if dados['tipo_detectado'] in CHECKLISTS:
                dados['frente_nome'] = CHECKLISTS[dados['tipo_detectado']]['nome']
            else:
                # O título do relatório é a única origem aceita para descobrir
                # uma frente nova; não usamos nome de arquivo nem similaridade.
                cabecalho = re.search(
                    r'AVALIA.{0,40}PROCESSOS\s*[-–—:]\s*([^\n(]+?)\s*\(\s*INTERNO\s*\)',
                    conteudo_pdf[:1500], flags=re.IGNORECASE,
                )
                cabecalho = re.search(
                    r'(?:AVALIA|AUDITORIA).{0,40}PROCESSOS\s*[-:]\s*([^\n(]+?)\s*\(\s*INTERNO\s*\)',
                    conteudo_pdf[:1500], flags=re.IGNORECASE,
                ) or cabecalho
                cabecalho_flex = re.search(
                    r'(?:AVALIA|AUDITORIA).{0,40}PROCESSOS\s*(?:-|:|\u2013|\u2014)\s*([^\n(]+?)\s*\(\s*INTERNO\s*\)',
                    conteudo_pdf[:1500], flags=re.IGNORECASE,
                )
                if cabecalho_flex:
                    cabecalho = cabecalho_flex
                if cabecalho:
                    dados['frente_nome'] = re.sub(r'\s+', ' ', cabecalho.group(1)).strip(' -–—')
                    if dados['frente_nome']:
                        dados['tipo_detectado'] = _codigo_frente_flexivel(dados['frente_nome'])
            
            def resumir_descricao(descricao):
                d = descricao.strip()
                m = re.search(r'^.{20,}?\?', d)
                if m: return d[:m.end()].strip()
                if '?' in d: return d[:d.index('?') + 1].strip()
                m2 = re.search(r'^.{30,}?\.', d)
                if m2: return d[:m2.end()].strip()
                return (d[:150].rstrip() + '…') if len(d) > 150 else d
            
            # Teto do número de tópico válido (parte antes do ponto num código "N.N"):
            # lido do bloco de CRITÉRIOS/RESUMO na 1ª página (antes de qualquer rodapé
            # de página seguinte, então sempre íntegro). Usado logo abaixo para
            # separar corretamente o número de versão do código do próximo item, e
            # de novo mais adiante para filtrar códigos espúrios — sem fixar em 5/6,
            # o que quebraria em checklists futuros com mais ou menos tópicos.
            topicos_no_titulo = re.findall(r'\n\s*([1-9])\s*-\s*[A-ZÀ-Ú]', conteudo_pdf[:1500])
            topico_max = max((int(x) for x in topicos_no_titulo), default=6)

            # Remove o rodapé de cada página (4 linhas: "Desenvolvido por PariPassu® /
            # Material confidencial / <código> / Versão: X.X...X"). O número de versão
            # fica colado, sem separador, ao código do próximo item (ex.: "Versão:
            # 1.2611.4 - Todos os colaboradores..."), e o comprimento desse número
            # varia entre checklists — por isso não fixamos a quantidade de dígitos:
            # varremos a partir de cada posição até achar um código "N.N -" plausível
            # (N dentro do teto de tópicos conhecido) e preservamos só esse código.
            def _resolver_rodape(m):
                resto = m.group(1)
                # Varre todas as posições e guarda cada candidato plausível; o número
                # de versão em si também "parece" um código válido (ex.: em
                # "1.2611.4" o prefixo "1.261" passa no teste 1<=1<=6), então o código
                # real do item — sempre colado ao final da string — é o ÚLTIMO
                # candidato encontrado, não o primeiro.
                candidato = None
                for i in range(len(resto)):
                    cm = re.match(r'(\d{1,2})\.(\d{1,3})', resto[i:])
                    if cm and 1 <= int(cm.group(1)) <= topico_max:
                        candidato = resto[i:i + cm.end()]
                if candidato:
                    return ' ' + candidato + ' -'
                return ' -'  # nenhum código plausível: descarta a versão inteira

            texto = re.sub(
                r'Desenvolvido\s+por\s+PariPassu[^\n]*\n\s*Material\s+confidencial\s*\n\s*\d+\s*\n\s*'
                r'Vers[aã]o:\s*(\d[\d.]*)\s*-',
                _resolver_rodape, conteudo_pdf, flags=re.IGNORECASE
            )
            # Remove anexos de fotos ("Fotos das questões do tópico N ...") — eles
            # reimprimem a pergunta e a nota do item já processado (às vezes mais de
            # uma vez, uma por foto anexada), o que duplicava o item na extração.
            texto = re.sub(
                r'Fotos\s+das\s+quest[oõ]es\s+do\s+t[oó]pico.*?(?=\d[\.\d]*\s*♦|RESULTADOS|\Z)',
                '\n', texto, flags=re.IGNORECASE | re.DOTALL
            )
            texto = re.sub(r'\n\s*\d{1,2}\s*\n', '\n', texto)
            
            match_loja = re.search(r'Loja\s*(\d{1,2})\s*-\s*([^\n]+)', texto)
            if match_loja: dados['loja'] = match_loja.group(1).zfill(2)
            
            match_data = re.search(r'(\d{2})/(\d{2})/(\d{2})', texto)
            if match_data: dados['data'] = f"20{match_data.group(3)}-{match_data.group(2)}-{match_data.group(1)}"
            
            match_hora = re.search(r'(\d{2}):(\d{2}):(\d{2})', texto)
            if match_hora: dados['hora'] = f"{match_hora.group(1)}:{match_hora.group(2)}:{match_hora.group(3)}"
            
            match_nota = re.search(r'TOTAL\s+100[.,]00\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)\s*%', texto)
            if match_nota: dados['nota_total'] = float(match_nota.group(2).replace(',', '.'))
            
            bloco_resumo = re.search(r'RESUMO DOS TÓPICOS(.*?)RESULTADOS', texto, re.DOTALL | re.IGNORECASE)
            if bloco_resumo:
                bloco = bloco_resumo.group(1)
                matches_numeros = re.findall(r'(\d+[.,]\d+)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)\s*%', bloco)
                padrao_nomes = re.compile(r'([1-5])\s*-\s*(.*?)(?=\d+[.,]\d+\s+\d+[.,]\d+\s+\d+[.,]\d+\s*%)', re.DOTALL | re.IGNORECASE)
                matches_nomes = padrao_nomes.findall(bloco)
                
                for i in range(min(5, len(matches_numeros))):
                    dados['topicos_possivel'][i] = float(matches_numeros[i][0].replace(',', '.'))
                    dados['topicos_obtido'][i] = float(matches_numeros[i][1].replace(',', '.'))
                    dados['topicos'][i] = float(matches_numeros[i][2].replace(',', '.'))
                    if i < len(matches_nomes):
                        nome = matches_nomes[i][1].strip()
                        nome = re.sub(r'\s+', ' ', nome)
                        nome = re.sub(r'\d+[.,]?\d*\s*$', '', nome).strip()
                        dados['topicos_nomes'][i] = nome
            
            for i in range(5):
                if dados['topicos_nomes'][i]:
                    nome = re.sub(r'^\d+\s*[\.\-]\s*', '', dados['topicos_nomes'][i])
                    nome = re.sub(r'\s+', ' ', nome)
                    dados['topicos_nomes'][i] = nome.strip()
            
            padrao_obs = re.compile(r'Observa[çc][aã]o:\s*([^\n]+)', re.IGNORECASE)
            for match in padrao_obs.finditer(texto):
                obs = match.group(1).strip()
                if obs and len(obs) > 3: dados['observacoes'].append(obs)
            
            pos_result = re.search(r'RESULTADOS', texto, re.IGNORECASE)
            corpo = texto[pos_result.end():] if pos_result else texto
            padrao_nota_item = re.compile(r'\(\s*(\d+[.,]\d+)\s*/\s*(\d+[.,]\d+)\s*-\s*>\s*([\d.,]+)\s*%\s*\)')
            codigos = list(re.finditer(r'(\d+\.\d+)\s*-\s*', corpo))

            # Teto do número de tópico válido (parte antes do ponto, ex.: o "5" em
            # "5.3"): usa o maior tópico visto em RESUMO DOS TÓPICOS + margem para a
            # seção de assinatura, que sempre vem depois. Não fixamos em 5/6 porque
            # um checklist futuro pode ter mais ou menos tópicos que os atuais.
            topico_max = max((i + 1 for i, n in enumerate(dados['topicos_nomes']) if n), default=0)
            teto_topico = max(topico_max + 2, 20)

            for n, m in enumerate(codigos):
                inicio = m.end()
                fim = codigos[n + 1].start() if n + 1 < len(codigos) else len(corpo)
                chunk = corpo[inicio:fim]
                m_nota = padrao_nota_item.search(chunk)
                if not m_nota: continue

                codigo = m.group(1)

                # ── VALIDA O CÓDIGO ──
                # Descarta casamentos espúrios da regex genérica \d+\.\d+ (ex.:
                # números de página ou protocolo como "2642.9") que não são
                # códigos reais de item do checklist.
                partes = codigo.split('.')
                if len(partes) == 2:
                    try:
                        num_principal = int(partes[0])
                        num_secundario = int(partes[1])
                        if num_principal > teto_topico or num_secundario > 99:
                            continue  # Ignora códigos inválidos
                    except:
                        continue
                else:
                    continue  # Ignora códigos sem formato X.Y
                
                descricao = re.sub(r'\s+', ' ', chunk[:m_nota.start()]).strip()
                descricao_curta = resumir_descricao(descricao)
                obtido = float(m_nota.group(1).replace(',', '.'))
                possivel = float(m_nota.group(2).replace(',', '.'))
                pct = float(m_nota.group(3).replace(',', '.'))
                
                resto = chunk[m_nota.end():]
                nivel_num = None; nivel_txt = ''; obs_item = ''; linhas_nivel = []
                
                for ln in resto.split('\n'):
                    s = ln.strip()
                    if not s: continue
                    if '♦' in s: break
                    # Rodapé de página sem código de item plausível depois dele (ex.:
                    # o último item do documento, antes da seção de assinatura) não é
                    # removido no pré-processamento — corta aqui para não grudar no
                    # texto do nível.
                    if re.match(r'Desenvolvido\s+por\s+PariPassu', s, re.IGNORECASE): break
                    if re.match(r'Observa[çc][aã]o', s, re.IGNORECASE):
                        obs_item = re.sub(r'^Observa[çc][aã]o:\s*', '', s, flags=re.IGNORECASE).strip()
                        break
                    if linhas_nivel or re.match(r'\d\s*-\s*', s): linhas_nivel.append(s)
                    else: break
                
                if linhas_nivel:
                    nivel_bruto = ' '.join(linhas_nivel)
                    mn = re.match(r'(\d)\s*-\s*(.*)', nivel_bruto)
                    if mn:
                        nivel_num = int(mn.group(1))
                        nivel_txt = re.sub(r'\s+', ' ', mn.group(2)).strip()
                
                # Só usa o texto genérico da escala 0-5 como fallback: algumas seções
                # do checklist (ex.: "Estrutura Física") usam uma escala descritiva
                # própria (ex.: "2 - Muitas não conformidades") que não deve ser
                # sobrescrita pelo texto padrão das demais seções.
                if not nivel_txt and nivel_num is not None and nivel_num in NIVEIS_ITEM:
                    nivel_txt = NIVEIS_ITEM[nivel_num]
                
                item = {'codigo': codigo, 'descricao': descricao, 'descricao_curta': descricao_curta, 'obtido': obtido, 'possivel': possivel, 'pct': pct, 'nivel': nivel_num, 'nivel_txt': nivel_txt, 'observacao': obs_item}
                dados['itens'].append(item)
            
            return dados
        
        st.markdown(cab_html(
            "Importar PDF",
            "Envie o relatório de auditoria em PDF para extrair loja, notas e não conformidades automaticamente.",
            "⭳",
        ), unsafe_allow_html=True)

        # ── Upload do PDF com key dinâmica ──
        uploaded_file = st.file_uploader(
            "PDF da auditoria",
            type=['pdf'], 
            label_visibility="collapsed", 
            key=f"pdf_uploader_{st.session_state.uploader_key}"
        )
        
        if uploaded_file:
            st.success(f"Arquivo carregado: **{uploaded_file.name}**")
            
            # ── Verifica se PyPDF2 está instalado ──
            try:
                import PyPDF2
            except ImportError:
                st.error("Biblioteca PyPDF2 não instalada. Execute: `pip install PyPDF2`")
                st.stop()
            
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                texto_completo = ""
                for page in pdf_reader.pages: 
                    texto_completo += page.extract_text() or ""
                
                if not texto_completo.strip():
                    st.warning("Não foi possível extrair texto do PDF. Verifique se o PDF não está escaneado.")
                    texto_completo = ""
                
                dados_extraidos = extrair_dados_pdf(texto_completo)
                
                st.markdown("---")
                st.markdown("### Dados extraídos — confirme antes de salvar")
                
                # ── CAMPOS DO FORMULÁRIO (sem st.form para evitar Enter salvar) ──
                col1, col2 = st.columns(2)
                
                with col1:
                    loja_opts = [f"{l[0]} - {l[1]}" for l in LOJAS]
                    loja_default = next((l for l in loja_opts if l.startswith(dados_extraidos['loja'])), loja_opts[0])
                    
                    st.markdown('<span class="label-destaque">Loja</span>', unsafe_allow_html=True)
                    loja = st.selectbox("Loja", loja_opts, index=loja_opts.index(loja_default) if loja_default in loja_opts else 0, key="import_loja", label_visibility="hidden")
                    
                    tipo_default = dados_extraidos.get('tipo_detectado') or ''
                    frente_detectada = dados_extraidos.get('frente_nome') or ''
                    if tipo_default and tipo_default not in CHECKLISTS:
                        tipo_default = _registrar_checklist_flexivel(
                            frente_detectada or tipo_default,
                            codigo=tipo_default,
                            slots=dados_extraidos.get('topicos_nomes'),
                        )

                    st.markdown('<span class="label-destaque">Frente</span>', unsafe_allow_html=True)
                    if not tipo_default:
                        frente_informada = st.text_input(
                            "Nome da frente/setor",
                            value=frente_detectada,
                            key="import_frente_nome",
                            placeholder="Ex.: Segurança Alimentar",
                        ).strip()
                        if frente_informada:
                            tipo_default = _registrar_checklist_flexivel(
                                frente_informada,
                                slots=dados_extraidos.get('topicos_nomes'),
                            )
                            dados_extraidos['tipo_detectado'] = tipo_default
                            dados_extraidos['frente_nome'] = frente_informada

                    tipos_import_map = {
                        f"{config['nome']} — {codigo}": codigo
                        for codigo, config in CHECKLISTS.items()
                    }
                    if not tipo_default:
                        tipos_import_map = {
                            "Frente não identificada — informe acima": None,
                            **tipos_import_map,
                        }
                    tipo_default_rotulo = next(
                        (rotulo for rotulo, codigo in tipos_import_map.items() if codigo == tipo_default),
                        next(iter(tipos_import_map)),
                    )
                    tipo_import_rotulo = st.selectbox(
                        "Frente", list(tipos_import_map),
                        index=list(tipos_import_map).index(tipo_default_rotulo),
                        key="import_tipo",
                        label_visibility="hidden"
                    )
                    tipo = tipos_import_map[tipo_import_rotulo]
                    
                    from datetime import datetime
                    if dados_extraidos['data']:
                        try: 
                            data_obj = datetime.strptime(dados_extraidos['data'], '%Y-%m-%d')
                            data_default_str = data_obj.strftime('%d/%m/%Y')
                        except: 
                            data_default_str = datetime.now().strftime('%d/%m/%Y')
                    else: 
                        data_default_str = datetime.now().strftime('%d/%m/%Y')
                    
                    st.markdown('<span class="label-destaque">Data</span>', unsafe_allow_html=True)
                    data_audit_str = st.text_input("Data", value=data_default_str, key="import_data", help="Digite a data no formato DD/MM/AAAA", label_visibility="hidden")
                    
                    try: 
                        data_audit = datetime.strptime(data_audit_str, '%d/%m/%Y')
                    except ValueError: 
                        st.error("Formato de data inválido. Use DD/MM/AAAA")
                        data_audit = None
                    
                    st.markdown('<span class="label-destaque">Auditor</span>', unsafe_allow_html=True)
                    avaliador = st.text_input("Auditor", value="Auditor Controladoria", key="import_avaliador", label_visibility="hidden")
                    
                    if dados_extraidos['nota_total'] > 0: 
                        st.caption(f"Nota total extraída: **{dados_extraidos['nota_total']:.2f}%**")
                
                with col2:
                    st.markdown('<span class="label-topicos">Resumo dos Tópicos</span>', unsafe_allow_html=True)
                    pcts = []
                    slots = CHECKLISTS.get(tipo, {'slots': SLOTS_CURTOS})['slots']
                    
                    for i in range(5):
                        nome_pdf = ""
                        if i < len(dados_extraidos['topicos_nomes']) and dados_extraidos['topicos_nomes'][i]: 
                            nome_pdf = dados_extraidos['topicos_nomes'][i]
                        
                        valor_padrao = dados_extraidos['topicos'][i] if i < len(dados_extraidos['topicos']) and dados_extraidos['topicos'][i] > 0 else 0.0
                        obtido = dados_extraidos['topicos_obtido'][i] if i < len(dados_extraidos['topicos_obtido']) else 0.0
                        possivel = dados_extraidos['topicos_possivel'][i] if i < len(dados_extraidos['topicos_possivel']) else 0.0
                        
                        if nome_pdf and valor_padrao > 0: 
                            label = f"{i+1}. {nome_pdf} — {obtido:.2f}/{possivel:.2f} ({valor_padrao:.1f}%)"
                        elif nome_pdf: 
                            label = f"{i+1}. {nome_pdf} (não detectado)"
                        else: 
                            label = f"{i+1}. {slots[i]} (não detectado - {valor_padrao:.1f}%)"
                        
                        pct = st.number_input(label, min_value=0.0, max_value=100.0, value=float(valor_padrao), step=0.5, key=f"pct_import_{i}")
                        pcts.append(pct)
                
                # ── POP-BASE DA AUDITORIA ──
                # O checklist inteiro avalia um POP só; o que muda por item é o ponto
                # interno (seção, anexo, página).
                try:
                    df_pops_todos = load()
                except Exception:
                    df_pops_todos = pd.DataFrame()

                st.markdown(
                    '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
                    'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
                    'POP avaliado por este checklist — vínculo obrigatório</div>',
                    unsafe_allow_html=True,
                )
                # Frentes conhecidas recebem o POP-base cadastrado como sugestão,
                # mas o auditor pode escolher explicitamente outro POP legível.
                # Frentes novas também usam a lista completa, sem seleção automática.
                pop_base_cadastrado = pop_base_da_frente(df_pops_todos, tipo)
                # Known fronts suggest the configured base POP, but the auditor
                # may explicitly choose another readable POP. New fronts also
                # use this list, with no automatic first-item selection.
                pops_importacao = _pops_com_pdf(df_pops_todos)
                pop_opcoes = {'— selecione o POP com PDF vinculado —': None}
                pop_por_rotulo = {}
                for pop in pops_importacao:
                    rotulo = pop['rotulo']
                    if rotulo in pop_opcoes:
                        rotulo = f"{rotulo} · ID {pop['id']}"
                    pop_opcoes[rotulo] = pop
                    pop_por_rotulo[rotulo] = pop

                rotulo_sugerido = next(iter(pop_opcoes))
                if pop_base_cadastrado is not None:
                    pop_base_padrao = next(
                        (pop for pop in pops_importacao
                         if str(pop.get('id')) == str(pop_base_cadastrado.get('id'))),
                        None,
                    )
                    if pop_base_padrao:
                        rotulo_sugerido = next(
                            (rotulo for rotulo, pop in pop_por_rotulo.items()
                             if pop is pop_base_padrao),
                            rotulo_sugerido,
                        )
                opcoes_pop_lista = list(pop_opcoes)
                escolha_base = st.selectbox(
                    "POP de referência", opcoes_pop_lista,
                    index=opcoes_pop_lista.index(rotulo_sugerido),
                    key=f"import_pop_base_{tipo or 'sem-frente'}", label_visibility="collapsed",
                )
                pop_escolhido = pop_por_rotulo.get(escolha_base)
                if pop_escolhido:
                    pop_base_id = pop_escolhido['id']
                    pop_base_nome = pop_escolhido['nome']
                    pop_base_cod = pop_escolhido['codigo']
                    pop_base_link = pop_escolhido['link']
                    st.success(f"**{pop_base_cod or 'POP'}** — {pop_base_nome}")
                    st.caption(
                        "Este documento será lido página a página e usado para rastrear "
                        "cada item do checklist. A seleção é explícita e fica registrada na auditoria."
                    )
                    pop_preview = drive_preview(pop_base_link)
                    if pop_preview:
                        st.link_button("Abrir / visualizar POP vinculado", pop_preview)
                else:
                    pop_base_id, pop_base_nome, pop_base_cod, pop_base_link = None, '', '', ''
                    if pop_base_cadastrado is not None and not pops_importacao:
                        pop_cod_sem_pdf = str(pop_base_cadastrado.get('codigo_2') or '').strip()
                        pop_nome_sem_pdf = str(pop_base_cadastrado.get('processo') or '').strip()
                        st.warning(
                            f"O POP-base desta frente ({pop_cod_sem_pdf} — {pop_nome_sem_pdf}) "
                            "está cadastrado, mas não possui PDF vinculado e não pode ser auditado."
                        )
                    elif not pops_importacao:
                        st.error(
                            "Nenhum POP-base está configurado para esta frente. Cadastre e vincule "
                            "o documento correspondente antes de importar o checklist."
                        )

                # Nenhuma etapa de auditoria é montada antes de o POP ser
                # selecionado e lido com sucesso. O checklist pode ser exibido,
                # mas não gera pontos críticos nem editores de NC sem documento.
                    elif tipo:
                        st.info(
                            "Selecione manualmente o POP correspondente. O sistema nao usa nome, "
                            "palavras semelhantes ou o primeiro documento da lista para criar o vinculo."
                        )

                paginas_pop = _texto_pop_por_pagina(pop_base_link) if pop_base_link else []
                pop_texto_lido = bool(
                    paginas_pop and any(str(pagina or '').strip() for pagina in paginas_pop)
                )
                analises_pop = []
                itens_sem_evidencia_textual = []
                criticas_estruturadas = []
                limite_nivel_nc = None

                if not pop_base_link:
                    st.error(
                        "A importação só pode ser concluída com um POP selecionado e vinculado a um PDF. "
                        "O checklist foi lido, mas permanece em revisão."
                    )
                elif not pop_texto_lido:
                    st.error(
                        "O PDF do POP foi selecionado, mas não pôde ser lido. Verifique se o link é público, "
                        "se aponta para um PDF e tente novamente antes de salvar."
                    )
                else:
                    st.success(
                        f"POP confrontado: {len(paginas_pop)} página(s) lida(s) · "
                        f"{len(dados_extraidos['itens'])} item(ns) prontos para auditoria automática."
                    )
                    limite_nivel_nc = st.selectbox(
                        "Gerar não conformidade para itens com nota até",
                        options=[2, 3, 4],
                        index=1,
                        format_func=lambda nivel: str(nivel),
                        key="import_limite_nc",
                    )

                    def item_critico_importacao(item):
                        nivel = item.get('nivel')
                        # A elegibilidade segue somente a régua explícita do checklist,
                        # como no HTML v2. Percentual não substitui nota ausente.
                        return nivel is not None and int(nivel) <= limite_nivel_nc

                    st.markdown(
                        '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
                        'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
                        'Pontos de atenção sinalizados pelo checklist</div>'
                        '<div style="font-size:.8rem;color:#728177;margin:.2rem 0 .6rem;">'
                        'Itens até a nota selecionada viram não conformidade preliminar. A criticidade, a evidência do '
                        'POP, o responsável e o prazo devem ser confirmados pela equipe.</div>',
                        unsafe_allow_html=True,
                    )

                    # ── CONFRONTO ITEM A ITEM COM O TEXTO DO POP ──
                    for item in dados_extraidos['itens']:
                        confronto = confrontar_item_com_pop(item, paginas_pop)
                        item['_confronto_pop'] = confronto
                        analises_pop.append((item, confronto))
                    itens_sem_evidencia_textual = [
                        (item, confronto) for item, confronto in analises_pop
                        if confronto['status'] == 'POP associado ao checklist'
                    ]

                    pontos_atencao = [
                        (item, confronto) for item, confronto in analises_pop
                        if item_critico_importacao(item)
                    ]
                    itens_sem_nota_regua = [
                        item for item in dados_extraidos['itens']
                        if item.get('nivel') is None
                    ]
                    if itens_sem_nota_regua:
                        st.info(
                            f"{len(itens_sem_nota_regua)} item(ns) sem nota explícita da régua do checklist "
                            "não foram convertidos automaticamente em não conformidade."
                        )
                    with st.expander(
                        f"Pontos críticos encontrados ({len(pontos_atencao)} item(ns))",
                        expanded=True,
                    ):
                        st.caption(
                            f"São exibidos somente os itens com nota até {limite_nivel_nc} no checklist importado."
                        )
                        if pontos_atencao:
                            st.dataframe(
                                pd.DataFrame([{
                                    'Item': item.get('codigo', '—'),
                                    'Nota': item.get('nivel', '—'),
                                    'Nota %': round(float(item.get('pct') or 0), 1),
                                    'Criticidade': _criticidade_item(item),
                                    'Ponto crítico': item.get('descricao_curta') or item.get('descricao', '—'),
                                    'Referência POP': confronto['referencia'],
                                } for item, confronto in pontos_atencao]),
                                use_container_width=True, hide_index=True,
                            )
                        else:
                            st.success("Nenhum ponto crítico encontrado.")

                    itens_criticos = [i for i in dados_extraidos['itens'] if item_critico_importacao(i)]

                    if not itens_criticos:
                        st.success(f"Nenhum item com nota até {limite_nivel_nc} neste PDF.")
                    else:
                        for item in itens_criticos:
                            nc_auto = auditar_item_automaticamente(
                                item, tipo, data_audit,
                                pop_nome=pop_base_nome, pop_link=pop_base_link,
                            )
                            confronto = item.get('_confronto_pop') or {}
                            if confronto:
                                nc_auto['ponto_pop'] = confronto.get('referencia') or nc_auto.get('ponto_pop', '')
                                nc_auto['confianca'] = confronto.get('confianca')
                                nc_auto['pop_status'] = confronto.get('status')
                                nc_auto['pop_match_score'] = confronto.get('pontuacao', 0)
                                nc_auto['pop_pagina'] = confronto.get('pagina', '')
                                nc_auto['pop_termos_comuns'] = confronto.get('termos_comuns', [])
                            nc_auto.update({
                                'pop_id': pop_base_id,
                                'pop_nome': pop_base_nome,
                                'pop_codigo_2': pop_base_cod,
                                'pop_link': pop_base_link,
                            })
                            criticas_estruturadas.append(nc_auto)

                        # Os itens já ficam prontos para gravação com os campos
                        # derivados da auditoria e do POP. Responsável, prazo e
                        # tratativa são ajustados depois na subaba Não conformidades,
                        # como no fluxo do HTML v2; não abrir um editor gigante aqui.

                st.markdown("---")
                
                if pcts:
                    total_nota = sum(POSSIVEL[i] * pcts[i] / 100 for i in range(5))
                    f = faixa(total_nota)
                    st.markdown(f"""
                    <div style="background:{f['cor']}15;border:2px solid {f['cor']};border-radius:8px;padding:12px 20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;">Nota total calculada</span>
                        <span style="font-size:24px;font-weight:700;color:{f['cor']}">{total_nota:.2f}% — {f['rot']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    nota_pdf = dados_extraidos.get('nota_total', 0)
                    if nota_pdf > 0:
                        diverge = abs(nota_pdf - total_nota) > 0.5
                        if diverge:
                            st.warning(
                                f"⚠️ A nota recalculada ({total_nota:.2f}%) diverge da nota total "
                                f"impressa no PDF ({nota_pdf:.2f}%) — revise os tópicos antes de salvar."
                            )
                        else:
                            st.caption(f"✓ Confere com a nota total impressa no PDF ({nota_pdf:.2f}%).")
                
                # ── BOTÃO ÚNICO (Enter NÃO salva) ──
                # ── Auditoria já existente para essa loja+frente+data? ──
                # inserir_auditoria() sempre faz INSERT puro; sem essa checagem,
                # importar o mesmo PDF duas vezes cria dois registros e as médias
                # do Painel Geral/Rankings passam a contar a auditoria em dobro.
                existente_pdf = None
                if loja and tipo and data_audit:
                    try:
                        existente_pdf = buscar_auditoria_existente(
                            loja.split(' - ')[0], tipo, data_audit.strftime('%Y-%m-%d')
                        )
                    except Exception:
                        existente_pdf = None

                if existente_pdf:
                    st.warning(
                        f"⚠️ Já existe uma auditoria salva para esta loja, frente e data "
                        f"(nota atual: {existente_pdf['total']:.2f}%). Salvar de novo vai "
                        f"**substituir** o registro existente."
                    )

                if st.button(
                    "Substituir auditoria existente" if existente_pdf else "Salvar auditoria",
                    use_container_width=True, type="primary", key="btn_salvar_pdf",
                    disabled=not (pop_base_id and pop_base_link and pop_texto_lido),
                ):
                    if not loja or not tipo or not data_audit:
                        st.error("Preencha todos os campos obrigatórios.")
                    elif any(p < 0 or p > 100 for p in pcts):
                        st.error("As notas devem estar entre 0 e 100.")
                    elif not pop_base_id or not pop_base_link or not pop_texto_lido:
                        st.error(
                            "Não é possível salvar: selecione um POP com PDF acessível e aguarde o "
                            "confronto item a item terminar."
                        )
                    elif not dados_extraidos['itens']:
                        st.error("Não é possível salvar: nenhum ponto do checklist foi lido no PDF.")
                    else:
                        cod_loja = loja.split(' - ')[0]
                        # Salva exclusivamente as NCs elegíveis pela régua da nota
                        # selecionada; não há entrada textual livre que possa criar
                        # divergência entre a importação e as demais subabas.
                        criticas_list = criticas_estruturadas
                        topicos_importados = [
                            {
                                'nome': CHECKLISTS[tipo]['slots'][i],
                                'possivel': POSSIVEL[i],
                                'pct': pcts[i],
                                'pop_id': pop_base_id,
                                'pop_codigo_2': pop_base_cod,
                                'pop_nome': pop_base_nome,
                                'pop_link': pop_base_link,
                                'pop_paginas_lidas': len(paginas_pop),
                                'pop_limite_nivel_nc': limite_nivel_nc,
                                'pop_itens_com_evidencia': len(analises_pop) - len(itens_sem_evidencia_textual),
                                'pop_itens_sem_evidencia_textual': len(itens_sem_evidencia_textual),
                            }
                            for i in range(5)
                        ]
                        dados_para_salvar = {
                            'loja': cod_loja,
                            'data': data_audit.strftime('%Y-%m-%d'),
                            'tipo': tipo,
                            'avaliador': avaliador,
                            'topicos': topicos_importados,
                            'total': total_nota,
                            'criticas': criticas_list
                        }
                        try:
                            if existente_pdf:
                                deletar_auditoria(int(existente_pdf['id']))
                            inserir_auditoria(dados_para_salvar)
                            msg = "🔄 Auditoria substituída" if existente_pdf else "✅ Auditoria salva"
                            st.success(f"{msg} com sucesso! Loja {cod_loja} - {CHECKLISTS[tipo]['nome']}")
                            st.cache_data.clear()

                            # ── INCREMENTA A KEY PARA RESETAR O UPLOADER ──
                            st.session_state.uploader_key += 1

                            import time
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco: {e}")
            
            except Exception as e:
                st.error(f"Erro ao processar PDF: {e}")
                st.stop()
                    
    
    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 8 - LANÇAR MANUAL
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[7]:
        # ── CSS específico para ABA 8 ──
        st.markdown("""
        <style>
        /* ── LABELS EM DESTAQUE ── */
        .label-destaque {
            font-size: 0.85rem !important;
            font-weight: 800 !important;
            color: #0d2a16 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: -40px !important;
            display: block !important;
        }
        .label-topicos {
            font-size: 0.85rem !important;
            font-weight: 800 !important;
            color: #0d2a16 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 0 !important;
            display: block !important;
        }
        
        /* ── TEXTAREA ── */
        .stTextArea textarea { 
            min-height: 240px !important; 
            max-height: 400px !important; 
        }
        
        /* ── BOTÃO VERDE ESCURO ── */
        .stButton button {
            background-color: #0d6632 !important; 
            color: white !important; 
            border-color: #0d6632 !important;
        }
        .stButton button:hover {
            background-color: #0a4f27 !important; 
            color: white !important; 
            border-color: #0a4f27 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(cab_html(
            "Lançar auditoria manual",
            "Registre manualmente as notas e as tratativas; o POP-base da frente continua obrigatório e precisa ser legível.",
            "＋",
        ), unsafe_allow_html=True)

        # ── Inicializa o estado para controle de reset ──
        if "manual_reset" not in st.session_state:
            st.session_state.manual_reset = False

        # ── WIDGETS (sem form para evitar Enter salvar) ──
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<span class="label-destaque">Loja</span>', unsafe_allow_html=True)
            loja = st.selectbox("Loja", [f"{l[0]} - {l[1]}" for l in LOJAS], key="manual_loja", label_visibility="hidden")
            
            st.markdown('<span class="label-destaque">Frente</span>', unsafe_allow_html=True)
            tipos_manuais = {
                f"{config['nome']} — {codigo}": codigo
                for codigo, config in CHECKLISTS.items()
            }
            tipos_manuais["Nova frente/setor — informar"] = None
            tipo_rotulo = st.selectbox(
                "Frente",
                list(tipos_manuais),
                key="manual_tipo",
                label_visibility="hidden"
            )
            tipo = tipos_manuais[tipo_rotulo]
            if tipo is None:
                nome_frente_manual = st.text_input(
                    "Nome da nova frente/setor",
                    key="manual_frente_nome",
                    placeholder="Ex.: Segurança Alimentar",
                ).strip()
                if nome_frente_manual:
                    tipo = _registrar_checklist_flexivel(nome_frente_manual)
            
            from datetime import datetime
            data_default_str = datetime.now().strftime('%d/%m/%Y')
            
            st.markdown('<span class="label-destaque">Data</span>', unsafe_allow_html=True)
            data_audit_str = st.text_input(
                "Data",
                value=data_default_str, 
                key="manual_data",
                help="Digite a data no formato DD/MM/AAAA",
                label_visibility="hidden"
            )
            
            st.markdown('<span class="label-destaque">Auditor</span>', unsafe_allow_html=True)
            avaliador = st.text_input("Auditor", value="Auditor Controladoria", key="manual_avaliador", label_visibility="hidden")
        
        with col2:
            st.markdown('<span class="label-topicos">Resumo dos Tópicos</span>', unsafe_allow_html=True)
            pcts = []
            for i, slot in enumerate(CHECKLISTS.get(tipo, {'slots': SLOTS_CURTOS})['slots']):
                pct = st.number_input(
                    f"{i+1}. {slot}",
                    min_value=0.0, max_value=100.0,
                    value=70.0, step=0.5,
                    key=f"pct_manual_{i}"
                )
                pcts.append(pct)
        
        # ── POP-BASE DA AUDITORIA ──
        try:
            df_pops_manual = load()
        except Exception:
            df_pops_manual = pd.DataFrame()

        pop_base_cadastrado_m = pop_base_da_frente(df_pops_manual, tipo)
        pop_base_m = pop_base_cadastrado_m
        pops_manuais = _pops_com_pdf(df_pops_manual)
        pop_m_opcoes = {'— selecione o POP com PDF vinculado —': None}
        pop_m_por_rotulo = {}
        for pop in pops_manuais:
            rotulo = pop['rotulo']
            if rotulo in pop_m_opcoes:
                rotulo = f"{rotulo} · ID {pop['id']}"
            pop_m_opcoes[rotulo] = pop
            pop_m_por_rotulo[rotulo] = pop
        rotulo_m_default = next(iter(pop_m_opcoes))
        if pop_base_m is not None:
            pop_m_padrao = next(
                (pop for pop in pops_manuais
                 if str(pop.get('id')) == str(pop_base_m.get('id'))),
                None,
            )
            if pop_m_padrao:
                rotulo_m_default = next(
                    (rotulo for rotulo, pop in pop_m_por_rotulo.items()
                     if pop is pop_m_padrao),
                    rotulo_m_default,
                )
        escolha_pop_manual = st.selectbox(
            "POP de referencia", list(pop_m_opcoes),
            index=list(pop_m_opcoes).index(rotulo_m_default),
            key=f"manual_pop_base_{tipo or 'sem-frente'}", label_visibility="collapsed",
        )
        pop_m_escolhido = pop_m_por_rotulo.get(escolha_pop_manual)
        if pop_m_escolhido:
            # Normaliza o registro da lista para o formato usado no restante
            # do fluxo manual, sem alterar o cadastro da aba Processos.
            pop_base_m = {
                'id': pop_m_escolhido.get('id'),
                'processo': pop_m_escolhido.get('nome', ''),
                'codigo_2': pop_m_escolhido.get('codigo', ''),
                'link_documento': pop_m_escolhido.get('link', ''),
            }
        else:
            pop_base_m = None
        st.markdown(
            '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
            'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
            'POP avaliado por este checklist</div>',
            unsafe_allow_html=True,
        )
        pop_m_id, pop_m_nome, pop_m_cod, pop_m_link = None, '', '', ''
        paginas_pop_manual = []
        pop_texto_lido_manual = False
        if pop_base_m is not None:
            pop_m_id = pop_base_m.get('id')
            pop_m_nome = str(pop_base_m.get('processo', '')).strip()
            pop_m_cod = str(pop_base_m.get('codigo_2', '')).strip()
            pop_m_link = str(pop_base_m.get('link_documento') or '').strip()
            st.success(f"**{pop_m_cod}** — {pop_m_nome}")
            if not pop_m_link:
                st.error(
                    "O POP-base desta frente está cadastrado, mas não possui PDF vinculado. "
                    "A auditoria manual está bloqueada até o documento ser anexado."
                )
            else:
                paginas_pop_manual = _texto_pop_por_pagina(pop_m_link)
                pop_texto_lido_manual = bool(
                    paginas_pop_manual and any(str(pagina or '').strip() for pagina in paginas_pop_manual)
                )
                if pop_texto_lido_manual:
                    st.success(
                        f"POP validado antes do lançamento: {len(paginas_pop_manual)} página(s) lida(s)."
                    )
                else:
                    st.error(
                        "O PDF do POP-base não pôde ser lido. A auditoria manual permanece bloqueada."
                    )
        else:
            if pop_base_cadastrado_m is not None and not pops_manuais:
                st.warning(
                    "O POP-base sugerido está cadastrado, mas não possui PDF legível. "
                    "A auditoria manual permanece bloqueada."
                )
            elif not pops_manuais:
                st.error(
                    "Nenhum POP cadastrado com PDF legível está disponível para esta frente. "
                    "Cadastre e vincule o documento correspondente antes de lançar a auditoria."
                )
            elif tipo:
                st.info(
                    "Selecione manualmente o POP correspondente. O sistema não usa nome, "
                    "palavras semelhantes ou o primeiro documento da lista para criar o vínculo."
                )

        st.markdown(
            '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
            'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
            'Não conformidades</div>'
            '<div style="font-size:.8rem;color:#728177;margin:.2rem 0 .6rem;">'
            'Cada card vira uma não conformidade rastreável, com POP, status, responsável e prazo.</div>',
            unsafe_allow_html=True,
        )

        if "manual_ncs" not in st.session_state:
            st.session_state.manual_ncs = []

        # Cada NC herda o POP-base validado acima. Não oferecer POPs de outras
        # frentes nem a opção sem vínculo, que criaria inconsistência no histórico.
        opcoes_pop_ncs = {
            '— herdar POP do checklist acima —': 'HERDAR'
            if pop_texto_lido_manual else None
        }

        for idx, nc_card in enumerate(st.session_state.manual_ncs):
            with st.container(border=True):
                col_h1, col_h2 = st.columns([5, 1])
                with col_h1:
                    st.markdown(f"**Não conformidade {idx + 1}**")
                with col_h2:
                    if st.button("✕ Remover", key=f"nc_remove_{idx}"):
                        st.session_state.manual_ncs.pop(idx)
                        st.rerun()

                nc_card['texto'] = st.text_area(
                    "Descrição", value=nc_card.get('texto', ''),
                    placeholder="Ex: 5.3 — Praga de ratos nas câmaras",
                    key=f"nc_texto_{idx}", height=70,
                )
                col1n, col2n, col3n = st.columns(3)
                with col1n:
                    nc_card['codigo_item'] = st.text_input(
                        "Código do item (opcional)", value=nc_card.get('codigo_item', ''),
                        key=f"nc_cod_{idx}",
                    )
                    nc_card['criticidade'] = st.selectbox(
                        "Criticidade", ['Alta', 'Média', 'Baixa'],
                        index=['Alta', 'Média', 'Baixa'].index(nc_card.get('criticidade') or 'Média'),
                        key=f"nc_crit_{idx}",
                    )
                with col2n:
                    nc_card['status'] = st.selectbox(
                        "Status", ['Aberta', 'Em andamento', 'Concluída', 'Cancelada'],
                        index=['Aberta', 'Em andamento', 'Concluída', 'Cancelada'].index(nc_card.get('status') or 'Aberta'),
                        key=f"nc_status_{idx}",
                    )
                    nc_card['responsavel'] = st.text_input(
                        "Responsável", value=nc_card.get('responsavel', ''), key=f"nc_resp_{idx}",
                    )
                with col3n:
                    escolha_pop_nc = st.selectbox(
                        "Documento (POP)", list(opcoes_pop_ncs), key=f"nc_pop_{idx}",
                    )
                    prazo_default = None
                    if nc_card.get('prazo'):
                        try:
                            prazo_default = datetime.strptime(nc_card['prazo'], '%Y-%m-%d')
                        except Exception:
                            prazo_default = None
                    prazo_nc = st.date_input("Prazo", value=prazo_default, format="DD/MM/YYYY", key=f"nc_prazo_{idx}")
                    nc_card['prazo'] = prazo_nc.strftime('%Y-%m-%d') if prazo_nc else ''

                nc_card['ponto_pop'] = st.text_input(
                    "Ponto do POP divergente", value=nc_card.get('ponto_pop', ''),
                    placeholder="Etapa, passo, seção, anexo ou página", key=f"nc_ponto_{idx}",
                )
                nc_card['acao_corretiva'] = st.text_area(
                    "Ação corretiva", value=nc_card.get('acao_corretiva', ''),
                    key=f"nc_acao_{idx}", height=70,
                )

                # Resolve o vínculo de POP escolhido (herdar do checklist / linha específica / nenhum)
                row_pop_nc = opcoes_pop_ncs.get(escolha_pop_nc)
                if row_pop_nc == 'HERDAR':
                    nc_card['pop_id'], nc_card['pop_nome'], nc_card['pop_codigo_2'] = pop_m_id, pop_m_nome, pop_m_cod
                elif row_pop_nc is not None:
                    nc_card['pop_id'] = row_pop_nc.get('id')
                    nc_card['pop_nome'] = str(row_pop_nc.get('processo', '')).strip()
                    nc_card['pop_codigo_2'] = str(row_pop_nc.get('codigo_2', '')).strip()
                else:
                    nc_card['pop_id'], nc_card['pop_nome'], nc_card['pop_codigo_2'] = None, '', ''
                nc_card['confianca'] = 'base' if nc_card['pop_nome'] else None

        if st.button("➕ Adicionar não conformidade", key="manual_nc_add"):
            st.session_state.manual_ncs.append({'status': 'Aberta', 'criticidade': 'Média'})
            st.rerun()

        st.markdown("---")
        
        # ── CÁLCULO DA NOTA ──
        if pcts:
            total_nota = sum(POSSIVEL[i] * pcts[i] / 100 for i in range(5))
            f = faixa(total_nota)
            st.markdown(f"""
            <div style="background:{f['cor']}15;border:2px solid {f['cor']};border-radius:8px;
                padding:12px 20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:600;">Nota Total Calculada</span>
                <span style="font-size:24px;font-weight:700;color:{f['cor']}">
                    {total_nota:.2f}% — {f['rot']}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # ── Auditoria já existente para essa loja+frente+data? ──
        existente_manual = None
        try:
            data_check = datetime.strptime(data_audit_str, '%d/%m/%Y')
            existente_manual = buscar_auditoria_existente(
                loja.split(' - ')[0], tipo, data_check.strftime('%Y-%m-%d')
            )
        except Exception:
            existente_manual = None

        if existente_manual:
            st.warning(
                f"⚠️ Já existe uma auditoria salva para esta loja, frente e data "
                f"(nota atual: {existente_manual['total']:.2f}%). Salvar de novo vai "
                f"**substituir** o registro existente."
            )

        # ── BOTÃO (Enter NÃO salva porque não está dentro de um form) ──
        if st.button(
            "Substituir Auditoria Existente" if existente_manual else "Salvar Auditoria",
            use_container_width=True, type="primary", key="btn_salvar_manual",
            disabled=not (pop_m_id and pop_m_link and pop_texto_lido_manual),
        ):
            # VALIDA E SALVA DIRETO
            try:
                data_audit = datetime.strptime(data_audit_str, '%d/%m/%Y')
            except:
                st.error("Formato de data inválido. Use DD/MM/AAAA")
                st.stop()

            if not loja or not tipo:
                st.error("Preencha todos os campos obrigatórios.")
                st.stop()
            elif any(p < 0 or p > 100 for p in pcts):
                st.error("As notas devem estar entre 0 e 100.")
                st.stop()
            elif not pop_m_id or not pop_m_link or not pop_texto_lido_manual:
                st.error(
                    "Não é possível salvar: valide o POP-base correto da frente e aguarde a leitura do PDF."
                )
                st.stop()
            else:
                cod_loja = loja.split(' - ')[0]
                criticas_list = [
                    {**CRITICA_CAMPOS, **nc}
                    for nc in st.session_state.manual_ncs
                    if (nc.get('texto') or '').strip()
                ]

                dados_para_salvar = {
                    'loja': cod_loja,
                    'data': data_audit.strftime('%Y-%m-%d'),
                    'tipo': tipo,
                    'avaliador': avaliador,
                    'topicos': [
                        {
                            'nome': CHECKLISTS[tipo]['slots'][i], 'possivel': POSSIVEL[i], 'pct': pcts[i],
                            'pop_id': pop_m_id, 'pop_codigo_2': pop_m_cod,
                            'pop_nome': pop_m_nome, 'pop_link': pop_m_link,
                            'pop_paginas_lidas': len(paginas_pop_manual),
                        }
                        for i in range(5)
                    ],
                    'total': total_nota,
                    'criticas': criticas_list
                }
                
                try:
                    if existente_manual:
                        deletar_auditoria(int(existente_manual['id']))
                    inserir_auditoria(dados_para_salvar)
                    msg = "🔄 Auditoria substituída" if existente_manual else "✅ Auditoria salva"
                    st.success(f"{msg} com sucesso! Loja {cod_loja} - {CHECKLISTS[tipo]['nome']}")
                    st.cache_data.clear()

                    # ── MARCA PARA RESETAR OS CAMPOS ──
                    st.session_state.manual_reset = True
                    
                    import time
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar no banco: {e}")
        
        # ── RESETA OS CAMPOS APÓS SALVAR ──
        if st.session_state.manual_reset:
            st.session_state.manual_reset = False
            # Limpa os campos do session_state
            for key in ["manual_loja", "manual_tipo", "manual_frente_nome", "manual_data", "manual_avaliador"]:
                if key in st.session_state:
                    del st.session_state[key]
            for i in range(5):
                key = f"pct_manual_{i}"
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.manual_ncs = []
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 9 - DADOS & EXPORTAÇÃO
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[8]:
        st.markdown(cab_html(
            "Dados e exportação",
            "Situação do armazenamento, exportações para Excel e consolidação entre auditores.",
            "⛁",
        ), unsafe_allow_html=True)

        n_aud = len(df_auditorias)
        n_lojas_aud = df_auditorias['loja'].nunique() if not df_auditorias.empty and 'loja' in df_auditorias.columns else 0
        n_ncs = int(df_auditorias['criticas'].apply(len).sum()) if not df_auditorias.empty and 'criticas' in df_auditorias.columns else 0

        col_exp, col_imp = st.columns(2)

        with col_exp:
            st.markdown('<div class="aud-card"><h3>Exportar</h3>', unsafe_allow_html=True)
            st.caption("Os CSVs abrem direto no Excel com separador ponto e vírgula.")

            if df_auditorias.empty:
                st.info("Nenhuma auditoria para exportar ainda.")
            else:
                csv_auditorias = df_para_csv_br(auditorias_para_exportacao(df_auditorias))
                csv_ncs = df_para_csv_br(ncs_para_exportacao(todas_ncs(df_auditorias)))

                st.download_button("Auditorias (CSV)", data=csv_auditorias,
                    file_name=f"auditorias_ferreira_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True, key="dados_export_auditorias_csv")
                st.download_button("Não conformidades (CSV)", data=csv_ncs,
                    file_name=f"nao_conformidades_ferreira_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True, key="dados_export_ncs_csv")

                st.caption(f"{n_aud} auditorias · {n_ncs} não conformidades · {n_lojas_aud} loja(s)")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_imp:
            st.markdown('<div class="aud-card"><h3>Importar</h3>', unsafe_allow_html=True)
            st.caption("Cole o JSON exportado de outro painel ou backup. Registros com a mesma loja, "
                       "frente e data são atualizados; os demais são acrescentados.")

            st.markdown(
                '<style>textarea[aria-label="JSON de auditorias"]{min-height:90px !important;height:90px !important;}</style>',
                unsafe_allow_html=True,
            )
            imp_txt = st.text_area("JSON de auditorias", placeholder="Cole aqui o JSON exportado", height=90,
                                    key="dados_import_txt", label_visibility="collapsed")

            if st.button("Importar e consolidar", type="primary", use_container_width=True, key="dados_import_btn"):
                import json as _json
                if not imp_txt.strip():
                    st.error("Cole o conteúdo do arquivo JSON antes de importar.")
                else:
                    try:
                        dados_json = _json.loads(imp_txt)
                    except Exception:
                        st.error("O conteúdo colado não é um JSON válido.")
                        dados_json = None

                    if dados_json is not None:
                        lista = dados_json if isinstance(dados_json, list) else dados_json.get('audits', [])
                        if not isinstance(lista, list):
                            st.error("O JSON não contém uma lista de auditorias.")
                        else:
                            campos_obrig = {'loja', 'data', 'tipo', 'total', 'topicos', 'criticas'}
                            invalidos = [r for r in lista if not campos_obrig.issubset(set(r.keys()))]
                            if invalidos:
                                st.error(f"{len(invalidos)} registro(s) sem os campos obrigatórios "
                                         f"({', '.join(sorted(campos_obrig))}) foram ignorados.")
                                lista = [r for r in lista if r not in invalidos]

                            novos, substituidos = 0, 0
                            erros = []
                            for r in lista:
                                try:
                                    existe = df_auditorias[
                                        (df_auditorias['loja'].astype(str) == str(r['loja'])) &
                                        (df_auditorias['tipo'] == r['tipo']) &
                                        (df_auditorias['data'] == r['data'])
                                    ] if not df_auditorias.empty else pd.DataFrame()

                                    if not existe.empty:
                                        deletar_auditoria(int(existe.iloc[0]['id']))
                                        substituidos += 1
                                    else:
                                        novos += 1

                                    inserir_auditoria({
                                        'loja': str(r['loja']),
                                        'data': r['data'],
                                        'tipo': r['tipo'],
                                        'avaliador': r.get('avaliador', 'Auditor Controladoria'),
                                        'topicos': r.get('topicos', []),
                                        'total': r.get('total', 0),
                                        'criticas': r.get('criticas', []),
                                    })
                                except Exception as e:
                                    erros.append(str(e))

                            st.cache_data.clear()
                            if novos or substituidos:
                                st.success(f"✅ {novos} auditoria(s) adicionada(s) e {substituidos} atualizada(s).")
                            if erros:
                                st.error(f"{len(erros)} registro(s) falharam ao salvar: {erros[0]}")
                            if novos or substituidos:
                                import time
                                time.sleep(1.5)
                                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── RÉGUA DE CLASSIFICAÇÃO (idêntica à usada nos cálculos do painel) ──
        st.markdown('<div class="aud-card"><h3>Régua de classificação aplicada '
                     '<span style="font-size:11px;color:#728177;font-weight:500">idêntica à dos checklists</span></h3>',
                     unsafe_allow_html=True)

        faixas_regua = [
            (
                item['min'],
                100 if indice == 0 else FAIXAS_AUDITORIA[indice - 1]['min'] - 1,
                item['rot'], item['hex'], item['risco'], item['prio'],
            )
            for indice, item in reversed(list(enumerate(FAIXAS_AUDITORIA)))
        ]
        linhas_regua = "".join(f"""
            <tr>
                <td style="padding:10px;border-bottom:1px solid #eef3ee;"><b>{ini}–{fim}%</b></td>
                <td style="padding:10px;border-bottom:1px solid #eef3ee;">
                    <span class="aud-selo" style="background:{hex_}">{rot}</span>
                </td>
                <td style="padding:10px;border-bottom:1px solid #eef3ee;">{risco}</td>
                <td style="padding:10px;border-bottom:1px solid #eef3ee;font-size:12.5px;">{prio}</td>
            </tr>""" for ini, fim, rot, hex_, risco, prio in faixas_regua)

        st.markdown(f"""
        <div class="aud-heat">
        <table>
            <thead><tr><th>Score</th><th>Classificação</th><th>Risco</th><th>Prioridade de atuação</th></tr></thead>
            <tbody>{linhas_regua}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Central de Processos e Riscos &nbsp;·&nbsp; Ferreira Supermercados &nbsp;·&nbsp; Sistema Interno
</div>""", unsafe_allow_html=True)
