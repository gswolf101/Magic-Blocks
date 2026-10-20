@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Atualizar Site MagicBlocks no GitHub

:: ========================================================
:: PATH: tira aspas soltas (uma entrada quebrada "C:\php" no PATH do Windows
:: derruba o Git Credential Manager) e garante o Git e o gerenciador de login
:: ========================================================
set "PATH=%PATH:"=%"
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd;%LOCALAPPDATA%\Programs\Git Credential Manager;%LOCALAPPDATA%\Programs\Git\cmd;C:\Program Files\Git\cmd;C:\Program Files\Git\bin"

echo ========================================================
echo        Atualizador do Site MagicBlocks (GitHub)
echo ========================================================
echo.

:: Roda sempre na pasta do script
cd /d "%~dp0"

:: --------------------------------------------------------
:: Git instalado?
:: --------------------------------------------------------
where git >nul 2>&1
if errorlevel 1 (
    echo [ERRO] O Git nao foi encontrado no sistema!
    echo Baixe em: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

:: Branch atual (padrao: main)
set "BRANCH=main"
for /f "tokens=*" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%b"

:: --------------------------------------------------------
:: Opcional: gerar a wiki de novo antes de enviar
:: --------------------------------------------------------
if not exist "gerar_wiki.py" goto :skip_wiki
set "RUN_WIKI=n"
set /p RUN_WIKI="Gerar a wiki de novo antes de enviar (python gerar_wiki.py)? [s/N]: "
if /i not "%RUN_WIKI%"=="s" goto :skip_wiki
echo.
echo [*] Gerando a wiki...
python gerar_wiki.py
if errorlevel 1 echo [AVISO] Falha ao gerar a wiki. Continuando com os arquivos atuais...
echo.
:skip_wiki

:: --------------------------------------------------------
:: 1. Salva as alteracoes locais num commit
:: --------------------------------------------------------
echo [1/3] Verificando alteracoes locais...
set "HAS_CHANGES="
for /f "tokens=*" %%i in ('git status --porcelain 2^>nul') do set "HAS_CHANGES=1"
if not defined HAS_CHANGES (
    echo [INFO] Nenhuma alteracao nova nos arquivos.
    goto :sync
)

echo Alteracoes encontradas:
echo --------------------------------------------------------
git status --short
echo --------------------------------------------------------
echo.
set "COMMIT_MSG="
set /p COMMIT_MSG="Descricao do commit (ENTER para usar a data e hora): "
if defined COMMIT_MSG set "COMMIT_MSG=%COMMIT_MSG:"='%"
if not defined COMMIT_MSG call :default_msg

git add -A
git commit -q -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo [ERRO] Nao foi possivel criar o commit.
    pause
    exit /b 1
)
echo [*] Commit criado: %COMMIT_MSG%

:sync
:: --------------------------------------------------------
:: 2. Traz o que mudou no GitHub (se alguem mexeu por la)
:: --------------------------------------------------------
echo.
echo [2/3] Baixando novidades do GitHub...
:: (fetch + merge: o "pull --rebase" do MinGit falha com "Filename too long")
git fetch -q origin %BRANCH%
if errorlevel 1 (
    echo.
    echo [ERRO] Nao foi possivel falar com o GitHub. Confira a internet.
    echo Nada foi perdido: suas alteracoes continuam salvas aqui.
    pause
    exit /b 1
)
git merge -q --no-edit FETCH_HEAD
if errorlevel 1 (
    git merge --abort >nul 2>&1
    echo.
    echo [ERRO] O mesmo arquivo foi mudado aqui e no GitHub, e o Git nao
    echo conseguiu juntar sozinho. Nada foi perdido: suas alteracoes
    echo continuam salvas aqui.
    pause
    exit /b 1
)

:: --------------------------------------------------------
:: 3. Envia para o GitHub
:: --------------------------------------------------------
echo.
echo [3/3] Enviando para o GitHub...
set "NEEDS_PUSH="
for /f "tokens=*" %%c in ('git log origin/%BRANCH%..%BRANCH% --oneline 2^>nul') do set "NEEDS_PUSH=1"
if not defined NEEDS_PUSH (
    echo.
    echo ========================================================
    echo      O site ja esta 100%% atualizado no GitHub!
    echo ========================================================
    goto :end
)

echo (Na primeira vez abre uma janela para entrar na sua conta do GitHub.)
git push -u origin %BRANCH%
if errorlevel 1 (
    echo.
    echo ========================================================
    echo   [ERRO] Nao foi possivel enviar para o GitHub.
    echo   Confira a internet e se a conta usada no login tem
    echo   permissao no repositorio gswolf101/Magic-Blocks.
    echo ========================================================
    goto :end
)
echo.
echo ========================================================
echo      SUCESSO: site atualizado no GitHub!
echo      Em 1 ou 2 minutos aparece no GitHub Pages.
echo ========================================================

:end
echo.
pause
exit /b 0

:default_msg
set "HORA=%time:~0,5%"
set "HORA=%HORA: =0%"
set "COMMIT_MSG=Atualizacao do site em %date% as %HORA%"
exit /b 0
