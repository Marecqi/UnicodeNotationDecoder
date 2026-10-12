# US-001: Obsługa separatora średnika w CSV

## User story

Jako użytkownik aplikacji Unicode Notation Decoder chcę przetwarzać pliki CSV
rozdzielane średnikami, aby móc analizować eksporty z programów używających
średnika jako separatora bez ręcznej konwersji pliku.

## Kryteria akceptacji

1. Aplikacja rozpoznaje plik CSV rozdzielany przecinkami albo średnikami na
   podstawie wiersza nagłówków.
2. Dla pliku rozdzielanego średnikami aplikacja odczytuje wymagane kolumny
   `WORD1`–`WORD10` i tworzy notację Unicode w kolumnach `LETTER1`–`LETTER100`.
3. Plik wynikowy zachowuje separator zastosowany w pliku wejściowym.
4. Obsługa plików rozdzielanych przecinkami działa bez zmiany dotychczasowego
   zachowania.
5. Gdy w pliku brakuje wymaganych kolumn, aplikacja nadal wyświetla czytelny
   komunikat o brakujących nagłówkach.

## Uwagi techniczne

Zmiana obejmuje wyłącznie separator CSV. Kodowanie pliku wybiera się nadal za
pomocą opcji `--encoding` lub pola „Kodowanie pliku” w interfejsie graficznym.
