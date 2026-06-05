# ChainShield — AI-Powered Web3 Security Skills

> **Enterprise-grade smart contract intelligence, from a single command.**

ChainShield is a suite of AI agent skills designed for serious Solidity security work. Each skill orchestrates multiple specialized AI agents to deliver findings and intelligence that would take a human team hours — in minutes.

---

## Skills

### 🔍 [web3-audit](./solidity-auditor/)

**Deep-dive smart contract vulnerability hunter.**

Spawns 21 parallel specialist agents, each attacking your codebase from a unique angle — math precision, access control, economic exploits, reentrancy, read-only reentrancy, oracle/price-feed manipulation, cross-chain/bridge forgery, invariant violations, unlimited mint, unauthorized transfer, denial-of-service fund-lock, and more. Produces a structured security report with confidence-scored findings filtered to Critical/High/Medium, code-level diffs, and runnable Foundry PoCs for the critical classes.

**Trigger phrases:** `web3-audit`, `audit`, `check this contract`, `review for security`, `chain audit`

---

### 🛰️ [audit-prep](./x-ray/)

**Pre-audit protocol intelligence engine.**

Generates a complete pre-audit intelligence package: threat model, invariant map, entry point classification, architecture diagram, git history analysis. Know your attack surface before the auditors do.

**Trigger phrases:** `audit-prep`, `pre-audit report`, `prep this protocol`, `audit readiness`, `threat-scope`

---

## Compatibility — runs on any agentic runtime

Both skills are written against an **abstract capability set** (shell + file read/search + an optional sub-agent tool), so they run unmodified across agentic CLIs. On startup the auditor detects what your runtime offers and picks a `spawn_mode` — using parallel background sub-agents where available and gracefully degrading to a sequential **inline** mode (the orchestrator plays every specialist itself) where they aren't. **The methodology is identical everywhere; only the dispatch changes — no specialist is ever skipped.**

| Runtime | Sub-agent dispatch | Status |
| --- | --- | --- |
| **Claude Code** | parallel background agents | ✅ first-class (model picker, background fan-out) |
| **OpenCode** | `task` sub-agents (parallel/sequential) | ✅ supported |
| **Codex CLI** | sequential / inline | ✅ supported |
| **Gemini CLI** | sequential / inline | ✅ supported |
| **Cursor** (agent) | sub-agent or inline | ✅ supported |
| **Antigravity** | sub-agent or inline | ✅ supported |
| Any other (shell + file read) | inline fallback | ✅ supported |

Claude-Code-only conveniences (`ToolSearch`, `AskUserQuestion` model picker, `TodoWrite`) are auto-skipped on runtimes that lack them — they are not load-bearing.

The auditor also **self-provisions its toolchain** on first run (Foundry, Slither, solc-select, jq) for Windows / Linux / macOS / WSL — see [`solidity-auditor/scripts/`](./solidity-auditor/scripts/). Terminal-based, global, idempotent.

## Installation & usage

Point your agent at this repo and trigger with natural language:

```
Install https://github.com/Subhashis360/WEB3-AUDIT and run web3-audit on the codebase
```

```
Install https://github.com/Subhashis360/WEB3-AUDIT and run audit-prep on the codebase
```

**Per-runtime invocation:**

- **Claude Code** — `/web3-audit` (or say "web3-audit this repo" / "audit this contract").
- **OpenCode** — place the skill folder under your skills/commands dir and invoke `web3-audit` / `audit-prep`, or paste the trigger phrase.
- **Codex / Gemini / Cursor / Antigravity** — load `solidity-auditor/SKILL.md` (or `x-ray/SKILL.md`) as the task instructions and say "run web3-audit on the codebase". The skill adapts to the runtime's available tools automatically.
- **Any agent** — feed it the SKILL.md and a target path; as long as it has a shell and can read files, it runs in `inline` mode.

---

## Recommended Workflow

```
1. audit-prep → full protocol intelligence picture
2. web3-audit → targeted vulnerability hunting on identified hotspots
3. Manual review → validate and deepen findings
4. Formal audit → final sign-off
```

---

## Output Quality

| What | web3-audit | audit-prep |
|------|:---:|:---:|
| Vulnerability findings | ✅ | — |
| Confidence scores | ✅ | — |
| Code-level fix diffs | ✅ | — |
| Threat model | — | ✅ |
| Invariant map | — | ✅ |
| Entry point classification | — | ✅ |
| Architecture diagram | — | ✅ |
| Git security analysis | — | ✅ |
| Audit readiness verdict | — | ✅ |

---

## License

MIT — use freely for security research, audit preparation, and development workflows.
