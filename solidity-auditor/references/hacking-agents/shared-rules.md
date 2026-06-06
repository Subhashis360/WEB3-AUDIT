# Shared Scan Rules

## Bundle contents

Your bundle is four concatenated files: all in-scope source code, the SOP (HOW to think), your specialty agent (WHAT to look for), and these shared rules (output format, dedup tags, AND mandatory mental tool protocol).

Read the whole bundle once at the start. The bundle contains all in-scope source. Use Read/Grep only for cross-file searches or out-of-scope context (interfaces/, lib/, mocks/, test/) — do not re-read in-scope files for the initial scan.

**The protocol below applies continuously during source reading — not just before it.** The "read source" phase does not turn off the protocol; every trigger condition fires the moment it occurs, throughout your entire review.

When matching function names, check both `functionName` and `_functionName` (Solidity convention).

## Mental tool protocol — MANDATORY

The five tools in `senior-auditor-sop.md` are NOT optional. Each tool has a specific trigger. **When the trigger fires, you MUST emit the corresponding marker in your output stream BEFORE continuing.** No skipping. The markers live in your working text — they do NOT go into the FINDING/LEAD output blocks.

### Triggers → required markers

| Trigger (the condition) | Marker (required immediately, literal `[Tool: ...]` syntax) | Content |
|---|---|---|
| You open a new function or contract to read | `[Feynman: <name>]` | Explain what it does in plain English — no Solidity jargon, no `mload`/`assembly`/`mstore`/`safeTransfer`/etc. Use as many sentences as you need until the explanation is solid. If your wording slips back to jargon, you're papering over an assumption — keep going. Wherever your plain-English explanation gets fuzzy or you have to reach for a Solidity term to keep it accurate, mark that spot — that is where bugs hide. |
| You stop on a line whose purpose isn't immediately clear | `[Socratic: <file:line> — why?]` | A one-line question that drills past "because that's how it's written." If your first answer is a restatement of the code, ask again. Stop when the answer exposes the implicit belief the code rests on — don't pad with extra steps just to hit a quota. |
| A code path reads as clean / a check looks sufficient / a guard looks correct | `[Inversion: <function>]` | Three concrete attacker moves that attempt to defeat the path. Specific addresses/values/states, not abstractions. |
| You begin a contract, or you identify what value the contract holds/moves | `[Invariant: <Contract>]` | One sentence per promise the protocol must keep (conservation of supply, no uncollateralized debt, share price never drops on others' deposits, etc.). Then, for each, name the function most likely to break it. This is your hunting list — the bug is whatever falsifies a named promise. |
| You see a pair that should be mirror images (deposit/withdraw, mint/burn, view/write, two writers of one slot, same pattern in a sibling contract) | `[Differential: <A> vs <B>]` | The one difference between the two — price source, rounding direction, fee treatment, a guard present on one but not the other. The difference is the candidate bug; prove it is exploitable or rule it out with values. |

When you reach a "bug" conclusion, plug in concrete token decimals, amounts, and attacker capital and walk the arithmetic before writing the FINDING. A defect you cannot put a number on is a LEAD.

### Rules

1. **Triggers are not optional.** If the condition fires, the marker follows. Always. No skipping.
2. **Use the literal `[Tool: ...]` syntax.** The orchestrator greps your output for these tags after the run.
3. **You may emit a marker without a trigger.** Extra Feynman / Inversion markers are fine. You may NOT skip a marker after its trigger fired.
4. **The protocol applies to reasoning depth, not output volume.** Heavy use of these tools is what produces the audit work. Skipping them = surface-level scanning, which is the failure mode of every junior auditor.

The orchestrator verifies marker counts after every run. Skipped markers downgrade the value of your findings and are recorded as workflow violations.

## Cross-contract patterns

When you find a bug in one contract, **weaponize that pattern across every other contract in the bundle.** Search by function name AND by code pattern. Finding native/ERC20 confusion in `ContractA.onRevert` means you check every other contract's `onRevert` — missing a repeat instance is an audit failure.

After scanning: escalate every finding to its worst exploitable variant (DoS may hide fund theft). Then revisit every function where you found something and attack the other branches.

## Do not defer to "it's already audited"

The most dangerous instinct you have is trusting that battle-tested, audited, or widely-used code must be correct. Real critical bugs — the ones that survive for years and pay the most — live precisely in code everyone assumed was fine. When you find a missing check, a missing constraint, or a broken assumption, your reflex will be to explain it away: "surely this is validated elsewhere," "this is upstream, it must be right," "I must be misreading a forked/backdoored version." **That reflex is how multi-year bugs survive.** When you cannot point to the *specific line* that enforces the property you expect, the absence of that line IS the finding. Demand the guard/constraint by name; if you cannot cite it, report the gap and let the gates judge it — do not pre-reject your own discovery. Skepticism is for your proof, not for suppressing the lead.

If reference material is available in your bundle or via Read (protocol spec, ZIPs, the halo2 book, EIPs, design docs), use it to learn what each value/function is *supposed* to guarantee — then hunt the place the code fails to enforce it. The gap between the spec's promise and the code's enforcement is where findings live.

## Severity reflex — always escalate to the money

For every finding, ask "what is the worst thing an unprivileged attacker can do with this?" before you write it down. A bug that looks like a revert (DoS) may actually strand funds permanently (fund-lock = high). A rounding error that looks like dust may compound across thousands of calls or be amplified by a flash loan into total drainage (critical). A view returning a stale value may be the input to a liquidation that pays the wrong party (critical). Never report a finding at its first-glance severity — report it at the worst exploitable variant you can prove. The highest-paying classes, in order, are: unlimited mint / supply inflation, direct theft of user or protocol funds, permanent fund-lock, then everything else. If your finding touches one of those, say so explicitly.

## Do not report

Admin-only functions doing admin things. Standard DeFi tradeoffs (MEV, rounding dust, first-depositor with MINIMUM_LIQUIDITY). Self-harm-only bugs. "Admin can rug" without a concrete mechanism.

## Token discipline — be terse

This governs **your raw scan output as an agent** — not the final report. The orchestrator expands confirmed findings into a full, detailed bug-bounty writeup later (`report-formatting.md`); your job is to find the bug cheaply and hand over tight, complete FINDING blocks. Spend tokens on finding bugs, not on narrating. Hard rules:

- **No preamble, no conclusion.** Do not restate the task, announce what you're about to do ("I will now analyze…"), or summarize at the end. Start with markers/findings, stop when done.
- **No commentary or decoration.** No headings, bullet lists, tables, or recap prose around your output. Only the mandatory mental-tool markers and the FINDING/LEAD blocks.
- **Markers stay mandatory but compact.** Each `[Tool: …]` marker is one tight line — the minimal content that does the reasoning, no padding. The markers are reasoning, not commentary; keep them, but do not inflate them.
- **One line per field.** Every FINDING/LEAD field (`path`, `proof`, `description`, `fix`, etc.) is a single line. Quote only the few lines of code needed as proof — never paste whole functions.
- **No bug found = one line.** If your specialty turns up nothing, emit a single line saying so. Do not pad.

Terseness is about output volume, not analysis depth — think hard, write little.

## Output

Return findings as structured blocks:

FINDINGs have concrete, unguarded, exploitable attack paths. LEADs have real code smells with partial paths — default to LEAD over dropping.

**Every FINDING must have a `proof:` field** — concrete values, traces, or state sequences from the actual code. No proof = LEAD, no exceptions.

**One vulnerability per item.** Same root cause = one item. Different fixes needed = separate items.

```
FINDING | contract: Name | function: func | bug_class: kebab-tag | group_key: Contract | function | bug-class
severity: Critical | High | Medium | Low  (your proposed impact, rated at the worst exploitable variant; orchestrator may re-rate)
path: caller → function → state change → impact
proof: concrete values/trace demonstrating the bug
description: one sentence
fix: one-sentence suggestion

LEAD | contract: Name | function: func | bug_class: kebab-tag | group_key: Contract | function | bug-class
code_smells: what you found
description: one sentence explaining trail and what remains unverified
```

The `group_key` enables deduplication: `ContractName | functionName | bug_class`. Agents may add custom fields.
