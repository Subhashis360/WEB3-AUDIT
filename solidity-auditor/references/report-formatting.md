# Report Formatting

## Report Path

Save the report to `{project-name}-chainshield-ai-audit-report-{timestamp}.md` in the current working directory, where `{project-name}` is the repo root basename and `{timestamp}` is `YYYYMMDD-HHMMSS` at scan time.

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

### 🔴 Critical

[Critical · 95] **1. <Title>**

`ContractName.functionName` · Severity: Critical · Confidence: 95

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

**Fix**

```diff
- vulnerable line(s)
+ fixed line(s)
```
---

< ... all Critical findings >

### 🟠 High

[High · 88] **2. <Title>**

`ContractName.functionName` · Severity: High · Confidence: 88

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

**Fix**

```diff
- vulnerable line(s)
+ fixed line(s)
```
---

< ... all High findings >

### 🟡 Medium

[Medium · 75] **3. <Title>**

`ContractName.functionName` · Severity: Medium · Confidence: 75

**Description**
<The vulnerable code pattern and why it is exploitable, in 1 short sentence>

< Findings with confidence ≥ 80 include a **Fix** block; below 80 get description only. >

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

**Rules:** Follow the template above exactly. **Apply the severity floor from `judging.md`:** only Critical/High/Medium appear in the main Findings sections; Low findings go in the collapsed appendix; Informational issues are dropped entirely (never printed). Sort by severity band (Critical → High → Medium), then by confidence within each band. Findings with confidence ≥ 80 get a **Fix** block; below 80 get description only. If a band has no findings, omit its heading. If there are zero Critical/High/Medium findings, state that plainly and still show the Low appendix if any. Draft findings directly in report format — do not re-generate.

