#!/usr/bin/env python3
"""Convert selected CSV name fields into BMP Unicode notation columns.

The program is intentionally offline: it only uses Python's standard library
and reads/writes local CSV files.
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path
from typing import Iterable


NAME_COLUMNS = ("APP_FIRST_NAME", "APP_SECOND_NAME", "APP_LAST_NAME")
LETTER_COLUMNS = tuple("LETTER{0}".format(number) for number in range(1, 21))
SUPPORTED_RANGES = (
    (0x0000, 0x007F),  # C0 Controls and Basic Latin
    (0x0080, 0x00FF),  # C1 Controls and Latin-1 Supplement
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
    (0x1E00, 0x1EFF),  # Latin Extended Additional
)


class DecodeError(ValueError):
    """Raised when a row cannot be represented in the requested output."""


def is_supported(character: str) -> bool:
    """Return whether *character* belongs to one of the configured BMP blocks."""
    code_point = ord(character)
    return any(start <= code_point <= end for start, end in SUPPORTED_RANGES)


def character_label(character: str) -> str:
    """Make invisible input characters unambiguous and CSV-safe."""
    code_point = ord(character)
    if code_point == 0x0020:
        return "SPACE"
    if code_point < 0x0020 or 0x007F <= code_point <= 0x009F:
        return "\\u{0:04X}".format(code_point)
    return character


def unicode_notation(character: str) -> str:
    """Return one CSV cell in the required ``znak -> U+XXXX`` format."""
    return "{0} -> U+{1:04X}".format(character_label(character), ord(character))


def combined_name(row: dict[str, str]) -> str:
    """Join non-empty name parts while retaining every source-space character."""
    return " ".join(row.get(column, "") for column in NAME_COLUMNS if row.get(column, "") != "")


def decode_name(name: str, row_number: int, overflow: str) -> list[str]:
    """Validate and decode a combined name into at most 20 notation cells."""
    for position, character in enumerate(name, start=1):
        if not is_supported(character):
            raise DecodeError(
                "Wiersz {0}, znak {1}: U+{2:04X} nie należy do obsługiwanych zakresów BMP.".format(
                    row_number, position, ord(character)
                )
            )

    if len(name) > len(LETTER_COLUMNS):
        if overflow == "error":
            raise DecodeError(
                "Wiersz {0} ma {1} znaków, a dostępnych jest tylko {2} kolumn LETTER. "
                "Użyj --overflow truncate, aby zapisać pierwsze 20 znaków.".format(
                    row_number, len(name), len(LETTER_COLUMNS)
                )
            )
        name = name[: len(LETTER_COLUMNS)]

    return [unicode_notation(character) for character in name]


def output_headers(input_headers: Iterable[str]) -> list[str]:
    """Keep input headers and ensure all 20 LETTER columns are present once."""
    headers = list(input_headers)
    return headers + [column for column in LETTER_COLUMNS if column not in headers]


def decode_csv(input_path: Path, output_path: Path, encoding: str = "utf-8-sig", overflow: str = "error") -> int:
    """Decode *input_path* to *output_path* atomically and return row count."""
    if input_path.resolve() == output_path.resolve():
        raise DecodeError("Plik wyjściowy musi mieć inną ścieżkę niż plik wejściowy.")

    with input_path.open("r", encoding=encoding, newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise DecodeError("Plik CSV nie zawiera wiersza nagłówków.")
        missing = [column for column in NAME_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise DecodeError("Brakuje wymaganych kolumn: {0}.".format(", ".join(missing)))

        headers = output_headers(reader.fieldnames)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = None
        row_count = 0
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding=encoding, newline="", dir=output_path.parent, delete=False
            ) as temporary:
                temporary_name = temporary.name
                writer = csv.DictWriter(temporary, fieldnames=headers, extrasaction="ignore")
                writer.writeheader()
                for row_count, row in enumerate(reader, start=1):
                    decoded = decode_name(combined_name(row), row_count, overflow)
                    for column in LETTER_COLUMNS:
                        row[column] = ""
                    for column, notation in zip(LETTER_COLUMNS, decoded):
                        row[column] = notation
                    writer.writerow(row)
            os.replace(temporary_name, output_path)
            temporary_name = None
        finally:
            if temporary_name is not None:
                os.unlink(temporary_name)
    return row_count


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lokalnie zapisuje notację Unicode znaków imion i nazwisk w kolumnach LETTER1–LETTER20."
    )
    parser.add_argument("input_csv", type=Path, help="wejściowy plik CSV")
    parser.add_argument("output_csv", type=Path, help="wyjściowy plik CSV")
    parser.add_argument("--encoding", default="utf-8-sig", help="kodowanie CSV (domyślnie: utf-8-sig)")
    parser.add_argument(
        "--overflow",
        choices=("error", "truncate"),
        default="error",
        help="reakcja na tekst dłuższy niż 20 znaków (domyślnie: error)",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        rows = decode_csv(arguments.input_csv, arguments.output_csv, arguments.encoding, arguments.overflow)
    except (DecodeError, OSError, UnicodeError, csv.Error) as error:
        print("Błąd: {0}".format(error))
        return 1
    print("Zapisano {0} wiersz(y) w pliku {1}.".format(rows, arguments.output_csv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
