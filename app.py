"""
app.py — Central de Processos e Riscos | Ferreira Supermercados
Banco: Supabase | PDFs: Google Drive (público via link)
"""

import streamlit as st
import pandas as pd
import base64, os
from db import (
    listar_processos, inserir_processo, atualizar_processo, deletar_processo,
    filter_opts, drive_preview, drive_direct,
    COLS_TABELA, LABELS, COL, STATUS_OPTS, CRITICIDADE_OPTS,
    usuario_aceitou_lgpd, registrar_aceite_lgpd,   # ← adicione aqui
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

# ── Auth ──────────────────────────────────────────────────────────────────────

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
        if st.button("✅ Aceitar e Entrar", use_container_width=True, type="primary"):
            try:
                registrar_aceite_lgpd(_user)
                st.session_state["lgpd_ok"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao registrar aceite: {e}")
    with col2:
        if st.button("❌ Recusar e Sair", use_container_width=True):
            for k in ["auth", "username", "admin", "lgpd_ok"]:
                st.session_state.pop(k, None)
            st.rerun()


def lgpd_gate():
    if st.session_state.get("lgpd_ok"):
        return True

    if usuario_aceitou_lgpd(_user):
        st.session_state["lgpd_ok"] = True
        return True

    # Abre o modal nativo — botões funcionam corretamente
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

# ── Verificação LGPD ──────────────────────────────────────────────────────────
if not lgpd_gate():
    st.stop()
# ── Helpers de renderização ───────────────────────────────────────────────────

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

# ── Sidebar ───────────────────────────────────────────────────────────────────
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

# ── Filtros ───────────────────────────────────────────────────────────────────
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

# ── Header ────────────────────────────────────────────────────────────────────
_logo_h_tag = f'<img src="{_LOGO_HEADER}" class="fff-logo-img" alt="Ferreira Supermercados">' if _LOGO_HEADER else '<div class="fff-badge">FFF</div>'
st.markdown(f"""
<div class="fff-header">
    {_logo_h_tag}
    <div class="header-text">
        <h1>Central de Processos e Riscos</h1>
        <p>Ferreira Supermercados · Repositório Corporativo</p>
    </div>
</div>""", unsafe_allow_html=True)

# ── Abas ──────────────────────────────────────────────────────────────────────
tab_labels = ["Processos"]
if _admin:
    tab_labels += ["Novo Processo", "Gerenciar"]
tabs = st.tabs(tab_labels)

# ════════════ ABA 1 — VISUALIZAÇÃO ════════════════════════════════════════════
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
        <span class="results-pill">📋 {n_filt} processo(s)</span>
        <span style="font-size:.72rem;color:var(--mu);">{total} total · filtre pela barra lateral</span>
      </div>""", unsafe_allow_html=True)

    if df.empty:
        st.markdown("</div>", unsafe_allow_html=True)
        st.info("Nenhum processo encontrado com os filtros aplicados.")
    else:
        th = "".join(f"<th>{LABELS.get(c, c)}</th>" for c in cols_visiveis)
        th += '<th class="c-doc">📄 Documento</th>'

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
                    st.success("🗑️ Processo removido.")
                    st.cache_data.clear(); st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Central de Processos e Riscos &nbsp;·&nbsp; Ferreira Supermercados &nbsp;·&nbsp; Sistema Interno
</div>""", unsafe_allow_html=True)