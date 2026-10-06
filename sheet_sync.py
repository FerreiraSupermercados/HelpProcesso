"""Sincronização unidirecional: planilha oficial -> catálogo no Supabase."""
import re
import unicodedata
import threading
from sheets_reader import fetch_public_sheet_data

_SYNC_LOCK = threading.Lock()


def process_name(value):
    # Correção ortográfica presente na migração do catálogo antigo.
    return comparable(value).replace("INVETARIOS", "INVENTARIOS")


def document_key(value):
    value = str(value or "").strip()
    match = re.search(r"/file/d/([\w-]+)", value) or re.search(r"[?&]id=([\w-]+)", value)
    return match.group(1) if match and "drive.google.com" in value else value


def comparable(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip().upper()


FIELDS = {
    "tipo_documento": ["Tipo de documento"],
    "sigla": ["Sigla"],
    "tipo_atividade": ["Tipo de atividade"],
    "sigla_1": ["Sigla 2", "Sigla_1"],
    "macroprocesso": ["Macroprocessos"],
    "codigo": ["Código"],
    "processo": ["Coluna 7", "Processos", "Processo"],
    "codigo_1": ["Código 2", "Código_1"],
    "codigo_2": ["Código 3", "Código_2"],
    "revisado_gestor": ["Revisado pelo Gestor"],
    "observacoes": ["Observações"],
    "status": ["Status"],
    "nivel_atual": ["Nível atual"],
    "tipo_criterio": ["Tipo de critério"],
    "criticidade": ["Nive de Criticidade", "Nível de Criticidade"],
    "ultima_revisao": ["Ultima Revisão"],
    "link_documento": ["Link Documento"],
    "objetivo": ["Objetivo Estratégico"],
}


def sheet_records(frame):
    columns = {comparable(c): c for c in frame.columns if not c.startswith("_link_")}
    mapping = {}
    for field, aliases in FIELDS.items():
        for alias in aliases:
            if comparable(alias) in columns:
                mapping[field] = columns[comparable(alias)]
                break
    missing = set(FIELDS) - mapping.keys()
    if missing:
        raise ValueError("Colunas ausentes na planilha: " + ", ".join(sorted(missing)))
    records = []
    for raw in frame.fillna("").to_dict("records"):
        record = {field: str(raw.get(column, "")).strip() for field, column in mapping.items()}
        if not record["processo"]:
            continue
        link_column = mapping["link_documento"]
        link = str(raw.get(f"_link_{link_column}", "") or record["link_documento"]).strip()
        if link and not re.match(r"^https?://", link, re.I):
            raise ValueError(f"Documento sem hiperlink válido: {record['processo']}")
        record["link_documento"] = link
        records.append(record)
    if not records:
        raise ValueError("Nenhum processo encontrado na planilha; banco preservado.")
    for field in ("processo", "codigo_2"):
        values = [comparable(r[field]) for r in records if r[field]]
        if len(values) != len(set(values)):
            raise ValueError(f"Planilha possui {field} duplicado; sincronização cancelada.")
    return records


def build_sync_plan(records, existing):
    """Preserva IDs pelo nome; códigos podem ter sido renumerados na planilha."""
    existing = existing.fillna("").to_dict("records")
    names, codes, documents = {}, {}, {}
    for row in existing:
        names.setdefault(process_name(row["processo"]), []).append(row)
        if row.get("link_documento"):
            documents.setdefault(document_key(row["link_documento"]), []).append(row)
        if row.get("codigo_2"):
            codes.setdefault(comparable(row["codigo_2"]), []).append(row)
    sheet_names = {process_name(r["processo"]) for r in records}
    used, updates, inserts = set(), [], []
    for record in records:
        matches = names.get(process_name(record["processo"]), [])
        if not matches and record["link_documento"]:
            matches = [r for r in documents.get(document_key(record["link_documento"]), [])
                       if process_name(r["processo"]) not in sheet_names]
        if not matches and record["codigo_2"]:
            matches = [r for r in codes.get(comparable(record["codigo_2"]), [])
                       if process_name(r["processo"]) not in sheet_names]
        if len(matches) > 1:
            raise ValueError(f"Cadastro ambíguo no banco: {record['processo']}")
        if not matches:
            inserts.append(record)
            continue
        old = matches[0]
        if old["id"] in used:
            raise ValueError("Dois processos da planilha correspondem ao mesmo cadastro.")
        used.add(old["id"])
        changes = {k: v for k, v in record.items() if str(old.get(k, "")).strip() != v}
        if changes:
            updates.append((int(old["id"]), changes))
    # Não deixa registros externos à planilha ocuparem códigos importados.
    for record in records:
        if record["codigo_2"] and any(r["id"] not in used for r in codes.get(comparable(record["codigo_2"]), [])):
            raise ValueError(f"Código em conflito com cadastro fora da planilha: {record['codigo_2']}")
    return {"updates": updates, "inserts": inserts, "total": len(records)}


def synchronize_processes():
    with _SYNC_LOCK:
        return _synchronize_processes()


def _synchronize_processes():
    from db import listar_processos, atualizar_processo, inserir_processo
    records = sheet_records(fetch_public_sheet_data())
    plan = build_sync_plan(records, listar_processos())
    for process_id, changes in plan["updates"]:
        atualizar_processo(process_id, changes)
    for record in plan["inserts"]:
        inserir_processo(record)
    return {"total": plan["total"], "updated": len(plan["updates"]), "inserted": len(plan["inserts"])}
