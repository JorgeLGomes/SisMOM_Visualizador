# GISELE — script de migracao para a estrutura final do monorepo.
#
# ANTES:
#   C:\Projetos\Visualizador\           (atual)
#   ├── figuras_SisMOM_v23.html
#   ├── electron-app\
#   ├── miscelaneas\
#   ├── docs\
#   ├── HANDOVER_GISELE.md
#   ├── ESPECIFICACOES_GISELE.md
#   ├── BACKEND_PROPOSTA.md
#   ├── gisele-backend\            (NOVO, criado por esta sessao)
#   ├── commit-changes.bat
#   ├── rebuild-electron.bat
#   └── ... (outros)
#
# DEPOIS:
#   C:\Projetos\Gisele\                 (renomeado)
#   ├── Visualizador-frontend\          (todo conteudo antigo aqui dentro)
#   │   ├── figuras_SisMOM_v23.html
#   │   ├── electron-app\
#   │   ├── miscelaneas\
#   │   ├── commit-changes.bat
#   │   └── ... (outros)
#   ├── gisele-backend\                 (no topo do novo monorepo)
#   ├── docs\                           (compartilhado entre frontend + backend)
#   ├── HANDOVER_GISELE.md
#   ├── ESPECIFICACOES_GISELE.md
#   ├── BACKEND_PROPOSTA.md
#   └── README.md                       (NOVO, descreve o monorepo)
#
# USO:
#   1. Feche TODOS os apps que estejam usando arquivos do projeto
#      (VS Code, Electron rodando, Git GUI, etc).
#   2. Abra PowerShell COMO ADMINISTRADOR.
#   3. cd C:\Projetos\Visualizador\gisele-backend\scripts
#   4. .\migrate-to-gisele-monorepo.ps1 -DryRun           # simula
#   5. .\migrate-to-gisele-monorepo.ps1                   # executa
#
# REVERSAO: o script tem -RollBack que desfaz se algo der errado.

[CmdletBinding()]
param(
    [string]$SourceDir = "C:\Projetos\Visualizador",
    [string]$TargetDir = "C:\Projetos\Gisele",
    [switch]$DryRun,
    [switch]$RollBack,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Step($msg) { Write-Host "  → $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "  ✗ $msg" -ForegroundColor Red }

if ($RollBack) {
    Write-Host "=== ROLLBACK ===" -ForegroundColor Magenta
    if (-not (Test-Path $TargetDir)) { Err "$TargetDir nao existe — nada a reverter."; exit 1 }
    if (Test-Path $SourceDir)        { Err "$SourceDir ainda existe — abortando para nao sobrescrever."; exit 1 }
    Step "Renomeando $TargetDir → $SourceDir"
    if (-not $DryRun) {
        $frontendDir = Join-Path $TargetDir "Visualizador-frontend"
        if (Test-Path $frontendDir) {
            Step "Movendo conteudo de Visualizador-frontend\ de volta para a raiz"
            Get-ChildItem $frontendDir -Force | Move-Item -Destination $TargetDir
            Remove-Item $frontendDir
        }
        Rename-Item -Path $TargetDir -NewName "Visualizador"
        Ok "Rollback concluido. Pasta restaurada como $SourceDir"
    } else { Ok "DRY RUN — rollback nao foi executado." }
    exit 0
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  GISELE — migracao para monorepo (C:\Projetos\Gisele)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
if ($DryRun) { Write-Host "MODO: DRY RUN (nenhuma alteracao real sera feita)" -ForegroundColor Yellow }
Write-Host "Source: $SourceDir"
Write-Host "Target: $TargetDir"
Write-Host ""

# Validacoes
if (-not (Test-Path $SourceDir)) { Err "$SourceDir nao existe."; exit 1 }
if (Test-Path $TargetDir -and -not $Force) {
    Err "$TargetDir ja existe. Use -Force para sobrescrever (CUIDADO) ou -RollBack para desfazer."
    exit 1
}

# Confirmacao
if (-not $DryRun) {
    Write-Host "Esta operacao vai:" -ForegroundColor Yellow
    Write-Host "  1. Renomear $SourceDir → $TargetDir" -ForegroundColor Yellow
    Write-Host "  2. Criar $TargetDir\Visualizador-frontend\" -ForegroundColor Yellow
    Write-Host "  3. Mover todos os arquivos do frontend para essa subpasta" -ForegroundColor Yellow
    Write-Host "  4. Manter no topo: gisele-backend, docs, *.md, BACKEND_PROPOSTA.md" -ForegroundColor Yellow
    Write-Host "  5. Criar um README.md novo no topo descrevendo o monorepo" -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "Continuar? (digite SIM em maiusculas)"
    if ($confirm -ne "SIM") { Warn "Cancelado pelo usuario."; exit 0 }
}

try {
    # 1. Rename
    Step "Renomeando $SourceDir → $TargetDir"
    if (-not $DryRun) { Rename-Item -Path $SourceDir -NewName "Gisele" }
    Ok "Renomeado."

    # 2. Cria subpasta de frontend
    $frontendDir = Join-Path $TargetDir "Visualizador-frontend"
    Step "Criando $frontendDir"
    if (-not $DryRun) { New-Item -ItemType Directory -Path $frontendDir | Out-Null }
    Ok "Subpasta de frontend criada."

    # 3. Move arquivos do frontend
    #    Mantem no topo: gisele-backend, docs, README.md (novo), *.md de docs
    $keepAtTop = @(
        'gisele-backend',
        'docs',
        'HANDOVER_GISELE.md',
        'ESPECIFICACOES_GISELE.md',
        'BACKEND_PROPOSTA.md',
        '.git', '.gitignore',
        'README.md'
    )
    Step "Movendo arquivos do frontend para $frontendDir"
    $items = Get-ChildItem $TargetDir -Force | Where-Object { $keepAtTop -notcontains $_.Name }
    foreach ($item in $items) {
        Step "  - $($item.Name)"
        if (-not $DryRun) { Move-Item -Path $item.FullName -Destination $frontendDir }
    }
    Ok "$($items.Count) item(s) movido(s) para Visualizador-frontend\"

    # 4. Cria README.md no topo do monorepo
    $readmeTop = @"
# GISELE — Monorepo

Plataforma de visualização de modelos meteorológicos do CPTEC/INPE.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| ``Visualizador-frontend/`` | Frontend HTML+JS+Electron (v2.6.0). Cliente do GISELE. |
| ``gisele-backend/`` | Microsserviços poliglotas (Go/Python/Node). Roadmap de 18 semanas. |
| ``docs/`` | PDFs gerados (Manual, HANDOVER, ESPECIFICACOES, BACKEND_PROPOSTA). |

## Documentos chave

- [Manual de Uso](docs/GISELE_Manual_Uso.pdf) — guia do usuário final.
- [HANDOVER](HANDOVER_GISELE.md) — handover técnico de toda a sessão de desenvolvimento.
- [ESPECIFICACOES](ESPECIFICACOES_GISELE.md) — especificações para reimplementação from-scratch.
- [BACKEND_PROPOSTA](BACKEND_PROPOSTA.md) — proposta de arquitetura distribuída v1.0.

## Quick start

**Frontend (continua funcionando standalone):**

``````bash
cd Visualizador-frontend/electron-app
npm install && npm start
``````

**Backend (modo local):**

``````bash
cd gisele-backend
make up
make healthcheck
``````

**Conectar frontend ao backend:** ajustar ``GISELE_BACKEND_URL=http://localhost:8080`` no Electron (a partir da Fase 1 do roadmap).

## Versionamento

- ``Visualizador-frontend`` versão: **2.6.0** (build marker ``20260529-5600-vectormask``)
- ``gisele-backend`` versão: **0.1.0-skeleton** (Fase 0 concluída)

---

CPTEC/INPE · Última atualização: 29/05/2026
"@
    Step "Criando README.md no topo do monorepo"
    if (-not $DryRun) { Set-Content -Path (Join-Path $TargetDir "README.md") -Value $readmeTop -Encoding UTF8 }
    Ok "README.md criado."

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  MIGRACAO CONCLUIDA com sucesso." -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Estrutura final:"
    Write-Host "    $TargetDir\"
    Write-Host "    ├── Visualizador-frontend\   (todo o frontend)"
    Write-Host "    ├── gisele-backend\          (7 microsservicos)"
    Write-Host "    ├── docs\                    (PDFs)"
    Write-Host "    ├── *.md                     (documentos chave)"
    Write-Host "    └── README.md                (novo)"
    Write-Host ""
    Write-Host "  Proximos passos:"
    Write-Host "    1. cd $TargetDir\gisele-backend"
    Write-Host "    2. make up        # sobe o backend local"
    Write-Host "    3. make healthcheck"
    Write-Host ""
    Write-Host "  Para reverter: .\scripts\migrate-to-gisele-monorepo.ps1 -RollBack"
    Write-Host ""
}
catch {
    Err "Falha na migracao: $_"
    Err "Para reverter manualmente, use -RollBack ou restaure de backup."
    exit 1
}
