"""
app.py — Central de Processos e Riscos | Ferreira Supermercados
Banco: Supabase | PDFs: Google Drive (público via link)
"""
import pdfplumber
import re
import streamlit as st
import pandas as pd
import base64, os
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
with tabs[3]:
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
    .aud-card h3{font-family:var(--disp);font-size:16px;font-weight:600;color:var(--verde-tinta);letter-spacing:.3px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between}
    .aud-kpi .rot{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--suave);font-weight:600}
    .aud-kpi .num{font-family:var(--disp);font-size:40px;font-weight:700;line-height:1;margin:8px 0 2px;color:var(--verde-tinta)}
    .aud-kpi .pe{font-size:12px;color:var(--suave);margin-bottom:2px}
    .aud-kpi .faixa{height:4px;border-radius:3px;margin-top:12px;background:var(--papel);overflow:hidden}
    .aud-kpi .faixa i{display:block;height:100%}
    .aud-selo{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.3px;color:#fff}
    .aud-barra{display:flex;align-items:center;gap:10px;padding:6px 0}
    .aud-barra .nome{width:150px;font-size:12.5px;font-weight:500;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
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
    .aud-cab h1{font-family:var(--disp);font-weight:700;font-size:26px;color:var(--verde-tinta);line-height:1.15;letter-spacing:.2px;margin:0}
    .aud-cab h1 .ic{margin-right:8px}
    .aud-cab .desc{color:var(--suave);font-size:13px;margin-top:6px;max-width:660px}

    /* ── Tag genérica (chip de contexto) ── */
    .aud-tag{display:inline-block;padding:1px 8px;border-radius:5px;font-size:11px;font-weight:600;
        border:1px solid var(--borda);background:var(--papel);color:var(--suave)}

    /* ── Vínculo com POP ── */
    .pop-vinculo{font-size:12px;color:var(--verde-esc);background:rgba(46,158,55,.10);
        border:1px solid rgba(46,158,55,.30);border-radius:6px;padding:3px 9px;display:inline-block;font-weight:600}
    .pop-vinculo.faltando{background:rgba(214,69,69,.12);border-color:rgba(214,69,69,.40);color:var(--crit)}
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
        ]}
    }
    
    POSSIVEL = [35, 20, 15, 15, 15]
    SLOTS_CURTOS = ['Aderência', 'Maturidade', 'Conhecimento', 'Eficiência', 'Gaps/Estrut.']
    
    def faixa(nota):
        if nota >= 90: return {'rot': 'Excelente', 'cor': '#1E7A2A', 'hex': '#1E7A2A'}
        if nota >= 80: return {'rot': 'Bom', 'cor': '#5FB65B', 'hex': '#5FB65B'}
        if nota >= 70: return {'rot': 'Atenção', 'cor': '#E8B23A', 'hex': '#E8B23A'}
        if nota >= 60: return {'rot': 'Risco', 'cor': '#E67E22', 'hex': '#E67E22'}
        return {'rot': 'Crítico', 'cor': '#D64545', 'hex': '#D64545'}
    
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

    def vencida(nc: dict) -> bool:
        """True se a NC tem prazo definido, ainda não foi concluída e o prazo já passou."""
        from datetime import datetime as _dt
        prazo = (nc.get('prazo') or '').strip()
        if not prazo or nc.get('status') == 'Concluída':
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
    # SUB-ABA 1 - PAINEL GERAL (COM KPIs DO HTML)
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[0]:
        st.markdown(cab_html(
            "Painel geral da rede",
            "Consolidação das auditorias internas de Açougue, Frente de Loja e Recebimento.",
            "▩",
        ), unsafe_allow_html=True)
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            # ── KPIs ──
            metricas = calcular_metricas(df_auditorias)
            ncs_rede = todas_ncs(df_auditorias)
            ncs_abertas = [n for n in ncs_rede if n.get('status') != 'Concluída']
            ncs_vencidas = [n for n in ncs_abertas if vencida(n)]
            ncs_sem_pop = [n for n in ncs_abertas if not (n.get('pop_nome') or '').strip()]

            if ncs_sem_pop:
                st.markdown(f"""
                <div style="background:#fdeeee;border:1px solid #eebcbc;border-left:4px solid #D64545;
                    border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:14px;display:flex;gap:10px;">
                    <span>⚑</span>
                    <div><b>{len(ncs_sem_pop)} não conformidade(s) sem rastreio ao POP.</b>
                    Toda NC deveria indicar o documento e o ponto exato do POP divergente.
                    Veja a aba <b>Não conformidades</b> para regularizar.</div>
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
                    sufixo_cob = f" ({n_frentes} de {n_frentes_total} frentes)" if n_frentes < n_frentes_total else ""
                    html_rank += f"""<div class="aud-barra">
                        <div class="nome"><span class="aud-cod" style="font-size:12px">{loja}</span> {nome_loja}{sufixo_cob}</div>
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
                        topicos_medias.append({'topico': nome, 'media': sum(pcts_t)/len(pcts_t), 'peso': POSSIVEL[i]})

                st.markdown('<div class="aud-card"><h3>Desempenho por processo</h3>', unsafe_allow_html=True)
                html_proc = ""
                for tipo, nota in notas_tipo.items():
                    f = faixa(nota)
                    nome = CHECKLISTS[tipo]['nome']
                    html_proc += f"""<div class="aud-barra">
                        <div class="nome">{nome}</div>
                        <div class="trilho"><i style="width:{min(100,nota)}%;background:{f['cor']}"></i></div>
                        <div class="val" style="color:{f['cor']}">{nota:.2f}</div>
                    </div>"""
                html_proc += '<h3 style="margin-top:22px">Score por bloco do checklist <span style="font-size:11px;color:#728177;font-weight:500">toda a rede</span></h3>'
                for item in topicos_medias:
                    f = faixa(item['media'])
                    html_proc += f"""<div class="aud-barra">
                        <div class="nome">{item['topico']} <span style="color:#728177;font-weight:400">(peso {item['peso']}%)</span></div>
                        <div class="trilho"><i style="width:{min(100,item['media'])}%;background:{f['cor']}"></i></div>
                        <div class="val" style="color:{f['cor']}">{item['media']:.2f}</div>
                    </div>"""
                st.markdown(html_proc + '</div>', unsafe_allow_html=True)

            # ── GAPS RECORRENTES NA REDE (PARETO) ──
            st.markdown('<div class="aud-card" style="margin-top:16px"><h3>Gaps recorrentes na rede <span style="font-size:11px;color:#728177;font-weight:500">não conformidades agrupadas pelo item do checklist</span></h3>', unsafe_allow_html=True)
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
                    lojas_txt = ' '.join(f'<span class="aud-cod" style="font-size:12px">{l}</span>' for l in sorted(g['lojas']))
                    largura = 100 * g['n'] / max_n
                    linhas += f"""<tr>
                        <td style="font-weight:500">{g['texto'][:90]}</td>
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
            csv_data = df_auditorias.to_csv(index=False, sep=';')
            st.download_button("📊 Exportar CSV", data=csv_data,
                file_name=f"auditorias_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True, key="export_csv_painel_geral")

        # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 2 - RANKINGS
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[1]:
        st.markdown(cab_html(
            "Rankings",
            "Classificações pela auditoria mais recentes de cada loja/frente.",
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
                    topicos_medias.append({'topico': nome, 'media': sum(pcts)/len(pcts), 'peso': POSSIVEL[i]})
            
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
                    html += "<div style='width:150px;font-size:0.85rem;font-weight:600;color:#0d2a16;'>" + item['topico'] + f" <span style='color:#728177;font-weight:400'>(peso {item['peso']}%)</span></div>"
                    html += "<div style='flex:1;height:24px;background:#F4F7F3;border-radius:6px;overflow:hidden;'>"
                    html += "<div style='height:100%;width:" + media_pct + "%;background:" + cor + ";border-radius:6px;'></div>"
                    html += "</div>"
                    html += "<div style='width:50px;text-align:right;font-weight:700;font-size:0.9rem;color:" + cor + ";'>" + media_str + "</div>"
                    html += "</div>"

                st.markdown(html, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background:#fff8e6;border:1px solid #f0dca0;border-left:4px solid #F2C300;
                    border-radius:8px;padding:11px 14px;font-size:13px;margin-top:16px;display:flex;gap:10px;">
                    <span>ⓘ</span><div>O primeiro bloco tem peso {POSSIVEL[0]}% — cada ponto perdido nele custa mais que nos demais.</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ═══════════════════════════════════════════════════════════
            # LINHA 2: Rankings por frente (3 colunas)
            # ═══════════════════════════════════════════════════════════
            col_acougue, col_frente, col_receb = st.columns(3)
            
            for col, tipo_key, titulo, cor_badge in [
                (col_acougue, 'AÇO-AUD-01', 'Açougue', '#B0442E'),
                (col_frente, 'FRE-AUD-02', 'Frente de Loja', '#2E6BB0'),
                (col_receb, 'REC-AUD-03', 'Recebimento', '#7A4EB0')
            ]:
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
    
    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 3 - MAPA DE RISCO (HEATMAP)
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[2]:
        st.markdown(cab_html(
            "Mapa de risco",
            "Resumo dos Tópicos da auditoria mais recentes.",
            "▦",
        ), unsafe_allow_html=True)
        
        # ─ VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            
            tipo_heatmap = st.selectbox(
                "Selecione a Frente",
                list(CHECKLISTS.keys()),
                format_func=lambda x: f"{CHECKLISTS[x]['nome']} — {x}",
                key="heatmap_tipo"
            )
            
            df_heat = df_auditorias[df_auditorias['tipo'] == tipo_heatmap]
            
            if df_heat.empty:
                st.info(f"Nenhuma auditoria de {CHECKLISTS[tipo_heatmap]['nome']} foi registrada. "
                        "Use a aba 'Importar PDF' ou 'Lançar Manual' para registrar a primeira.")
            else:
                # Última auditoria por loja
                df_heat = df_heat.sort_values('data').groupby('loja').last().reset_index()
                
                # ── FUNÇÃO PARA COR DO TEXTO ──
                def cor_nota(nota):
                    if nota >= 90: return '#1E7A2A'
                    elif nota >= 80: return '#5FB65B'
                    elif nota >= 70: return '#E8B23A'
                    elif nota >= 60: return '#E67E22'
                    else: return '#D64545'
                
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
                    f"<th>{nome}<br><span style='font-weight:400;color:#9aa89c'>{POSSIVEL[i]}%</span></th>"
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
                st.components.v1.html(html_table, height=500, scrolling=True)
                
                st.caption(f"{len(df_heat)} loja(s) auditada(s) · Exibindo a última auditoria de cada loja")
                
                # ── LEGENDA (gerada a partir de faixa(), sem duplicar valores) ──
                faixas_ref = [(95, '≥ 90'), (85, '80-89'), (75, '70-79'), (65, '60-69'), (30, '< 60')]
                legenda_html = '<div style="display:flex;gap:20px;flex-wrap:wrap;font-size:0.85rem;color:#728177;margin-top:16px;padding-top:12px;border-top:1px solid #EEF3EE;">'
                for amostra, faixa_txt in faixas_ref:
                    fx = faixa(amostra)
                    legenda_html += (
                        '<span style="display:flex;align-items:center;gap:6px;">'
                        f'<span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:{fx["cor"]};"></span>'
                        f'{fx["rot"]} ({faixa_txt})</span>'
                    )
                legenda_html += '</div>'
                st.markdown(legenda_html, unsafe_allow_html=True)
                
                # ── EXPORTAR E ATUALIZAR ──
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    csv_heat = df_heat.to_csv(index=False, sep=';')
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
        st.markdown(cab_html(
            "Análise por loja",
            "Card central compilado a partir do Resumo dos Tópicos de cada frente. Compara a loja com a média da rede e destaca fortalezas e fragilidades.",
            "◎",
        ), unsafe_allow_html=True)
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            # ── Seleção de Loja ──
            loja_selecionada = st.selectbox(
                "Selecione a Loja",
                sorted(df_auditorias['loja'].unique().tolist()),
                format_func=lambda x: f"{x} — {dict(LOJAS).get(x, x)}"
            )
            
            df_loja = df_auditorias[df_auditorias['loja'] == loja_selecionada]
            
            if df_loja.empty:
                st.warning(f"Nenhuma auditoria para a loja {loja_selecionada}")
            else:
                # ── MÉTRICAS DA LOJA ──
                nota_loja = df_loja['total'].mean()
                f_loja = faixa(nota_loja)
                nivel_loja = nivel_maturidade(nota_loja)
                nota_rede = df_auditorias['total'].mean()
                
                ultima_data = df_loja.sort_values('data')['data'].iloc[-1] if not df_loja.empty else ""
                ultima_formatada = f"{ultima_data[8:10]}/{ultima_data[5:7]}/{ultima_data[:4]}" if ultima_data else ""
                
                # ── CARD PRINCIPAL (USANDO st.components) ──
                html_card = f"""
                <div style="background:white;border:1px solid #DDE6DC;border-radius:12px;padding:20px;margin-bottom:16px;">
                    <div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;">
                        <!-- ANEL -->
                        <div style="position:relative;width:96px;height:96px;flex-shrink:0;">
                            <svg width="96" height="96" viewBox="0 0 96 96">
                                <circle cx="48" cy="48" r="42" fill="none" stroke="#F4F7F3" stroke-width="9"/>
                                <circle cx="48" cy="48" r="42" fill="none" stroke="{f_loja['cor']}" stroke-width="9" 
                                    stroke-dasharray="{2*3.14159*42*min(100,nota_loja)/100} {2*3.14159*42*(1-min(100,nota_loja)/100)}" 
                                    stroke-linecap="round" transform="rotate(-90 48 48)"/>
                                <text x="48" y="48" text-anchor="middle" dy=".35em" font-size="22" font-weight="700" fill="#12331C">{nota_loja:.1f}</text>
                            </svg>
                        </div>
                        
                        <!-- INFORMAÇÕES DA LOJA -->
                        <div style="flex:1;min-width:200px;">
                            <div style="font-family:arial,sans-serif;font-size:22px;font-weight:700;color:#12331C;">
                                <span style="font-weight:700;color:#1E7A2A;font-size:20px;">{loja_selecionada}</span> {dict(LOJAS).get(loja_selecionada, '')}
                            </div>
                            <div style="color:#728177;font-size:13px;margin-top:2px;">
                                {len(df_loja)} frente(s) · última em {ultima_formatada}
                            </div>
                            <div style="margin-top:10px;">
                                <span style="background:{f_loja['cor']};color:white;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;">
                                    {f_loja['rot']}
                                </span>
                                <span style="font-size:12px;color:#728177;margin-left:6px;">
                                    Nível {nivel_loja} — {NIVEIS[nivel_loja]['rot']} · rede {nota_rede:.1f}
                                </span>
                            </div>
                        </div>
                        
                        <!-- NOTAS POR FRENTE -->
                        <div style="text-align:right;">
                            <div style="font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#728177;font-weight:600;margin-bottom:6px;">
                                Notas por frente
                            </div>
                """
                
                # Adiciona notas por frente
                for tipo in df_loja['tipo'].unique():
                    nota = df_loja[df_loja['tipo'] == tipo]['total'].mean()
                    f2 = faixa(nota)
                    nome = CHECKLISTS[tipo]['nome']
                    html_card += f"""
                            <div style="display:flex;gap:8px;align-items:center;justify-content:flex-end;margin-bottom:4px;">
                                <span style="font-size:12.5px;">{nome}</span>
                                <span style="font-family:arial,sans-serif;font-weight:700;font-size:16px;color:{f2['cor']};">
                                    {nota:.1f}
                                </span>
                            </div>
                    """
                
                html_card += """
                        </div>
                    </div>
                </div>
                """
                
                # Renderiza usando components
                st.components.v1.html(html_card, height=180)
                
                # ── RESUMO DOS TÓPICOS ──
                st.markdown("### 📊 Resumo dos tópicos — loja vs rede")
                
                # Calcula médias
                loja_medias = []
                rede_medias = []
                
                for i, nome in enumerate(SLOTS_CURTOS):
                    pcts_loja = []
                    pcts_rede = []
                    
                    for _, row in df_loja.iterrows():
                        if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                            pcts_loja.append(row['topicos'][i].get('pct', 0))
                    
                    for _, row in df_auditorias.iterrows():
                        if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                            pcts_rede.append(row['topicos'][i].get('pct', 0))
                    
                    if pcts_loja:
                        loja_medias.append(sum(pcts_loja)/len(pcts_loja))
                    else:
                        loja_medias.append(0)
                    
                    if pcts_rede:
                        rede_medias.append(sum(pcts_rede)/len(pcts_rede))
                    else:
                        rede_medias.append(0)
                
                # Exibe cada tópico com barra
                for i, nome in enumerate(SLOTS_CURTOS):
                    if i < len(loja_medias) and i < len(rede_medias):
                        val_loja = loja_medias[i]
                        val_rede = rede_medias[i]
                        f_item = faixa(val_loja)
                        pct_loja = min(100, val_loja)
                        pct_rede = min(99, val_rede)
                        
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                            <div style="width:120px;font-size:12.5px;font-weight:500;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                {nome}
                            </div>
                            <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;position:relative;">
                                <div style="display:block;height:100%;width:{pct_loja}%;background:{f_item['cor']};border-radius:5px;"></div>
                                <div style="position:absolute;left:{pct_rede}%;top:-3px;transform:translateX(-50%);width:8px;height:8px;border-radius:50%;background:#5b6a5e;" 
                                     title="rede {val_rede:.1f}"></div>
                            </div>
                            <div style="width:52px;text-align:right;font-weight:700;font-size:15px;color:{f_item['cor']};">
                                {val_loja:.1f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # ── LEGENDA ──
                st.markdown("""
                <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:11.5px;color:#728177;margin-top:14px;padding-top:10px;border-top:1px solid #EEF3EE;">
                """, unsafe_allow_html=True)
                
                for label, cor in [('Excelente', '#1E7A2A'), ('Bom', '#5FB65B'), 
                                   ('Atenção', '#E8B23A'), ('Risco', '#E67E22'), 
                                   ('Crítico', '#D64545')]:
                    st.markdown(f"""
                    <span>
                        <span style="display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:middle;background:{cor};"></span>
                        {label}
                    </span>
                    """, unsafe_allow_html=True)
                
                st.markdown("""
                    <span style="margin-left:auto;">
                        <span style="display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px;vertical-align:middle;background:#5b6a5e;"></span>
                        média da rede
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # ── LEITURA RÁPIDA ──
                st.markdown('<div class="aud-card"><h3>📋 Leitura rápida</h3>', unsafe_allow_html=True)

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
                
                comparacao = "✅ Loja acima da média da rede." if nota_loja >= nota_rede else "📌 Loja abaixo da média da rede — priorizar no acompanhamento."
                cor_comparacao = "#1E7A2A" if nota_loja >= nota_rede else "#E67E22"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div style="background:#EFFAF0;border:1px solid #BFE6C2;border-left:4px solid #1E7A2A;border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:12px;display:flex;gap:10px;">
                        <span style="font-size:18px;">▲</span>
                        <div>
                            <b>Maior fortaleza:</b> {melhor_nome} ({melhor_valor:.1f}).
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div style="background:#FDEEEE;border:1px solid #EEBCBC;border-left:4px solid #D64545;border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:12px;display:flex;gap:10px;">
                        <span style="font-size:18px;">▼</span>
                        <div>
                            <b>Prioridade de ação:</b> {pior_nome} ({pior_valor:.1f}).
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background:{'#EFFAF0' if nota_loja >= nota_rede else '#FFF8E6'};border:1px solid {'#BFE6C2' if nota_loja >= nota_rede else '#F0DCA0'};border-left:4px solid {cor_comparacao};border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:12px;display:flex;gap:10px;">
                        <span style="font-size:18px;">{'✓' if nota_loja >= nota_rede else '≈'}</span>
                        <div>
                            {comparacao}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                # ── NÃO CONFORMIDADES ──
                # (sem wrapper .aud-card: st.dataframe é renderizado pelo Streamlit fora
                # da hierarquia HTML de uma div aberta via unsafe_allow_html, então o
                # card ficaria vazio e o conteúdo "vazaria" para fora dele)
                ncs_loja_todas = [n for n in todas_ncs(df_loja)]
                ncs_loja_abertas = [n for n in ncs_loja_todas if n.get('status') != 'Concluída']
                st.markdown(f"### ⚠️ Situação das não conformidades "
                            f"<span style='font-size:13px;color:#728177;font-weight:400'>"
                            f"{len(ncs_loja_abertas)} em aberto de {len(ncs_loja_todas)}</span>",
                            unsafe_allow_html=True)

                if ncs_loja_todas:
                    linhas_nc = []
                    for nc in ncs_loja_todas:
                        frente = CHECKLISTS.get(nc.get('_tipo'), {}).get('nome', nc.get('_tipo'))
                        pop = nc.get('pop_nome') or '— sem vínculo —'
                        if nc.get('pop_codigo_2'):
                            pop = f"{nc['pop_codigo_2']} — {pop}"
                        atrasada = vencida(nc)
                        prazo_txt = nc.get('prazo') or '—'
                        if atrasada:
                            prazo_txt = f"⚠ {prazo_txt}"
                        linhas_nc.append({
                            'Frente': frente,
                            'Não conformidade': nc.get('texto') or '',
                            'POP vinculado': pop,
                            'Status': nc.get('status') or 'Aberta',
                            'Prazo': prazo_txt,
                        })

                    df_criticas = pd.DataFrame(linhas_nc)
                    sem_vinculo = int((df_criticas['POP vinculado'] == '— sem vínculo —').sum())
                    if sem_vinculo:
                        st.warning(
                            f"{sem_vinculo} de {len(df_criticas)} não conformidade(s) sem POP "
                            "de referência. Vincule na importação do PDF ou no lançamento manual."
                        )

                    st.dataframe(
                        df_criticas[['Frente', 'Não conformidade', 'POP vinculado', 'Status', 'Prazo']],
                        column_config={
                            'Frente': st.column_config.Column('Frente', width='small'),
                            'Não conformidade': st.column_config.Column('Não conformidade'),
                            'POP vinculado': st.column_config.Column('POP vinculado', width='medium'),
                            'Status': st.column_config.Column('Status', width='small'),
                            'Prazo': st.column_config.Column('Prazo', width='small'),
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    st.caption("Para editar status, responsável, prazo ou ação corretiva de uma NC, use a aba **Não conformidades**.")
                else:
                    st.info("Nenhuma não conformidade crítica registrada nesta unidade.")

                st.markdown("---")

                # ── EVOLUÇÃO ── (sem .aud-card: st.line_chart quebra dentro de div manual)
                st.markdown("### 📈 Evolução no tempo")
                
                df_evolucao = df_loja.sort_values('data')
                
                if len(df_evolucao) >= 2:
                    st.caption(f"{len(df_evolucao)} auditoria(s) registrada(s) para esta loja.")
                    
                    evol_data = []
                    for _, row in df_evolucao.iterrows():
                        data_formatada = f"{row['data'][8:10]}/{row['data'][5:7]}/{row['data'][2:4]}"
                        evol_data.append({
                            'Data': data_formatada,
                            'Nota': row['total'],
                            'Frente': CHECKLISTS.get(row['tipo'], {}).get('nome', row['tipo']),
                            'tipo': row['tipo']
                        })

                    if evol_data:
                        df_evol = pd.DataFrame(evol_data)

                        # Uma coluna por frente (paridade com o gráfico do HTML, que traça
                        # uma linha colorida por frente em vez de uma média agregada única).
                        df_pivot = df_evol.pivot_table(
                            index='Data', columns='Frente', values='Nota', aggfunc='mean'
                        )
                        cores_frentes = [CHECKLISTS.get(t, {}).get('cor', '#728177')
                                          for t in CHECKLISTS if CHECKLISTS[t]['nome'] in df_pivot.columns]
                        st.line_chart(df_pivot, color=cores_frentes or None)

                        st.markdown("**Detalhamento por auditoria**")
                        for _, row in df_evol.iterrows():
                            cor = CHECKLISTS.get(row['tipo'], {}).get('cor', '#728177')
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #EEF3EE;">
                                <span style="font-weight:600;font-size:13px;color:#728177;">{row['Data']}</span>
                                <span style="background:{cor};color:white;padding:2px 9px;border-radius:20px;font-size:10px;font-weight:700;">{row['Frente']}</span>
                                <span style="margin-left:auto;font-weight:700;color:{faixa(row['Nota'])['cor']};">{row['Nota']:.1f}%</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("Apenas um ciclo registrado. A série aparece quando você lançar a próxima auditoria desta loja.")
    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 5 - NÃO CONFORMIDADES
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[4]:
        st.markdown(cab_html(
            "Não conformidades",
            "Ciclo de vida completo das NCs registradas: status, responsável, prazo e ação corretiva.",
            "✕",
        ), unsafe_allow_html=True)

        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            ncs_all = todas_ncs(df_auditorias)

            if not ncs_all:
                st.info("Nenhuma não conformidade registrada ainda.")
            else:
                ncs_abertas_all = [n for n in ncs_all if n.get('status') != 'Concluída']
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

                st.markdown("<br>", unsafe_allow_html=True)

                # ── FILTROS ──
                fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
                with fc1:
                    f_loja = st.selectbox("Loja", ["Todas"] + sorted({n['_loja'] for n in ncs_all if n.get('_loja')}), key="nc_f_loja")
                with fc2:
                    f_tipo = st.selectbox("Frente", ["Todas"] + list(CHECKLISTS.keys()),
                                           format_func=lambda x: CHECKLISTS[x]['nome'] if x in CHECKLISTS else x, key="nc_f_tipo")
                with fc3:
                    f_crit = st.selectbox("Criticidade", ["Todas", "Alta", "Média", "Baixa"], key="nc_f_crit")
                with fc4:
                    f_status = st.selectbox("Status", ["Todas", "Aberta", "Em andamento", "Concluída"], key="nc_f_status")
                with fc5:
                    f_pop = st.selectbox("Rastreio ao POP", ["Todas", "Com POP", "Sem POP"], key="nc_f_pop")
                with fc6:
                    f_venc = st.selectbox("Prazo", ["Todas", "Vencidas"], key="nc_f_venc")

                ncs_filtradas = ncs_all
                if f_loja != "Todas":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('_loja') == f_loja]
                if f_tipo != "Todas":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('_tipo') == f_tipo]
                if f_crit != "Todas":
                    ncs_filtradas = [n for n in ncs_filtradas if n.get('criticidade') == f_crit]
                if f_status != "Todas":
                    ncs_filtradas = [n for n in ncs_filtradas if (n.get('status') or 'Aberta') == f_status]
                if f_pop == "Com POP":
                    ncs_filtradas = [n for n in ncs_filtradas if (n.get('pop_nome') or '').strip()]
                elif f_pop == "Sem POP":
                    ncs_filtradas = [n for n in ncs_filtradas if not (n.get('pop_nome') or '').strip()]
                if f_venc == "Vencidas":
                    ncs_filtradas = [n for n in ncs_filtradas if vencida(n)]

                st.caption(f"{len(ncs_filtradas)} não conformidade(s) no recorte atual.")

                # ── EXPORTAR CSV DAS NCs FILTRADAS ──
                if ncs_filtradas:
                    df_export_nc = pd.DataFrame([{
                        'Loja': n.get('_loja'), 'Frente': CHECKLISTS.get(n.get('_tipo'), {}).get('nome', n.get('_tipo')),
                        'Data auditoria': n.get('_data'), 'Item': n.get('codigo_item'), 'Descrição': n.get('texto'),
                        'POP': n.get('pop_nome'), 'Ponto do POP': n.get('ponto_pop'), 'Criticidade': n.get('criticidade'),
                        'Status': n.get('status'), 'Responsável': n.get('responsavel'), 'Prazo': n.get('prazo'),
                        'Ação corretiva': n.get('acao_corretiva'),
                    } for n in ncs_filtradas])
                    st.download_button(
                        "📊 Exportar NCs filtradas (CSV)", data=df_export_nc.to_csv(index=False, sep=';'),
                        file_name=f"nao_conformidades_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv", key="export_csv_ncs",
                    )

                st.markdown("---")

                # ── CARTÕES EDITÁVEIS ──
                for i, nc in enumerate(ncs_filtradas):
                    frente_nome = CHECKLISTS.get(nc.get('_tipo'), {}).get('nome', nc.get('_tipo'))
                    atrasada = vencida(nc)
                    cor_crit = {'Alta': '#D64545', 'Média': '#E8B23A', 'Baixa': '#728177'}.get(nc.get('criticidade'), '#728177')
                    titulo = f"[{nc.get('_loja')}] {frente_nome} · {nc.get('codigo_item') or '—'} — {(nc.get('texto') or '')[:70]}"
                    if atrasada:
                        titulo = "⚠ " + titulo

                    with st.expander(titulo, expanded=False):
                        st.markdown(f"**Frente:** {frente_nome} · **Loja:** {nc.get('_loja')} · **Data da auditoria:** {nc.get('_data')}")
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
                            novo_prazo = st.date_input("Prazo", value=prazo_atual, key=f"{key_base}_prazo")
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
                loja_filtro_hist = st.selectbox(
                    "Filtrar por Loja",
                    ["Todas"] + sorted(df_auditorias['loja'].unique().tolist()),
                    key="hist_loja_final"
                )
            with col2:
                tipo_filtro_hist = st.selectbox(
                    "Filtrar por Frente",
                    ["Todas"] + df_auditorias['tipo'].unique().tolist(),
                    key="hist_tipo_final"
                )
            
            df_hist = df_auditorias.copy()
            if loja_filtro_hist != "Todas":
                df_hist = df_hist[df_hist['loja'] == loja_filtro_hist]
            if tipo_filtro_hist != "Todas":
                df_hist = df_hist[df_hist['tipo'] == tipo_filtro_hist]
            
            # ── CRIA TABELA ESTILIZADA ──
            if not df_hist.empty:
                # Mapeamento de cores por tipo
                cores_tipo = {
                    'AÇO-AUD-01': ('Açougue', 'badge-acougue'),
                    'FRE-AUD-02': ('Frente de Loja', 'badge-frente'),
                    'REC-AUD-03': ('Recebimento', 'badge-recebimento')
                }
                
                # Função para badge de nota
                def badge_nota(nota):
                    if nota >= 90: return f'<span class="badge-status badge-excelente">Excelente</span>'
                    elif nota >= 80: return f'<span class="badge-status badge-bom">Bom</span>'
                    elif nota >= 70: return f'<span class="badge-status badge-atencao">Atenção</span>'
                    elif nota >= 60: return f'<span class="badge-status badge-risco">Risco</span>'
                    else: return f'<span class="badge-status badge-critico">Crítico</span>'
                
                # Função para cor da nota
                def cor_nota(nota):
                    if nota >= 90: return '#1E7A2A'
                    elif nota >= 80: return '#5FB65B'
                    elif nota >= 70: return '#E8B23A'
                    elif nota >= 60: return '#E67E22'
                    else: return '#D64545'
                
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
                            <th>Cód.</th>
                            <th class="center">Aderência</th>
                            <th class="center">Maturidade</th>
                            <th class="center">Conhecimento</th>
                            <th class="center">Eficiência</th>
                            <th class="center">Gaps/Estrut.</th>
                            <th class="center">Nota</th>
                            <th class="center">Nível</th>
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
                    
                    # Código
                    codigo_html = f'<span class="codigo-tipo">{row["tipo"]}</span>'
                    
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
                    
                    # Nível
                    nivel = nivel_maturidade(nota)
                    nivel_html = f'<td class="center"><span class="badge-status" style="background:{NIVEIS[nivel]["hex"]};color:white">N{nivel}</span></td>'
                    
                    html_table += f"""
                        <tr>
                            <td>{data_str}</td>
                            <td>{loja_str}</td>
                            <td>{frente_html}</td>
                            <td>{codigo_html}</td>
                            {topicos_html}
                            {nota_html}
                            {nivel_html}
                        </tr>
                    """
                
                html_table += """
                    </tbody>
                </table>
                </div>
                """
                
                # ── RENDERIZA O HTML COM components ──
                st.components.v1.html(html_table, height=500, scrolling=True)
                
                st.caption(f"{len(df_hist)} registro(s) · {df_hist['loja'].nunique()} lojas auditadas")
                
                # ── EXPORTAR HISTÓRICO ──
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    csv_hist = df_hist.to_csv(index=False, sep=';')
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
            LIMIAR_NAO_CONFORMIDADE = 60.0
            
            dados = {
                'loja': '', 
                'data': '', 
                'hora': '', 
                'nota_total': 0.0,
                'tipo_detectado': '',
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
            else:
                dados['tipo_detectado'] = ''
            
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
                r'Fotos\s+das\s+quest[oõ]es\s+do\s+t[oó]pico.*?(?=\d[\.\d]*♦|RESULTADOS|\Z)',
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
                
                if pct < LIMIAR_NAO_CONFORMIDADE:
                    nivel_str = f" | Nível {nivel_num}: {nivel_txt}" if nivel_num is not None else ""
                    obs_str = f" | Obs: {obs_item}" if obs_item else ""
                    dados['criticas'].append(f"{codigo} — {descricao_curta} ({obtido:.2f}/{possivel:.2f} → {pct:.1f}%){nivel_str}{obs_str}")
            
            return dados
        
        st.markdown(cab_html(
            "Importar PDF",
            "Envie o relatório de auditoria em PDF para extrair loja, notas e não conformidades automaticamente.",
            "⭳",
        ), unsafe_allow_html=True)

        # ── Upload do PDF com key dinâmica ──
        uploaded_file = st.file_uploader(
            "", 
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
                st.markdown("### Dados Extraídos - Confirme antes de salvar")
                
                # ── CAMPOS DO FORMULÁRIO (sem st.form para evitar Enter salvar) ──
                col1, col2 = st.columns(2)
                
                with col1:
                    loja_opts = [f"{l[0]} - {l[1]}" for l in LOJAS]
                    loja_default = next((l for l in loja_opts if l.startswith(dados_extraidos['loja'])), loja_opts[0])
                    
                    st.markdown('<span class="label-destaque">Loja</span>', unsafe_allow_html=True)
                    loja = st.selectbox("", loja_opts, index=loja_opts.index(loja_default) if loja_default in loja_opts else 0, key="import_loja", label_visibility="hidden")
                    
                    titulo_pdf = texto_completo[:300].upper()
                    
                    tipo_default = 'AÇO-AUD-01'  
                    
                    if 'AÇOUGUE' in titulo_pdf:
                        tipo_default = 'AÇO-AUD-01'
                    elif 'FRENTE DE LOJA' in titulo_pdf:
                        tipo_default = 'FRE-AUD-02'
                    elif 'RECEBIMENTO' in titulo_pdf:
                        tipo_default = 'REC-AUD-03'
                    
                    st.markdown('<span class="label-destaque">Frente</span>', unsafe_allow_html=True)
                    tipo = st.selectbox(
                        "", 
                        list(CHECKLISTS.keys()), 
                        index=list(CHECKLISTS.keys()).index(tipo_default) if tipo_default in CHECKLISTS else 0, 
                        format_func=lambda x: f"{CHECKLISTS[x]['nome']} — {x}", 
                        key="import_tipo",
                        label_visibility="hidden"
                    )
                    
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
                    data_audit_str = st.text_input("", value=data_default_str, key="import_data", help="Digite a data no formato DD/MM/AAAA", label_visibility="hidden")
                    
                    try: 
                        data_audit = datetime.strptime(data_audit_str, '%d/%m/%Y')
                    except ValueError: 
                        st.error("Formato de data inválido. Use DD/MM/AAAA")
                        data_audit = None
                    
                    st.markdown('<span class="label-destaque">Auditor</span>', unsafe_allow_html=True)
                    avaliador = st.text_input("", value="Auditor Controladoria", key="import_avaliador", label_visibility="hidden")
                    
                    if dados_extraidos['nota_total'] > 0: 
                        st.caption(f"Nota total extraída: **{dados_extraidos['nota_total']:.2f}%**")
                
                with col2:
                    st.markdown('<span class="label-topicos">Resumo dos Tópicos</span>', unsafe_allow_html=True)
                    pcts = []
                    slots = CHECKLISTS[tipo]['slots']
                    
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

                pop_base = pop_base_da_frente(df_pops_todos, tipo)

                st.markdown(
                    '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
                    'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
                    'POP avaliado por este checklist</div>',
                    unsafe_allow_html=True,
                )
                if pop_base is not None:
                    pop_base_id = pop_base.get('id')
                    pop_base_nome = str(pop_base.get('processo', '')).strip()
                    pop_base_cod = str(pop_base.get('codigo_2', '')).strip()
                    st.success(f"**{pop_base_cod}** — {pop_base_nome}")
                else:
                    pop_base_id, pop_base_nome, pop_base_cod = None, '', ''
                    df_frente = listar_processos_por_frente(df_pops_todos, tipo)
                    base_pool = df_frente if not df_frente.empty else df_pops_todos

                    opcoes = {'— nenhum POP cadastrado para esta frente —': None}
                    if not base_pool.empty:
                        for _, row in base_pool.iterrows():
                            cod = str(row.get('codigo_2', '')).strip()
                            nome = str(row.get('processo', '')).strip()
                            if nome:
                                opcoes[f"{cod} — {nome}" if cod else nome] = row

                    st.caption(
                        "O POP desta frente ainda não está cadastrado na aba Processos. "
                        "Escolha o documento correspondente ou deixe sem vínculo."
                    )
                    escolha_base = st.selectbox(
                        "POP de referência", list(opcoes), key="import_pop_base",
                        label_visibility="collapsed",
                    )
                    row_base = opcoes.get(escolha_base)
                    if row_base is not None:
                        pop_base_id = row_base.get('id')
                        pop_base_nome = str(row_base.get('processo', '')).strip()
                        pop_base_cod = str(row_base.get('codigo_2', '')).strip()

                st.markdown(
                    '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
                    'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
                    'Não Conformidades Críticas</div>'
                    '<div style="font-size:.8rem;color:#728177;margin:.2rem 0 .6rem;">'
                    'Itens abaixo de 60%. O ponto do POP vem do próprio enunciado quando ele '
                    'cita seção, anexo ou página — confira e ajuste se precisar.</div>',
                    unsafe_allow_html=True,
                )

                itens_criticos = [i for i in dados_extraidos['itens'] if i['pct'] < 60.0]

                criticas_estruturadas = []
                if not itens_criticos:
                    st.success("Nenhum item abaixo de 60% neste PDF.")
                else:
                    for item in itens_criticos:
                        pontos = detectar_pontos_pop(item['descricao'])
                        selo = "📎 " + " · ".join(pontos[:3]) if pontos else "sem ponto citado"

                        # Criticidade sugerida a partir do próprio pct do item (paridade
                        # com o HTML: nota mais baixa = mais crítico), sempre editável.
                        if item['pct'] < 30:
                            crit_sugerida = 'Alta'
                        elif item['pct'] < 50:
                            crit_sugerida = 'Média'
                        else:
                            crit_sugerida = 'Baixa'

                        with st.expander(
                            f"[{item['codigo']}] {item['pct']:.1f}% · {item['descricao_curta'][:80]} — {selo}",
                            expanded=False,
                        ):
                            if item.get('observacao'):
                                st.caption(f"Observação do auditor: {item['observacao']}")
                            ponto = st.text_input(
                                "Ponto do POP divergente",
                                value=" · ".join(pontos[:3]),
                                placeholder="Etapa, passo, seção, anexo ou página",
                                key=f"pop_ponto_{item['codigo']}",
                            )

                            col_a, col_b = st.columns(2)
                            with col_a:
                                criticidade_item = st.selectbox(
                                    "Criticidade", ['Alta', 'Média', 'Baixa'],
                                    index=['Alta', 'Média', 'Baixa'].index(crit_sugerida),
                                    key=f"pop_crit_{item['codigo']}",
                                )
                                status_item = st.selectbox(
                                    "Status", ['Aberta', 'Em andamento', 'Concluída'],
                                    key=f"pop_status_{item['codigo']}",
                                )
                            with col_b:
                                responsavel_item = st.text_input(
                                    "Responsável", key=f"pop_resp_{item['codigo']}",
                                )
                                prazo_item = st.date_input(
                                    "Prazo", value=None, key=f"pop_prazo_{item['codigo']}",
                                )
                            acao_item = st.text_area(
                                "Ação corretiva", key=f"pop_acao_{item['codigo']}", height=70,
                            )

                        criticas_estruturadas.append({
                            'texto': (
                                f"{item['codigo']} — {item['descricao_curta']} "
                                f"({item['obtido']:.2f}/{item['possivel']:.2f} → {item['pct']:.1f}%)"
                                + (f" | Nível {item['nivel']}: {item['nivel_txt']}" if item['nivel'] is not None else "")
                                + (f" | Obs: {item['observacao']}" if item.get('observacao') else "")
                            ),
                            'codigo_item': item['codigo'],
                            'pop_id': pop_base_id,
                            'pop_nome': pop_base_nome,
                            'pop_codigo_2': pop_base_cod,
                            'ponto_pop': ponto.strip(),
                            'confianca': 'base' if pop_base_nome else None,
                            'status': status_item,
                            'criticidade': criticidade_item,
                            'responsavel': responsavel_item.strip(),
                            'prazo': prazo_item.strftime('%Y-%m-%d') if prazo_item else '',
                            'acao_corretiva': acao_item.strip(),
                            'evidencia': item.get('observacao', '') or '',
                        })

                    if not pop_base_nome:
                        st.warning(
                            f"As {len(criticas_estruturadas)} não conformidade(s) ficarão sem POP "
                            "vinculado. Dá para salvar assim, mas elas não ficam rastreáveis ao processo."
                        )

                with st.expander("Editar texto bruto das críticas (avançado)", expanded=False):
                    st.caption(
                        "Se preencher aqui, este texto substitui os itens vinculados acima "
                        "e a auditoria é salva sem vínculo ao POP."
                    )
                    criticas_input = st.text_area(
                        "",
                        value="",
                        key="import_criticas_bruto",
                        placeholder="Uma por linha. Ex: 5.3 — Ausência de mofo, infiltrações ou pragas? (0,16/0,79 → 20.3%)",
                        height=200,
                        label_visibility="collapsed",
                    )

                st.markdown("---")
                
                if pcts:
                    total_nota = sum(POSSIVEL[i] * pcts[i] / 100 for i in range(5))
                    f = faixa(total_nota)
                    st.markdown(f"""
                    <div style="background:{f['cor']}15;border:2px solid {f['cor']};border-radius:8px;padding:12px 20px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;">Nota Total Calculada</span>
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
                    "Substituir Auditoria Existente" if existente_pdf else "Salvar Auditoria",
                    use_container_width=True, type="primary", key="btn_salvar_pdf",
                ):
                    if not loja or not tipo or not data_audit:
                        st.error("Preencha todos os campos obrigatórios.")
                    elif any(p < 0 or p > 100 for p in pcts):
                        st.error("As notas devem estar entre 0 e 100.")
                    else:
                        cod_loja = loja.split(' - ')[0]
                        # Texto bruto (expander avançado) tem prioridade quando preenchido;
                        # caso contrário salva os itens já vinculados ao POP.
                        if criticas_input.strip():
                            criticas_list = [
                                {**normalizar_critica(c.strip())}
                                for c in criticas_input.split('\n') if c.strip()
                            ]
                        else:
                            criticas_list = criticas_estruturadas
                        dados_para_salvar = {
                            'loja': cod_loja,
                            'data': data_audit.strftime('%Y-%m-%d'),
                            'tipo': tipo,
                            'avaliador': avaliador,
                            'topicos': [{'nome': CHECKLISTS[tipo]['slots'][i], 'possivel': POSSIVEL[i], 'pct': pcts[i]} for i in range(5)],
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
            "Registre manualmente os dados da auditoria sem necessidade de PDF.",
            "＋",
        ), unsafe_allow_html=True)

        # ── Inicializa o estado para controle de reset ──
        if "manual_reset" not in st.session_state:
            st.session_state.manual_reset = False

        # ── WIDGETS (sem form para evitar Enter salvar) ──
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<span class="label-destaque">Loja</span>', unsafe_allow_html=True)
            loja = st.selectbox("", [f"{l[0]} - {l[1]}" for l in LOJAS], key="manual_loja", label_visibility="hidden")
            
            st.markdown('<span class="label-destaque">Frente</span>', unsafe_allow_html=True)
            tipo = st.selectbox(
                "", 
                list(CHECKLISTS.keys()),
                format_func=lambda x: f"{CHECKLISTS[x]['nome']} — {x}",
                key="manual_tipo",
                label_visibility="hidden"
            )
            
            from datetime import datetime
            data_default_str = datetime.now().strftime('%d/%m/%Y')
            
            st.markdown('<span class="label-destaque">Data</span>', unsafe_allow_html=True)
            data_audit_str = st.text_input(
                "", 
                value=data_default_str, 
                key="manual_data",
                help="Digite a data no formato DD/MM/AAAA",
                label_visibility="hidden"
            )
            
            st.markdown('<span class="label-destaque">Auditor</span>', unsafe_allow_html=True)
            avaliador = st.text_input("", value="Auditor Controladoria", key="manual_avaliador", label_visibility="hidden")
        
        with col2:
            st.markdown('<span class="label-topicos">Resumo dos Tópicos</span>', unsafe_allow_html=True)
            pcts = []
            for i, slot in enumerate(CHECKLISTS[tipo]['slots']):
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

        pop_base_m = pop_base_da_frente(df_pops_manual, tipo)
        st.markdown(
            '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
            'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
            'POP avaliado por este checklist</div>',
            unsafe_allow_html=True,
        )
        if pop_base_m is not None:
            pop_m_id = pop_base_m.get('id')
            pop_m_nome = str(pop_base_m.get('processo', '')).strip()
            pop_m_cod = str(pop_base_m.get('codigo_2', '')).strip()
            st.success(f"**{pop_m_cod}** — {pop_m_nome}")
        else:
            pop_m_id, pop_m_nome, pop_m_cod = None, '', ''
            df_frente_m = listar_processos_por_frente(df_pops_manual, tipo)
            pool_m = df_frente_m if not df_frente_m.empty else df_pops_manual

            opcoes_m = {'— nenhum POP cadastrado para esta frente —': None}
            if not pool_m.empty:
                for _, row in pool_m.iterrows():
                    cod = str(row.get('codigo_2', '')).strip()
                    nome = str(row.get('processo', '')).strip()
                    if nome:
                        opcoes_m[f"{cod} — {nome}" if cod else nome] = row

            st.caption(
                "O POP desta frente ainda não está cadastrado na aba Processos. "
                "Escolha o documento correspondente ou deixe sem vínculo."
            )
            escolha_m = st.selectbox(
                "POP de referência", list(opcoes_m), key="manual_pop_base",
                label_visibility="collapsed",
            )
            row_m = opcoes_m.get(escolha_m)
            if row_m is not None:
                pop_m_id = row_m.get('id')
                pop_m_nome = str(row_m.get('processo', '')).strip()
                pop_m_cod = str(row_m.get('codigo_2', '')).strip()

        st.markdown(
            '<div style="font-size:.85rem;font-weight:800;color:#0d2a16;'
            'text-transform:uppercase;letter-spacing:.05em;margin-top:1.2rem;">'
            'Não Conformidades</div>'
            '<div style="font-size:.8rem;color:#728177;margin:.2rem 0 .6rem;">'
            'Cada card vira uma não conformidade rastreável, com POP, status, responsável e prazo.</div>',
            unsafe_allow_html=True,
        )

        if "manual_ncs" not in st.session_state:
            st.session_state.manual_ncs = []

        # ── POOL de POPs para o select de cada card (mesmo filtro por frente já usado acima) ──
        df_frente_ncs = listar_processos_por_frente(df_pops_manual, tipo)
        pool_ncs = df_frente_ncs if not df_frente_ncs.empty else df_pops_manual
        opcoes_pop_ncs = {'— herdar POP do checklist acima —': 'HERDAR', '— sem vínculo —': None}
        if not pool_ncs.empty:
            for _, row in pool_ncs.iterrows():
                cod = str(row.get('codigo_2', '')).strip()
                nome = str(row.get('processo', '')).strip()
                if nome:
                    opcoes_pop_ncs[f"{cod} — {nome}" if cod else nome] = row

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
                        "Status", ['Aberta', 'Em andamento', 'Concluída'],
                        index=['Aberta', 'Em andamento', 'Concluída'].index(nc_card.get('status') or 'Aberta'),
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
                    prazo_nc = st.date_input("Prazo", value=prazo_default, key=f"nc_prazo_{idx}")
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
                        {'nome': CHECKLISTS[tipo]['slots'][i], 'possivel': POSSIVEL[i], 'pct': pcts[i]}
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
            for key in ["manual_loja", "manual_tipo", "manual_data", "manual_avaliador"]:
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

        st.markdown(f"""
        <div style="background:#EFFAF0;border:1px solid #BFE6C2;border-left:4px solid #1E7A2A;border-radius:8px;padding:11px 14px;font-size:13px;margin-bottom:16px;display:flex;gap:10px;">
            <span style="font-size:18px;">✓</span>
            <div><b>Dados compartilhados em tempo real.</b> Toda auditoria registrada aqui fica salva
            automaticamente e aparece para qualquer pessoa que abrir o painel, em qualquer computador,
            na mesma hora.</div>
        </div>
        """, unsafe_allow_html=True)

        col_exp, col_imp = st.columns(2)

        with col_exp:
            st.markdown('<div class="aud-card"><h3>Exportar</h3>', unsafe_allow_html=True)
            st.caption("Os CSVs abrem direto no Excel com separador ponto e vírgula.")

            if df_auditorias.empty:
                st.info("Nenhuma auditoria para exportar ainda.")
            else:
                csv_auditorias = df_auditorias.drop(columns=['nivel'], errors='ignore').to_csv(index=False, sep=';')

                linhas_nc = []
                for _, row in df_auditorias.iterrows():
                    if isinstance(row.get('criticas'), list):
                        for c in row['criticas']:
                            cn = normalizar_critica(c)
                            linhas_nc.append({
                                'loja': row['loja'],
                                'loja_nome': dict(LOJAS).get(row['loja'], ''),
                                'frente': CHECKLISTS.get(row['tipo'], {}).get('nome', row['tipo']),
                                'data_auditoria': row['data'],
                                'item_checklist': cn['codigo_item'],
                                'nao_conformidade': cn['texto'],
                                'pop_codigo': cn['pop_codigo_2'],
                                'pop_nome': cn['pop_nome'],
                                'ponto_pop': cn['ponto_pop'],
                            })
                df_nc = pd.DataFrame(linhas_nc)
                csv_ncs = df_nc.to_csv(index=False, sep=';') if not df_nc.empty else (
                    "loja;loja_nome;frente;data_auditoria;item_checklist;"
                    "nao_conformidade;pop_codigo;pop_nome;ponto_pop\n"
                )

                json_base = df_auditorias.drop(columns=['nivel'], errors='ignore').to_json(orient='records', force_ascii=False, indent=1)

                st.download_button("Auditorias (CSV)", data=csv_auditorias,
                    file_name=f"auditorias_ferreira_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True, key="dados_export_auditorias_csv")
                st.download_button("Não conformidades (CSV)", data=csv_ncs,
                    file_name=f"nao_conformidades_ferreira_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True, key="dados_export_ncs_csv")
                st.download_button("Base completa (JSON)", data=json_base,
                    file_name=f"base_auditorias_ferreira_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
                    mime="application/json", use_container_width=True, key="dados_export_json")

                st.caption(f"{n_aud} auditorias · {n_ncs} não conformidades · {n_lojas_aud} loja(s)")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_imp:
            st.markdown('<div class="aud-card"><h3>Importar</h3>', unsafe_allow_html=True)
            st.caption("Cole o JSON exportado de outro painel ou backup. Registros com a mesma loja, "
                       "frente e data são atualizados; os demais são acrescentados.")

            imp_txt = st.text_area("", placeholder="Cole aqui o JSON exportado", height=160,
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
            (90, 100, 'Excelente', '#1E7A2A', 'Mínimo', 'Expansão — disseminar o modelo para outras lojas'),
            (80, 89,  'Bom',       '#5FB65B', 'Baixo',  'Melhoria contínua — revisão mensal dos gaps'),
            (70, 79,  'Atenção',   '#E8B23A', 'Médio',  'Prioritária — plano de ação em 60 dias'),
            (60, 69,  'Risco',     '#E67E22', 'Alto',   'Urgente — plano estrutural em até 30 dias'),
            (0,  59,  'Crítico',   '#D64545', 'Crítico','Imediata — intervenção emergencial'),
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
