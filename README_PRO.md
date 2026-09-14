# Wypożyczalnia Instrumentów — wersja profesjonalna

Wersja aplikacji: **2.0.0**

## Co zostało dodane

- profesjonalny branding i ikona programu,
- numer wersji widoczny w aplikacji,
- profesjonalny instalator Inno Setup,
- instalacja do Program Files,
- skrót Start Menu + opcjonalny pulpit,
- własna ikona instalatora i programu,
- dane użytkownika w `%LOCALAPPDATA%\\WypozyczalniaInstrumentow`,
- dane nie są kasowane podczas aktualizacji,
- przycisk **Sprawdź aktualizacje**,
- mechanizm pobierania i uruchamiania nowego instalatora,
- automatyczne publikowanie `Setup.exe` przez GitHub Actions po utworzeniu taga `v2.0.0`.

## Automatyczne aktualizacje

W `config.json` ustaw:

```json
"update_manifest_url": "https://twoja-domena.pl/update-manifest.json"
```

Manifest powinien mieć:

```json
{
  "version": "2.0.1",
  "installer_url": "https://.../WypozyczalniaInstrumentow_Setup.exe",
  "channel": "stable"
}
```

Po wykryciu nowszej wersji aplikacja pobierze instalator i uruchomi go.

## Najlepszy sposób budowania

Nie trzeba budować na komputerze użytkownika. Repozytorium można wysłać do GitHub i uruchomić:

**Actions → Windows Installer → Run workflow**

Przy tagu `v2.0.0` workflow dodatkowo tworzy GitHub Release z instalatorem.

## Branding

Domyślna nazwa: **Wypożyczalnia Instrumentów**.

Jeżeli ma być używana konkretna nazwa firmy, zmień `company_name` w `config.json` oraz wartości `MyAppPublisher` i tekst logo.
