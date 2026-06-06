# Report Formatting

## Report Path

Save the report to `{project-name}-chainshield-ai-audit-report-{timestamp}.md` in the current working directory, where `{project-name}` is the repo root basename and `{timestamp}` is `YYYYMMDD-HHMMSS` at scan time.

## Report fullness (read first)

> The "be terse" rule in `shared-rules.md` governs the **agents' raw scan output only** — it keeps their internal hunting cheap. It does **NOT** apply here. **The final report is the deliverable a researcher submits to a bug bounty platform (Immunefi, Code4rena, Sherlock, Cantina, HackerOne), so every main finding must be COMPLETE and self-contained:** full root-cause explanation, concrete impact, a step-by-step exploit scenario with real values, and a remediation with a code diff. Do not collapse main findings to one-liners. A reviewer who has never seen the codebase must be able to validate the bug from the writeup alone. Write fully here; be brief only in the Low appendix and the Leads list.

## Output Format

````
# 🔐 Security Review — <ContractName or repo name>

---

## Scope

|                                  |                                                        |
| -------------------------------- | ------------------------------------------------------ |
| **Mode**                         | ALL / default / filename                               |
| **Files reviewed**               | `File1.sol` · `File2.sol`<br>`File3.sol` · `File4.sol` | <!-- list every file, 3 per line -->
| **Confidence threshold (1-100)** | N                                                      |

---

## Findings

> Sorted by **severity** (Critical → High → Medium), then by confidence within each band. Critical-exploit classes (unlimited mint, unauthorized transfer, bridge forgery, reentrancy, oracle manipulation) surface first within their band. **Low-severity findings are in the collapsed appendix below; Informational issues (gas, style, NatSpec, missing events, centralization-without-exploit, best-practice nits) are excluded entirely** per the severity floor in `judging.md`.

<!-- Every Critical / High / Medium finding uses this FULL block. Do not abbreviate any field. -->

### 🔴 Critical

[Critical · 95] **1. <Title — concise statement of the bug>**

| | |
|---|---|
| **Contract** | `ContractName` |
| **Function** | `functionName(...)` |
| **Location** | `path/to/File.sol:L120-L138` |
| **Severity** | Critical |
| **Confidence** | 95 |
| **Bug class** | `unlimited-mint` |

**Summary**
<1–2 sentences: what the vulnerability is and what it lets an attacker do.>

**Root cause**
<Full technical explanation: the exact code-level defect, the protocol invariant or assumption it breaks, and why existing checks/modifiers do NOT prevent it. Cite the specific lines. Use as many sentences as the bug needs to be fully understood — this is the section a reviewer reads to confirm the bug is real.>

**Impact**
<Concrete consequence: what the attacker gains and the magnitude (funds drainable, supply inflatable, value permanently locked), who is harmed, and any preconditions or privileges required. Quantify in tokens/$ where the code allows. Name the highest-paying class it maps to (supply inflation / direct theft / permanent fund-lock / …).>

**Exploit scenario**
<Numbered attacker call sequence with concrete addresses, token amounts, and decimals — the same trace the agent proved it with.>
1. Attacker calls `...` with `...`
2. `...`
3. → Result: attacker nets `X`, protocol loses `Y`.

_Runnable proof: see **🧪 Proof-of-Concept Tests → PoC #N** below._

**Recommended fix**
<1–2 sentences explaining the mitigation and why it closes the path, then the diff.>

```diff
- vulnerable line(s)
+ fixed line(s)
```
---

< ... all Critical findings, each in the full block above >

### 🟠 High

[High · 88] **2. <Title>**

< same FULL block as above: metadata table, Summary, Root cause, Impact, Exploit scenario, Recommended fix >

---

< ... all High findings >

### 🟡 Medium

[Medium · 75] **3. <Title>**

< same FULL block as above. Medium findings get the complete writeup too — they are still submittable bugs. >

---

< ... all Medium findings >

---

Findings List

| # | Severity | Confidence | Title |
|---|---|---|---|
| 1 | 🔴 Critical | 95 | <title> |
| 2 | 🟠 High | 88 | <title> |
| 3 | 🟡 Medium | 75 | <title> |

---

<details>
<summary>🔵 Low-severity findings (N) — minor / bounded impact, expand to review</summary>

[Low · 60] **L1. <Title>** — `ContractName.functionName`
<1 short sentence: the issue and its bounded impact>

< ... all Low findings, description only, no Fix block >

</details>

---

## Leads

_Vulnerability trails with concrete code smells where the full exploit path could not be completed in one analysis pass. These are not false positives — they are high-signal leads for manual review. Not scored._

- **<Title>** — `Contract.function` — Code smells: <missing guard, unsafe arithmetic, etc.> — <1-2 sentence description of the trail and what remains unverified>
- **<Title>** — `Contract.function` — Code smells: <...> — <1-2 sentence description>

---

> ⚠️ This review was performed by an AI assistant (ChainShield). AI analysis can never verify the complete absence of vulnerabilities and no guarantee of security is given. Team security reviews, bug bounty programs, and on-chain monitoring are strongly recommended. Always perform a formal manual audit before deploying to production.

````

**Rules:** Follow the template above exactly. **Apply the severity floor from `judging.md`:** only Critical/High/Medium appear in the main Findings sections; Low findings go in the collapsed appendix; Informational issues are dropped entirely (never printed). Sort by severity band (Critical → High → Medium), then by confidence within each band. **Every Critical/High/Medium finding gets the FULL block — Summary, Root cause, Impact, Exploit scenario, and Recommended fix — regardless of confidence. Never reduce a main finding to description-only.** If a finding's exploit chain was only partially proven, still write all fields and state plainly in Exploit scenario which step is unverified (do not silently drop the section). When the Fix-preservation gate produced ≥2 distinct fixes, render them as **Fix (Option A — label)** / **Fix (Option B — label)** with the verbatim diffs (per SKILL.md Turn 4). Only the Low appendix and the Leads list stay brief (one to two lines each). If a band has no findings, omit its heading. If there are zero Critical/High/Medium findings, state that plainly and still show the Low appendix if any. Draft findings directly in report format — do not re-generate.

