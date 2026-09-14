# Wypożyczalnia Instrumentów — wersja rozszerzona

## Nowe funkcje
- numer ewidencyjny instrumentu (unikalny),
- wartość instrumentu,
- zdjęcie instrumentu (kopiowane do folderu `photos`),
- status: Dostępny / Wypożyczony / Serwis / Wycofany,
- raport KPI: liczba instrumentów, dostępne, wypożyczone, wartość ewidencyjna, klienci,
- raport przychodów i przeterminowanych wypożyczeń,
- TOP 5 najczęściej wypożyczanych instrumentów,
- eksport historii i raportów do CSV (Excel otworzy te pliki).

## Uruchomienie z Pythonem
`uruchom.bat`

Opcjonalny podgląd zdjęć wymaga Pillow:
`python -m pip install Pillow`

## Zbudowanie EXE
Najprościej na Windows:
1. Zainstaluj Python 3.11+.
2. Otwórz CMD w folderze aplikacji.
3. Wykonaj:
   `python -m pip install --upgrade pip`
   `python -m pip install pyinstaller Pillow`
4. Zbuduj:
   `python -m PyInstaller --noconsole --onefile --name WypozyczalniaInstrumentow app.py`
5. EXE znajdziesz w:
   `dist\WypozyczalniaInstrumentow.exe`

### Ważne dla zdjęć
Program tworzy folder `photos` obok EXE. Przy dystrybucji najlepiej używać wersji `--onedir`, bo baza i zdjęcia są wtedy naturalnie przechowywane obok programu:
`python -m PyInstaller --noconsole --onedir --name WypozyczalniaInstrumentow app.py`

Po zbudowaniu skopiuj cały:
`dist\WypozyczalniaInstrumentow\`
na komputer docelowy. Uruchamiaj EXE z tego folderu.

### Baza danych
`rental.db` jest tworzona automatycznie obok programu. Rób kopię tego pliku, aby mieć backup danych.
