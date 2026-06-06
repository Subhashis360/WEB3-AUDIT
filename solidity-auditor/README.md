# web3-audit

A high-precision smart contract security agent — surface critical vulnerabilities in minutes, not weeks.

Built for:

- **Solidity developers** who want a rigorous security check before every commit
- **Security researchers** looking for fast, high-signal wins before a manual review
- **Protocol teams** who want an extra pair of expert eyes before going live

Not a substitute for a formal audit — but the check you should never skip.

## What It Does

Spawns **22 parallel specialist agents** (plus a 23rd ZK circuit-soundness agent when zero-knowledge circuit files are detected), each attacking your codebase from a unique angle — including a dedicated **gold-bug hunter** that targets the bugs every other agent structurally misses (missing-constraint, trust-boundary, cross-specialty seam, and spec-vs-code gaps):

| # | Agent | Specialty |
|---|-------|----------|
| 1 | Math & Precision | Arithmetic overflows, rounding, fixed-point errors |
| 2 | Access Control | Ownership, role bypass, privilege escalation |
| 3 | Economic Security | MEV, dependency/token misbehavior, incentive abuse |
| 4 | Execution Trace | Cross-function/transaction flow exploitation |
| 5 | Invariant Hunting | Broken conservation laws & protocol guarantees |
| 6 | Periphery | Library/helper/encoder weaknesses |
| 7 | First Principles | Logic errors from violated assumptions |
| 8 | Asymmetry | State/value asymmetries |
| 9 | Boundary | Edge cases, off-by-one, limit conditions |
| 10 | Numerical Gap | Hidden numeric precision gaps (seam) |
| 11 | Trust Gap | Cross-lens trust-assumption failures (seam) |
| 12 | Flow Gap | Execution-flow vulnerabilities (seam) |
| 13 | Unlimited Mint | Unauthorized minting / supply inflation |
| 14 | Unauthorized Transfer | Direct theft of user/protocol funds |
| 15 | Swap Without Auth | Unauthorized swaps / AMM manipulation |
| 16 | Signature Exploit | ecrecover / permit / EIP-712 / replay bugs |
| 17 | Flash Loan Attack | Atomic capital-amplified exploits |
| 18 | Reentrancy | Classic / cross-function / read-only / hook / cross-contract |
| 19 | Oracle Manipulation | Price manipulation, staleness, L2 sequencer, decimals |
| 20 | Cross-Chain / Bridge | Message forgery, replay, trusted-remote gaps |
| 21 | DoS / Griefing | Permanent fund-lock, liquidation-blocking, unbounded loops |
| 22 | **Gold-Bug Hunter** | The bugs every other agent misses — absence / trust-boundary / seam / spec-gap / novel-mechanism |
| 23* | Circuit Soundness (ZK) | Missing-constraint / soundness bugs — *only when ZK circuit files are detected* |

*Agent 23 spawns conditionally when `.circom` / `.nr` / `.cairo` / halo2 gadget files are in scope.

## Compatibility

Runs on **Claude Code, OpenCode, Codex, Gemini CLI, Cursor, Antigravity, and any agent with a shell + file read.** The orchestrator detects your runtime's capabilities and chooses a `spawn_mode` — parallel background sub-agents where available, degrading to a sequential **inline** mode (it plays every specialist itself) where they aren't. Same methodology everywhere; no specialist is ever dropped. Claude-Code-only conveniences (`ToolSearch`, the `AskUserQuestion` model picker, `TodoWrite`) auto-skip on runtimes that lack them. On first run it self-provisions Foundry / Slither / solc-select / jq for Windows / Linux / macOS / WSL.

## Usage

```
Install https://github.com/Subhashis360/WEB3-AUDIT and run web3-audit on the codebase
```

```
run web3-audit on *specified files*
```

```
update skill to latest version
```

## Tips

- **Target hot contracts.** Rather than scanning an entire repo, point the tool at the 2-5 contracts you're actively changing. Smaller scope means denser context for each agent and higher-signal findings.
- **Run more than once.** LLM output is non-deterministic — each run can surface different vulnerabilities. Two or three passes over the same code often catch things a single pass misses.
- **Record outcomes to make it smarter.** After you learn whether a finding paid, was a dup, or was a false positive, run `scripts/record_outcome.py` — the agents fold those lessons into their next run (precision and recall improve over time).
