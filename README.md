# Unicode Notation Decoder

Samodzielny, lokalny program w Pythonie 3 do zapisywania notacji Unicode
znaków wyrazów i danych tekstowych z pliku CSV. Program nie korzysta z sieci ani z
zewnętrznych pakietów.

Systemy komputerowe przechowują i przetwarzają informacje w postaci bitów,
czyli zer i jedynek. Dotyczy to również tekstu: każdy znak ma określoną
reprezentację, a standard Unicode przypisuje znakom punkty kodowe zapisywane
na przykład jako `U+0118` dla litery `Ę`. Kodowanie pliku, takie jak UTF-8,
określa natomiast sposób zapisania tych punktów kodowych w bajtach.

Znaki, które na ekranie lub wydruku wyglądają identycznie albo różnią się
niemal niezauważalnie, mogą mieć różne punkty kodowe Unicode. Na przykład
w niektórych krojach pisma wielka litera `I` (`U+0049`) jest trudna do
odróżnienia od małej litery `l` (`U+006C`). Dla systemu są to jednak dwa
różne znaki. Takie różnice mogą prowadzić do rozbieżności przy porównywaniu
danych tekstowych wprowadzonych do różnych systemów, utrudniać dopasowanie
rekordów lub powodować uznanie pozornie identycznych wartości za różne.

Unicode Notation Decoder powstał, aby ułatwić sprawdzenie, jakie znaki
rzeczywiście znajdują się w danych. Program odczytuje wyrazy i dane tekstowe
z pliku CSV i zapisuje notację Unicode każdego znaku, uwzględniając również
spacje. Dzięki wynikowi w postaci `Ę -> U+0118` można porównywać konkretne
punkty kodowe zamiast polegać wyłącznie na wyglądzie liter. Program wspiera
wykrywanie różnic; nie poprawia automatycznie tekstu ani nie rozstrzyga,
czy dwa rekordy mają to samo znaczenie.

Całe przetwarzanie odbywa się lokalnie na komputerze użytkownika. Program
nie przesyła plików ani ich zawartości do serwerów zewnętrznych, dzięki czemu
można analizować także dane osobowe bez udostępniania ich dekoderom
internetowym. Pliki wejściowe i wynikowe pozostają pod kontrolą użytkownika
i wymagają takiej samej ochrony jak pozostałe pliki zawierające dane osobowe.

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

### Interfejs graficzny

Aby wybrać plik CSV z dysku w oknie aplikacji, uruchom:

```bash
python3 unicode_notation_decoder_gui.py
```

Kliknij **Wybierz plik…**, wskaż wejściowy plik CSV, a następnie wybierz
miejsce zapisu albo pozostaw automatycznie zaproponowaną nazwę z końcówką
`_unicode.csv`. W oknie można także wybrać kodowanie wejściowego pliku oraz
zdecydować, czy tekst dłuższy niż 100 znaków ma zatrzymać eksport czy zostać
skrócony. Interfejs korzysta wyłącznie z biblioteki standardowej Pythona i
nie wysyła plików poza komputer.

Plik [szablon_danych.csv](szablon_danych.csv) zawiera gotowy układ nagłówków.
Skopiuj go pod nową nazwą, na przykład `moje_dane.csv`, wpisz dane w kolumnach
`WORD1`–`WORD10`, a następnie wskaż ten
plik jako pierwszy argument programu. Kolumn `LETTER1`–`LETTER100` nie trzeba
wypełniać: program zapisze w nich wynik dekodowania.

Domyślne kodowanie wejścia i wyjścia to UTF-8 (wejście może mieć znacznik
BOM). Opcja `--encoding` pozwala podać inne kodowanie, na przykład
`--encoding cp1250`.

Program odczytuje pola `WORD1`–`WORD10`, które mogą zawierać
wyrazy i dane tekstowe z obsługiwanych zakresów Unicode. Obecna wersja
programu wymaga tych nazw nagłówków we wszystkich plikach wejściowych.
Niepuste pola łączy pojedynczą spacją; spacje znajdujące się
wewnątrz pól są zachowywane. Każdy znak wynikowego tekstu trafia kolejno do
kolumn `LETTER1`–`LETTER100` w formacie `Ę -> U+0118`.

Spacja jest zapisywana jednoznacznie jako `SPACE -> U+0020`, a znaki
kontrolne jako zapis ucieczkowy, na przykład `\\u000A -> U+000A`. Pozostałe
pola CSV są zachowywane.

Jeżeli tekst ma ponad 100 znaków po połączeniu (łącznie ze spacjami),
program kończy pracę z błędem i nie tworzy częściowego pliku. Aby świadomie
zapisać pierwsze 100 pozycji, użyj `--overflow truncate`.

## Testy

```bash
python3 -m unittest -v
```
