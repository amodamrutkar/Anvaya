# scripts/run.ps1
# Sutradhar PowerShell Task Runner
# Usage: .\scripts\run.ps1 <command> [args]
param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(Position=1)]
    [string]$Version = "v1",

    [Parameter(Position=2)]
    [int]$Seed = 42
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host ""
    Write-Host "Sutradhar Task Runner (PowerShell)" -ForegroundColor Cyan
    Write-Host "-------------------------------------------------------"
    Write-Host "  .\scripts\run.ps1 test               Run all pytest tests (fail-fast)"
    Write-Host "  .\scripts\run.ps1 data [ver] [seed]  Generate synthetic dataset (default: v1 42)"
    Write-Host "  .\scripts\run.ps1 er [ver]           Run entity resolution pipeline"
    Write-Host "  .\scripts\run.ps1 graph [ver]        Run graph analytics pipeline"
    Write-Host "  .\scripts\run.ps1 eval [ver]         Run evaluation against ground truth"
    Write-Host "  .\scripts\run.ps1 api                Start FastAPI backend server"
    Write-Host "  .\scripts\run.ps1 web                Start React/Vite frontend server"
    Write-Host "  .\scripts\run.ps1 all [ver] [seed]   Run test -> data -> er -> graph -> eval (fails fast)"
    Write-Host ""
}

function Run-Step([string]$name, [scriptblock]$action) {
    Write-Host ""
    Write-Host "===> Running: $name" -ForegroundColor Yellow
    & $action
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        Write-Error "Step failed: $name with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

switch ($Command.ToLower()) {
    "test" {
        Run-Step "pytest suite" { pytest -v --tb=short }
    }
    "data" {
        Run-Step "data generation" { python -m sutradhar_data.generate --version $Version --seed $Seed --out data/ }
    }
    "er" {
        Run-Step "entity resolution" { python -m sutradhar_er.run --data "data/$Version" --out artifacts/er }
    }
    "graph" {
        Run-Step "graph analytics" { python -m sutradhar_graph.run --data "data/$Version" --er artifacts/er --out artifacts/graph }
    }
    "eval" {
        Run-Step "evaluation" { python -m sutradhar_eval.run --data "data/$Version" --truth "data/truth/$Version" --artifacts artifacts --out artifacts/metrics.json }
    }
    "api" {
        Write-Host "Starting API server on http://localhost:8000..." -ForegroundColor Green
        python -m uvicorn sutradhar_api.main:app --reload --host 0.0.0.0 --port 8000
    }
    "web" {
        Write-Host "Starting Web dev server on http://localhost:5173..." -ForegroundColor Green
        npm --prefix apps/web run dev
    }
    "all" {
        Write-Host "Running full verification pipeline (fail-fast)..." -ForegroundColor Cyan
        Run-Step "1/5: pytest" { pytest -v --tb=short }
        Run-Step "2/5: data"   { python -m sutradhar_data.generate --version $Version --seed $Seed --out data/ }
        Run-Step "3/5: er"     { python -m sutradhar_er.run --data "data/$Version" --out artifacts/er }
        Run-Step "4/5: graph"  { python -m sutradhar_graph.run --data "data/$Version" --er artifacts/er --out artifacts/graph }
        Run-Step "5/5: eval"   { python -m sutradhar_eval.run --data "data/$Version" --truth "data/truth/$Version" --artifacts artifacts --out artifacts/metrics.json }
        Write-Host ""
        Write-Host "All steps passed successfully!" -ForegroundColor Green
    }
    default {
        Show-Help
    }
}
