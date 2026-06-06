#!/usr/bin/env python3
"""
record_outcome.py - ChainShield Layer 2: HARDENED outcome capture & agent self-evolution feed.

WHY THIS SCRIPT IS THE ONLY WRITER
----------------------------------
The agents "evolve" because lesson ledgers (memory/*.lessons.md) are concatenated into
every audit bundle (SKILL.md Turn 2). That makes the ledger a *trusted input to every
future audit* - so a single bad entry poisons all agents on every later run.

Therefore the ledger has exactly ONE writer: this deterministic, validated script, driven
by an explicit HUMAN outcome decision. No LLM - weak (Gemini inline) or strong (Claude) -
ever writes a lesson. The orchestrator's only loop output is the audit-log JSON, which
carries `outcome: null` and never feeds back into a bundle. This makes ledger integrity
INDEPENDENT of LLM capability.

Defenses that make "any LLM cannot ruin the skill" true in practice:
  * Structural validation   - a lesson must be well-formed for its outcome or it is rejected.
  * Input sanitization      - control chars, markdown headers, and comment/marker injection
                              are stripped, so a lesson string cannot corrupt the file format.
  * Provenance footers      - every entry carries a `ledger-id`; entries lacking one are foreign.
  * Integrity manifest      - sha256 per ledger file; `--verify` detects any out-of-band edit
                              (e.g. an LLM that "helpfully" appended a lesson). Empty ledgers
                              are inherently trusted (nothing to poison).
  * Recomputed scoreboard   - derived from source-of-truth audit-logs, so re-recording is
                              idempotent and cannot inflate an agent's stats.
  * Caps                    - per-lesson length and per-file entry caps stop ledger-rot.
  * Reversibility           - `--revert <ledger-id>` removes a mistaken lesson cleanly.

USAGE
-----
  List findings in the latest (or a given) audit:
    python record_outcome.py --list
    python record_outcome.py --audit 2026-06-06-myproject --list

  Show ledger entries (with their ledger-ids, for --revert):
    python record_outcome.py --show
    python record_outcome.py --show --agent reentrancy-agent

  Record the outcome of a finding (lesson is validated before it is ever written):
    python record_outcome.py --id 3 --outcome confirmed --paid 25000 --global \
        --lesson "Pattern: read-only reentrancy via getPricePerShare during ERC777 hook. | Tell: a view used as a price source reads a balance mutated mid-callback. | Generalize: any view oracle touching a hook-bearing token."

    python record_outcome.py --id 5 --outcome false-positive \
        --lesson "Claim: reentrancy on withdraw(). | Stop when: nonReentrant present AND state write precedes the external call (CEI)."

  Record a bug the audit MISSED (teach the agent the class it failed to catch):
    python record_outcome.py --missed --agent oracle-manipulation-agent \
        --lesson "Pattern: TWAP window too short -> single-block manipulation. | Tell: oracle uses <=2 observations or window < 30min. | Generalize: any consult() with caller-influenceable window."

  Preview without writing:                  add --dry-run to any record command
  Remove a mistaken lesson:                 python record_outcome.py --revert <ledger-id>
  Check ledger integrity (run anytime):     python record_outcome.py --verify
  Establish/refresh the trusted baseline:   python record_outcome.py --reseal

OUTCOMES
  confirmed       real, valid bug      -> credit + CONFIRMED lesson  (needs Pattern: + Tell:)
  paid            alias for confirmed, with --paid amount
  dup             valid but duplicate  -> neutral (no lesson; counted separately)
  false-positive  invalid / rejected   -> FALSE-POSITIVE lesson      (needs Stop when:)
  missed          real bug not found   -> CONFIRMED lesson           (needs Pattern: + Tell:)
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # solidity-auditor/
MEM_DIR = os.path.join(ROOT, "references", "hacking-agents", "memory")
AGENTS_DIR = os.path.join(ROOT, "references", "hacking-agents")
LOG_DIR = os.path.join(ROOT, "audit-log")
SCOREBOARD = os.path.join(MEM_DIR, "scoreboard.json")
GLOBAL_LESSONS = os.path.join(MEM_DIR, "_global.lessons.md")
MANIFEST = os.path.join(MEM_DIR, ".ledger-manifest.json")
MISSED_LOG = os.path.join(LOG_DIR, "_missed.json")
LESSON_MARKER = "<!-- BEGIN LESSONS (do not delete this marker; record_outcome.py appends below it) -->"

OUTCOME_ALIASES = {"paid": "confirmed"}
VALID_OUTCOMES = {"confirmed", "dup", "false-positive", "missed"}
TALLY_OUTCOMES = {"confirmed", "dup", "false-positive"}  # outcomes that live in audit-logs

# Anti-rot / anti-poison caps.
MAX_LESSON_CHARS = 800     # body (the Pattern/Tell/Stop-when text)
MAX_BLOCK_CHARS = 1100     # whole entry incl. header + footer
MAX_ENTRIES_PER_FILE = 200

LEDGER_ID_RE = re.compile(r"<!--\s*ledger-id:\s*(\S+)")


# --------------------------------------------------------------------------- utils
def today():
    return datetime.date.today().isoformat()


def now_stamp():
    return datetime.datetime.now().strftime("%Y%m%dT%H%M%S")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path, default=None):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        die(f"cannot read {os.path.relpath(path, ROOT)}: {e}")


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
        fh.write("\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def lessons_files():
    if not os.path.isdir(MEM_DIR):
        return []
    return sorted(
        os.path.join(MEM_DIR, f)
        for f in os.listdir(MEM_DIR)
        if f.endswith(".lessons.md")
    )


# ------------------------------------------------------------------- audit resolution
def latest_audit():
    if not os.path.isdir(LOG_DIR):
        die(f"no audit-log directory at {LOG_DIR} - run an audit first")
    logs = sorted(
        f for f in os.listdir(LOG_DIR)
        if f.endswith(".json") and not f.startswith("_")
    )
    if not logs:
        die(f"no audit-log JSON files in {LOG_DIR} - run an audit first")
    return os.path.join(LOG_DIR, logs[-1])


def resolve_audit(name):
    if not name:
        return latest_audit()
    for cand in (name, name + ".json", os.path.join(LOG_DIR, name),
                 os.path.join(LOG_DIR, name + ".json")):
        if os.path.isfile(cand):
            return cand
    die(f"audit log not found: {name}")


def validate_audit_schema(data, path):
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        die(f"malformed audit-log {os.path.relpath(path, ROOT)}: missing findings[]")
    seen = set()
    for f in data["findings"]:
        if not isinstance(f, dict) or "id" not in f:
            die(f"malformed finding (no id) in {os.path.relpath(path, ROOT)}")
        if f["id"] in seen:
            die(f"duplicate finding id {f['id']} in {os.path.relpath(path, ROOT)}")
        seen.add(f["id"])
        if not isinstance(f.get("agents", []), list):
            die(f"finding #{f['id']}: agents must be a list")
    return data


def known_agent(agent):
    base = agent[:-6] if agent.endswith("-agent") else agent
    return os.path.isfile(os.path.join(AGENTS_DIR, base + "-agent.md"))


# ----------------------------------------------------------------- lesson formatting
def sanitize_part(s):
    """Neutralize anything that could corrupt the ledger format or inject structure."""
    s = s or ""
    # drop control chars except tab
    s = "".join(ch for ch in s if ch == "\t" or (32 <= ord(ch) != 127))
    s = s.replace(LESSON_MARKER, "")
    s = s.replace("<!--", "(").replace("-->", ")")   # no comment injection
    s = re.sub(r"ledger-id", "ledger", s, flags=re.I)  # no fake-footer text
    s = re.sub(r"^\s*#+\s*", "", s)                   # no markdown header injection
    s = re.sub(r"\s+", " ", s).strip()               # collapse newlines/whitespace
    return s


def build_body(outcome, raw):
    """Validate + assemble the lesson body. Rejects ill-formed/empty/oversized lessons."""
    if not raw or not raw.strip():
        die("a --lesson is required for this outcome (and must be well-formed)")
    parts = [sanitize_part(p) for p in raw.split("|")]
    parts = [p for p in parts if p]
    body = "\n".join(parts)
    if not body:
        die("lesson is empty after sanitization")
    low = body.lower()
    if outcome in ("confirmed", "missed"):
        missing = [k for k in ("pattern:", "tell:") if k not in low]
        if missing:
            die("CONFIRMED/missed lessons must contain "
                f"{' and '.join(m.rstrip(':').title()+':' for m in ('pattern:','tell:'))}. "
                f"Missing: {', '.join(m.rstrip(':').title()+':' for m in missing)}. "
                "Example: \"Pattern: ... | Tell: ... | Generalize: ...\"")
    elif outcome == "false-positive":
        if "stop when:" not in low:
            die("FALSE-POSITIVE lessons must contain 'Stop when:' so the agent learns the "
                "exact condition that makes it a non-issue. "
                "Example: \"Claim: ... | Stop when: ...\"")
    if len(body) > MAX_LESSON_CHARS:
        die(f"lesson too long ({len(body)} > {MAX_LESSON_CHARS} chars) - keep it compact; "
            "ledgers are read by every agent every run")
    return body


def make_block(outcome, bug_class, body, ledger_id):
    bug_class = sanitize_part(bug_class) or "unknown"
    if outcome == "false-positive":
        head = f"## FALSE-POSITIVE - {today()} - {bug_class}"
    elif outcome == "missed":
        head = f"## CONFIRMED (missed-then-learned) - {today()} - {bug_class}"
    else:
        head = f"## CONFIRMED - {today()} - {bug_class}"
    footer = f"<!-- ledger-id: {ledger_id} | outcome: {outcome} | ts: {today()} -->"
    block = f"{head}\n{body}\n{footer}"
    if len(block) > MAX_BLOCK_CHARS:
        die(f"assembled lesson block too long ({len(block)} > {MAX_BLOCK_CHARS})")
    return block


# --------------------------------------------------------------- ledger file I/O
def header_for(agent):
    return (
        f"# Lessons - {agent}\n\n"
        "> SAFETY: This file is concatenated into agent bundles every audit (SKILL.md Turn 2),\n"
        "> so it is a TRUSTED INPUT to every future run. It has exactly ONE writer:\n"
        "> scripts/record_outcome.py, driven by an explicit human outcome decision.\n"
        "> NEVER edit this file by hand or let an LLM write to it - out-of-band edits are\n"
        "> detected by `record_outcome.py --verify` (sha256 manifest + provenance footers).\n\n"
        f"{LESSON_MARKER}\n"
    )


def ensure_lessons_file(path, agent):
    if not os.path.isfile(path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(header_for(agent))


def split_ledger(path):
    """Return (head_through_marker, [entry_block, ...])."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if LESSON_MARKER in text:
        head, _, tail = text.partition(LESSON_MARKER)
        head = head + LESSON_MARKER
    else:
        head, tail = text, ""
    blocks = re.split(r"\n(?=## )", tail.strip())
    entries = [b.strip() for b in blocks if b.strip()]
    return head, entries


def write_ledger(path, head, entries):
    body = "\n\n".join(entries)
    text = head.rstrip() + "\n\n" + (body + "\n" if body else "")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def entry_id(block):
    m = LEDGER_ID_RE.search(block)
    return m.group(1) if m else None


def upsert_entry(path, agent, block, ledger_id):
    ensure_lessons_file(path, agent)
    head, entries = split_ledger(path)
    entries = [e for e in entries if entry_id(e) != ledger_id]  # idempotent re-record
    if len(entries) >= MAX_ENTRIES_PER_FILE:
        die(f"{os.path.basename(path)} already has {len(entries)} entries "
            f"(cap {MAX_ENTRIES_PER_FILE}). Prune/distill before adding more.")
    entries.append(block)
    write_ledger(path, head, entries)
    seal_file(path)


def remove_entry(path, ledger_id):
    if not os.path.isfile(path):
        return False
    head, entries = split_ledger(path)
    kept = [e for e in entries if entry_id(e) != ledger_id]
    if len(kept) == len(entries):
        return False
    write_ledger(path, head, kept)
    seal_file(path)
    return True


# --------------------------------------------------------------- integrity manifest
def load_manifest():
    return load_json(MANIFEST, default={"version": 1, "updated": None, "files": {}})


def seal_file(path):
    """Record the current sha256 of a ledger file as trusted baseline."""
    man = load_manifest()
    name = os.path.basename(path)
    _, entries = split_ledger(path)
    man["files"][name] = {"sha256": sha256_file(path), "entries": len(entries)}
    man["updated"] = today()
    save_json(MANIFEST, man)


def cmd_reseal():
    man = {"version": 1, "updated": today(), "files": {}}
    files = lessons_files()
    for p in files:
        _, entries = split_ledger(p)
        man["files"][os.path.basename(p)] = {
            "sha256": sha256_file(p), "entries": len(entries)
        }
    save_json(MANIFEST, man)
    print(f"resealed {len(files)} ledger file(s) - current state is now the trusted baseline.")
    for p in files:
        _, e = split_ledger(p)
        print(f"  {os.path.basename(p):<40} {len(e)} entrie(s)")


def cmd_verify():
    man = load_manifest()
    failures, warnings = [], []
    files = lessons_files()

    for p in files:
        name = os.path.basename(p)
        with open(p, "r", encoding="utf-8") as fh:
            raw = fh.read()
        head, entries = split_ledger(p)

        # Empty ledger = inherently trusted (nothing to poison).
        if not entries:
            continue

        if LESSON_MARKER not in raw:
            failures.append(f"{name}: missing BEGIN-LESSONS marker (file structure damaged)")
            continue

        rec = man.get("files", {}).get(name)
        if rec is None:
            failures.append(f"{name}: has {len(entries)} entrie(s) but is NOT in the manifest "
                            "- appeared outside record_outcome.py (possible LLM/manual edit). "
                            "Review it, then `--reseal` if legitimate.")
        elif rec.get("sha256") != sha256_file(p):
            failures.append(f"{name}: sha256 MISMATCH - file was edited outside record_outcome.py "
                            "(tampering / LLM write). Review, then `--reseal` if legitimate.")

        for e in entries:
            eid = entry_id(e)
            if not eid:
                failures.append(f"{name}: an entry has NO ledger-id footer - not written by "
                                "record_outcome.py (foreign/LLM-injected). First line: "
                                f"{e.splitlines()[0][:70]!r}")
            if len(e) > MAX_BLOCK_CHARS:
                warnings.append(f"{name}: entry {eid} is {len(e)} chars (cap {MAX_BLOCK_CHARS}).")
        if len(entries) > MAX_ENTRIES_PER_FILE:
            warnings.append(f"{name}: {len(entries)} entries exceeds cap {MAX_ENTRIES_PER_FILE}.")

    # manifest references a file that no longer exists / lost its entries
    for name, rec in man.get("files", {}).items():
        p = os.path.join(MEM_DIR, name)
        if not os.path.isfile(p):
            if rec.get("entries", 0) > 0:
                failures.append(f"{name}: in manifest with {rec['entries']} entrie(s) but the "
                                "file is GONE (deleted outside record_outcome.py).")

    # scoreboard internal consistency
    sb = load_json(SCOREBOARD, default={})
    for ag, a in (sb.get("agents", {}) or {}).items():
        denom = a.get("confirmed", 0) + a.get("false_positive", 0)
        want = round(a["confirmed"] / denom, 3) if denom else None
        if a.get("precision") != want:
            warnings.append(f"scoreboard[{ag}].precision={a.get('precision')} but should be "
                            f"{want} - run any record (auto-recomputes) or check for manual edits.")

    print("=== ChainShield ledger integrity ===")
    print(f"ledger files: {len(files)} | manifest entries: {len(man.get('files', {}))}")
    for w in warnings:
        print(f"  WARN  {w}")
    for f in failures:
        print(f"  FAIL  {f}")
    if failures:
        print(f"\nRESULT: FAIL ({len(failures)} integrity violation(s)). The agents may be "
              "compromised - do NOT run audits until resolved (revert or reseal).")
        sys.exit(2)
    print(f"\nRESULT: PASS - ledger is intact{' (with warnings)' if warnings else ''}.")


# ---------------------------------------------------------------- scoreboard (derived)
def recompute_scoreboard():
    """Scoreboard is DERIVED from audit-logs + _missed.json - never hand-incremented,
    so re-recording an outcome is idempotent and cannot inflate stats."""
    agents = {}

    def ent(ag):
        return agents.setdefault(ag, {
            "confirmed": 0, "dup": 0, "false_positive": 0, "missed": 0,
            "paid_total": 0, "precision": None,
        })

    if os.path.isdir(LOG_DIR):
        for fn in sorted(os.listdir(LOG_DIR)):
            if not fn.endswith(".json") or fn.startswith("_"):
                continue
            data = load_json(os.path.join(LOG_DIR, fn), default={})
            for f in data.get("findings", []):
                oc = f.get("outcome")
                if oc not in TALLY_OUTCOMES:
                    continue
                for ag in (f.get("agents") or []):
                    a = ent(ag)
                    if oc == "confirmed":
                        a["confirmed"] += 1
                        if f.get("paid"):
                            a["paid_total"] += f["paid"]
                    elif oc == "dup":
                        a["dup"] += 1
                    elif oc == "false-positive":
                        a["false_positive"] += 1

    for m in (load_json(MISSED_LOG, default=[]) or []):
        ent(m["agent"])["missed"] += 1

    for a in agents.values():
        denom = a["confirmed"] + a["false_positive"]
        a["precision"] = round(a["confirmed"] / denom, 3) if denom else None

    sb = {
        "_comment": "DERIVED from audit-logs + _missed.json by record_outcome.py "
                    "(recompute_scoreboard). Do not hand-edit; changes are overwritten. "
                    "precision = confirmed / (confirmed + false_positive).",
        "version": 1,
        "updated": today(),
        "agents": dict(sorted(agents.items())),
    }
    save_json(SCOREBOARD, sb)
    return sb


# --------------------------------------------------------------------------- commands
def cmd_list(audit):
    data = validate_audit_schema(load_json(audit), audit)
    print(f"Audit: {data.get('audit_id', os.path.basename(audit))}  "
          f"({data.get('project', '?')}, {data.get('date', '?')})")
    for f in data.get("findings", []):
        oc = f.get("outcome") or "-"
        paid = f.get("paid")
        paidstr = f"  ${paid}" if paid else ""
        agents = ",".join(f.get("agents", []))
        print(f"  #{f['id']:<3} [{oc:<14}] {f.get('severity','?'):<8} "
              f"{f.get('group_key','?')}  [{agents}]{paidstr}")


def cmd_show(agent_filter):
    files = lessons_files()
    if agent_filter:
        want = agent_lessons_path(agent_filter)
        files = [p for p in files if os.path.abspath(p) == os.path.abspath(want)]
    any_entry = False
    for p in files:
        _, entries = split_ledger(p)
        if not entries:
            continue
        any_entry = True
        print(f"\n# {os.path.basename(p)}  ({len(entries)} entrie(s))")
        for e in entries:
            print(f"  [{entry_id(e) or '??'}]  {e.splitlines()[0]}")
    if not any_entry:
        print("(no lesson entries yet)")


def agent_lessons_path(agent):
    if not agent.endswith("-agent") and known_agent(agent):
        agent = agent + "-agent"
    return os.path.join(MEM_DIR, f"{agent}.lessons.md")


def cmd_revert(ledger_id):
    removed = []
    for p in lessons_files():
        if remove_entry(p, ledger_id):
            removed.append(os.path.relpath(p, ROOT))
    # also drop any matching missed-log record, then recompute
    missed = load_json(MISSED_LOG, default=[]) or []
    new_missed = [m for m in missed if m.get("ledger_id") != ledger_id]
    if len(new_missed) != len(missed):
        save_json(MISSED_LOG, new_missed)
    recompute_scoreboard()
    if removed:
        print(f"reverted ledger-id {ledger_id} from: {', '.join(removed)}")
        print("scoreboard recomputed.")
    else:
        die(f"no lesson with ledger-id {ledger_id} found (use --show to list ids)")


def cmd_record_finding(args, audit):
    outcome = OUTCOME_ALIASES.get(args.outcome, args.outcome)
    data = validate_audit_schema(load_json(audit), audit)
    finding = next((f for f in data["findings"] if f.get("id") == args.id), None)
    if not finding:
        die(f"finding #{args.id} not in {os.path.basename(audit)} (use --list to see ids)")

    agents = finding.get("agents") or []
    bug_class = finding.get("bug_class", "unknown")
    audit_id = data.get("audit_id") or os.path.splitext(os.path.basename(audit))[0]
    ledger_id = f"{audit_id}#{args.id}"

    # Build+validate the lesson FIRST, before mutating anything, so a bad lesson aborts cleanly.
    block = None
    if outcome in ("confirmed", "false-positive") and args.lesson:
        body = build_body(outcome, args.lesson)
        block = make_block(outcome, bug_class, body, ledger_id)

    if args.dry_run:
        print(f"[dry-run] would set finding #{args.id} outcome={outcome}"
              + (f", paid={args.paid}" if args.paid is not None else ""))
        print(f"[dry-run] credited agents: {', '.join(agents) or '(none)'}")
        if block:
            print("[dry-run] lesson block:\n" + block)
        else:
            print("[dry-run] no lesson would be written"
                  + (" (none supplied)" if not args.lesson else ""))
        return

    finding["outcome"] = outcome
    if args.paid is not None:
        finding["paid"] = args.paid
    if args.note:
        finding["note"] = sanitize_part(args.note)
    finding["recorded"] = today()
    save_json(audit, data)

    recompute_scoreboard()

    targets = []
    if block:
        for ag in agents:
            p = agent_lessons_path(ag)
            upsert_entry(p, ag, block, ledger_id)
            targets.append(os.path.relpath(p, ROOT))
        if args.to_global:
            upsert_entry(GLOBAL_LESSONS, "global", block, ledger_id)
            targets.append(os.path.relpath(GLOBAL_LESSONS, ROOT))

    print(f"recorded {outcome.upper()} for finding #{args.id}: {finding.get('group_key')}")
    print(f"  ledger-id: {ledger_id}")
    print("  scoreboard recomputed for: " + (", ".join(agents) or "(no agents credited)"))
    if targets:
        print("  lesson written -> " + "; ".join(targets))
    elif outcome in ("confirmed", "false-positive"):
        print("  (no --lesson supplied; nothing written to the ledger)")


def cmd_record_missed(args):
    if not args.agent:
        die("--missed requires --agent (which specialist should learn this class)")
    if not known_agent(args.agent):
        die(f"unknown agent '{args.agent}' - no matching {AGENTS_DIR}\\<name>-agent.md. "
            "Use the specialty file basename, e.g. oracle-manipulation-agent.")
    if not args.lesson:
        die("--missed requires --lesson (the pattern to teach)")

    body = build_body("missed", args.lesson)  # validates Pattern:+Tell:
    ledger_id = f"missed:{args.agent}:{now_stamp()}"
    block = make_block("missed", "missed-bug", body, ledger_id)

    if args.dry_run:
        print(f"[dry-run] would teach {args.agent} (ledger-id {ledger_id}):\n{block}")
        return

    p = agent_lessons_path(args.agent)
    upsert_entry(p, args.agent, block, ledger_id)
    targets = [os.path.relpath(p, ROOT)]
    if args.to_global:
        upsert_entry(GLOBAL_LESSONS, "global", block, ledger_id)
        targets.append(os.path.relpath(GLOBAL_LESSONS, ROOT))

    missed = load_json(MISSED_LOG, default=[]) or []
    missed.append({"ledger_id": ledger_id, "agent": args.agent,
                   "date": today(), "bug_class": "missed-bug"})
    save_json(MISSED_LOG, missed)
    recompute_scoreboard()

    print(f"recorded MISSED for {args.agent}")
    print(f"  ledger-id: {ledger_id}")
    print("  lesson written -> " + "; ".join(targets))


def main():
    ap = argparse.ArgumentParser(
        description="ChainShield hardened outcome recorder / agent self-evolution feed",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", help="audit id or path (default: latest in audit-log/)")
    ap.add_argument("--list", action="store_true", help="list findings in the audit and exit")
    ap.add_argument("--show", action="store_true", help="show ledger entries + their ledger-ids")
    ap.add_argument("--verify", action="store_true", help="check ledger integrity and exit")
    ap.add_argument("--reseal", action="store_true",
                    help="snapshot current ledger state as the trusted baseline")
    ap.add_argument("--revert", metavar="LEDGER_ID", help="remove a lesson entry by its ledger-id")
    ap.add_argument("--id", type=int, help="finding id to record an outcome for")
    ap.add_argument("--outcome", choices=sorted(VALID_OUTCOMES | set(OUTCOME_ALIASES)),
                    help="outcome to record")
    ap.add_argument("--paid", type=float, help="bounty amount (with confirmed/paid)")
    ap.add_argument("--note", help="free-text note stored on the finding")
    ap.add_argument("--lesson",
                    help="'|'-separated lesson, e.g. 'Pattern: ... | Tell: ... | Generalize: ...'")
    ap.add_argument("--global", dest="to_global", action="store_true",
                    help="also append the lesson to the shared _global.lessons.md")
    ap.add_argument("--missed", action="store_true",
                    help="record a bug the audit MISSED (use with --agent + --lesson)")
    ap.add_argument("--agent", help="agent basename for --missed / --show filter")
    ap.add_argument("--dry-run", action="store_true", help="preview without writing")
    args = ap.parse_args()

    # Integrity / inspection commands run without needing an audit log.
    if args.verify:
        return cmd_verify()
    if args.reseal:
        return cmd_reseal()
    if args.show:
        return cmd_show(args.agent)
    if args.revert:
        return cmd_revert(args.revert)

    if args.missed:
        return cmd_record_missed(args)

    if args.id is not None:
        if not args.outcome:
            die("--outcome is required when recording against --id")
        audit = resolve_audit(args.audit)
        return cmd_record_finding(args, audit)

    # default: list the (latest or given) audit
    audit = resolve_audit(args.audit)
    cmd_list(audit)
    print("\n(record: --id N --outcome ... [--lesson ...] | teach: --missed --agent ... --lesson ...)")
    print("(inspect: --show | integrity: --verify | undo: --revert <ledger-id>)")


if __name__ == "__main__":
    main()
