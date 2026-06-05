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

## Installation

Add the skills to your AI agent environment (Antigravity, Claude Code, etc.) and trigger them with natural language commands listed above.

```
Install https://github.com/Subhashis360/LLM-SKILLS and run web3-audit on the codebase
```

```
Install https://github.com/Subhashis360/LLM-SKILLS and run audit-prep on the codebase
```

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
