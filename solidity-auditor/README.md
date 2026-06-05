# web3-audit

A high-precision smart contract security agent — surface critical vulnerabilities in minutes, not weeks.

Built for:

- **Solidity developers** who want a rigorous security check before every commit
- **Security researchers** looking for fast, high-signal wins before a manual review
- **Protocol teams** who want an extra pair of expert eyes before going live

Not a substitute for a formal audit — but the check you should never skip.

## What It Does

Spawns **22 parallel specialist agents** (plus a 23rd ZK circuit-soundness agent when zero-knowledge circuit files are detected), each attacking your codebase from a unique angle — including a dedicated **gold-bug hunter** that targets the bugs every other agent structurally misses (missing-constraint, trust-boundary, cross-specialty seam, and spec-vs-code gaps):

| Agent | Specialty |
|-------|----------|
| Math & Precision | Arithmetic overflows, rounding, fixed-point errors |
| Access Control | Ownership, role bypass, privilege escalation |
| Economic Security | MEV, price manipulation, flash loan attacks |
| Execution Trace | Reentrancy, callback exploitation |
| Invariant Hunting | Broken protocol guarantees |
| Periphery | Integration weaknesses |
| First Principles | Logic errors from spec deviation |
| Asymmetry | State/value asymmetries |
| Boundary | Edge cases, off-by-one, limit conditions |
| Numerical Gap | Hidden numeric precision gaps |
| Trust Gap | Cross-contract trust assumption failures |
| Flow Gap | Execution flow vulnerabilities |

## Usage

```
Install https://github.com/Subhashis360/LLM-SKILLS and run web3-audit on the codebase
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
- **Pair with audit-prep.** Run `audit-prep` first to get a full protocol picture, then run `web3-audit` for deep vulnerability hunting.
