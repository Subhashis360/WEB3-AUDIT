# Global Lessons Ledger (cross-agent)

> This file is concatenated into **every** agent bundle at audit time (SKILL.md Turn 2).
> It holds cross-cutting, high-signal lessons learned from past audits: confirmed bug
> patterns worth re-weaponizing on new targets, and recurring false-positives to stop
> reporting. Keep entries **compact and generalized** — raw per-finding detail belongs in
> the per-agent `<agent>.lessons.md` files, not here.
>
> SAFETY — single writer. This ledger is a TRUSTED INPUT to every future audit, so it has
> exactly ONE writer: `scripts/record_outcome.py`, driven by an explicit human outcome
> decision. **NEVER edit this file by hand, and NEVER let an LLM/agent/orchestrator write to
> it.** Every legitimate entry carries a `<!-- ledger-id: ... -->` provenance footer; entries
> without one are foreign. Out-of-band edits are detected by `record_outcome.py --verify`
> (sha256 manifest + provenance check). Each entry MUST stay short — this file is read by 22+
> agents every run, so bloat here taxes every audit.
>
> Format (keep it tight):
>
> ```
> ## CONFIRMED - <date> - <bug-class>
> Pattern: <one-line generalized pattern>.
> Tell: <the observable signal in code that flags it>.
> Generalize: <where else this class hides>.
>
> ## FALSE-POSITIVE - <date> - <bug-class>
> Claim: <what was wrongly reported>.
> Stop when: <the exact code condition that makes it a non-issue>.
> ```

<!-- BEGIN LESSONS (do not delete this marker; record_outcome.py appends below it) -->
