#!/usr/bin/env python3
"""Lokalnie zapisuje notację Unicode znaków danych tekstowych w pliku CSV.

Cel biznesowy: użytkownik może przekazać plik osobom lub systemom, które
potrzebują jednoznacznego zapisu liter z danych tekstowych, bez wysyłania
danych do zewnętrznej usługi. Program działa wyłącznie na lokalnych plikach i
korzysta tylko z biblioteki standardowej Pythona.
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path
from typing import Iterable


# Kontrakt wejścia/wyjścia z procesem biznesowym: trzy pola tekstowe są źródłem
# danych, a wynik musi zostać zapisany w dokładnie 20 przewidzianych polach.
WORD_COLUMNS = ("WORD1", "WORD2", "WORD3")
LETTER_COLUMNS = tuple("LETTER{0}".format(number) for number in range(1, 21))

# Zakres jest ograniczony do bloków uzgodnionych dla tego procesu. Dzięki temu
# nietypowy znak nie zostanie opisany jako poprawny, jeśli odbiorca nie obsługuje
# go w swoim systemie.
SUPPORTED_RANGES = (
    (0x0000, 0x007F),  # C0 Controls and Basic Latin
    (0x0080, 0x00FF),  # C1 Controls and Latin-1 Supplement
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
    (0x1E00, 0x1EFF),  # Latin Extended Additional
)


class DecodeError(ValueError):
    """Błąd danych, który zapobiega zapisaniu niepełnego lub mylącego wyniku."""


def is_supported(character: str) -> bool:
    """Sprawdza, czy znak można bezpiecznie przekazać w uzgodnionym zakresie."""
    code_point = ord(character)
    return any(start <= code_point <= end for start, end in SUPPORTED_RANGES)


def character_label(character: str) -> str:
    """Nadaje widoczną etykietę znakom, których nie widać w arkuszu CSV.

    Dzięki temu spacja i znaki kontrolne nie wyglądają jak pusta komórka lub
    błąd eksportu, lecz zachowują jednoznaczną informację dla użytkownika.
    """
    code_point = ord(character)
    if code_point == 0x0020:
        return "SPACE"
    if code_point < 0x0020 or 0x007F <= code_point <= 0x009F:
        return "\\u{0:04X}".format(code_point)
    return character


def unicode_notation(character: str) -> str:
    """Tworzy wartość komórki w formacie wymaganym przez odbiorcę danych."""
    return "{0} -> U+{1:04X}".format(character_label(character), ord(character))


def combined_words(row: dict[str, str]) -> str:
    """Łączy niepuste pola tekstowe, zachowując spacje mające znaczenie.

    Puste pole nie tworzy dodatkowej pozycji. Pojedyncza spacja między
    niepustymi wartościami zapewnia spójny zapis danych do porównania.
    """
    return " ".join(row.get(column, "") for column in WORD_COLUMNS if row.get(column, "") != "")


def decode_text(text: str, row_number: int, overflow: str) -> list[str]:
    """Waliduje tekst i przypisuje każdą jego pozycję do jednej kolumny LETTER.

    Najpierw blok wykrywa nieobsługiwane znaki, aby nie powstał częściowo
    poprawny opis tekstu. Następnie kontroluje limit 20 komórek: domyślnie
    zatrzymuje eksport, a tryb ``truncate`` jest świadomym wyjątkiem biznesowym.
    """
    for position, character in enumerate(text, start=1):
        if not is_supported(character):
            raise DecodeError(
                "Wiersz {0}, znak {1}: U+{2:04X} nie należy do obsługiwanych zakresów BMP.".format(
                    row_number, position, ord(character)
                )
            )

    if len(text) > len(LETTER_COLUMNS):
        if overflow == "error":
            raise DecodeError(
                "Wiersz {0} ma {1} znaków, a dostępnych jest tylko {2} kolumn LETTER. "
                "Użyj --overflow truncate, aby zapisać pierwsze 20 znaków.".format(
                    row_number, len(text), len(LETTER_COLUMNS)
                )
            )
        text = text[: len(LETTER_COLUMNS)]

    return [unicode_notation(character) for character in text]


def output_headers(input_headers: Iterable[str]) -> list[str]:
    """Chroni istniejące kolumny pliku i zapewnia komplet pól wyniku.

    Umożliwia to użycie eksportu zarówno z szablonem zawierającym LETTER1–20,
    jak i z plikiem, w którym kolumny wyniku trzeba dopiero dodać.
    """
    headers = list(input_headers)
    return headers + [column for column in LETTER_COLUMNS if column not in headers]


def decode_csv(input_path: Path, output_path: Path, encoding: str = "utf-8-sig", overflow: str = "error") -> int:
    """Wykonuje bezpieczny eksport całego pliku i zwraca liczbę rekordów.

    Ta część pilnuje biznesowego kontraktu kolumn, przechowuje wszystkie inne
    dane z wiersza oraz nadpisuje pola LETTER aktualną notacją. Zapis tymczasowy
    i atomowe zastąpienie pliku oznaczają, że błąd w jednym rekordzie nie
    pozostawi odbiorcy częściowo wygenerowanego raportu.
    """
    if input_path.resolve() == output_path.resolve():
        raise DecodeError("Plik wyjściowy musi mieć inną ścieżkę niż plik wejściowy.")

    with input_path.open("r", encoding=encoding, newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise DecodeError("Plik CSV nie zawiera wiersza nagłówków.")
        missing = [column for column in WORD_COLUMNS if column not in reader.fieldnames]
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
                    decoded = decode_text(combined_words(row), row_count, overflow)
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
    """Udostępnia prosty, powtarzalny sposób uruchomienia przez operatora."""
    parser = argparse.ArgumentParser(
        description="Lokalnie zapisuje notację Unicode znaków danych tekstowych w kolumnach LETTER1–LETTER20."
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
    """Łączy obsługę plików z czytelnym komunikatem dla osoby uruchamiającej."""
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
