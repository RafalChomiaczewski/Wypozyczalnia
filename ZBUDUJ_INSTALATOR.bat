@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Wypozyczalnia Instrumentow - budowanie instalatora

echo ============================================================
echo   Wypozyczalnia Instrumentow - profesjonalny instalator
echo ============================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo Nie znaleziono Pythona. Ten skrypt wymaga go TYLKO podczas budowania.
    echo Najlatwiej uruchomic workflow GitHub Actions z katalogu .github\workflows.
    pause
    exit /b 1
  )
)

echo [1/4] Instalowanie zaleznosci...
%PY% -m pip install --upgrade pip
if errorlevel 1 exit /b 1
%PY% -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [2/4] Budowanie EXE...
%PY% -m PyInstaller --noconsole --onedir --clean --name WypozyczalniaInstrumentow app.py
if errorlevel 1 exit /b 1

echo [3/4] Szukanie Inno Setup...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
  echo Nie znaleziono Inno Setup.
  echo Zainstaluj Inno Setup 6 i uruchom ten skrypt ponownie.
  echo.
  echo Mozesz tez uzyc GitHub Actions - wtedy niczego nie instalujesz lokalnie.
  pause
  exit /b 1
)

echo [4/4] Budowanie Setup.exe...
if not exist release mkdir release
"%ISCC%" "installer\WypozyczalniaInstrumentow.iss"
if errorlevel 1 exit /b 1

echo.
echo GOTOWE!
echo Instalator:
echo %CD%\release\WypozyczalniaInstrumentow_Setup_v2.0.0.exe
echo.
pause
