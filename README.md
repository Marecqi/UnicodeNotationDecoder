# Unicode Notation Decoder

Samodzielny, lokalny program w Pythonie 3 do zapisywania notacji Unicode
znaków imienia i nazwiska z pliku CSV. Program nie korzysta z sieci ani z
zewnętrznych pakietów.

## Obsługiwane zakresy Unicode

- C0 Controls and Basic Latin (`U+0000`–`U+007F`)
- C1 Controls and Latin-1 Supplement (`U+0080`–`U+00FF`)
- Latin Extended-A (`U+0100`–`U+017F`)
- Latin Extended-B (`U+0180`–`U+024F`)
- Latin Extended Additional (`U+1E00`–`U+1EFF`)

## Uruchomienie

W katalogu repozytorium:

```bash
python3 unicode_notation_decoder.py dane_wejsciowe.csv dane_wyjsciowe.csv
```

Domyślne kodowanie wejścia i wyjścia to UTF-8 (wejście może mieć znacznik
BOM). Opcja `--encoding` pozwala podać inne kodowanie, na przykład
`--encoding cp1250`.

Program odczytuje pola `APP_FIRST_NAME`, `APP_SECOND_NAME` i
`APP_LAST_NAME`. Niepuste pola łączy pojedynczą spacją; spacje znajdujące się
wewnątrz pól są zachowywane. Każdy znak wynikowego tekstu trafia kolejno do
kolumn `LETTER1`–`LETTER20` w formacie `Ę -> U+0118`.

Spacja jest zapisywana jednoznacznie jako `SPACE -> U+0020`, a znaki
kontrolne jako zapis ucieczkowy, na przykład `\\u000A -> U+000A`. Pozostałe
pola CSV są zachowywane.

Jeżeli nazwisko ma ponad 20 znaków po połączeniu (łącznie ze spacjami),
program kończy pracę z błędem i nie tworzy częściowego pliku. Aby świadomie
zapisać pierwsze 20 pozycji, użyj `--overflow truncate`.

## Testy

```bash
python3 -m unittest -v
```
