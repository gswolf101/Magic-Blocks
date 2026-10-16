@echo off
chcp 65001 >nul
title Atualizar Site MagicBlocks no GitHub

:: Garante que o Git seja encontrado caso o PATH ainda nao tenha recarregado
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd;%LOCALAPPDATA%\Programs\Git\cmd;C:\Program Files\Git\cmd"

echo ========================================================
echo        Atualizador do Site MagicBlocks (GitHub)
echo ========================================================
echo.

:: Muda para a pasta onde esta o script
cd /d "%~dp0"

:: Verifica se o Git esta disponivel
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRO] O Git nao foi encontrado no sistema!
    echo Certifique-se de que o Git esta instalado.
    echo.
    pause
    exit /b 1
)

echo [1/3] Verificando alteracoes locais...
git status --short
echo.

:: Pergunta pela mensagem do commit ou usa data/hora como padrao
set "COMMIT_MSG="
set /p COMMIT_MSG="Digite a descricao da atualizacao (ou pressione ENTER para data atual): "

if "%COMMIT_MSG%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set DATA=%%a-%%b-%%c
    for /f "tokens=1-2 delims=: " %%a in ("%time%") do set HORA=%%a:%%b
    set "COMMIT_MSG=Atualizacao do site em %DATA% as %HORA%"
)

echo.
echo [2/3] Salvando alteracoes (git add e commit)...
git add -A
git commit -m "%COMMIT_MSG%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [INFO] Nenhuma nova alteracao encontrada para enviar.
    echo O site ja esta atualizado no GitHub!
    echo.
    pause
    exit /b 0
)

echo.
echo [3/3] Enviando para o GitHub (git push)...
git push origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo      SUCESSO: Site atualizado com exito no GitHub!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   [AVISO] Ocorreu um erro ao enviar para o GitHub.
    echo   Verifique sua conexao ou se precisa fazer login.
    echo ========================================================
)

echo.
pause
