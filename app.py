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
    listar_auditorias, inserir_auditoria, deletar_auditoria,  
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
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Nunito:wght@400;500;600;700;800&display=swap');

:root {
    --vd:#0a3d1f; --vm:#115c2e; --vc:#1a8040; --vmt:#e6f4ec;
    --am:#f8c10a; --amd:#d4a200; --aml:#fff8d6;
    --cr:#f5f9f6; --tx:#0d2a16; --mu:#4d7a5e; --bd:#b8ddc7; --wh:#ffffff;
    --shadow: 0 4px 24px rgba(10,61,31,.10);
}
html,body,[class*="css"]{font-family:'Nunito',sans-serif;color:var(--tx);}
.stApp{background:var(--cr);}
.block-container{padding:0 1.5rem 3rem!important;}

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
.metric-card{background:var(--wh);border-radius:2px;padding:.85rem 1rem;border:1px solid var(--bd);border-left:3px solid var(--vm);}
.metric-num{font-family:'Oswald',sans-serif;font-size:2rem;font-weight:700;color:var(--vd);line-height:1;margin-bottom:.2rem;}
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
        u = st.text_input("Usuário", placeholder="seu.usuario")
        p = st.text_input("Senha", type="password", placeholder="••••••••")
        if st.button("Entrar →", use_container_width=True):
            if check_credentials(u.strip(), p):
                st.session_state.update(auth=True, username=u.strip(), admin=is_admin(u.strip()))
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

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
    <div class="sb-user"><span>👤</span><span>{{_user}}</span>{{ab}}</div>
    """, unsafe_allow_html=True)

    if st.button("Sair", use_container_width=True):
        [st.session_state.pop(k, None) for k in ["auth","username","admin"]]
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
    <div class="admin-header">
        <div>
            <div class="admin-title">Dashboard de Auditorias</div>
            <div class="admin-sub">
                Análise de conformidade dos checklists de Açougue, Frente de Loja e Recebimento
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    
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
    
    TEMAS = [
        {'tag': 'Painéis, anexos e gestão visual não afixados', 'kw': ['painel', 'anexo', 'gestão visual', 'quadros']},
        {'tag': 'Plano de ação inexistente ou informal', 'kw': ['plano de ação', 'plano de acao']},
        {'tag': 'POP vigente não afixado nos pontos', 'kw': ['pop', 'vigente', 'plastificad']},
        {'tag': 'Indicadores / KPIs não monitorados', 'kw': ['indicador', 'kpi', 'metas', 'métricas']},
        {'tag': 'Pragas e estrutura física deteriorada', 'kw': ['praga', 'rato', 'mofo', 'infiltra', 'ferrugem']},
        {'tag': 'Controle de temperatura manual/frágil', 'kw': ['temperatura', 'sensor', 'câmara']},
        {'tag': 'Reuniões de alinhamento não realizadas', 'kw': ['reunião', 'alinhamento']},
        {'tag': 'Integração e reciclagem de equipe frágeis', 'kw': ['integração', 'reciclagem', 'treina']},
        {'tag': 'Registros manuais / dupla digitação', 'kw': ['manual', 'caderno', 'dupla entrada']},
        {'tag': 'Falha de rotina no caixa', 'kw': ['cpf', 'sangria']}
    ]
    
    def tags_de(texto):
        texto_lower = texto.lower()
        return [t['tag'] for t in TEMAS if any(k in texto_lower for k in t['kw'])]
    
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
    
    def calcular_maturidade(df):
        """Calcula distribuição de maturidade"""
        df['nivel'] = df['total'].apply(nivel_maturidade)
        distrib = df['nivel'].value_counts().sort_index()
        return distrib
    
    def calcular_reincidencias(df):
        """Calcula reincidências de não conformidades"""
        # ── VERIFICA SE O DATAFRAME ESTÁ VAZIO OU NÃO TEM A COLUNA ──
        if df.empty or 'criticas' not in df.columns:
            return pd.DataFrame()
        
        todas_tags = []
        for criticas in df['criticas']:
            if isinstance(criticas, list):
                for c in criticas:
                    tags = tags_de(c)
                    todas_tags.extend(tags)
        
        if todas_tags:
            from collections import Counter
            freq = Counter(todas_tags)
            return pd.DataFrame(freq.items(), columns=['Tema', 'Frequência']).sort_values('Frequência', ascending=False)
        return pd.DataFrame()
    
    def gerar_insights(df):
        """Gera insights automáticos"""
        insights = []
        
        # Tópico mais frágil
        if 'topicos' in df.columns and not df.empty:
            topicos_medias = []
            for i, nome in enumerate(SLOTS_CURTOS):
                pcts = []
                for _, row in df.iterrows():
                    if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                        pcts.append(row['topicos'][i].get('pct', 0))
                if pcts:
                    topicos_medias.append({'topico': nome, 'media': sum(pcts)/len(pcts)})
            if topicos_medias:
                mais_fragil = min(topicos_medias, key=lambda x: x['media'])
                acima_80 = len([t for t in topicos_medias if t['media'] >= 80])
                insights.append(f"▼ **{mais_fragil['topico']}** é o tópico mais frágil da rede (média {mais_fragil['media']:.1f}%), abaixo de 80 em {len(df)-acima_80} de {len(df)} auditorias")
        
        # Frente com menor nota
        if not df.empty:
            notas_tipo = df.groupby('tipo')['total'].mean()
            if len(notas_tipo) > 0:
                pior = notas_tipo.idxmin()
                melhor = notas_tipo.idxmax()
                insights.append(f"◆ Entre as frentes, **{CHECKLISTS.get(pior, {}).get('nome', pior)}** tem a menor nota média ({notas_tipo[pior]:.1f}%) e **{CHECKLISTS.get(melhor, {}).get('nome', melhor)}** a maior ({notas_tipo[melhor]:.1f}%)")
        
        # Reincidência mais comum
        todas_tags = []
        for criticas in df['criticas']:
            if isinstance(criticas, list):
                for c in criticas:
                    todas_tags.extend(tags_de(c))
        
        if todas_tags:
            from collections import Counter
            freq_tags = Counter(todas_tags)
            if freq_tags:
                top = freq_tags.most_common(1)[0]
                lojas_com_top = set()
                for _, row in df.iterrows():
                    if isinstance(row['criticas'], list):
                        for c in row['criticas']:
                            if top[0] in tags_de(c):
                                lojas_com_top.add(row['loja'])
                insights.append(f"↻ A não conformidade que **mais se repete** é '{top[0]}', presente em {len(lojas_com_top)} loja(s)")
        
        return insights
    
    # ── SUB-ABAS ──
    sub_tabs = st.tabs([
        "📊 Painel geral", 
        "◎ Análise por loja", 
        "▲ Mapa de maturidade",
        "✦ Reincidências & insights",
        "≡ Rankings",
        "▦ Mapa de risco",
        "⭳ Importar PDF",
        "＋ Lançar manual",
        "☰ Histórico"
    ])
    
       # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 1 - PAINEL GERAL (COM KPIs DO HTML)
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[0]:
        st.markdown("### 📊 Painel geral da rede")
        st.caption("Consolidação das auditorias internas de Açougue, Frente de Loja e Recebimento.")
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            # ── KPIs ──
            metricas = calcular_metricas(df_auditorias)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                f = faixa(metricas['nota_rede'])
                st.markdown(f"""
                <div style="background:white;border:1px solid #DDE6DC;border-radius:12px;padding:16px;">
                    <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#728177;font-weight:600;">Nota média da rede</div>
                    <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:40px;font-weight:700;line-height:1;margin:8px 0 2px;color:#12331C;">
                        {metricas['nota_rede']:.1f}
                    </div>
                    <div style="font-size:12px;color:#728177;">
                        <span style="background:{f['cor']};color:white;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;">
                            {f['rot']}
                        </span>
                    </div>
                    <div style="height:4px;border-radius:3px;margin-top:12px;background:#F4F7F3;overflow:hidden;">
                        <div style="width:{min(100, metricas['nota_rede'])}%;height:100%;background:{f['cor']};border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                nivel = nivel_maturidade(metricas['nota_rede'])
                st.markdown(f"""
                <div style="background:white;border:1px solid #DDE6DC;border-radius:12px;padding:16px;">
                    <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#728177;font-weight:600;">Nível de maturidade</div>
                    <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:40px;font-weight:700;line-height:1;margin:8px 0 2px;color:#12331C;">
                        N{nivel}
                    </div>
                    <div style="font-size:15px;color:#728177;">
                        {NIVEIS[nivel]['rot']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background:white;border:1px solid #DDE6DC;border-radius:12px;padding:16px;">
                    <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#728177;font-weight:600;">Lojas auditadas</div>
                    <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:40px;font-weight:700;line-height:1;margin:8px 0 2px;color:#12331C;">
                        {metricas['lojas']}
                    </div>
                    <div style="font-size:16px;color:#728177;">
                        de {len(LOJAS)} lojas
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                cor_criticas = '#D64545' if metricas['total_criticas'] > 5 else '#1E7A2A'
                st.markdown(f"""
                <div style="background:white;border:1px solid #DDE6DC;border-radius:12px;padding:16px;">
                    <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#728177;font-weight:600;">Não conformidades críticas</div>
                    <div style="font-family:'Barlow Semi Condensed',sans-serif;font-size:40px;font-weight:700;line-height:1;margin:8px 0 2px;color:#12331C;">
                        {metricas['total_criticas']}
                    </div>
                    <div style="font-size:12px;color:#728177;">
                        <span style="background:{cor_criticas};color:white;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;">
                            {'Atenção' if metricas['total_criticas'] > 5 else 'Ok'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ── RANKING DAS LOJAS (BARRA) ──
            st.markdown("### 🏆 Ranking das lojas")
            st.caption("Média das frentes por loja")
            
            ranking_loja, _ = calcular_rankings(df_auditorias)
            
            for loja, nota in ranking_loja.items():
                f = faixa(nota)
                nome_loja = dict(LOJAS).get(loja, loja)
                pct = min(100, nota)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                    <div style="width:150px;font-size:12.5px;font-weight:500;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        <span style="font-weight:700;color:#1E7A2A;font-size:15px;">{loja}</span> {nome_loja}
                    </div>
                    <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;position:relative;">
                        <div style="display:block;height:100%;width:{pct}%;background:{f['cor']};border-radius:5px;transition:width 0.6s;"></div>
                    </div>
                    <div style="width:52px;text-align:right;font-family:'Barlow Semi Condensed',sans-serif;font-weight:700;font-size:15px;color:{f['cor']};">
                        {nota:.1f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ── GRÁFICOS ──
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Desempenho por processo")
                
                notas_tipo = df_auditorias.groupby('tipo')['total'].mean()
                
                for tipo, nota in notas_tipo.items():
                    f = faixa(nota)
                    nome = CHECKLISTS[tipo]['nome']
                    pct = min(100, nota)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                        <div style="width:150px;font-size:12.5px;font-weight:500;flex-shrink:0;">{nome}</div>
                        <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;position:relative;">
                            <div style="display:block;height:100%;width:{pct}%;background:{f['cor']};border-radius:5px;"></div>
                        </div>
                        <div style="width:52px;text-align:right;font-weight:700;font-size:15px;color:{f['cor']};">
                            {nota:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 📊 Desempenho por tópico")
                
                topicos_medias = []
                for i, nome in enumerate(SLOTS_CURTOS):
                    pcts = []
                    for _, row in df_auditorias.iterrows():
                        if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                            pcts.append(row['topicos'][i].get('pct', 0))
                    if pcts:
                        topicos_medias.append({'topico': nome, 'media': sum(pcts)/len(pcts)})
                
                for item in topicos_medias:
                    f = faixa(item['media'])
                    pct = min(100, item['media'])
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                        <div style="width:150px;font-size:12.5px;font-weight:500;flex-shrink:0;">{item['topico']}</div>
                        <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;position:relative;">
                            <div style="display:block;height:100%;width:{pct}%;background:{f['cor']};border-radius:5px;"></div>
                        </div>
                        <div style="width:52px;text-align:right;font-weight:700;font-size:15px;color:{f['cor']};">
                            {item['media']:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ── EXPORTAR ──
            csv_data = df_auditorias.to_csv(index=False, sep=';')
            st.download_button("📊 Exportar CSV", data=csv_data, 
                file_name=f"auditorias_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True)
    
       # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 2 - ANÁLISE POR LOJA
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[1]:
        st.markdown("### ◎ Análise por loja")
        st.caption("Card central compilado a partir do Resumo dos Tópicos de cada frente. Compara a loja com a média da rede e destaca fortalezas e fragilidades.")
        
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
                st.markdown("### 📋 Leitura rápida")
                
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
                
                st.markdown("---")
                
                # ── NÃO CONFORMIDADES ──
                st.markdown("### ⚠️ Não conformidades registradas")
                
                criticas_loja = []
                for _, row in df_loja.iterrows():
                    if isinstance(row['criticas'], list):
                        for c in row['criticas']:
                            criticas_loja.append({'tipo': row['tipo'], 'texto': c})
                
                if criticas_loja:
                    df_criticas = pd.DataFrame(criticas_loja)
                    df_criticas['Frente'] = df_criticas['tipo'].apply(
                        lambda x: CHECKLISTS.get(x, {}).get('nome', x)
                    )
                    df_criticas['Não conformidade'] = df_criticas['texto']
                    
                    st.dataframe(
                        df_criticas[['Frente', 'Não conformidade']],
                        column_config={
                            'Frente': st.column_config.Column('Frente', width='small'),
                            'Não conformidade': st.column_config.Column('Não conformidade'),
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Nenhuma não conformidade crítica registrada.")
                
                st.markdown("---")
                
                # ── EVOLUÇÃO ──
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
                        
                        st.line_chart(
                            df_evol.set_index('Data')[['Nota']],
                            color='#1E7A2A'
                        )
                        
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
    # SUB-ABA 3 - MAPA DE MATURIDADE
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[2]:
        st.markdown("### ▲ Mapa de maturidade")
        st.caption("Diagnóstico do nível de maturidade da rede a partir das auditorias aplicadas.")
        
        # ── VERIFICA SE HÁ DADOS ──
        if df_auditorias.empty:
            st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
        else:
            nota_media = df_auditorias['total'].mean()
            nivel_atual = nivel_maturidade(nota_media)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Escada de maturidade da rede**")
                
                for i in range(5, 0, -1):
                    n = NIVEIS[i]
                    is_atual = i == nivel_atual
                    st.markdown(f"""
                    <div style="padding:12px 16px;margin-bottom:6px;border-left:5px solid {n['hex']};
                        background:{'#e6f4ec' if is_atual else '#ffffff'};border-radius:10px;
                        border:1px solid {'#1E7A2A' if is_atual else '#DDE6DC'};
                        display:flex;justify-content:space-between;align-items:center;position:relative;">
                        <div>
                            <span style="font-weight:700;font-size:30px;width:40px;text-align:center;line-height:1;color:{n['hex']};">{i}</span>
                            <span style="font-weight:700;font-size:14px;margin-left:10px;">{n['rot']}</span>
                            <span style="font-size:11px;color:#728177;margin-left:6px;">({n['fx']})</span>
                            <p style="font-size:12px;color:#2A3A2E;margin-top:2px;">{n['desc']}</p>
                        </div>
                        {f'<span style="background:#1E7A2A;color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;position:absolute;right:14px;top:14px;">📍 ATUAL</span>' if is_atual else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Gap para próximo nível
                if nivel_atual < 5:
                    prox = 80 if nivel_atual == 4 else 70 if nivel_atual == 3 else 60
                    gap = prox - nota_media
                    st.info(f"📌 Faltam **{gap:.1f} pontos** na média da rede para alcançar o **Nível {nivel_atual+1} — {NIVEIS[nivel_atual+1]['rot']}** (limiar {prox}).")
                else:
                    st.success("⭐ Rede no nível máximo. Foco em sustentar e reduzir variabilidade entre lojas.")
            
            with col2:
                st.markdown("**Distribuição das lojas por nível**")
                
                df_niveis = df_auditorias.copy()
                df_niveis['nivel'] = df_niveis['total'].apply(nivel_maturidade)
                
                for i in range(5, 0, -1):
                    n = NIVEIS[i]
                    count = len(df_niveis[df_niveis['nivel'] == i])
                    total = len(df_niveis)
                    pct = 100 * count / total if total > 0 else 0
                    
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                        <div style="width:170px;font-size:12.5px;font-weight:500;flex-shrink:0;">
                            <span style="font-weight:700;color:{n['hex']};">N{i}</span> {n['rot']}
                        </div>
                        <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;">
                            <div style="display:block;height:100%;width:{pct}%;background:{n['hex']};border-radius:5px;"></div>
                        </div>
                        <div style="width:30px;text-align:right;font-weight:700;font-size:14px;">
                            {count}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.caption(f"{len(df_niveis)} loja(s) auditada(s). Meta: mover as lojas de Atenção/Risco para no mínimo **Nível 4 (Gerenciado)**.")
            
            st.markdown("---")
            
            # ── NÍVEL POR PROCESSO ──
            st.markdown("### 📊 Nível por processo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Nível por processo**")
                for tipo in df_auditorias['tipo'].unique():
                    nota = df_auditorias[df_auditorias['tipo'] == tipo]['total'].mean()
                    nv = nivel_maturidade(nota)
                    f = faixa(nota)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                        <div style="width:120px;font-size:12.5px;font-weight:500;flex-shrink:0;">{CHECKLISTS[tipo]['nome']}</div>
                        <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;">
                            <div style="display:block;height:100%;width:{min(100,nota)}%;background:{f['cor']};border-radius:5px;"></div>
                        </div>
                        <div style="width:80px;text-align:right;font-weight:700;font-size:14px;color:{f['cor']};">
                            N{nv} · {nota:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Nível por tópico**")
                for i, nome in enumerate(SLOTS_CURTOS):
                    pcts = []
                    for _, row in df_auditorias.iterrows():
                        if isinstance(row['topicos'], list) and len(row['topicos']) > i:
                            pcts.append(row['topicos'][i].get('pct', 0))
                    if pcts:
                        media = sum(pcts)/len(pcts)
                        nv = nivel_maturidade(media)
                        f = faixa(media)
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                            <div style="width:120px;font-size:12.5px;font-weight:500;flex-shrink:0;">{nome}</div>
                            <div style="flex:1;height:22px;background:#F4F7F3;border-radius:5px;overflow:hidden;">
                                <div style="display:block;height:100%;width:{min(100,media)}%;background:{f['cor']};border-radius:5px;"></div>
                            </div>
                            <div style="width:80px;text-align:right;font-weight:700;font-size:14px;color:{f['cor']};">
                                N{nv} · {media:.1f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
    
       # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 4 - REINCIDÊNCIAS & INSIGHTS
    # ═══════════════════════════════════════════════════════════════════

def classificar_causa_raiz(tema: str) -> str:
    """Agrupa o tema da não conformidade em uma categoria de causa raiz."""
    t = tema.lower()
    if any(k in t for k in ['painel', 'anexo', 'gestão visual', 'visual']):
        return 'Gestão Visual & Padronização'
    if any(k in t for k in ['plano de ação', 'informal', 'indicador', 'kpi', 'monitorado']):
        return 'Gestão & Indicadores'
    if any(k in t for k in ['pop', 'procedimento', 'afixado']):
        return 'Cumprimento de POP'
    if any(k in t for k in ['praga', 'estrutura', 'deteriorada', 'infiltra', 'mofo', 'ralo']):
        return 'Estrutura & Manutenção'
    if any(k in t for k in ['temperatura', 'manual', 'frágil', 'equipamento']):
        return 'Controle de Processo / Equipamento'
    if any(k in t for k in ['reunião', 'alinhamento']):
        return 'Rotina de Gestão'
    if any(k in t for k in ['integração', 'reciclagem', 'equipe', 'treinamento']):
        return 'Capacitação de Pessoas'
    if any(k in t for k in ['falha', 'caixa']):
        return 'Execução Operacional'
    return 'Outros'


def calcular_ranking_risco_lojas(df_filtrada):
    """Ranking de lojas por risco real, calculado pela escala oficial de Níveis 0 a 5.
    Nível 0 = Prática ausente (peso máximo: 5 pts) até Nível 5 = Excelência (0 pts)."""
    
    pesos = {
        'Nível 0': 5,  # Prática completamente ausente - peso máximo
        'Nível 1': 4,  # Iniciativa sem formalização
        'Nível 2': 3,  # Processo incompleto/inconsistente
        'Nível 3': 2,  # Processo com desvios frequentes
        'Nível 4': 1,  # Executado com falhas mínimas
        'Nível 5': 0   # Excelência - zero risco
    }
    risco = {}

    for _, row in df_filtrada.iterrows():
        loja = str(row['loja'])
        if loja not in risco:
            risco[loja] = {'score_risco': 0, 'total_criticas': 0, 'auditorias': 0, 'notas': []}

        risco[loja]['auditorias'] += 1
        risco[loja]['notas'].append(row['total'])

        if isinstance(row['criticas'], list):
            for c in row['criticas']:
                risco[loja]['total_criticas'] += 1
                peso_aplicado = 2  # Peso padrão (Nível 3) caso não identifique
                for nivel_str, peso in pesos.items():
                    if nivel_str in c:
                        peso_aplicado = peso
                        break
                risco[loja]['score_risco'] += peso_aplicado

    ranking = []
    for loja, d in risco.items():
        ranking.append({
            'loja': loja,
            'score_risco': d['score_risco'],
            'total_criticas': d['total_criticas'],
            'auditorias': d['auditorias'],
            'nota_media': sum(d['notas']) / len(d['notas']),
        })

    return sorted(ranking, key=lambda x: -x['score_risco'])


    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 4 - REINCIDÊNCIAS & INSIGHTS (VERSÃO LIMPA)
    # ═══════════════════════════════════════════════════════════════════
with sub_tabs[3]:
    st.markdown("### Reincidências & Insights")
    st.caption("Análise de causa raiz e ações prioritárias com base nos dados reais das auditorias.")

    if df_auditorias.empty:
        st.info("📌 Nenhuma auditoria registrada. Use a aba 'Importar PDF' ou 'Lançar Manual' para começar.")
    else:
        # ── FILTROS ──
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            filtro_loja = st.selectbox(
                "Filtrar por Loja",
                ["Todas"] + sorted(df_auditorias['loja'].unique().tolist()),
                key="reinc_loja"
            )

        with col_f2:
            filtro_frente = st.selectbox(
                "Filtrar por Frente",
                ["Todas"] + df_auditorias['tipo'].unique().tolist(),
                format_func=lambda x: CHECKLISTS.get(x, {}).get('nome', x) if x != "Todas" else "Todas",
                key="reinc_frente"
            )

        df_filtrada = df_auditorias.copy()
        if filtro_loja != "Todas":
            df_filtrada = df_filtrada[df_filtrada['loja'] == filtro_loja]
        if filtro_frente != "Todas":
            df_filtrada = df_filtrada[df_filtrada['tipo'] == filtro_frente]

        if df_filtrada.empty:
            st.info("Nenhuma auditoria encontrada com os filtros selecionados.")
        else:
            # ── CÁLCULOS ──
            df_reinc = calcular_reincidencias(df_filtrada)
            ranking_lojas = calcular_ranking_risco_lojas(df_filtrada)

            lojas_risco_sanitario = set()
            for _, row in df_filtrada.iterrows():
                if isinstance(row['criticas'], list):
                    for c in row['criticas']:
                        if any(x in c.lower() for x in ['praga', 'mofo', 'infiltra', 'estrutura', 'ralo']):
                            lojas_risco_sanitario.add(row['loja'])

            # ── DIAGNÓSTICO EXECUTIVO ──
            insights = []

            if lojas_risco_sanitario:
                insights.append({
                    'icone': '⚠️',
                    'classe': 'insight-critical',
                    'texto': (f"Risco sanitário ativo: {', '.join(sorted(lojas_risco_sanitario))} "
                                f"com registro de praga/infiltração — tratativa prioritária.")
                })

            if ranking_lojas:
                pior_loja = ranking_lojas[0]
                nome_pior = dict(LOJAS).get(pior_loja['loja'], pior_loja['loja'])
                insights.append({
                    'icone': '◆',
                    'classe': 'insight-warning',
                    'texto': (f"<b>{pior_loja['loja']} - {nome_pior}</b> lidera o ranking de risco "
                                f"({pior_loja['score_risco']} pts em {pior_loja['total_criticas']} não conformidades) "
                                f"— candidata a auditoria de acompanhamento prioritária.")
                })

            if not df_reinc.empty:
                top_tema = df_reinc.iloc[0]
                insights.append({
                    'icone': '▼',
                    'classe': 'insight-highlight',
                    'texto': (f"O tema mais recorrente é '<b>{top_tema['Tema']}</b>' "
                                f"com {int(top_tema['Frequência'])} ocorrências — indica falha sistêmica de padrão.")
                })

            # ── AÇÕES RECOMENDADAS (COM BUSCA POR PALAVRAS-CHAVE) ──
            acoes_recomendadas = []

            for _, row in df_reinc.iterrows():
                tema = row['Tema']
                freq = row['Frequência']
                causa = classificar_causa_raiz(tema)

                exemplos_reais = []
                lojas_afetadas = set()
                niveis_encontrados = []

                # ── EXTRAI PALAVRAS-CHAVE DO TEMA ──
                stopwords = {'de', 'da', 'do', 'das', 'dos', 'e', 'ou', 'para', 'com', 'sem', 
                            'em', 'na', 'no', 'nas', 'nos', 'à', 'ao', 'aos', 'que', 'se', 'por',
                            'um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as', 'é', 'não', 'mais'}
                
                palavras_chave = []
                for p in tema.lower().split():
                    p_limpa = p.strip('.,;:!?()[]{}"\'')
                    if len(p_limpa) > 3 and p_limpa not in stopwords:
                        palavras_chave.append(p_limpa)
                
                if not palavras_chave:
                    palavras_chave = tema.lower().split()[:3]

                for _, r in df_filtrada.iterrows():
                    if isinstance(r['criticas'], list):
                        for c in r['criticas']:
                            c_lower = c.lower()
                            # Busca por qualquer palavra-chave (match_count >= 1)
                            match_count = sum(1 for palavra in palavras_chave if palavra in c_lower)
                            
                            if match_count >= 1:
                                exemplos_reais.append({'loja': r['loja'], 'texto': c})
                                lojas_afetadas.add(str(r['loja']))

                                for n in range(0, 6):
                                    if f'nível {n}' in c_lower or f'nivel {n}' in c_lower:
                                        niveis_encontrados.append(n)
                                        break

                # Se não encontrou lojas, tenta uma busca mais ampla
                if not lojas_afetadas:
                    for _, r in df_filtrada.iterrows():
                        if isinstance(r['criticas'], list):
                            for c in r['criticas']:
                                c_lower = c.lower()
                                for palavra in palavras_chave[:3]:
                                    if palavra in c_lower:
                                        lojas_afetadas.add(str(r['loja']))
                                        break
                                if lojas_afetadas:
                                    break
                        if lojas_afetadas:
                            break

                # Nível médio
                nivel_medio = sum(niveis_encontrados) / len(niveis_encontrados) if niveis_encontrados else 3.0
                num_lojas = len(lojas_afetadas)

                # Urgência
                if nivel_medio <= 1.0:
                    urgencia = "alta"
                elif num_lojas > 2:
                    urgencia = "média"
                else:
                    urgencia = "baixa"

                if num_lojas > 3:
                    padrao_txt = "sistêmico"
                elif num_lojas > 1:
                    padrao_txt = "recorrente"
                else:
                    padrao_txt = "isolado"

                if nivel_medio == 0:
                    diagnostico = (f"[{causa}] ⛔ PRÁTICA AUSENTE em {num_lojas} loja(s) — "
                                    f"processo não está sendo executado. Gravidade máxima.")
                else:
                    diagnostico = (f"[{causa}] Problema {padrao_txt} em {num_lojas} loja(s), "
                                    f"gravidade média nível {nivel_medio:.1f}.")

                # Ações
                if nivel_medio == 0:
                    acao = (diagnostico + " AÇÃO URGENTE: Implementar imediatamente a prática ausente, "
                            "mesmo que de forma simplificada, para eliminar o risco. Em seguida, "
                            "desenhar o processo completo, treinar a equipe e integrar à rotina de gestão.")
                elif causa == 'Cumprimento de POP':
                    acao = (diagnostico + " AÇÃO: O procedimento já existe — o problema é adesão. "
                            "Fazer blitz de verificação sem aviso prévio e vincular resultado à avaliação do líder.")
                elif causa == 'Gestão Visual & Padronização':
                    acao = (diagnostico + " AÇÃO: Padronizar checklist de afixação nos pontos críticos e "
                            "incluir verificação de gestão visual na rotina diária do líder.")
                elif causa == 'Gestão & Indicadores':
                    acao = (diagnostico + " AÇÃO: Cobrar plano de ação formal (5W2H) em comitê mensal de "
                            "controladoria; sem plano registrado, o item permanece em aberto.")
                elif causa == 'Estrutura & Manutenção':
                    if nivel_medio <= 1.0:
                        acao = (diagnostico + " AÇÃO CRÍTICA: Acionar manutenção emergencial e controle de "
                                "pragas imediatamente, com validação fotográfica em até 48h.")
                    else:
                        acao = (diagnostico + " AÇÃO: Incluir a loja em cronograma preventivo de manutenção "
                                "e controle de pragas com verificação mensal.")
                elif causa == 'Controle de Processo / Equipamento':
                    if num_lojas > 2:
                        acao = (diagnostico + " AÇÃO: Avaliar substituição por monitoramento digital de "
                                "temperatura (elimina dependência de registro manual).")
                    else:
                        acao = (diagnostico + " AÇÃO: Reforçar o procedimento já existente com registro "
                                "obrigatório assinado e calibração de equipamento.")
                elif causa == 'Rotina de Gestão':
                    acao = (diagnostico + " AÇÃO: Cobrar cumprimento do ritual semanal já definido, com pauta "
                            "e ata obrigatórias anexadas ao painel de gestão.")
                elif causa == 'Capacitação de Pessoas':
                    acao = (diagnostico + " AÇÃO: Verificar se o programa de integração já existente está "
                            "sendo de fato aplicado a 100% dos admitidos; auditar registros de reciclagem.")
                else:
                    acao = (diagnostico + " AÇÃO: Análise de causa raiz dedicada com o gerente da loja, "
                            "com plano corretivo formal e prazo definido.")

                exemplos_formatados = [{'loja': ex['loja'], 'texto': ex['texto'][:120]} for ex in exemplos_reais[:3]]

                acoes_recomendadas.append({
                    'tema': tema,
                    'causa': causa,
                    'ocorr': freq,
                    'acao': acao,
                    'exemplos': exemplos_formatados,
                    'urgencia': urgencia,
                    'lojas_afetadas': sorted(lojas_afetadas) if lojas_afetadas else ['Não identificado']
                })

            urgencia_order = {'alta': 0, 'média': 1, 'baixa': 2}
            acoes_recomendadas.sort(key=lambda x: (urgencia_order.get(x['urgencia'], 3), -x['ocorr']))

            # ── EXIBIÇÃO ──
            style = """
            <style>
            .insight-item { padding: 12px 0; border-bottom: 1px solid #EEF3EE; }
            .insight-icon { font-size: 16px; margin-right: 8px; }
            .insight-text { font-size: 13px; color: #0d2a16; line-height: 1.5; }
            .insight-highlight { font-weight: 700; color: #1E7A2A; }
            .insight-warning { font-weight: 700; color: #E67E22; }
            .insight-critical { font-weight: 700; color: #D64545; }
            .data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 8px; }
            .data-table th { text-align: left; padding: 0.7rem; background: #0a3d1f; color: #9ecfb2; font-weight: 700; font-size: 0.68rem; text-transform: uppercase; border-bottom: 3px solid #f8c10a; }
            .data-table td { padding: 0.7rem; border-bottom: 1px solid #EEF3EE; vertical-align: top; }
            .data-table tr:hover { background: #f8faf8; }
            .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; }
            .tag-alta { background: #D64545; color: white; }
            .tag-media { background: #E67E22; color: white; }
            .tag-baixa { background: #728177; color: white; }
            </style>
            """
            st.markdown(style, unsafe_allow_html=True)

            # --- Diagnóstico executivo ---
            st.markdown("**Diagnóstico executivo**")
            html = ""
            for insight in insights:
                html += "<div class='insight-item'><div class='insight-text'>"
                html += f"<span class='insight-icon'>{insight['icone']}</span>"
                classe = insight['classe']
                html += f"<span class='{classe}'>{insight['texto']}</span>" if classe else insight['texto']
                html += "</div></div>"
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- Ranking de lojas por risco ---
            st.markdown("### Ranking de lojas por risco ponderado")
            st.caption("Score pela escala oficial: Nível 0 (5 pts - Prática ausente), Nível 1 (4 pts), Nível 2 (3 pts), Nível 3 (2 pts), Nível 4 (1 pt), Nível 5 (0 pts - Excelência).")

            if ranking_lojas:
                html = "<table class='data-table'><thead><tr><th>Loja</th><th>Score</th><th>N.C.</th><th>Nota média</th></tr></thead><tbody>"
                for r in ranking_lojas[:10]:
                    nome_loja = dict(LOJAS).get(r['loja'], r['loja'])
                    html += "<tr>"
                    html += f"<td><b>{r['loja']}</b> - {nome_loja}</td>"
                    html += f"<td style='color:#D64545;font-weight:700;'>{r['score_risco']}</td>"
                    html += f"<td>{r['total_criticas']}</td>"
                    html += f"<td>{r['nota_media']:.1f}%</td>"
                    html += "</tr>"
                html += "</tbody></table>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("Sem dados para ranking no recorte atual.")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- Ações recomendadas ---
            st.markdown("### Ações recomendadas por reincidência")

            if acoes_recomendadas:
                html = "<table class='data-table'><thead><tr>"
                html += "<th>Tema</th><th style='text-align:center;'>Ocorr.</th><th style='text-align:center;'>Urgência</th><th>Ação recomendada</th>"
                html += "</tr></thead><tbody>"

                for item in acoes_recomendadas:
                    tag_urg = f"<span class='tag tag-{item['urgencia'].replace('média','media')}'>{item['urgencia'].upper()}</span>"
                    html += "<tr>"
                    html += f"<td><b>{item['tema']}</b><br><span style='font-size:11px;color:#728177;'>{item['causa']}</span></td>"
                    html += f"<td style='text-align:center;font-weight:700;color:#D64545;'>{int(item['ocorr'])}</td>"
                    html += f"<td style='text-align:center;'>{tag_urg}</td>"
                    html += f"<td>{item['acao']}"
                    
                    if item.get('lojas_afetadas') and item['lojas_afetadas'] != ['Não identificado']:
                        html += f"<div style='font-size:0.75rem;color:#1E7A2A;margin-top:4px;'><strong>Lojas:</strong> {', '.join(item['lojas_afetadas'])}</div>"
                    
                    if item.get('exemplos'):
                        codigos_unicos = set()
                        for ex in item['exemplos']:
                            codigo = ex['texto'].split('—')[0].strip() if '—' in ex['texto'] else ex['texto'][:10]
                            if codigo and not codigo[0].isdigit():
                                codigo = ex['texto'][:10]
                            codigos_unicos.add(f"Loja {ex['loja']}: {codigo}")
                        
                        if codigos_unicos:
                            html += "<div style='font-size:0.75rem;color:#728177;margin-top:4px;'>"
                            html += f"<strong>Itens:</strong> {', '.join(list(codigos_unicos)[:3])}"
                            html += "</div>"
                    
                    html += "</td></tr>"

                html += "</tbody></table>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("Nenhuma ação recomendada no momento.")
                
    
        # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 5 - RANKINGS
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[4]:
        st.markdown("### Rankings")
        st.caption("Classificações pela auditoria mais recentes de cada loja/frente.")
        
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
                    topicos_medias.append({'topico': nome, 'media': sum(pcts)/len(pcts)})
            
            # ═══════════════════════════════════════════════════════════
            # LINHA 1: Ranking geral + Tópicos frágeis
            # ═══════════════════════════════════════════════════════════
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Ranking geral das lojas**")
                
                if not ranking_loja.empty:
                    html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem;'>"
                    html += "<thead><tr style='background:#0a3d1f;'>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:left;font-size:0.7rem;text-transform:uppercase;'>#</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:left;font-size:0.7rem;text-transform:uppercase;'>Loja</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:center;font-size:0.7rem;text-transform:uppercase;'>Nota</th>"
                    html += "<th style='color:#9ecfb2;padding:0.5rem 0.8rem;text-align:center;font-size:0.7rem;text-transform:uppercase;'>Faixa</th>"
                    html += "</tr></thead><tbody>"
                    
                    for i, (loja, nota) in enumerate(ranking_loja.items(), 1):
                        f = faixa(nota)
                        nome_loja = dict(LOJAS).get(loja, loja)
                        cor = f['cor']
                        rot = f['rot']
                        
                        html += "<tr style='border-bottom:1px solid #e8f3ec;'>"
                        html += "<td style='padding:0.65rem 0.8rem;font-weight:700;color:#1E7A2A;'>" + str(i) + "</td>"
                        html += "<td style='padding:0.65rem 0.8rem;font-weight:600;'><span style='font-weight:700;color:#1E7A2A;'>" + loja + "</span> " + nome_loja + "</td>"
                        html += "<td style='padding:0.65rem 0.8rem;text-align:center;font-weight:700;font-size:0.95rem;color:" + cor + ";'>" + f"{nota:.2f}" + "</td>"
                        html += "<td style='padding:0.65rem 0.8rem;text-align:center;'><span style='background:" + cor + ";color:white;padding:2px 10px;border-radius:20px;font-size:0.65rem;font-weight:700;'>" + rot + "</span></td>"
                        html += "</tr>"
                    
                    html += "</tbody></table>"
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma loja auditada.")
            
            with col2:
                st.markdown("**Tópicos mais frágeis da rede**")
                st.caption("Onde a rede mais perde pontos.")
                
                topicos_ordenados = sorted(topicos_medias, key=lambda x: x['media'])
                
                html = ""
                for item in topicos_ordenados:
                    f = faixa(item['media'])
                    cor = f['cor']
                    media_str = f"{item['media']:.2f}"
                    media_pct = f"{item['media']:.2f}"
                    
                    html += "<div style='display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #EEF3EE;'>"
                    html += "<div style='width:120px;font-size:0.85rem;font-weight:600;color:#0d2a16;'>" + item['topico'] + "</div>"
                    html += "<div style='flex:1;height:24px;background:#F4F7F3;border-radius:6px;overflow:hidden;'>"
                    html += "<div style='height:100%;width:" + media_pct + "%;background:" + cor + ";border-radius:6px;'></div>"
                    html += "</div>"
                    html += "<div style='width:50px;text-align:right;font-weight:700;font-size:0.9rem;color:" + cor + ";'>" + media_str + "</div>"
                    html += "</div>"
                
                st.markdown(html, unsafe_allow_html=True)
            
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
                    
                    st.markdown(html, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 6 - MAPA DE RISCO (HEATMAP)
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[5]:
        st.markdown("### Mapa de Risco")
        st.caption("Resumo dos Tópicos da auditoria mais recentes.")
        
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
                st.info(f"Nenhuma auditoria para {CHECKLISTS[tipo_heatmap]['nome']}")
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
                            <th>Aderência</th>
                            <th>Maturidade</th>
                            <th>Conhecimento</th>
                            <th>Eficiência</th>
                            <th>Gaps/Estrut.</th>
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
                
                # ── LEGENDA ─
                st.markdown("""
                <div style="display:flex;gap:20px;flex-wrap:wrap;font-size:0.85rem;color:#728177;margin-top:16px;padding-top:12px;border-top:1px solid #EEF3EE;">
                    <span style="display:flex;align-items:center;gap:6px;">
                        <span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:#1E7A2A;"></span>
                        Excelente (≥ 90)
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;">
                        <span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:#5FB65B;"></span>
                        Bom (80-89)
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;">
                        <span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:#E8B23A;"></span>
                        Atenção (70-79)
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;">
                        <span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:#E67E22;"></span>
                        Risco (60-69)
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;">
                        <span style="display:inline-block;width:16px;height:16px;border-radius:4px;background:#D64545;"></span>
                        Crítico (&lt; 60)
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
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
            
            texto = re.sub(r'Desenvolvido[^\n]*PariPassu[^\n]*', ' ', conteudo_pdf, flags=re.IGNORECASE)
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
            
            for n, m in enumerate(codigos):
                inicio = m.end()
                fim = codigos[n + 1].start() if n + 1 < len(codigos) else len(corpo)
                chunk = corpo[inicio:fim]
                m_nota = padrao_nota_item.search(chunk)
                if not m_nota: continue
                
                codigo = m.group(1)
                
                # ── CORREÇÃO: VALIDA O CÓDIGO ──
                # Ignora códigos inválidos como 2642.9, 2653.8, 2675.18
                partes = codigo.split('.')
                if len(partes) == 2:
                    try:
                        num_principal = int(partes[0])
                        num_secundario = int(partes[1])
                        # Código válido: 1 a 6 (tópicos) e secundário 1 a 99
                        if num_principal > 6 or num_secundario > 99:
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
                
                if nivel_num is not None and nivel_num in NIVEIS_ITEM: nivel_txt = NIVEIS_ITEM[nivel_num]
                
                item = {'codigo': codigo, 'descricao': descricao, 'descricao_curta': descricao_curta, 'obtido': obtido, 'possivel': possivel, 'pct': pct, 'nivel': nivel_num, 'nivel_txt': nivel_txt, 'observacao': obs_item}
                dados['itens'].append(item)
                
                if pct < LIMIAR_NAO_CONFORMIDADE:
                    nivel_str = f" | Nível {nivel_num}: {nivel_txt}" if nivel_num is not None else ""
                    obs_str = f" | Obs: {obs_item}" if obs_item else ""
                    dados['criticas'].append(f"{codigo} — {descricao_curta} ({obtido:.2f}/{possivel:.2f} → {pct:.1f}%){nivel_str}{obs_str}")
            
            return dados
        
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
                
                st.markdown('<span class="label-destaque">Não Conformidades Críticas</span>', unsafe_allow_html=True)
                criticas_text = ""
                if dados_extraidos['criticas']: 
                    criticas_text = "\n".join(dados_extraidos['criticas'])
                elif dados_extraidos['observacoes']: 
                    criticas_text = "\n".join([f"Observação: {obs}" for obs in dados_extraidos['observacoes']])
                
                criticas_input = st.text_area("", value=criticas_text, key="import_criticas", placeholder="Uma por linha. Ex: 5.3 — Ausência de mofo, infiltrações ou pragas? (0,16/0,79 → 20.3%) | Nível 1: Existe alguma iniciativa sem formalização.", help="Itens com nível 0-2 (percentual < 60%) são automaticamente identificados", height=240, label_visibility="hidden")
                
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
                
                # ── BOTÃO ÚNICO (Enter NÃO salva) ──
                if st.button("Salvar Auditoria", use_container_width=True, type="primary", key="btn_salvar_pdf"):
                    if not loja or not tipo or not data_audit: 
                        st.error("Preencha todos os campos obrigatórios.")
                    elif any(p < 0 or p > 100 for p in pcts): 
                        st.error("As notas devem estar entre 0 e 100.")
                    else:
                        cod_loja = loja.split(' - ')[0]
                        criticas_list = [c.strip() for c in criticas_input.split('\n') if c.strip()]
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
                            inserir_auditoria(dados_para_salvar)
                            st.success(f"✅ Auditoria salva com sucesso! Loja {cod_loja} - {CHECKLISTS[tipo]['nome']}")
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

        st.markdown("### Lançar Auditoria Manual")
        st.caption("Registre manualmente os dados da auditoria sem necessidade de PDF.")

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
        
        st.markdown('<span class="label-destaque">Não Conformidades Críticas</span>', unsafe_allow_html=True)
        criticas_text = st.text_area(
            "", 
            placeholder="Uma por linha. Ex: 5.3 — Praga de ratos nas câmaras (nota 1)",
            key="manual_criticas",
            height=200,
            label_visibility="hidden"
        )
        
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
        
        # ── BOTÃO (Enter NÃO salva porque não está dentro de um form) ──
        if st.button("Salvar Auditoria", use_container_width=True, type="primary", key="btn_salvar_manual"):
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
                criticas_list = [c.strip() for c in criticas_text.split('\n') if c.strip()]
                
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
                    inserir_auditoria(dados_para_salvar)
                    st.success(f"✅ Auditoria salva com sucesso! Loja {cod_loja} - {CHECKLISTS[tipo]['nome']}")
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
            for key in ["manual_loja", "manual_tipo", "manual_data", "manual_avaliador", "manual_criticas"]:
                if key in st.session_state:
                    del st.session_state[key]
            for i in range(5):
                key = f"pct_manual_{i}"
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
       # ═══════════════════════════════════════════════════════════════════
    # SUB-ABA 9 - HISTÓRICO
    # ═══════════════════════════════════════════════════════════════════
    with sub_tabs[8]:
        st.markdown("### Histórico de Auditorias")
        st.caption("Todas as auditorias registradas.")
        
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
                    
                    

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Central de Processos e Riscos &nbsp;·&nbsp; Ferreira Supermercados &nbsp;·&nbsp; Sistema Interno
</div>""", unsafe_allow_html=True)