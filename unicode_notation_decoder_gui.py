#!/usr/bin/env python3
"""Graficzny interfejs lokalnego dekodera notacji Unicode dla plików CSV."""

from __future__ import annotations

import csv
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from unicode_notation_decoder import DecodeError, decode_csv


class DecoderWindow:
    """Okno pozwalające wybrać plik wejściowy i zapisać zdekodowany CSV."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Unicode Notation Decoder")
        self.root.minsize(680, 390)
        self.root.columnconfigure(0, weight=1)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.encoding = tk.StringVar(value="utf-8-sig")
        self.overflow = tk.StringVar(value="error")
        self.status = tk.StringVar(value="Wybierz wejściowy plik CSV, aby rozpocząć.")

        self._build_content()

    def _build_content(self) -> None:
        container = ttk.Frame(self.root, padding=24)
        container.grid(sticky="nsew")
        container.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        ttk.Label(
            container,
            text="Unicode Notation Decoder",
            font=("TkDefaultFont", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text="Wszystkie pliki pozostają lokalnie na Twoim komputerze.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 20))

        files = ttk.LabelFrame(container, text="Pliki", padding=14)
        files.grid(row=2, column=0, sticky="ew")
        files.columnconfigure(0, weight=1)

        self._add_file_row(
            files,
            row=0,
            label="Plik wejściowy CSV",
            variable=self.input_path,
            command=self.choose_input_file,
            button_text="Wybierz plik…",
        )
        self._add_file_row(
            files,
            row=2,
            label="Plik wynikowy CSV",
            variable=self.output_path,
            command=self.choose_output_file,
            button_text="Wybierz miejsce…",
        )

        settings = ttk.LabelFrame(container, text="Opcje", padding=14)
        settings.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="Kodowanie pliku:").grid(row=0, column=0, sticky="w")
        encoding_box = ttk.Combobox(
            settings,
            textvariable=self.encoding,
            values=("utf-8-sig", "utf-8", "cp1250"),
            state="readonly",
            width=18,
        )
        encoding_box.grid(row=0, column=1, sticky="w", padx=(10, 0))

        ttk.Label(settings, text="Tekst dłuższy niż 100 znaków:").grid(
            row=1, column=0, sticky="nw", pady=(12, 0)
        )
        overflow_options = ttk.Frame(settings)
        overflow_options.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(8, 0))
        ttk.Radiobutton(
            overflow_options,
            text="Pokaż błąd (zalecane)",
            variable=self.overflow,
            value="error",
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            overflow_options,
            text="Zapisz pierwsze 100 znaków",
            variable=self.overflow,
            value="truncate",
        ).grid(row=1, column=0, sticky="w")

        actions = ttk.Frame(container)
        actions.grid(row=4, column=0, sticky="ew", pady=(20, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, textvariable=self.status, wraplength=500).grid(row=0, column=0, sticky="w")
        self.process_button = ttk.Button(actions, text="Dekoduj i zapisz", command=self.start_decoding)
        self.process_button.grid(row=0, column=1, sticky="e", padx=(16, 0))

    @staticmethod
    def _add_file_row(
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command: object,
        button_text: str,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=variable).grid(row=row + 1, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(parent, text=button_text, command=command).grid(row=row + 1, column=1, padx=(10, 0), pady=(4, 0))

    def choose_input_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Wybierz plik CSV do dekodowania",
            filetypes=(("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")),
        )
        if not selected:
            return
        self.input_path.set(selected)
        input_file = Path(selected)
        self.output_path.set(str(input_file.with_name(input_file.stem + "_unicode.csv")))
        self.status.set("Wybrano plik wejściowy. Wskaż miejsce zapisu lub użyj proponowanej nazwy.")

    def choose_output_file(self) -> None:
        initial = self.output_path.get() or "wynik_unicode.csv"
        selected = filedialog.asksaveasfilename(
            title="Wybierz miejsce zapisu pliku wynikowego",
            initialfile=Path(initial).name,
            initialdir=str(Path(initial).parent) if Path(initial).parent.exists() else None,
            defaultextension=".csv",
            filetypes=(("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")),
        )
        if selected:
            self.output_path.set(selected)

    def start_decoding(self) -> None:
        input_name = self.input_path.get().strip()
        output_name = self.output_path.get().strip()
        if not input_name:
            messagebox.showwarning("Brak pliku", "Wybierz wejściowy plik CSV.", parent=self.root)
            return
        if not output_name:
            messagebox.showwarning("Brak miejsca zapisu", "Wskaż plik wynikowy CSV.", parent=self.root)
            return
        if not Path(input_name).is_file():
            messagebox.showerror("Nie znaleziono pliku", "Wybrany plik wejściowy nie istnieje.", parent=self.root)
            return

        self.process_button.state(["disabled"])
        self.status.set("Trwa dekodowanie pliku…")
        worker = threading.Thread(
            target=self._decode_in_background,
            args=(Path(input_name), Path(output_name), self.encoding.get(), self.overflow.get()),
            daemon=True,
        )
        worker.start()

    def _decode_in_background(self, input_path: Path, output_path: Path, encoding: str, overflow: str) -> None:
        try:
            rows = decode_csv(input_path, output_path, encoding, overflow)
        except (DecodeError, OSError, UnicodeError, csv.Error) as error:
            self.root.after(0, self._show_error, str(error))
        else:
            self.root.after(0, self._show_success, rows, output_path)

    def _show_error(self, error: str) -> None:
        self.process_button.state(["!disabled"])
        self.status.set("Nie zapisano pliku — popraw dane i spróbuj ponownie.")
        messagebox.showerror("Nie można zdekodować pliku", error, parent=self.root)

    def _show_success(self, rows: int, output_path: Path) -> None:
        self.process_button.state(["!disabled"])
        message = "Zapisano {0} wiersz(y) w pliku:\n{1}".format(rows, output_path)
        self.status.set("Gotowe — plik wynikowy został zapisany.")
        messagebox.showinfo("Dekodowanie zakończone", message, parent=self.root)


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    DecoderWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
