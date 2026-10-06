"""
sheets_reader.py
Lê dados e hiperlinks da planilha via Google Sheets API v4.
"""

import requests
import pandas as pd
from typing import Optional
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal


SPREADSHEET_ID = "1joUKeyGMEi0TjL0aZ3-xGakW8AzhFJ6WwZ-fbrpSUbM"
SHEET_GID = "1167134340"


def fetch_public_sheet_data() -> pd.DataFrame:
    """Lê a aba pública em XLSX, preservando os hiperlinks que o CSV perde."""
    response = requests.get(
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export",
        params={"format": "xlsx", "gid": SHEET_GID}, timeout=30,
    )
    response.raise_for_status()
    return parse_sheet_xlsx(response.content)


def parse_sheet_xlsx(content: bytes) -> pd.DataFrame:
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(io.BytesIO(content)) as workbook:
        sheets = ET.fromstring(workbook.read("xl/workbook.xml")).findall("s:sheets/s:sheet", ns)
        if len(sheets) != 1:
            raise ValueError("A exportação deve conter somente a aba configurada da planilha.")
        strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            strings = ["".join(x.itertext()) for x in ET.fromstring(
                workbook.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        tree = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        styles = ET.fromstring(workbook.read("xl/styles.xml"))
        custom_formats = {int(x.attrib["numFmtId"]): x.attrib["formatCode"]
                          for x in styles.findall("s:numFmts/s:numFmt", ns)}
        format_ids = [int(x.attrib.get("numFmtId", 0))
                      for x in styles.findall("s:cellXfs/s:xf", ns)]
        rel_path = "xl/worksheets/_rels/sheet1.xml.rels"
        relationships = {}
        if rel_path in workbook.namelist():
            relationships = {x.attrib["Id"]: x.attrib.get("Target", "")
                             for x in ET.fromstring(workbook.read(rel_path))}
        links = {x.attrib["ref"]: relationships.get(x.attrib.get(f"{{{rel_ns}}}id"), "")
                 for x in tree.findall("s:hyperlinks/s:hyperlink", ns)}
        rows = []
        for row in tree.findall("s:sheetData/s:row", ns):
            values = {}
            for cell in row.findall("s:c", ns):
                ref = cell.attrib["r"]
                index = 0
                for letter in re.match(r"[A-Z]+", ref).group():
                    index = index * 26 + ord(letter) - ord("A") + 1
                value = cell.find("s:v", ns)
                value = value.text or "" if value is not None else ""
                if cell.attrib.get("t") == "s":
                    value = strings[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(cell.find("s:is", ns).itertext())
                elif value and cell.attrib.get("t", "n") == "n":
                    fmt_id = format_ids[int(cell.attrib.get("s", 0))]
                    fmt = custom_formats.get(fmt_id, "")
                    if fmt_id in range(14, 23) or re.search(r"[dy]", re.sub(r'"[^"]*"', '', fmt), re.I):
                        value = (datetime(1899, 12, 30) + timedelta(days=float(value))).strftime("%d/%m/%Y")
                    else:
                        value = format(Decimal(value).normalize(), "f")
                values[index - 1] = (value, links.get(ref, ""))
            rows.append(values)
        if not rows:
            raise ValueError("A planilha não possui cabeçalho.")
        headers, seen = [], {}
        for index in range(max(rows[0]) + 1):
            header = rows[0].get(index, ("", ""))[0].strip() or f"Col_{index}"
            count = seen.get(header, 0)
            seen[header] = count + 1
            headers.append(f"{header}_{count}" if count else header)
        records = []
        for row in rows[1:]:
            record = {}
            for index, header in enumerate(headers):
                value, link = row.get(index, ("", ""))
                record[header] = value
                if link:
                    record[f"_link_{header}"] = link
            if any(str(v).strip() for v in record.values()):
                records.append(record)
        return pd.DataFrame(records)


def get_sheet_name_by_gid(api_key: str, gid: str) -> Optional[str]:
    """Retorna o nome da aba pelo GID."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}?key={api_key}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    for sheet in data.get("sheets", []):
        props = sheet.get("properties", {})
        if str(props.get("sheetId")) == str(gid):
            return props.get("title")
    return None


def fetch_sheet_data(api_key: str) -> pd.DataFrame:
    """
    Busca dados da planilha incluindo hiperlinks das células.
    Retorna um DataFrame com uma coluna extra '_link_<col>' para cada coluna
    que tiver hiperlinks (normalmente a última coluna de PDF).
    """
    sheet_name = get_sheet_name_by_gid(api_key, SHEET_GID)
    if not sheet_name:
        raise ValueError(f"Aba com GID {SHEET_GID} não encontrada.")

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
        f"?includeGridData=true"
        f"&ranges={requests.utils.quote(sheet_name)}"
        f"&key={api_key}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    raw = resp.json()

    sheets = raw.get("sheets", [])
    if not sheets:
        raise ValueError("Nenhuma aba retornada pela API.")

    grid_data = sheets[0].get("data", [{}])[0]
    row_data = grid_data.get("rowData", [])

    if not row_data:
        return pd.DataFrame()

    def cell_value(cell: dict) -> str:
        """Extrai valor formatado ou bruto de uma célula."""
        if not cell:
            return ""
        fv = cell.get("formattedValue")
        if fv is not None:
            return str(fv)
        ev = cell.get("effectiveValue", {})
        for key in ("stringValue", "numberValue", "boolValue", "formulaValue"):
            if key in ev:
                return str(ev[key])
        return ""

    def cell_hyperlink(cell: dict) -> str:
        """Extrai hiperlink de uma célula (se houver)."""
        if not cell:
            return ""
        # Hiperlink direto na célula
        link = cell.get("hyperlink", "")
        if link:
            return link
        # Hiperlink dentro de runs de texto rico
        text_format_runs = cell.get("textFormatRuns", [])
        for run in text_format_runs:
            fmt = run.get("format", {})
            link = fmt.get("link", {}).get("uri", "")
            if link:
                return link
        return ""

    # Linha de cabeçalho
    header_row = row_data[0].get("values", []) if row_data else []
    headers = [cell_value(c) for c in header_row]

    # Normaliza cabeçalhos duplicados
    seen: dict = {}
    clean_headers = []
    for h in headers:
        h = h.strip()
        if h == "":
            h = f"Col_{len(clean_headers)}"
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        clean_headers.append(h)

    # Linhas de dados
    rows = []
    for row in row_data[1:]:
        cells = row.get("values", [])
        row_dict: dict = {}
        for i, col in enumerate(clean_headers):
            cell = cells[i] if i < len(cells) else {}
            row_dict[col] = cell_value(cell)
            link = cell_hyperlink(cell)
            if link:
                row_dict[f"_link_{col}"] = link
        rows.append(row_dict)

    df = pd.DataFrame(rows)

    # Remove linhas completamente vazias
    content_cols = [c for c in df.columns if not c.startswith("_link_")]
    df = df.dropna(subset=content_cols, how="all")
    df = df[df[content_cols].apply(lambda r: r.str.strip().ne("").any(), axis=1)]
    df = df.reset_index(drop=True)

    return df


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Detecta automaticamente quais colunas do DataFrame correspondem
    a cada campo esperado, por correspondência parcial de nome.
    Retorna um dicionário: papel -> nome_da_coluna_real
    """
    mapping = {}
    cols_lower = {c.lower(): c for c in df.columns if not c.startswith("_link_")}

    candidates = {
        "tipo_documento":  ["tipo de documento", "tipo_documento", "tipodocumento"],
        "objetivo":        ["objetivo estratégico", "objetivo estrategico", "objetivo"],
        "macroprocesso":   ["macroprocesso", "macro"],
        "codigo_macro":    ["código", "codigo"],
        "processo":        ["processo"],
        "codigo_processo": ["código_1", "codigo_1", "código 1"],
        "sigla":           ["sigla", "pop", "cod"],
        "status":          ["status"],
        "criticidade":     ["criticidade", "nivel de criticidade", "nível de criticidade"],
        "tipo_criterio":   ["tipo de critério", "tipo de criterio", "critério"],
        "ultima_revisao":  ["ultima revisão", "última revisão", "ultima revisao", "data"],
        "link_documento":  ["link documento", "link_documento", "link do documento", "arquivo"],
    }

    for role, keywords in candidates.items():
        for kw in keywords:
            for cl, real in cols_lower.items():
                if kw in cl:
                    mapping[role] = real
                    break
            if role in mapping:
                break

    return mapping
