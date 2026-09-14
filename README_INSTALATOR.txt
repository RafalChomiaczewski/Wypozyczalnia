WYPELNY PROJEKT INSTALATORA WINDOWS

Ten pakiet zawiera:
- aplikacje Wypozyczalnia Instrumentow,
- baze SQLite i zdjecia przechowywane w %LOCALAPPDATA%\\WypozyczalniaInstrumentow,
- skrypt Inno Setup instalujacy aplikacje do Program Files,
- automatyczny workflow GitHub Actions, ktory buduje gotowy WypozyczalniaInstrumentow_Setup.exe na serwerze Windows.

NAJMNIEJ PRACY:
1. Utworz prywatne repozytorium na GitHub.
2. Wgraj zawartosc tego folderu do repozytorium.
3. Otworz zakladke Actions.
4. Uruchom "Zbuduj instalator Windows" -> Run workflow.
5. Po zakonczeniu pobierz artefakt "WypozyczalniaInstrumentow-Windows-Installer".
6. W srodku znajduje sie gotowy WypozyczalniaInstrumentow_Setup.exe.

Uzytkownik koncowy nie potrzebuje Pythona ani PyInstaller.

UWAGA:
W tym srodowisku nie moge uruchomic natywnego kompilatora Windows ani Inno Setup, dlatego nie udaje, ze zalaczam juz skompilowany Setup.exe. Workflow wykonuje prawdziwe budowanie na Windows i jest przygotowany do wygenerowania gotowego instalatora.
