# Threat Scope

Know your protocol's attack surface before the auditors do.

Built for:

- **Protocol teams** preparing for an audit — fix the obvious gaps so auditors can focus on what truly matters
- **Security researchers** starting a new engagement — get the complete intelligence picture in minutes, not hours
- **DeFi builders** who want to understand their own threat model before shipping

Not a vulnerability scanner — it's the strategic briefing you read before opening the first file.

## What You Get

One command produces four intelligence artifacts:

| Output | What's Inside |
|--------|--------------|
| `threat-scope.md` | Protocol overview, full threat model, test gaps, git history analysis, readiness verdict |
| `entry-points.md` | Every state-changing function classified by access level with complete call chains |
| `invariants.md` | Full invariant map — enforced guards, single-contract invariants, cross-contract trust assumptions, and higher-order economic properties |
| `architecture.svg` | Visual architecture diagram — contracts, actors, trust boundaries |

## How It Works

Three fully autonomous phases:

1. **Enumerate & Measure** — Scans the entire codebase, runs git security analysis, detects test coverage
2. **Read & Classify** — Reads all source files in parallel, classifies entry points, synthesizes invariants
3. **Write Report** — Produces all four output artifacts concurrently

## Usage

```
Install https://github.com/Subhashis360/WEB3-AUDIT and run audit-prep on the codebase
```

## Tips

- **Start with the verdict.** The report ends with a tier (FORTIFIED → EXPOSED) and 3-5 concrete action items. If you only read one section, read that.
- **Use entry-points.md as your attack map.** Start with permissionless functions — those are the highest-risk surface for any attacker.
- **Check the invariants.** `On-chain=No` invariants in `invariants.md` are potential bugs, not just documentation — review them carefully.
- **Pair with web3-audit.** Run `audit-prep` first for the full intelligence picture, then run `web3-audit` for deep vulnerability hunting on the hotspots it surfaces.
