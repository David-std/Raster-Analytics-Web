import csv
from datetime import datetime

from openpyxl import Workbook
from pipelines.processing.onsv import build_lima_pedestrian_fatal_crashes


CRASH_HEADERS = [
    "CÓDIGO SINIESTRO",
    "FECHA SINIESTRO",
    "HORA SINIESTRO",
    "CLASE SINIESTRO",
    "CANTIDAD DE FALLECIDOS",
    "CANTIDAD DE LESIONADOS",
    "CANTIDAD DE VEHICULOS DAÑADOS",
    "DEPARTAMENTO",
    "PROVINCIA",
    "DISTRITO",
    "ZONA",
    "TIPO DE VÍA",
    "RED VIAL",
    "COD CARRETERA",
    "COORDENADAS LATITUD",
    "COORDENADAS  LONGITUD",
    "CONDICIÓN CLIMÁTICA",
    "ZONIFICACIÓN",
    "CARACTERÍSTICAS DE VÍA",
    "PERFIL LONGITUDINAL VÍA",
    "SUPERFICIE DE CALZADA",
    "¿EXISTE SEÑAL VERTICAL?",
    "¿EXISTE SEÑAL HORIZONTAL?",
    "CAUSA FACTOR PRINCIPAL",
    "CAUSA ESPECÍFICA",
]

PEOPLE_HEADERS = [
    "CÓDIGO SINIESTRO",
    "DEPARTAMENTO",
    "PROVINCIA",
    "DISTRITO",
    "TIPO PERSONA",
    "GRAVEDAD",
]


def _workbook(path, sheet_name, headers, rows) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    for _ in range(4):
        worksheet.append([])
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    workbook.save(path)


def test_build_lima_pedestrian_fatal_crashes(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    crash_path = raw_dir / "fatal_crashes_2021_2025.xlsx"
    people_path = raw_dir / "people_fatal_crashes_2021_2025.xlsx"

    crash_template = [
        datetime(2024, 5, 10),
        "08:30",
        "ATROPELLO",
        1,
        0,
        1,
        "LIMA",
        "LIMA",
        "ATE",
        "URBANA",
        "AVENIDA",
        "VECINAL",
        "",
        -12.04,
        -77.03,
        "DESPEJADO",
        "COMERCIAL",
        "RECTA",
        "PLANO",
        "ASFALTO",
        "SI",
        "SI",
        "IMPRUDENCIA",
        "EXCESO DE VELOCIDAD",
    ]
    _workbook(
        crash_path,
        "SINIESTROS",
        CRASH_HEADERS,
        [
            ["LIMA-1", *crash_template],
            ["LIMA-2", *crash_template],
            ["CALLAO-1", *crash_template[:6], "CALLAO", "CALLAO", *crash_template[8:]],
        ],
    )
    _workbook(
        people_path,
        "PERSONAS INVOLUCRADAS",
        PEOPLE_HEADERS,
        [
            ["LIMA-1", "LIMA", "LIMA", "ATE", "PEATÓN", "FALLECIDO"],
            ["LIMA-1", "LIMA", "LIMA", "ATE", "PEATÓN", "LESIONADO"],
            ["LIMA-1", "LIMA", "LIMA", "ATE", "CONDUCTOR", "ILESO"],
            ["LIMA-2", "LIMA", "LIMA", "ATE", "CONDUCTOR", "FALLECIDO"],
            ["CALLAO-1", "CALLAO", "CALLAO", "CALLAO", "PEATÓN", "FALLECIDO"],
        ],
    )

    output = tmp_path / "events.csv"
    summary = build_lima_pedestrian_fatal_crashes(raw_dir, output)

    assert summary["rows"] == 1
    assert summary["valid_coordinate_rows"] == 1
    assert summary["pedestrian_fatalities"] == 1
    assert summary["pedestrian_injured"] == 1

    with output.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    assert len(rows) == 1
    assert rows[0]["crash_id"] == "LIMA-1"
    assert rows[0]["district"] == "ATE"
    assert rows[0]["crash_date"] == "2024-05-10"
    assert rows[0]["pedestrians_involved"] == "2"
