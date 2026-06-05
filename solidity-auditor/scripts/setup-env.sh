#!/usr/bin/env bash
# web3-audit — environment preflight (POSIX: Linux, macOS, WSL, Git-Bash/MINGW).
# Installs terminal-based smart-contract audit tools GLOBALLY and IDEMPOTENTLY.
# Already-present tools are skipped. Optional tools fail soft (never block the audit).
set -u
log(){ printf '[preflight] %s\n' "$*"; }
have(){ command -v "$1" >/dev/null 2>&1; }

case "$(uname -s 2>/dev/null || echo unknown)" in
  Linux*)               PLATFORM=linux;;
  Darwin*)              PLATFORM=macos;;
  MINGW*|MSYS*|CYGWIN*) PLATFORM=windows;;
  *)                    PLATFORM=unknown;;
esac
# Make user-space bin dirs visible for the checks below (persisted separately by each installer).
export PATH="$HOME/.local/bin:$HOME/scoop/shims:$HOME/.foundry/bin:$HOME/.cargo/bin:$PATH"
log "platform=$PLATFORM"

PY=""; have python3 && PY=python3; { [ -z "$PY" ] && have python; } && PY=python
ensure_pipx(){
  [ -n "$PY" ] || { log "no python — skipping pipx tools"; return 1; }
  $PY -m pipx --version >/dev/null 2>&1 && return 0
  log "installing pipx"; $PY -m pip install --user -q --upgrade pipx >/dev/null 2>&1
  $PY -m pipx ensurepath >/dev/null 2>&1; return 0
}
PIPX(){ $PY -m pipx "$@"; }

# ---------- Foundry (forge/cast/anvil/chisel) — REQUIRED ----------
if have forge; then log "ok: foundry"; else
  log "installing foundry"
  if [ "$PLATFORM" = windows ]; then
    DEST="$HOME/scoop/shims"; [ -d "$DEST" ] || DEST="$HOME/.local/bin"; mkdir -p "$DEST"
    TMP="$(mktemp -d)"
    if curl -fsSL -o "$TMP/foundry.zip" \
        https://github.com/foundry-rs/foundry/releases/download/nightly/foundry_nightly_win32_amd64.zip; then
      (cd "$TMP" && unzip -oq foundry.zip 2>/dev/null) \
        || powershell -NoProfile -Command "Expand-Archive -Force '$(cygpath -w "$TMP/foundry.zip" 2>/dev/null || echo "$TMP/foundry.zip")' '$(cygpath -w "$TMP" 2>/dev/null || echo "$TMP")'" >/dev/null 2>&1
      cp -f "$TMP"/forge.exe "$TMP"/cast.exe "$TMP"/anvil.exe "$TMP"/chisel.exe "$DEST"/ 2>/dev/null
    fi
    rm -rf "$TMP"
  else
    curl -fsSL https://foundry.paradigm.xyz | bash >/dev/null 2>&1
    "$HOME/.foundry/bin/foundryup" >/dev/null 2>&1 || foundryup >/dev/null 2>&1
  fi
  have forge && log "ok: foundry installed" || log "WARN: foundry install failed — install manually"
fi

# ---------- jq — REQUIRED (report/JSON plumbing) ----------
if have jq; then log "ok: jq"; else
  log "installing jq"
  if   [ "$PLATFORM" = windows ] && have scoop; then scoop install jq >/dev/null 2>&1
  elif [ "$PLATFORM" = macos ]   && have brew;  then brew install jq >/dev/null 2>&1
  elif have apt-get; then sudo apt-get update -qq >/dev/null 2>&1 && sudo apt-get install -y -qq jq >/dev/null 2>&1
  elif have dnf;     then sudo dnf install -y -q jq >/dev/null 2>&1
  elif have pacman;  then sudo pacman -S --noconfirm jq >/dev/null 2>&1
  fi
  have jq && log "ok: jq installed" || log "WARN: jq not installed"
fi

# ---------- Python analyzers: slither + solc-select — REQUIRED ----------
if ensure_pipx; then
  if have slither; then log "ok: slither"; else log "installing slither"; PIPX install slither-analyzer >/dev/null 2>&1; fi
  if have solc-select; then log "ok: solc-select"; else log "installing solc-select"; PIPX install solc-select >/dev/null 2>&1; fi
  if have solc-select && ! solc --version >/dev/null 2>&1; then
    log "installing solc 0.8.28"; solc-select install 0.8.28 >/dev/null 2>&1; solc-select use 0.8.28 >/dev/null 2>&1
  fi
fi

# ---------- Optional (best-effort; need Rust/build-tools — skipped on plain Windows) ----------
# aderyn (Cyfrin static analyzer): prebuilt unix binary via cyfrinup, or cargo.
if ! have aderyn; then
  if [ "$PLATFORM" != windows ]; then
    curl -fsSL https://raw.githubusercontent.com/Cyfrin/aderyn/dev/cyfrinup/install 2>/dev/null | bash >/dev/null 2>&1 || true
    { ! have aderyn; } && have cargo && cargo install aderyn >/dev/null 2>&1 || true
    have aderyn && log "ok: aderyn installed" || log "skip: aderyn (optional)"
  else
    log "skip: aderyn (no Windows prebuilt — use WSL or 'cargo install aderyn')"
  fi
fi
# halmos / mythril (symbolic) need a C/C++ build toolchain; install only where pipx can build them.
if [ "$PLATFORM" != windows ] && [ -n "$PY" ]; then
  have halmos || PIPX install halmos >/dev/null 2>&1 || true
  have myth   || PIPX install mythril >/dev/null 2>&1 || true
fi

# ---------- Summary ----------
echo "=== web3-audit toolchain ==="
for t in forge cast anvil chisel slither solc solc-select jq aderyn halmos myth git node npm rg; do
  if have "$t"; then printf "  ok   %-12s %s\n" "$t" "$($t --version 2>/dev/null | head -1)"; else printf "  --   %-12s (not installed)\n" "$t"; fi
done
echo "Note: pipx/foundry add user bin dirs to PATH; open a NEW terminal if a just-installed tool isn't found this session."
