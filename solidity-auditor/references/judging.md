# Finding Validation

Every finding passes four sequential gates. Fail any gate → **rejected** or **demoted** to lead. Later gates are not evaluated for failed findings.

You are not defending the code. The job of these gates is to verify the attacker's claimed exploit actually fires end-to-end — anything that interrupts the attack between the attacker's call and the harm means the agent's claim does not execute, and only then does it fail to qualify as a finding.

## Gate 1 — Attack execution

Trace the agent's claimed attack path from caller to harm. Read every guard, check, modifier, and constraint that sits on that path. Confirm that none of them interrupts the attack before the exploit step fires.
- A specific guard / check / modifier on the attack path interrupts the claimed exploit step before harm occurs (quote the exact line and trace it) → **REJECTED** (or **DEMOTE** if a related code smell remains)
- The supposed interruption is speculative ("probably wouldn't happen", "the caller would notice", "the deployer would set X") → **clears**, continue

## Gate 2 — Reachability

Prove the vulnerable state exists in a live deployment.

- Structurally impossible (enforced invariant prevents it) → **REJECTED**
- Requires privileged actions outside normal operation → **DEMOTE**
- Achievable through normal usage or common token behaviors → **clears**, continue

## Gate 3 — Trigger

Prove an unprivileged actor executes the attack.

- Only trusted roles can trigger → **DEMOTE**
- Unprivileged actor triggers profitably → **clears**, continue

**Admin-action findings — reject unless an unprivileged amplifier is named.** This applies ONLY to actions performed by admin/owner, NOT to unprivileged attacker actions. If the harm requires the admin acting maliciously or against documented intent, **REJECT** — do not even emit as a LEAD (stricter than the DEMOTE above). The finding clears only when the body names a concrete unprivileged amplifier:

- **race** — admin sets X mid-flow; an unprivileged user exploits the window before the update propagates.
- **retroactive sweep** — an admin update rewrites a pending value already credited.
- **asymmetric formula** — admin output chains into a formula an unprivileged actor profits from.
- **access gap** — missing guard, tautological auth, or missing init guard (the access mechanism itself is the bug).

No amplifier named → **REJECTED**. Amplifier named → judge it on that unprivileged path.

## Gate 4 — Impact

Prove material harm to an identifiable victim.

- Self-harm only → **REJECTED**
- Dust-level, no compounding → **DEMOTE**
- Material loss to identifiable victim → **CONFIRMED**

## Confidence

Start at **100**, deduct: partial attack path **-20**, bounded non-compounding impact **-15**, requires specific (but achievable) state **-10**. Confidence ≥ 80 gets description + fix. Below 80 gets description only.

Confidence measures *how sure you are the exploit fires*. Severity (below) measures *how much damage it does*. They are independent — score both.

## Severity classification & report floor (HARD GATE)

After a finding CONFIRMS through the four gates, assign exactly one severity. This is an impact judgment, separate from confidence.

| Severity | Definition |
|---|---|
| **Critical** | Direct, largely unconditional loss/theft/lock of material user or protocol funds, or unlimited mint / supply inflation, triggerable by an **unprivileged** attacker under normal conditions. The protocol-ending bugs. |
| **High** | Theft, permanent fund-lock, or bad-debt creation that requires a non-trivial (but achievable) precondition, affects a subset of users, or is bounded but still large. Blocking liquidations → bad debt lives here. |
| **Medium** | Conditional or bounded value leak, griefing that imposes real cost on others, or a broken guarantee that materially harms protocol function without catastrophic loss. |
| **Low** | Minor or dust-level loss, hard-to-reach state, or impact that does not compound — real but small. |
| **Informational** | No fund-loss, fund-lock, or material-harm path for any attacker. **Not a finding.** |

**Report floor — enforce strictly:**
- **Critical / High / Medium** → main report.
- **Low** → collapsed appendix only (see `report-formatting.md`); never in the main list.
- **Informational → DROP entirely.** Do not emit, not even as a lead.

**Always classified Informational (drop, never report):** gas optimizations, code style / naming / formatting, NatSpec or comment issues, missing events / event-emission nits, compiler-version / linter warnings, unused variables, floating pragma, best-practice suggestions with no exploit, "centralization risk" with no concrete unprivileged exploit path, and any theoretical concern where no attacker gains and no user loses. If you cannot name a victim and a loss, it is Informational — drop it.

**Severity escalation reminder:** before assigning, apply the severity reflex from `shared-rules.md` — rate the finding at its *worst exploitable variant*, not its first-glance impact. A DoS that permanently locks a vault is High/Critical, not Low. A rounding error a flash loan amplifies to full drainage is Critical, not Low.

## Safe patterns (do not flag)

- `unchecked` in 0.8+ (but verify the reasoning is correct)
- Explicit narrowing casts in 0.8+ (reverts on overflow)
- MINIMUM_LIQUIDITY burn on first deposit
- SafeERC20 (`safeTransfer`/`safeTransferFrom`)
- `nonReentrant` (only flag cross-contract attacks)
- Two-step admin transfer
- Consistent protocol-favoring rounding unless compounding or zero-rounding

## Lead promotion

Before finalizing leads, promote where warranted:

- **Cross-contract echo.** Same root cause confirmed as FINDING in one contract → promote in every contract where the identical pattern appears.
- **Multi-agent convergence.** 2+ agents flagged same area, lead was demoted (not rejected) → promote to FINDING at confidence 75.
- **Partial-path completion.** Only weakness is incomplete trace but path is reachable and unguarded → promote to FINDING at confidence 75, description only.

## Leads

High-signal trails for manual investigation. No confidence score, no fix — title, code smells, and what remains unverified.

## Do Not Report

Linter/compiler issues, gas micro-opts, naming, NatSpec. Admin privileges by design. Missing events. Centralization without exploit path. Implausible preconditions (but fee-on-transfer, rebasing, blacklisting ARE plausible for contracts accepting arbitrary tokens).
