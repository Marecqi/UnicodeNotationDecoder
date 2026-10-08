"""Testy wymagań biznesowych lokalnego dekodera notacji Unicode."""

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from unicode_notation_decoder import DecodeError, decode_csv


class UnicodeNotationDecoderTests(unittest.TestCase):
    """Chroni najważniejsze reguły eksportu danych osobowych do CSV."""

    def write_input(self, directory: Path, rows: list[dict[str, str]]) -> Path:
        """Tworzy lokalny plik wejściowy, aby testy nie potrzebowały sieci ani bazy."""
        path = directory / "input.csv"
        headers = ["ROWNUM"] + ["WORD{0}".format(number) for number in range(1, 11)]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_writes_unicode_notation_and_spaces(self) -> None:
        """Sprawdza litery rozszerzone i obie spacje w połączonych polach tekstowych."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            input_path = self.write_input(
                directory,
                [{"ROWNUM": "1", "WORD1": "ĐỨA OUẾ", "WORD2": "", "WORD3": "AGUYỄN"}],
            )
            output_path = directory / "output.csv"

            decode_csv(input_path, output_path, encoding="utf-8")

            with output_path.open("r", encoding="utf-8", newline="") as file:
                row = next(csv.DictReader(file))
            self.assertEqual(row["LETTER1"], "Đ -> U+0110")
            self.assertEqual(row["LETTER4"], "SPACE -> U+0020")
            self.assertEqual(row["LETTER7"], "Ế -> U+1EBE")
            self.assertEqual(row["LETTER8"], "SPACE -> U+0020")
            self.assertEqual(row["LETTER13"], "Ễ -> U+1EC4")
            self.assertEqual(row["LETTER14"], "N -> U+004E")
            self.assertEqual(row["LETTER15"], "")

    def test_example_e_ogonek(self) -> None:
        """Utrwala wymagany przykład biznesowy: Ę trafia do LETTER1 jako U+0118."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            input_path = self.write_input(
                directory,
                [{"ROWNUM": "1", "WORD1": "Ę", "WORD2": "", "WORD3": ""}],
            )
            output_path = directory / "output.csv"

            decode_csv(input_path, output_path, encoding="utf-8")

            with output_path.open("r", encoding="utf-8", newline="") as file:
                row = next(csv.DictReader(file))
            self.assertEqual(row["LETTER1"], "Ę -> U+0118")

    def test_overflow_is_an_error_by_default(self) -> None:
        """Chroni przed cichym obcięciem tekstu, gdy 100 komórek nie wystarcza."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            input_path = self.write_input(
                directory,
                [{"ROWNUM": "1", "WORD1": "A" * 101}],
            )

            with self.assertRaises(DecodeError):
                decode_csv(input_path, directory / "output.csv", encoding="utf-8")

    def test_reads_all_ten_word_columns(self) -> None:
        """Łączy dane ze wszystkich dziesięciu pól tekstowych w ustalonej kolejności."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            row = {"ROWNUM": "1"}
            row.update({"WORD{0}".format(number): chr(64 + number) for number in range(1, 11)})
            input_path = self.write_input(directory, [row])
            output_path = directory / "output.csv"

            decode_csv(input_path, output_path, encoding="utf-8")

            with output_path.open("r", encoding="utf-8", newline="") as file:
                decoded_row = next(csv.DictReader(file))
            self.assertEqual(decoded_row["LETTER1"], "A -> U+0041")
            self.assertEqual(decoded_row["LETTER2"], "SPACE -> U+0020")
            self.assertEqual(decoded_row["LETTER19"], "J -> U+004A")

    def test_supports_one_hundred_characters(self) -> None:
        """Zapisuje wynik w ostatniej dostępnej kolumnie LETTER100."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            input_path = self.write_input(directory, [{"ROWNUM": "1", "WORD1": "A" * 100}])
            output_path = directory / "output.csv"

            decode_csv(input_path, output_path, encoding="utf-8")

            with output_path.open("r", encoding="utf-8", newline="") as file:
                decoded_row = next(csv.DictReader(file))
            self.assertEqual(decoded_row["LETTER100"], "A -> U+0041")

    def test_command_line_creates_output(self) -> None:
        """Potwierdza, że operator może uruchomić gotową aplikację z terminala."""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            input_path = self.write_input(
                directory,
                [{"ROWNUM": "1", "WORD1": "Ę", "WORD2": "", "WORD3": ""}],
            )
            output_path = directory / "output.csv"
            script = Path(__file__).with_name("unicode_notation_decoder.py")

            result = subprocess.run(
                [sys.executable, str(script), str(input_path), str(output_path)],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with output_path.open("r", encoding="utf-8-sig", newline="") as file:
                row = next(csv.DictReader(file))
            self.assertEqual(row["LETTER1"], "Ę -> U+0118")


if __name__ == "__main__":
    unittest.main()
