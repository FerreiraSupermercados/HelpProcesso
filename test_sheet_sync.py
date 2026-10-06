import io
import unittest
import zipfile
import pandas as pd
from sheet_sync import FIELDS, build_sync_plan, sheet_records
from sheets_reader import parse_sheet_xlsx


def record(name, code, link=""):
    return {**dict.fromkeys(FIELDS, ""), "processo": name, "codigo_2": code, "link_documento": link}


class SyncTests(unittest.TestCase):
    def test_renumbered_processes_keep_ids(self):
        old = pd.DataFrame([{**record("Caixas", "POP-25"), "id": 1},
                            {**record("Atacado", "POP-23"), "id": 2}])
        plan = build_sync_plan([record("Caixas", "POP-23"), record("Atacado", "POP-25")], old)
        self.assertEqual(plan["updates"], [(1, {"codigo_2": "POP-23"}), (2, {"codigo_2": "POP-25"})])
        self.assertEqual(plan["inserts"], [])

    def test_renamed_process_matches_exact_document(self):
        old = pd.DataFrame([{**record("Nome antigo", "POP-26", "https://drive.google.com/file/d/abc/view"), "id": 8}])
        plan = build_sync_plan([record("Nome novo", "POP-24", "https://drive.google.com/file/d/abc/view?usp=sharing")], old)
        self.assertEqual(plan["updates"][0][0], 8)
        self.assertEqual(plan["inserts"], [])

    def test_conflicting_external_code_blocks_writes(self):
        old = pd.DataFrame([{**record("Caixas", "OLD"), "id": 1},
                            {**record("Outro cadastro", "NEW"), "id": 2}])
        with self.assertRaises(ValueError):
            build_sync_plan([record("Caixas", "NEW")], old)

    def test_idempotent_and_preserves_external_rows(self):
        r = record("Caixas", "POP-23")
        old = pd.DataFrame([{**r, "id": 1}, {**record("Manual", "MANUAL"), "id": 2}])
        plan = build_sync_plan([r], old)
        self.assertEqual(plan["updates"], [])
        self.assertEqual(plan["inserts"], [])

    def test_duplicate_sheet_codes_rejected(self):
        rows = [{FIELDS[k][0]: v for k, v in record(name, "SAME").items()} for name in ["A", "B"]]
        with self.assertRaises(ValueError):
            sheet_records(pd.DataFrame(rows))

    def test_hyperlink_used_instead_of_pdf_label(self):
        row = {FIELDS[k][0]: v for k, v in record("Caixas", "POP-23").items()}
        row["Link Documento"] = "nome.pdf"
        row["_link_Link Documento"] = "https://drive.google.com/file/d/abc/view"
        self.assertEqual(sheet_records(pd.DataFrame([row]))[0]["link_documento"], row["_link_Link Documento"])

    def test_xlsx_links_dates_and_numeric_codes(self):
        root = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        files = {
            "xl/workbook.xml": f'<workbook {root}><sheets><sheet name="Novo" sheetId="1"/></sheets></workbook>',
            "xl/styles.xml": f'<styleSheet {root}><cellXfs><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>',
            "xl/worksheets/sheet1.xml": f'''<worksheet {root} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheetData>
            <row r="1"><c r="A1" t="inlineStr"><is><t>Código</t></is></c><c r="B1" t="inlineStr"><is><t>Ultima Revisão</t></is></c><c r="C1" t="inlineStr"><is><t>Link Documento</t></is></c></row>
            <row r="2"><c r="A2"><v>3.0</v></c><c r="B2" s="1"><v>46080</v></c><c r="C2" t="inlineStr"><is><t>POP.pdf</t></is></c></row>
            </sheetData><hyperlinks><hyperlink ref="C2" r:id="r1"/></hyperlinks></worksheet>''',
            "xl/worksheets/_rels/sheet1.xml.rels": '<Relationships><Relationship Id="r1" Target="https://example.com/pop.pdf"/></Relationships>',
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as workbook:
            for path, xml in files.items():
                workbook.writestr(path, xml.encode("utf-8"))
        row = parse_sheet_xlsx(buffer.getvalue()).iloc[0]
        self.assertEqual(row["Código"], "3")
        self.assertEqual(row["Ultima Revisão"], "27/02/2026")
        self.assertEqual(row["_link_Link Documento"], "https://example.com/pop.pdf")


if __name__ == "__main__":
    unittest.main()
