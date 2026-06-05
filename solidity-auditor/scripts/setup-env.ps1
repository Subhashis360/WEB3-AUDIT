# web3-audit — environment preflight (native Windows PowerShell).
# Installs terminal-based smart-contract audit tools GLOBALLY and IDEMPOTENTLY.
# Present tools are skipped; optional tools fail soft (never block the audit).
$ErrorActionPreference = 'Continue'
function Log($m){ Write-Host "[preflight] $m" }
function Have($c){ [bool](Get-Command $c -ErrorAction SilentlyContinue) }

$shims = Join-Path $env:USERPROFILE 'scoop\shims'
$localbin = Join-Path $env:USERPROFILE '.local\bin'
$env:PATH = "$localbin;$shims;$env:PATH"
Log "platform=windows"

# ---------- Foundry (forge/cast/anvil/chisel) — REQUIRED ----------
if (Have forge) { Log 'ok: foundry' } else {
  Log 'installing foundry (nightly win amd64)'
  try {
    $tmp = Join-Path $env:TEMP 'foundry_dl'; New-Item -ItemType Directory -Force $tmp | Out-Null
    $zip = Join-Path $tmp 'foundry.zip'
    Invoke-WebRequest -Uri 'https://github.com/foundry-rs/foundry/releases/download/nightly/foundry_nightly_win32_amd64.zip' -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $dest = $shims; if (-not (Test-Path $dest)) { $dest = $localbin; New-Item -ItemType Directory -Force $dest | Out-Null }
    foreach ($e in 'forge.exe','cast.exe','anvil.exe','chisel.exe') {
      $src = Join-Path $tmp $e; if (Test-Path $src) { Copy-Item $src $dest -Force }
    }
    Log 'ok: foundry installed'
  } catch { Log "WARN: foundry install failed - $($_.Exception.Message)" }
}

# ---------- jq — REQUIRED ----------
if (Have jq) { Log 'ok: jq' }
elseif (Have scoop)  { Log 'installing jq (scoop)';  scoop install jq | Out-Null }
elseif (Have winget) { Log 'installing jq (winget)'; winget install --silent --accept-source-agreements --accept-package-agreements jqlang.jq | Out-Null }
elseif (Have choco)  { Log 'installing jq (choco)';  choco install jq -y | Out-Null }
else { Log 'WARN: no package manager for jq (install scoop: https://scoop.sh)' }

# ---------- Python analyzers: slither + solc-select — REQUIRED ----------
$py = $null
if (Have python) { $py = 'python' } elseif (Have python3) { $py = 'python3' }
if ($py) {
  & $py -m pipx --version 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Log 'installing pipx'; & $py -m pip install --user -q --upgrade pipx | Out-Null; & $py -m pipx ensurepath | Out-Null }
  if (Have slither) { Log 'ok: slither' } else { Log 'installing slither'; & $py -m pipx install slither-analyzer | Out-Null }
  if (Have solc-select) { Log 'ok: solc-select' } else { Log 'installing solc-select'; & $py -m pipx install solc-select | Out-Null }
  $env:PATH = "$localbin;$env:PATH"
  if ((Have solc-select) -and -not (Have solc)) { Log 'installing solc 0.8.28'; solc-select install 0.8.28 | Out-Null; solc-select use 0.8.28 | Out-Null }
} else { Log 'WARN: python not found - skipping slither/solc-select' }

# ---------- Optional (need Rust/MSVC build tools - use WSL for these) ----------
if (-not (Have aderyn)) { Log "skip: aderyn (no Windows prebuilt - use WSL or 'cargo install aderyn')" }
Log 'skip: halmos/mythril/echidna/medusa (best run under WSL or Docker on Windows)'

# ---------- Summary ----------
Write-Host '=== web3-audit toolchain ==='
foreach ($t in 'forge','cast','anvil','chisel','slither','solc','solc-select','jq','git','node','npm','rg') {
  if (Have $t) {
    $v = (& $t --version 2>$null | Select-Object -First 1)
    Write-Host ("  ok   {0,-12} {1}" -f $t, $v)
  } else { Write-Host ("  --   {0,-12} (not installed)" -f $t) }
}
Write-Host 'Note: open a NEW terminal if a just-installed tool is not found this session (PATH was extended).'
