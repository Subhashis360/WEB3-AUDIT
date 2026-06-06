# ChainShield — AI-Powered Web3 Security Auditor

> **Enterprise-grade smart contract vulnerability hunting, from a single command.**

ChainShield is an AI agent skill for serious Solidity security work. It orchestrates a swarm of specialized AI agents to deliver findings that would take a human team hours — in minutes.

---

## Skill

### 🔍 [web3-audit](./solidity-auditor/)

**Deep-dive smart contract vulnerability hunter.**

Spawns 22 parallel specialist agents (plus a conditional 23rd for ZK circuit soundness when circuit files are in scope), each attacking your codebase from a unique angle — math precision, access control, economic exploits, reentrancy, read-only reentrancy, oracle/price-feed manipulation, cross-chain/bridge forgery, invariant violations, unlimited mint, unauthorized transfer, denial-of-service fund-lock, and more. Produces a structured security report with confidence-scored findings filtered to Critical/High/Medium, code-level diffs, and runnable Foundry PoCs for the critical classes.

**Trigger phrases:** `web3-audit`, `audit`, `check this contract`, `review for security`, `chain audit`

**Self-evolving over time.** The agents get sharper with every audit via a tamper-proof, file-based feedback loop — see below.

---

## 🧬 Self-evolving agents

The 22+ agents are prompt files, so they have no memory of their own. ChainShield gives them one with a **file-based learning loop** — no fine-tuning, no black box, just accumulated experience that every agent reads at the start of its next audit.

**The loop:**

```
1. Run web3-audit        → writes audit-log/<date>-<project>.json (every finding, outcome: null)
2. Learn the real result → bounty paid? duplicate? false positive? a bug it missed?
3. Record it             → python scripts/record_outcome.py --id N --outcome ... --lesson "..."
4. Next audit            → each agent's lesson ledger is folded into its bundle automatically
```

Confirmed bugs get re-weaponized on new targets (recall climbs); false-positives get suppressed by an explicit "stop reporting when…" rule (precision climbs). A per-agent **scoreboard** tracks confirmed / dup / false-positive / missed and precision over time.

### Built so no LLM — weak or strong — can corrupt it

The ledger is a **trusted input to every future audit**, so one bad entry would poison all agents. ChainShield enforces a hard invariant: **the knowledge base has exactly one writer — the validated `record_outcome.py`, driven by an explicit human outcome decision.** No model ever writes a lesson, which makes integrity independent of runtime capability (a weak Gemini-inline run is as safe as Claude).

- **Human-gated** — nothing becomes a lesson until *you* state the outcome. A false positive can never silently train the agents.
- **Strict validation** — a lesson is rejected unless it's well-formed (`Pattern:`+`Tell:` for confirmed, `Stop when:` for false-positive); input is sanitized so a lesson string can't break the ledger format.
- **Tamper detection** — every entry carries a provenance footer and the ledger is sha256-tracked. `record_outcome.py --verify` flags any out-of-band edit, and the auditor refuses to load a ledger that fails the check (runs without lessons + warns instead).
- **Idempotent & reversible** — the scoreboard is recomputed from source-of-truth logs (re-recording can't inflate stats), and any mistaken lesson is removed with `--revert`.

### Commands

```bash
python scripts/record_outcome.py --list                       # findings from the last audit
python scripts/record_outcome.py --id 3 --outcome paid --paid 25000 --global \
       --lesson "Pattern: ... | Tell: ... | Generalize: ..."   # record a confirmed bug
python scripts/record_outcome.py --id 5 --outcome false-positive \
       --lesson "Claim: ... | Stop when: ..."                  # suppress a false positive
python scripts/record_outcome.py --missed --agent oracle-manipulation-agent \
       --lesson "Pattern: ... | Tell: ..."                     # teach a bug it missed
python scripts/record_outcome.py --show                        # list ledger entries + ids
python scripts/record_outcome.py --verify                      # check ledger integrity
python scripts/record_outcome.py --revert <ledger-id>          # undo a mistaken lesson
```

> Self-evolution only happens if you record outcomes — that human step is both the engine and the safety gate.

---

## Compatibility — runs on any agentic runtime

The skill is written against an **abstract capability set** (shell + file read/search + an optional sub-agent tool), so it runs unmodified across agentic CLIs. On startup the auditor detects what your runtime offers and picks a `spawn_mode` — using parallel background sub-agents where available and gracefully degrading to a sequential **inline** mode (the orchestrator plays every specialist itself) where they aren't. **The methodology is identical everywhere; only the dispatch changes — no specialist is ever skipped.**

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

**Per-runtime invocation:**

- **Claude Code** — `/web3-audit` (or say "web3-audit this repo" / "audit this contract").
- **OpenCode** — place the skill folder under your skills/commands dir and invoke `web3-audit`, or paste the trigger phrase.
- **Codex / Gemini / Cursor / Antigravity** — load `solidity-auditor/SKILL.md` as the task instructions and say "run web3-audit on the codebase". The skill adapts to the runtime's available tools automatically.
- **Any agent** — feed it the SKILL.md and a target path; as long as it has a shell and can read files, it runs in `inline` mode.

---

## Recommended Workflow

```
1. web3-audit       → parallel multi-agent vulnerability hunting
2. Record outcomes  → scripts/record_outcome.py (feeds agent self-evolution)
3. Manual review    → validate and deepen findings
4. Formal audit     → final sign-off
```

---

## Output Quality

| What | web3-audit |
|------|:---:|
| Vulnerability findings | ✅ |
| Confidence scores | ✅ |
| Code-level fix diffs | ✅ |
| Runnable Foundry PoCs (critical classes) | ✅ |
| Critical/High/Medium severity filtering | ✅ |
| Cross-audit self-evolution (lesson ledgers) | ✅ |

---

## License

MIT — use freely for security research, audit preparation, and development workflows.
