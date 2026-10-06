"""Tabela de processos com filtros nos próprios cabeçalhos."""
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, JsCode


VALUES_FILTER = JsCode(r"""
class ColumnValuesFilter {
    init(params) {
        this.params = params;
        this.selected = null;
        this.root = document.createElement('div');
        this.root.style.cssText = 'width:300px;padding:14px;background:#fff;color:#0d2a16;font:14px Arial,sans-serif';
        this.search = document.createElement('input');
        this.search.type = 'search';
        this.search.placeholder = 'Pesquisar opções…';
        this.search.setAttribute('aria-label', 'Pesquisar opções de ' + params.colDef.headerName);
        this.search.style.cssText = 'box-sizing:border-box;width:100%;padding:8px;border:1px solid #b8ddc7;border-radius:5px;background:#fff;color:#0d2a16';
        this.search.addEventListener('input', () => this.renderList());
        this.root.appendChild(this.search);
        const allLabel = document.createElement('label');
        allLabel.style.cssText = 'display:flex;gap:8px;padding:12px 0;align-items:center;font-weight:700';
        this.all = document.createElement('input');
        this.all.type = 'checkbox';
        this.all.setAttribute('aria-label', 'Selecionar todos');
        allLabel.append(this.all, document.createTextNode('Selecionar todos'));
        this.all.addEventListener('change', () => {
            this.visibleValues().forEach(value => this.all.checked ? this.draft.add(value) : this.draft.delete(value));
            this.renderList();
        });
        this.root.appendChild(allLabel);
        this.list = document.createElement('div');
        this.list.style.cssText = 'max-height:240px;overflow:auto;border-top:1px solid #e8f3ec;border-bottom:1px solid #e8f3ec';
        this.root.appendChild(this.list);
        const actions = document.createElement('div');
        actions.style.cssText = 'display:flex;justify-content:space-between;gap:8px;padding-top:12px';
        const clear = document.createElement('button');
        clear.type = 'button'; clear.textContent = 'Limpar filtro';
        clear.style.cssText = 'padding:7px 12px;border:1px solid #b8ddc7;border-radius:5px;background:#fff;color:#0d2a16;cursor:pointer';
        clear.addEventListener('click', () => {
            this.selected = null;
            this.params.filterChangedCallback();
            if (this.hidePopup) this.hidePopup();
        });
        const apply = document.createElement('button');
        apply.type = 'button'; apply.textContent = 'Aplicar';
        apply.style.cssText = 'padding:7px 18px;border:0;border-radius:5px;background:#0a3d1f;color:#fff;cursor:pointer';
        apply.addEventListener('click', () => {
            const chosen = this.values.filter(value => this.draft.has(value));
            this.selected = chosen.length === this.values.length ? null : new Set(chosen);
            this.params.filterChangedCallback();
            if (this.hidePopup) this.hidePopup();
        });
        actions.append(clear, apply);
        this.root.appendChild(actions);
        this.refreshValues();
        this.draft = new Set(this.values);
        this.renderList();
    }
    value(node) { return String(node.data[this.params.colDef.field] ?? '').trim(); }
    refreshValues() {
        const values = new Set();
        this.params.api.forEachLeafNode(node => { if (node.data) values.add(this.value(node)); });
        this.values = [...values].sort((a, b) => a.localeCompare(b, 'pt-BR'));
    }
    visibleValues() {
        const term = this.search.value.toLocaleLowerCase('pt-BR');
        return this.values.filter(value => (value || '(Não preenchido)').toLocaleLowerCase('pt-BR').includes(term));
    }
    renderList() {
        this.list.replaceChildren();
        const visible = this.visibleValues();
        visible.forEach(value => {
            const label = document.createElement('label');
            label.style.cssText = 'display:flex;align-items:flex-start;gap:8px;padding:7px 2px;cursor:pointer;overflow-wrap:anywhere';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox'; checkbox.checked = this.draft.has(value);
            checkbox.setAttribute('aria-label', value || '(Não preenchido)');
            checkbox.addEventListener('change', () => {
                checkbox.checked ? this.draft.add(value) : this.draft.delete(value);
                this.updateAll();
            });
            label.append(checkbox, document.createTextNode(value || '(Não preenchido)'));
            this.list.appendChild(label);
        });
        if (!visible.length) this.list.textContent = 'Nenhuma opção encontrada.';
        this.updateAll();
    }
    updateAll() {
        const visible = this.visibleValues();
        const count = visible.filter(value => this.draft.has(value)).length;
        this.all.checked = visible.length > 0 && count === visible.length;
        this.all.indeterminate = count > 0 && count < visible.length;
    }
    afterGuiAttached(params) {
        this.removeDismissListeners();
        this.hidePopup = params.hidePopup;
        this.refreshValues();
        this.search.value = '';
        this.draft = this.selected === null ? new Set(this.values) : new Set(this.selected);
        this.renderList(); this.search.focus();
        // O menu está em um iframe; cliques no dashboard não chegam ao grid.
        this.outsideClick = event => {
            if (!this.root.contains(event.target)) this.closePopup();
        };
        this.escapeKey = event => {
            if (event.key === 'Escape') this.closePopup();
        };
        this.windowBlur = () => this.closePopup();
        this.dismissDocuments = [document];
        try {
            if (window.parent !== window && window.parent.document) {
                this.dismissDocuments.push(window.parent.document);
            }
        } catch (_) { /* Em outra origem, blur ainda fecha ao sair do iframe. */ }
        this.dismissDocuments.forEach(doc => {
            doc.addEventListener('pointerdown', this.outsideClick, true);
            doc.addEventListener('keydown', this.escapeKey, true);
        });
        window.addEventListener('blur', this.windowBlur);
    }
    closePopup() {
        this.removeDismissListeners();
        if (this.hidePopup) this.hidePopup();
    }
    removeDismissListeners() {
        (this.dismissDocuments || []).forEach(doc => {
            doc.removeEventListener('pointerdown', this.outsideClick, true);
            doc.removeEventListener('keydown', this.escapeKey, true);
        });
        if (this.windowBlur) window.removeEventListener('blur', this.windowBlur);
        this.dismissDocuments = [];
    }
    afterGuiDetached() { this.removeDismissListeners(); }
    destroy() { this.removeDismissListeners(); }
    getGui() { return this.root; }
    isFilterActive() { return this.selected !== null; }
    doesFilterPass(params) { return this.selected === null || this.selected.has(this.value(params.node)); }
    getModel() { return this.selected === null ? null : {filterType:'columnValues', values:[...this.selected]}; }
    setModel(model) { this.selected = model && Array.isArray(model.values) ? new Set(model.values) : null; }
    onNewRowsLoaded() { this.refreshValues(); }
}
""")


PDF_RENDERER = JsCode(r"""
class PdfLink {
    init(params) {
        const url = String(params.data.link_direto || '');
        this.element = document.createElement(/^https?:\/\//i.test(url) ? 'a' : 'span');
        this.element.textContent = /^https?:\/\//i.test(url) ? '📄 Abrir PDF' : '—';
        if (this.element.tagName === 'A') {
            this.element.href = url;
            this.element.target = '_blank';
            this.element.rel = 'noopener noreferrer';
            this.element.style.cssText = 'color:#0a3d1f;font-weight:700;text-decoration:underline';
        }
    }
    getGui() { return this.element; }
}
""")


def grid_options(columns, labels, state=None):
    definitions = [{"field": c, "headerName": labels.get(c, c),
                    "width": 320 if c == "processo" else 230 if c in ("macroprocesso", "tipo_documento", "tipo_criterio") else 150,
                    "tooltipField": c} for c in columns]
    definitions.append({"field": "documento", "headerName": "Documento", "width": 170,
                        "cellRenderer": PDF_RENDERER})
    options = {
        "columnDefs": definitions,
        "defaultColDef": {
            "filter": VALUES_FILTER, "floatingFilter": False,
            "sortable": True, "resizable": True, "editable": False,
            "suppressHeaderMenuButton": False, "menuTabs": ["filterMenuTab"],
        },
        "rowHeight": 44, "headerHeight": 44, "columnMenu": "legacy", "suppressMenuHide": True,
        "icons": {"menu": '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 3h12L9 9v4l-2-1V9z" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'},
        "getRowId": JsCode("function(params) { return String(params.data.id); }"),
        "overlayNoRowsTemplate": '<span>Nenhum processo encontrado com os filtros aplicados.</span>',
        "localeText": {"filterOoo": "Filtrar…", "contains": "Contém", "equals": "Igual a",
                       "notEqual": "Diferente de", "startsWith": "Começa com", "blank": "Não preenchido",
                       "notBlank": "Preenchido", "resetFilter": "Limpar", "andCondition": "E",
                       "orCondition": "OU", "noRowsToShow": "Nenhum processo encontrado",
                       "ariaFilterColumn": "Filtrar coluna", "ariaMenuColumn": "Menu da coluna"},
    }
    if state:
        options["initialState"] = state
    return options


def render_process_grid(frame, columns, labels):
    data = frame.copy()
    data["documento"] = data.get("link_direto", pd.Series("", index=data.index)).fillna("").astype(str).map(
        lambda url: "Com PDF" if url.startswith("http") else "Sem PDF")
    result = AgGrid(
        data, gridOptions=grid_options(columns, labels, st.session_state.get("processos_grid_state")),
        height=550, theme="light", key=f"processos_grid_values_{st.session_state.get('processos_grid_reset', 0)}",
        allow_unsafe_jscode=True, enable_enterprise_modules=False,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_on=[("filterChanged", 400), "sortChanged"], server_sync_strategy="server_wins",
        custom_css={
            ".ag-header": {"background-color": "#0a3d1f !important", "color": "#ffffff !important"},
            ".ag-header-cell-text": {"color": "#ffffff !important", "font-weight": "700"},
            ".ag-header-icon": {"color": "#ffffff !important"},
            ".ag-floating-filter-input input": {"color": "#0d2a16 !important", "background-color": "#ffffff !important"},
            ".ag-row": {"color": "#0d2a16 !important", "background-color": "#ffffff !important", "font-family": "Arial, sans-serif"},
            ".ag-row-odd": {"background-color": "#f4fbf6 !important"},
            ".ag-root-wrapper": {"border-color": "#b8ddc7 !important", "border-radius": "10px"},
        },
    )
    if result.grid_state:
        st.session_state["processos_grid_state"] = result.grid_state
    filtered = result.data
    return data if filtered is None else filtered
