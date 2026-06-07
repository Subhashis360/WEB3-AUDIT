---
name: web3-audit
description: Deep-dive security audit of Solidity / web3 code while you develop. Trigger on "web3-audit", "audit", "check this contract", "review for security", "chain audit", "audit this". Modes - default (full repo) or a specific filename.
---

# Smart Contract Security Audit

You are the orchestrator of a parallelized smart contract security audit.

## Runtime Compatibility (read first)

This skill runs on **any agentic runtime** — Claude Code, OpenCode, Codex, Gemini CLI, Cursor, Antigravity, and others. It is written against an abstract capability set. Map each capability to your host runtime's equivalent tool; the steps below use **Claude Code tool names as the canonical example**.

| Capability | Claude Code | OpenCode | Codex / Gemini / Cursor / other |
| --- | --- | --- | --- |
| Run shell | `Bash` | `bash` | the runtime's shell/exec tool |
| Read file | `Read` | `read` | the runtime's file-read tool |
| Search / list | `Grep` / `Glob` | `grep` / `glob` | the runtime's search tools, or `grep`/`find` via shell |
| Spawn sub-agent | `Agent` (Task) | `task` subagent | the runtime's subagent/task tool, if any |
| Ask the user | `AskUserQuestion` | (prompt) | skip if unavailable |
| Load deferred tool | `ToolSearch` | — | skip — Claude-Code-only convenience |
| Track todos | `TodoWrite` | — | optional — skip if absent |

`ToolSearch`, `AskUserQuestion`, and `TodoWrite` are **conveniences, not load-bearing** — if your runtime lacks them, skip those steps. Shell + file-read are the only hard requirements.

**Determine `{spawn_mode}`** from how your runtime can run the N specialty agents, and use it everywhere a step says "spawn agent N":

- **`parallel-background`** — runtime spawns sub-agents that run concurrently in the background (Claude Code `Agent` + `run_in_background`). Spawn all at once, collect on completion. *(Canonical path used by the steps below.)*
- **`parallel-foreground`** — sub-agent tool exists but blocks: spawn in parallel batches, wait inline for each batch.
- **`sequential`** — sub-agent tool runs one at a time: run each agent in turn, collect findings, continue.
- **`inline`** — **NO sub-agent tool at all** (universal fallback): the orchestrator itself plays every agent. For each agent bundle, do a dedicated, focused reasoning pass over *that bundle only* (source + SOP + that one specialty + shared rules), emit its FINDING/LEAD blocks, then move to the next specialty. Slower, **identical methodology**, runs anywhere with a shell + file read.

The **method is identical** across runtimes — each specialty reads its bundle and produces findings; the orchestrator dedups, gates, and reports. Only the dispatch mechanism changes. **Never skip a specialty because background spawning is unavailable — fall back to a lower `{spawn_mode}` (down to `inline`).** A run that executes all specialties sequentially is correct; a run that drops specialties is not.

## Mode Selection

**Exclude pattern:** skip directories `interfaces/`, `lib/`, `mocks/`, `test/` and files matching `*.t.sol`, `*Test*.sol` or `*Mock*.sol`.

- **Default** (no arguments): scan all `.sol` files using the exclude pattern. Use Bash `find` (not Glob).
- **`$filename ...`**: scan the specified file(s) only.

**ZK circuit detection (conditional 23rd agent).** Also detect zero-knowledge circuit sources in scope: files matching `*.circom`, `*.nr` (Noir), `*.cairo`, and halo2/arkworks/gnark/bellman Rust gadgets (`.rs` files whose path contains `circuit`/`gadget`/`halo2`/`plonk`, or whose contents import `halo2`, `ark_`, `bellman`, `plonky2`, or `gnark`). If any are found, set `{zk_present}=true` and collect them as `{zk_files}`. This enables the circuit-soundness agent (agent-23) — the missing-constraint / soundness specialist (the Orchard/Zcash inflation bug class). If none are found, `{zk_present}=false` and the audit runs the standard 22 agents.

**Flags:**

- `--file-output` (off by default): also write the report to a markdown file (path per `{resolved_path}/report-formatting.md`). Never write a report file unless explicitly passed.
## Orchestration

**Turn 0 — Environment preflight (toolchain bootstrap).** Before discovery, ensure the terminal-based audit toolchain is installed so PoC generation and static analysis are fast and self-provisioning on any machine. **All tools are terminal-based.**

1. **Fast presence check (one Bash call):** `command -v forge slither solc jq cast anvil`, prefixed with `export PATH="$HOME/.local/bin:$HOME/scoop/shims:$HOME/.foundry/bin:$HOME/.cargo/bin:$PATH"` so user-space installs from a prior run resolve.
2. **If `forge`, `slither`, `solc`, and `jq` are ALL present** → print `✓ audit toolchain ready` and proceed to Turn 1. (These four are the required floor; do not reinstall.)
3. **If any of the four is missing** → locate the setup scripts (Glob `**/scripts/setup-env.sh` → its directory is `{skill_dir}/scripts`) and run the OS-appropriate one ONCE, non-interactively, tolerating failures:
   - **Windows** (`uname` is `MINGW*`/`MSYS*`/`CYGWIN*`, or PowerShell is available): prefer `PowerShell` → `powershell -NoProfile -ExecutionPolicy Bypass -File {skill_dir}/scripts/setup-env.ps1`. (The Git-Bash path also works: `bash {skill_dir}/scripts/setup-env.sh`.)
   - **Linux / macOS / WSL:** `bash {skill_dir}/scripts/setup-env.sh`.
   The scripts are idempotent (skip present tools), install globally to user space (scoop shims / pipx `~/.local/bin` / `~/.foundry/bin` — all persisted to PATH), and print a toolchain summary. Re-run the presence check afterward.
4. **Never block the audit on a failed optional tool.** `forge` + `slither` + `solc` + `jq` are the floor; `aderyn`/`halmos`/`mythril`/`echidna`/`medusa` are optional (best under WSL/Docker on Windows). If a required install genuinely fails, print a one-line warning and proceed to Turn 1 anyway — the agents still audit by reasoning; tools only accelerate PoCs. Do NOT retry installs in a loop.
5. Run preflight **once per session**; if a `✓ audit toolchain ready` was already printed earlier this session, skip straight to Turn 1.

**Turn 1 — Discover.** Make these parallel tool calls in one message:

a. Bash `find` for in-scope `.sol` files per mode selection — and, in the same call, for ZK circuit files (`*.circom`, `*.nr`, `*.cairo`, and halo2/arkworks/gnark gadget `.rs`) to set `{zk_present}` / `{zk_files}` per Mode Selection
b. Glob for `**/references/hacking-agents/shared-rules.md` — extract the `references/` directory (two levels up) as `{resolved_path}`
c. (Claude Code only) ToolSearch `select:Agent` to load the sub-agent tool. On runtimes without `ToolSearch`, skip this — use whatever sub-agent/task tool your runtime exposes per `{spawn_mode}`, or `inline` if it has none.
d. Read the local `VERSION` file from the same directory as this skill
e. Bash `curl -sf https://raw.githubusercontent.com/Subhashis360/WEB3-AUDIT/main/solidity-auditor/VERSION`
f. Bash `mktemp -d ./.audit-XXXXXX` → store as `{bundle_dir}`

If the remote VERSION fetch succeeds and differs from local, print `⚠️ You are not using the latest version. Please upgrade for best security coverage. See https://github.com/Subhashis360/WEB3-AUDIT`. If it fails, skip silently.

**Turn 1b — Model selection (Claude Code only).** This turn applies ONLY when both `AskUserQuestion` and the `Agent` tool (with a `model` parameter) are available in your runtime — i.e., Claude Code. On Codex, Gemini, Cursor's native agent, or any runtime without these, SKIP this turn entirely, leave `{agent_model}` unset, and proceed to Turn 2. Do NOT emit the question as prose. Do NOT substitute any other mechanism.

On Claude Code:

1. Read your system prompt to detect your own model **family** (Opus, Sonnet, or Haiku). Ignore the version digits — the Agent tool's `model` parameter takes the family name (`"opus"` / `"sonnet"` / `"haiku"`), and the runtime resolves to the latest version in that family.
2. Call `AskUserQuestion` with:
   - Question: `"Which Claude model should the 22 audit agents use?"`
   - Three single-select options. Mark the orchestrator's own family as `(Recommended)` and place it first.
   - On each option, set the `description` field to `latest`.
   - On each option, set the `preview` field verbatim (preserve all whitespace exactly — the box widths must stay equal across all three):

   Opus preview:

   ```
   ┌──────────────────────────────────────────────────────────┐
   │  opus  ·  highest reasoning  ·  most expensive           │
   └──────────────────────────────────────────────────────────┘
   ```

   Sonnet preview:

   ```
   ┌──────────────────────────────────────────────────────────┐
   │  sonnet  ·  balanced reasoning  ·  mid cost              │
   └──────────────────────────────────────────────────────────┘
   ```

   Haiku preview:

   ```
   ┌──────────────────────────────────────────────────────────┐
   │  haiku  ·  lowest reasoning  ·  cheapest                 │
   └──────────────────────────────────────────────────────────┘
   ```
3. Store the runner's choice as `{agent_model}`. If no answer, default to the orchestrator's own model.

**Turn 2 — Prepare.** In one message, make parallel tool calls: (a) Read `{resolved_path}/report-formatting.md`, (b) Read `{resolved_path}/judging.md`.

Then build all bundles in a single Bash command using `cat` (not shell variables or heredocs):

1. `{bundle_dir}/source.md` — ALL in-scope `.sol` files, each with a `### path` header and fenced code block.
2. Agent bundles = `source.md` + agent-specific files:

| Bundle                | Appended files (relative to `{resolved_path}`)                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent-1-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/math-precision-agent.md` + `hacking-agents/shared-rules.md`                            |
| `agent-2-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/access-control-agent.md` + `hacking-agents/shared-rules.md`                            |
| `agent-3-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/economic-security-agent.md` + `hacking-agents/shared-rules.md`                         |
| `agent-4-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/execution-trace-agent.md` + `hacking-agents/shared-rules.md`                           |
| `agent-5-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/invariant-agent.md` + `hacking-agents/shared-rules.md`                                 |
| `agent-6-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/periphery-agent.md` + `hacking-agents/shared-rules.md`                                 |
| `agent-7-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/first-principles-agent.md` + `hacking-agents/shared-rules.md`                          |
| `agent-8-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/asymmetry-agent.md` + `hacking-agents/shared-rules.md`                                 |
| `agent-9-bundle.md`   | `source.md` + `senior-auditor-sop.md` + `hacking-agents/boundary-agent.md` + `hacking-agents/shared-rules.md`                                  |
| `agent-10-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/numerical-gap-agent.md` + `hacking-agents/shared-rules.md`                             |
| `agent-11-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/trust-gap-agent.md` + `hacking-agents/shared-rules.md`                                 |
| `agent-12-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/flow-gap-agent.md` + `hacking-agents/shared-rules.md`                                  |
| `agent-13-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/unlimited-mint-agent.md` + `hacking-agents/shared-rules.md`                            |
| `agent-14-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/unauthorized-transfer-agent.md` + `hacking-agents/shared-rules.md`                     |
| `agent-15-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/swap-without-auth-agent.md` + `hacking-agents/shared-rules.md`                         |
| `agent-16-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/signature-exploit-agent.md` + `hacking-agents/shared-rules.md`                         |
| `agent-17-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/flash-loan-attack-agent.md` + `hacking-agents/shared-rules.md`                         |
| `agent-18-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/reentrancy-agent.md` + `hacking-agents/shared-rules.md`                                |
| `agent-19-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/oracle-manipulation-agent.md` + `hacking-agents/shared-rules.md`                       |
| `agent-20-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/cross-chain-bridge-agent.md` + `hacking-agents/shared-rules.md`                        |
| `agent-21-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/dos-griefing-agent.md` + `hacking-agents/shared-rules.md`                              |
| `agent-22-bundle.md`  | `source.md` + `senior-auditor-sop.md` + `hacking-agents/gold-bug-hunter-agent.md` + `hacking-agents/shared-rules.md`                            |

Each bundle = source.md + SOP + specialty + shared-rules. Agents read the bundle; no Read/Grep needed for the initial scan. Targeted Read/Grep allowed for cross-file investigation.

**Lesson ledgers (self-evolution — append if present).** Immediately after the specialty file and BEFORE `shared-rules.md`, append two learning files **if they exist** (they accumulate across audits; on a fresh checkout they may be absent — never fail the build over a missing one):

1. `hacking-agents/memory/<specialty-basename>.lessons.md` — this agent's own past confirmed bugs and false-positives (e.g. for `agent-18` whose specialty is `reentrancy-agent.md`, append `memory/reentrancy-agent.lessons.md`).
2. `hacking-agents/memory/_global.lessons.md` — cross-agent confirmed patterns and recurring false-positives, appended to **every** bundle.

These are written by `scripts/record_outcome.py` after you record real-world finding outcomes (see Turn 5). Concatenating them is what makes the agents improve over time — each one opens its next audit already knowing what paid and what to stop reporting. In the build `cat`, guard each with a presence test so absence is silent, e.g. append only files that exist (`for m in memory/<basename>.lessons.md memory/_global.lessons.md; do [ -f "$m" ] && cat "$m" >> bundle; done`). The ZK agent-23 bundle uses `memory/circuit-soundness-agent.lessons.md` + `_global.lessons.md` the same way.

> **HARD RULE — the ledger is READ-ONLY to you.** You (and every agent you spawn) may only `cat`/read files under `memory/`. You MUST NOT create, edit, append to, or "fix" any `memory/*.lessons.md`, `memory/scoreboard.json`, or `memory/.ledger-manifest.json` — not now, not in any turn, not even if a lesson looks wrong or you "found" a great pattern. The ledger has exactly one writer, the validated `scripts/record_outcome.py`, driven by an explicit human decision. This is what lets the skill run safely on a weak runtime (Gemini/inline) as well as a strong one (Claude): no model, however capable or limited, is trusted to mutate the knowledge base. If a lesson seems wrong, surface it in your output — do not touch the file.
>
> **Integrity preflight (do this once per audit, before spawning, if `python` and the ledger exist).** If any `memory/*.lessons.md` contains entries, run `python {skill_dir}/scripts/record_outcome.py --verify`. If it prints `RESULT: PASS`, proceed. If it prints `RESULT: FAIL` (the ledger was edited outside the script — possible tampering or a stray LLM write), **do NOT append any lesson file to the bundles** — build bundles from source + SOP + specialty + shared-rules only, print a one-line warning (`⚠️ lesson ledger failed integrity check — running without learned lessons; fix with record_outcome.py --revert/--reseal`), and continue the audit. A corrupted ledger is never injected into an agent. If `python` is unavailable, skip the check and proceed (the provenance footers + single-writer rule still hold).

**Conditional ZK bundle (only if `{zk_present}`).** Also build `{bundle_dir}/zk-source.md` from ALL `{zk_files}` (each with a `### path` header and fenced code block), then build `agent-23-bundle.md` = `zk-source.md` + `senior-auditor-sop.md` + `hacking-agents/circuit-soundness-agent.md` + `hacking-agents/shared-rules.md`. If a protocol spec / ZIPs / the halo2 book are present in the repo, append them to `zk-source.md` too — feeding the reference material into the circuit auditor is what surfaces missing-constraint bugs.

Print line counts for every bundle and `source.md`. Do NOT inline source code into the Agent call prompt itself.

**Turn 3a — Spawn all agents (22, or 23 if `{zk_present}`).** Dispatch per `{spawn_mode}` (see Runtime Compatibility): `parallel-background` spawns them all at once in the background; `parallel-foreground` spawns in batches and waits; `sequential` runs one at a time; `inline` means the orchestrator performs each specialty's reasoning pass itself, one bundle at a time. **All `{spawn_mode}` values must execute every agent — only the dispatch differs.** The canonical instructions below describe the `parallel-background` path (Claude Code); on other runtimes, apply the same per-agent prompt and bundle through your runtime's mechanism. In one message (when parallel), spawn all agents as **parallel BACKGROUND Agent calls** (`run_in_background=true`). If Turn 1b set `{agent_model}`, pass `model={agent_model}` on every Agent call. If `{agent_model}` is unset (Turn 1b skipped — Codex, Gemini, others), omit the `model` parameter entirely — do NOT substitute any default. The orchestrator will receive a notification when each agent completes — do NOT poll or sleep. Single phase, no later spawns. Proceed to Turn 3b only after every spawned agent (all 22, or 23 with ZK) has notified completion.

Agents 1–9 use the **single-specialty prompt** (Turn 3a-i). Agents 10–12 use the **gap-hunter prompt** (Turn 3a-ii). Agents 13–21 use the **critical-exploit prompt** (Turn 3a-iii). Agent 22 (gold-bug-hunter) uses the **single-specialty prompt** (Turn 3a-i). **If `{zk_present}`, additionally spawn agent-23 (circuit-soundness) using the critical-exploit prompt (Turn 3a-iii) — total 23 agents; otherwise 22.**

**Turn 3a-i — Single-specialty prompt template (agents 1–9, substitute real values):**

```
You are an attacker. Your specialty, mindset, source, and output rules
are in your bundle. Read it fully before producing findings.

Read first:
- {bundle_dir}/agent-N-bundle.md (XXXX lines) — source + SOP + specialty + shared rules.

The bundle contains all in-scope source. Do NOT re-read in-scope files
for the initial scan. Use Read/Grep only for cross-file searches or
out-of-scope context (interfaces/, lib/, mocks/, test/).

What a finding looks like:
- file, function
- root cause — the one-sentence code-level defect
- minimal fix — the smallest change that eliminates the defect
- proof — concrete numbers, a trace, or quoted code

Without concrete proof, it's a LEAD, not a finding. Leads are honest
about what you couldn't verify — they're not failures, they're
calibration. Emit them.

Don't skim. Don't trust your first read. Trust your discomfort.

Output format: see shared-rules.md inside your bundle.
```

**Turn 3a-ii — Gap-hunter prompt template (agents 10–12, substitute real values):**

```
You are an attacker. Your gap-hunter specialty, mindset, source, and
output rules are in your bundle. Read it fully before producing findings.

Read first:
- {bundle_dir}/agent-N-bundle.md (XXXX lines) — source + SOP + gap-hunter specialty + shared rules.

The bundle contains all in-scope source. Do NOT re-read in-scope files
for the initial scan. Use Read/Grep only for cross-file searches or
out-of-scope context (interfaces/, lib/, mocks/, test/).

What a finding looks like:
- file, function
- seam — which two or three lenses combine
- root cause — the one-sentence code-level defect that lives at the seam
- minimal fix — the smallest change that eliminates the defect
- proof — concrete numbers, a trace, or quoted code showing the seam

Without concrete proof of the seam, it's a LEAD, not a finding.
Leads are honest about what you couldn't verify — they're not failures,
they're calibration. Emit them.

Don't skim. Don't trust your first read. Trust your discomfort.

Output format: see shared-rules.md inside your bundle (gap-hunter-specific
output fields are in your specialty file).
```

**Turn 3a-iii — Critical-exploit prompt template (agents 13–21, substitute real values):**

```
You are an attacker with a specific critical-exploit specialty. Your attack model, targets, and proof requirements are in your bundle. Read it fully before producing findings.

Read first:
- {bundle_dir}/agent-N-bundle.md (XXXX lines) — source + SOP + exploit specialty + shared rules.

The bundle contains all in-scope source. Do NOT re-read in-scope files for the initial scan.
Use Read/Grep only for cross-file searches or out-of-scope context (interfaces/, lib/, mocks/, test/).

Your specialty is a CRITICAL exploit class — the bugs that cause the biggest losses:
- Unlimited token generation
- Unauthorized token transfers
- Swaps without authorization
- Signature/permit bypass
- Flash loan enabled attacks
- Reentrancy (classic / cross-function / read-only / hook / cross-contract)
- Oracle / price-feed manipulation and staleness
- Cross-chain / bridge message forgery and replay
- Denial of service / griefing that permanently locks funds
- ZK circuit soundness / missing constraint (unconstrained witness → forged nullifier, double-spend, undetectable inflation — agent-23, only when circuit files are in scope)

For EVERY finding in your class:
- Write the exploit as a numbered call sequence (attacker steps)
- Include concrete token amounts / dollar values
- Include the specific missing check that would prevent it

Without a numbered call sequence and concrete values, it is a LEAD, not a FINDING.

Output format: see shared-rules.md inside your bundle, plus your specialty's output fields.
```

**Turn 3b — Collect all agent results.** Once every spawned agent (all 22, or 23 if `{zk_present}`) has returned, proceed to Turn 4. Do NOT proceed to dedup until every agent has finished. On `parallel-background` (Claude Code), let them run to natural completion and act only on completion notifications — do NOT poll or sleep. On `parallel-foreground` / `sequential` / `inline`, "completion" simply means each agent's pass has returned its FINDING/LEAD output — gather all of them, then continue. Either way: every specialty's output must be in hand before Turn 4.

**Turn 4 — Deduplicate, validate & output.** Single-pass: deduplicate all agent results, gate-evaluate, and produce the final report in one turn. Do NOT print an intermediate dedup list — go straight to the report.

1. **Dedup.** Parse every FINDING and LEAD from all spawned agents (22, or 23 with the ZK circuit-soundness agent). Group by `group_key` (Contract | function | bug-class). Exact-match first; merge synonymous bug_class within same (Contract, function). Keep best per group, number sequentially, annotate `[agents: N]`.

   **MANDATORY — Wide-description (group_key).** Merged group with distinct mechanisms (different `fix:`, code-level cause, or attack path) MUST list every mechanism. No dropping. Same function can have multiple coexisting bugs at the same group_key — all MUST appear.

   **MANDATORY — Function-level second pass (after group_key dedup).** Run at (Contract, function), ignoring bug_class. Agents often label coexisting bugs with different bug_class tags but reference multiple mechanisms in the body. For every (Contract, function) with multiple final findings: scan body (description, path, proof, fix) of every constituent for distinct mechanisms across bug_class boundaries. Every mechanism in any constituent body MUST appear in ≥1 final finding.

   **MANDATORY — Function isolation (HARD).** NEVER merge across different `function:` fields. Dedup only within (Contract, function). Different function = different bug. Second pass above stays WITHIN (Contract, function), never across.

   **MANDATORY — Fix preservation (HARD GATE).** Before writing merged `fix:` on a multi-finding (Contract, function):
   1. Collect every raw `fix:` from agents flagging the tuple.
   2. Group by ADD-lines (`+` lines, or equivalent require/assignment).
   3. Distinct if ADD-lines differ in: called function/expression (e.g., `require(msg.value == amount)` vs `require(zrc20 != _ETH_ADDRESS_)`), check direction (validate/restrict/ban), or checked parameter.
   4. ≥2 distinct → present as Option A, B, … — one block per distinct fix, verbatim from agent text (no paraphrase).
   5. Label intuitively: validate / restrict / allow-and-handle / ban-path.

   **Output format when 2+ distinct fixes exist:**

   ```
   **Fix (Option A — <label>)**:

   ```diff
   <verbatim diff from raw agent N1's fix>
   ```

   **Fix (Option B — <label>)**:

   ```diff
   <verbatim diff from raw agent N2's fix>
   ```
   ```

   **Inline check before printing**: count distinct fixes from raw for this (Contract, function). ≥2 distinct but merged shows 1 → violation, add alternatives.

   **MANDATORY — Completeness (HARD GATE).** Before print: list every unique (Contract, function, bug-class) in any raw FINDING/LEAD across all spawned agents (22, or 23 with ZK). Every unique (Contract, function) MUST have ≥1 item in final. Zero = silent drop, fix it. Multiple bug-class within same (Contract, function) MAY collapse to one item (wide-description), but the (Contract, function) MUST survive. Print inline before report: `Completeness: N unique (Contract, function) in raw, N covered in final.`

   **MANDATORY — Completeness (HARD GATE).** Before print: list every unique (Contract, function, bug-class) in any raw FINDING/LEAD across all spawned agents (22, or 23 with ZK). Every unique (Contract, function) MUST have ≥1 item in final. Zero = silent drop, fix it. Multiple bug-class within same (Contract, function) MAY collapse to one item (wide-description), but the (Contract, function) MUST survive. Print inline before report: `Completeness: N unique (Contract, function) in raw, N covered in final.`

   **CRITICAL-EXPLOIT PRIORITY:** Findings from agents 13–21 (unlimited-mint, unauthorized-transfer, swap-without-auth, signature-exploit, flash-loan-attack, reentrancy, oracle-manipulation, cross-chain-bridge, dos-griefing), agent-22 (gold-bug-hunter — the meta-hunter for what other agents miss), and agent-23 (circuit-soundness) when ZK files are in scope — are **automatically prioritized** to the top of the report regardless of confidence score. These represent the highest-impact bug classes. List them in this order at the top of the report:
   0. ZK circuit soundness / missing constraint (undetectable inflation or double-spend) — when present, this outranks everything
   1. Unlimited mint / token inflation
   2. Unauthorized transfer / direct theft
   3. Cross-chain / bridge message forgery (unbacked mint / double-spend)
   4. Reentrancy drain (classic / cross-function / read-only / hook / cross-contract)
   5. Oracle / price-feed manipulation or staleness
   6. Swap without authorization
   7. Signature / permit bypass
   8. Flash loan attack
   9. Denial of service / griefing with permanent fund-lock
   Then remaining findings sorted by confidence.

   Composite chains: if A's output feeds B's precondition AND combined impact > either alone, add `Chain: [A] + [B]` at conf = min(A, B). Most audits: 0–2.

2. **Gate.** Run each deduped finding through the four gates in `judging.md` (no skip, no reorder, no revisit after verdict).

   **Single-pass:** every relevant code path ONCE in fixed order (constructor → setters → swap → mint → burn → liquidate). One-line verdict: `BLOCKS` / `ALLOWS` / `IRRELEVANT` / `UNCERTAIN`. `UNCERTAIN = ALLOWS`. Commit, no re-examination.

   **Severity classification & floor (apply to every CONFIRMED finding).** Assign exactly one severity per the rubric in `judging.md` (Critical / High / Medium / Low / Informational), rated at the worst exploitable variant. Then enforce the floor: Critical/High/Medium → main report; Low → collapsed appendix; **Informational → DROP (do not print, not even as a lead)**. Anything you cannot tie to a named victim and a concrete loss/lock is Informational — drop it. This keeps the report high-signal: only findings that can actually damage the protocol survive.

3. **Lead promotion / rejection.**
   - LEAD → FINDING (conf 75) if: full exploit chain in source, OR `[agents: 2+]` demoted (not rejected) same issue.
   - `[agents: 2+]` does NOT override a code path that interrupts attack before harm — demote to LEAD if execution uncertain.
   - No deployer-intent reasoning — what code allows, not how deployer might use it.

4. **Format/print** per `report-formatting.md`. Exclude rejected. If `--file-output`: also write to file. Do NOT re-read source to "verify the most critical claim" — agents did that, dedup filtered.

5. **Auto-clean.** After print (and `--file-output` write): `rm -rf {bundle_dir}`. Bundle dir = transient build state, not an artifact. Don't skip. For debugging: copy bundle elsewhere before re-running.

**Turn 4b — PoC Generation (CRITICAL EXPLOITS ONLY).** After the main report is printed, spawn ONE background Agent using `{resolved_path}/hacking-agents/poc-generator-agent.md` as its specialty file. Pass it:
- The full deduped FINDING list (all findings, not just critical)
- The source bundle `{bundle_dir}/source.md`
- Instruction: prioritize findings from bug classes: unlimited-mint, unauthorized-transfer, cross-chain-bridge, reentrancy, oracle-manipulation, swap-without-auth, signature-exploit, flash-loan-attack, dos-griefing (permanent fund-lock)

The PoC agent writes runnable Foundry test code for each confirmed FINDING. Wait for it to complete, then append the PoC section to the report (or write a separate `{project-name}-poc.sol` file if `--file-output` is active).

PoC output format:
```
## 🧪 Proof-of-Concept Tests

> Run: `forge test --match-test test_exploit_ -vvvv`

### PoC #1: [Finding Title]
[forge test code]

### PoC #2: [Finding Title]
[forge test code]
```

**Turn 5 — Audit-log write (self-evolution ground-truth seed).** After the report (and PoCs) are produced, persist a machine-readable record of this audit so its findings can later be scored and fed back into the agents. This is the capture half of the learning loop — Turn 2 reads the lessons, Turn 5 writes the raw material the lessons are distilled from.

1. Compute `{audit_id}` = `<YYYY-MM-DD>-<project-folder-name>` (sanitize to `[a-z0-9-]`).
2. Write `audit-log/{audit_id}.json` (relative to the skill dir, i.e. `{resolved_path}/../audit-log/{audit_id}.json`; create the `audit-log/` directory if absent) with this shape — one entry per **final deduped finding** (main report + Low appendix; not dropped Informational):

   ```json
   {
     "audit_id": "2026-06-06-myvault",
     "date": "2026-06-06",
     "project": "myvault",
     "findings": [
       {
         "id": 1,
         "group_key": "Vault | withdraw | reentrancy",
         "contract": "Vault",
         "function": "withdraw",
         "bug_class": "reentrancy",
         "severity": "Critical",
         "agents": ["reentrancy-agent", "gold-bug-hunter-agent"],
         "title": "one-line title",
         "outcome": null,
         "paid": null,
         "note": null
       }
     ]
   }
   ```

   The `agents` array MUST use the specialty **file basenames** (e.g. `reentrancy-agent`, `oracle-manipulation-agent`) of the agents that produced each finding — take them from the `[agents: N]` attribution carried through dedup. This is the key that lets `record_outcome.py` credit the right agent's scoreboard and lesson file.

   **HARD RULE — every `outcome`, `paid`, and `note` MUST be `null` when you write this file.** You are recording *what was found*, not judging whether it was right. Outcomes are set ONLY later by a human via `record_outcome.py`. Never pre-fill an outcome, never mark a finding confirmed/false-positive yourself, and never write to `memory/` in this turn (or any turn). The audit-log is the ONLY file this turn produces. This separation is what guarantees a false positive can never silently train the agents: nothing becomes a lesson until a human explicitly says so.
3. Print one line: `📒 audit-log written: audit-log/{audit_id}.json — record outcomes later with: python scripts/record_outcome.py --list`.
4. Do NOT delete `audit-log/` in the Turn 4 auto-clean — only the transient `{bundle_dir}` is removed; the audit-log is a durable artifact.

This file starts with every `outcome: null`. When you later learn a finding was paid, duped, or was a false positive — or you discover a bug the audit missed — run `scripts/record_outcome.py`, which validates the lesson, recomputes `memory/scoreboard.json`, and appends a provenance-stamped lesson into the relevant `memory/*.lessons.md`. Those lessons are picked up automatically by Turn 2 on the next run (after passing the integrity check). **No agent improves without this human step** — and because that step is the only writer, no agent can be *degraded* by an automated mistake either. Recording outcomes is what turns a static auditor into a safely self-evolving one.
