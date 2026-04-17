from __future__ import annotations

import argparse
import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "office": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "package": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    parser = argparse.ArgumentParser(
        description="Convert the 'Resultados dos processos' sheet from XLSX to CSV."
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        type=Path,
        default=project_root / "arquivos_adicionais" / "Hackaton_Enter_Base_Candidatos.xlsx",
        help="Path to the source XLSX file.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        default=project_root / "data" / "sentencas_60k.csv",
        help="Path to the destination CSV file.",
    )
    parser.add_argument(
        "--sheet",
        dest="sheet_name",
        default="Resultados dos processos",
        help="Workbook sheet name to export.",
    )
    return parser.parse_args()


def load_shared_strings(archive: ZipFile) -> list[str]:
    shared_strings_path = "xl/sharedStrings.xml"
    if shared_strings_path not in archive.namelist():
        return []

    shared_strings_tree = ET.fromstring(archive.read(shared_strings_path))
    values: list[str] = []
    for item in shared_strings_tree.findall("main:si", NS):
        text = "".join(node.text or "" for node in item.iterfind(".//main:t", NS))
        values.append(text)
    return values


def sheet_target(archive: ZipFile, sheet_name: str) -> str:
    workbook_tree = ET.fromstring(archive.read("xl/workbook.xml"))
    rels_tree = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationships = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_tree.findall("package:Relationship", NS)
    }

    for sheet in workbook_tree.findall("main:sheets/main:sheet", NS):
        if sheet.attrib["name"] != sheet_name:
            continue
        relationship_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        return "xl/" + relationships[relationship_id]

    raise ValueError(f"Sheet '{sheet_name}' not found in workbook.")


def column_index(cell_reference: str) -> int:
    letters = re.match(r"([A-Z]+)", cell_reference)
    if letters is None:
        raise ValueError(f"Invalid cell reference: {cell_reference}")

    value = 0
    for char in letters.group(1):
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value - 1


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iterfind(".//main:t", NS))

    raw_value = cell.find("main:v", NS)
    if raw_value is None:
        return ""

    value = raw_value.text or ""
    if cell_type == "s":
        return shared_strings[int(value)]
    return value


def iter_rows(archive: ZipFile, sheet_name: str) -> list[list[str]]:
    shared_strings = load_shared_strings(archive)
    target = sheet_target(archive, sheet_name)
    worksheet_tree = ET.fromstring(archive.read(target))
    xml_rows = worksheet_tree.findall(".//main:sheetData/main:row", NS)

    rows: list[list[str]] = []
    expected_length: int | None = None

    for row in xml_rows:
        cells = row.findall("main:c", NS)
        if not cells:
            continue

        if expected_length is None:
            expected_length = max(column_index(cell.attrib["r"]) for cell in cells) + 1

        values = [""] * expected_length
        for cell in cells:
            index = column_index(cell.attrib["r"])
            if index >= len(values):
                values.extend([""] * (index - len(values) + 1))
            values[index] = cell_value(cell, shared_strings)

        rows.append(values)

    return rows


def write_csv(rows: list[list[str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    with ZipFile(args.input_path) as archive:
        rows = iter_rows(archive, args.sheet_name)

    if not rows:
        raise ValueError("The selected sheet did not produce any rows.")

    write_csv(rows, args.output_path)

    data_rows = len(rows) - 1
    print(f"Sheet: {args.sheet_name}")
    print(f"Output: {args.output_path}")
    print(f"Columns: {len(rows[0])}")
    print(f"Data rows: {data_rows}")


if __name__ == "__main__":
    main()
