param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('all', 'eastmoney', 'ssgs', 'clean', 'run-eastmoney', 'run-ssgs')]
    [string]$Target = 'all'
)

$ErrorActionPreference = "Stop"

$VERSION = if (Get-Command git -ErrorAction SilentlyContinue) {
    git describe --tags --always --dirty 2>$null
} else {
    "dev"
}

$BUILD_TIME = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"
$LDFLAGS = "-s -w -X main.Version=$VERSION -X main.BuildTime=$BUILD_TIME"

function Build-EastMoney {
    Write-Host "Building eastmoney crawler..." -ForegroundColor Green
    Push-Location cmd/eastmoney
    go build -ldflags $LDFLAGS -o ../../bin/eastmoney_crawler.exe main.go
    Pop-Location
    Write-Host "✓ eastmoney_crawler.exe built successfully" -ForegroundColor Green
}

function Build-SSGS {
    Write-Host "Building ssgs crawler..." -ForegroundColor Green
    Push-Location cmd/ssgs
    go build -ldflags $LDFLAGS -o ../../bin/ssgs_crawler.exe main.go
    Pop-Location
    Write-Host "✓ ssgs_crawler.exe built successfully" -ForegroundColor Green
}

function Clean {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    Remove-Item -Path bin -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Clean completed" -ForegroundColor Green
}

function Run-EastMoney {
    Write-Host "Running eastmoney crawler..." -ForegroundColor Cyan
    if (-not (Test-Path bin/eastmoney_crawler.exe)) {
        Write-Host "eastmoney_crawler.exe not found, building first..." -ForegroundColor Yellow
        Build-EastMoney
    }
    & ./bin/eastmoney_crawler.exe
}

function Run-SSGS {
    Write-Host "Running ssgs crawler..." -ForegroundColor Cyan
    if (-not (Test-Path bin/ssgs_crawler.exe)) {
        Write-Host "ssgs_crawler.exe not found, building first..." -ForegroundColor Yellow
        Build-SSGS
    }
    & ./bin/ssgs_crawler.exe
}

switch ($Target) {
    'all' {
        Build-EastMoney
        Build-SSGS
    }
    'eastmoney' {
        Build-EastMoney
    }
    'ssgs' {
        Build-SSGS
    }
    'clean' {
        Clean
    }
    'run-eastmoney' {
        Run-EastMoney
    }
    'run-ssgs' {
        Run-SSGS
    }
}
