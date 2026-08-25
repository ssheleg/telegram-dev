#!/usr/bin/env python3
"""Structural validator for telegram-dev.

    python3 test/validate.py              # check this tree
    python3 test/validate.py --self-test  # plant each defect; every guard MUST refuse it

The self-test is what makes this a gate rather than decoration: for each check it
copies the tree, breaks exactly the thing that check exists for, and fails if the
validator still passes. A validator nobody has watched refuse something is a
validator that cannot be trusted to refuse anything.

Standard library only. No network.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("TGDEV_ROOT") or Path(__file__).resolve().parent.parent)
PLUGIN = "telegram-dev"
PLUGIN_DIR = ROOT / "plugins" / PLUGIN
SKILL_ROOT = PLUGIN_DIR / "skills"

# The Agent Skills spec caps, and the house limits that leave room for the next edit.
DESC_MAX, DESC_HOUSE = 1024, 970
BODY_MAX_TOKENS, BODY_HOUSE_TOKENS, BODY_MAX_LINES = 5000, 4750, 500
CHARS_PER_TOKEN = 3.9
RESERVED = ("anthropic", "claude")      # rejected by the Skills API on upload

_problems: list[str] = []
_notes: list[str] = []


def fail(msg: str) -> None:
    _problems.append(msg)


def note(msg: str) -> None:
    _notes.append(msg)


CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


def load_json(rel: str):
    path = ROOT / rel
    if not path.is_file():
        fail(f"{rel} is missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{rel}: invalid JSON — {exc}")
        return None


pkg = load_json("package.json")
plugin = load_json(f"plugins/{PLUGIN}/.claude-plugin/plugin.json")
market = load_json(".claude-plugin/marketplace.json")
version = (pkg or {}).get("version")
skill_dirs = sorted(d.name for d in SKILL_ROOT.iterdir()
                    if d.is_dir()) if SKILL_ROOT.is_dir() else []


def front_matter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, None
    return m.group(1), text[m.end():]


def scalar(block: str, key: str):
    m = re.search(rf"^{key}:\s*>-\n((?:[ \t]+.*\n)+)", block, re.M)
    if m:
        return " ".join(m.group(1).split())
    m = re.search(rf"^{key}:\s*(.+)$", block, re.M)
    return m.group(1).strip().strip("\"'") if m else None


# --------------------------------------------------------------------- structure

@check
def check_three_skills_ship():
    """The pack is its skills. A missing one is a silent halving of the product."""
    expected = ["telegram-bots", "telegram-miniapps", "telegram-userbots"]
    if skill_dirs != expected:
        fail(f"skills/ holds {skill_dirs}, expected {expected}")


@check
def check_one_version_four_files():
    """package.json, plugin.json, marketplace.json and the top CHANGELOG entry agree."""
    if not version:
        fail("package.json: missing version")
        return
    if plugin and plugin.get("version") != version:
        fail(f"version drift: plugin.json={plugin.get('version')!r} package.json={version!r}")
    for entry in (market or {}).get("plugins", []):
        if entry.get("version") != version:
            fail(f"version drift: marketplace.json {entry.get('name')!r}="
                 f"{entry.get('version')!r} package.json={version!r}")
        src = (entry.get("source") or "").lstrip("./")
        if not (ROOT / src).is_dir():
            fail(f"marketplace.json: source {entry.get('source')!r} does not exist")
    head = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lstrip().splitlines()[0]
    m = re.match(r"##\s*v(\S+)", head)
    if not m:
        fail(f"CHANGELOG.md: first line is not a `## vX.Y.Z` heading — {head!r}")
    elif m.group(1) != version:
        fail(f"CHANGELOG.md heads v{m.group(1)}, package.json says v{version}")


@check
def check_skill_front_matter():
    """The spec floor, per skill, plus the two house limits."""
    for name in skill_dirs:
        path = SKILL_ROOT / name / "SKILL.md"
        if not path.is_file():
            fail(f"{name}/SKILL.md is missing")
            continue
        block, _body = front_matter(path)
        if block is None:
            fail(f"{name}/SKILL.md: no YAML front matter")
            continue
        fm_name = scalar(block, "name")
        if fm_name != name:
            fail(f"{name}/SKILL.md: front-matter name is {fm_name!r}, must equal the directory")
        for word in RESERVED:
            if fm_name and word in fm_name.lower():
                fail(f"{name}/SKILL.md: name contains the reserved substring {word!r} — "
                     "Claude Code loads it and the Skills API rejects the upload")
        desc = scalar(block, "description")
        if not desc:
            fail(f"{name}/SKILL.md: no description")
            continue
        if "<" in desc or ">" in desc:
            fail(f"{name}/SKILL.md: description contains an angle bracket")
        if len(desc) > DESC_MAX:
            fail(f"{name}/SKILL.md: description is {len(desc)} chars, the cap is {DESC_MAX}")
        elif len(desc) > DESC_HOUSE:
            fail(f"{name}/SKILL.md: description is {len(desc)} chars, past the {DESC_HOUSE} "
                 "house limit — a near-miss neighbour needs room for a NOT-for clause")
        if not desc.startswith("Use when"):
            fail(f"{name}/SKILL.md: description does not open with 'Use when' (house rule)")
        if "Triggers" not in desc:
            fail(f"{name}/SKILL.md: description names no trigger phrases")
        if not re.search(r"[Ѐ-ӿ]", desc):
            fail(f"{name}/SKILL.md: description carries no Russian trigger phrases "
                 "(house rule: the operator works in both languages)")


@check
def check_body_budget():
    """Over the cap the host truncates and nothing errors, which is worse than a failure."""
    for name in skill_dirs:
        path = SKILL_ROOT / name / "SKILL.md"
        if not path.is_file():
            continue
        _block, body = front_matter(path)
        if body is None:
            continue
        lines = body.count("\n") + 1
        est = int(len(body) / CHARS_PER_TOKEN)
        if lines >= BODY_MAX_LINES:
            fail(f"{name}/SKILL.md: body is {lines} lines, the budget is < {BODY_MAX_LINES}")
        if est >= BODY_MAX_TOKENS:
            fail(f"{name}/SKILL.md: body is ~{est} tokens, the budget is < {BODY_MAX_TOKENS}")
        elif est >= BODY_HOUSE_TOKENS:
            fail(f"{name}/SKILL.md: body is ~{est} tokens, past the {BODY_HOUSE_TOKENS} "
                 "house working limit — the answer is a split into references/, not a trim")


@check
def check_references_resolve_both_ways():
    """No link to a missing reference, and no reference nobody links."""
    for name in skill_dirs:
        path = SKILL_ROOT / name / "SKILL.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        rdir = SKILL_ROOT / name / "references"
        on_disk = {p.name for p in rdir.glob("*.md")} if rdir.is_dir() else set()
        linked = set(re.findall(r"references/([A-Za-z0-9._-]+\.md)", text))
        for missing in sorted(linked - on_disk):
            fail(f"{name}/SKILL.md links references/{missing}, which does not exist")
        for orphan in sorted(on_disk - linked):
            fail(f"{name}/references/{orphan} exists and SKILL.md never links it — "
                 "an unreferenced reference is a file nobody loads")


@check
def check_fixtures_are_reachable_and_run():
    """A fixture the reader cannot find is prose, and one nothing runs rots green."""
    test_cmd = ((pkg or {}).get("scripts") or {}).get("test", "")
    for name in skill_dirs:
        fdir = SKILL_ROOT / name / "fixtures"
        if not fdir.is_dir():
            continue
        files = sorted(p.name for p in fdir.iterdir() if p.is_file())
        if not files:
            fail(f"{name}/fixtures/ is empty — an empty directory ships as a promise")
            continue
        text = (SKILL_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        for f in files:
            if f not in text:
                fail(f"{name}/SKILL.md never names fixtures/{f} — the reader cannot find it")
            if f.endswith(".py") and f"skills/{name}/fixtures/{f}" not in test_cmd:
                fail(f"package.json: `npm test` does not run {name}/fixtures/{f}")


@check
def check_every_fixture_path_named_in_markdown_resolves():
    """A renamed fixture may not leave a dead address behind."""
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts or "node_modules" in md.parts:
            continue
        rel = md.relative_to(ROOT)
        text = md.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for tok in set(re.findall(r"fixtures/([A-Za-z0-9._-]+)", line)):
                if not any((SKILL_ROOT / s / "fixtures" / tok).exists() for s in skill_dirs):
                    fail(f"{rel}:{lineno} points at fixtures/{tok}, which is not there")


@check
def check_no_stray_skill_md():
    """The skills CLI ships every SKILL.md in the tree as a real skill."""
    for path in ROOT.rglob("SKILL.md"):
        if ".git" in path.parts:
            continue
        rel = path.parent.relative_to(ROOT).as_posix()
        if not re.fullmatch(r"plugins/[^/]+/skills/[^/]+", rel):
            fail(f"stray SKILL.md at {rel}/SKILL.md — only plugins/*/skills/*/ may hold one")


@check
def check_no_secret_shapes_in_the_payload():
    """These files are copied into other people's repositories. Placeholders only."""
    # A live bot token is `<digits>:<35 chars>`. Matched from 30 rather than
    # exactly 35: a guard that only catches the exact length lets a near-miss
    # through, and the near-miss is what a hand-edited example looks like.
    shapes = (r"\b\d{6,12}:[A-Za-z0-9_-]{30,}",             # a real bot token
              r"\bsk_live_[A-Za-z0-9]{8,}", r"BEGIN [A-Z ]*PRIVATE KEY",
              r"\b[0-9a-f]{32}\b")                        # an api_hash
    for path in PLUGIN_DIR.rglob("*"):
        if not path.is_file():
            continue
        blob = path.read_text(encoding="utf-8", errors="ignore")
        for shape in shapes:
            m = re.search(shape, blob)
            if m and "PLACEHOLDER" not in m.group(0):
                fail(f"{path.relative_to(ROOT)}: carries something secret-shaped "
                     f"({shape}) — {m.group(0)[:12]}…")


@check
def check_the_readme_counts_what_ships():
    """A number typed by hand is an assertion; this one is compared to the tree."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*(\w+) skills\b", readme)
    if not m:
        fail("README.md: no '**N skills' sentence to check against the tree")
        return
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
    stated = words.get(m.group(1).lower()) or (int(m.group(1)) if m.group(1).isdigit() else None)
    if stated != len(skill_dirs):
        fail(f"README.md says {m.group(1)!r} skills; the tree ships {len(skill_dirs)}")


@check
def check_ci_runs_the_gate():
    """A gate CI does not run is a gate that stops holding on the first busy week."""
    wf = ROOT / ".github" / "workflows" / "validate.yml"
    if not wf.is_file():
        fail(".github/workflows/validate.yml is missing")
        return
    text = wf.read_text(encoding="utf-8")
    for needle in ("npm test", "--self-test", "claude plugin validate"):
        if needle not in text:
            fail(f"validate.yml never runs {needle!r}")
    rel = ROOT / ".github" / "workflows" / "release.yml"
    if rel.is_file() and "validate.yml" not in rel.read_text(encoding="utf-8"):
        fail("release.yml does not gate on validate.yml — a release can publish over a red suite")


@check
def check_routed_triggers_still_advertised():
    """The family's routing hook fires on words these descriptions have to keep.

    A member can ship green on its own gate having dropped a phrase that is a live
    trigger in the umbrella's `lib/triggers.js` — and it releases BEFORE the umbrella
    re-pins, so the umbrella finds out minutes after the tag. A hook firing on a promise
    nobody made is the defect.

    The table is NOT copied here: the umbrella's own checker is asked, reading the module
    the hook itself calls, so there is no duplicate to drift. With no umbrella above this
    checkout — the ordinary state of a standalone clone, and of this repository's own CI —
    it discloses instead of passing, because a check that cannot look must never read as
    one that looked.
    """
    script = ROOT.parent.parent / "test" / "advertised_check.js"
    if not script.is_file():
        note("routed triggers — no sshlg-skills umbrella above this checkout")
        return
    try:
        proc = subprocess.run(["node", str(script), "--member", "telegram-dev",
                               "--root", str(ROOT)],
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        note(f"routed triggers — could not run the umbrella's checker ({exc})")
        return
    if proc.returncode == 1:
        fail((proc.stdout + proc.stderr).strip())
    elif proc.returncode != 0:
        note(f"routed triggers — {(proc.stderr or 'the checker could not look').strip()}")


# ------------------------------------------------------------------- self-test

PLANTS = (
    ("a description over the house limit", "plugins/telegram-dev/skills/telegram-bots/SKILL.md",
     lambda t: t.replace("license: MIT", "  padding padding padding padding padding padding "
                         "padding padding padding padding padding padding padding padding\n"
                         "license: MIT", 1), "past the"),
    ("a front-matter name that does not match the directory",
     "plugins/telegram-dev/skills/telegram-bots/SKILL.md",
     lambda t: t.replace("name: telegram-bots", "name: telegram-bot", 1), "must equal the directory"),
    ("a reserved substring in a skill name",
     "plugins/telegram-dev/skills/telegram-bots/SKILL.md",
     lambda t: t.replace("name: telegram-bots", "name: claude-telegram", 1), "reserved substring"),
    ("a link to a reference that does not exist",
     "plugins/telegram-dev/skills/telegram-userbots/SKILL.md",
     lambda t: t.replace("references/rate-and-flood.md", "references/nope.md"), "does not exist"),
    # Derived, never written: a plant naming a literal version stops planting
    # anything the first time the package is released, and reports itself BROKEN
    # rather than passing — which is how this one was found, at v0.1.1.
    ("a version that drifted in one file", "package.json",
     lambda t: re.sub(r'("version":\s*")(\d+)\.(\d+)\.(\d+)(")',
                      lambda m: f"{m.group(1)}{m.group(2)}.{int(m.group(3)) + 1}.0{m.group(5)}",
                      t, count=1), "version drift"),
    ("a fixture the skill stops naming",
     "plugins/telegram-dev/skills/telegram-miniapps/SKILL.md",
     lambda t: t.replace("fixtures/verify_initdata.py", "fixtures/gone.py"), "which is not there"),
    ("a real-looking bot token in the payload",
     "plugins/telegram-dev/skills/telegram-bots/fixtures/update_delivery.py",
     lambda t: t.replace('"chg_PLACEHOLDER_1"',
                         '"7712345678:AAFakeTokenShapedStringForTheGuard0x"', 1),
     "secret-shaped"),
    ("a README count that stops matching the tree", "README.md",
     lambda t: t.replace("**Three skills", "**Four skills", 1), "the tree ships"),
)


def self_test() -> int:
    ok = True
    for label, rel, mutate, expect in PLANTS:
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "repo"
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "node_modules"))
            target = dst / rel
            before = target.read_text(encoding="utf-8")
            after = mutate(before)
            if before == after:
                print(f"  BROKEN  {label}: the plant changed nothing in {rel}")
                ok = False
                continue
            target.write_text(after, encoding="utf-8")
            run = subprocess.run([sys.executable, str(Path(__file__).resolve())],
                                 capture_output=True, text=True,
                                 env={**os.environ, "TGDEV_ROOT": str(dst)})
            out = run.stdout + run.stderr
            if run.returncode == 0:
                print(f"  BROKEN  {label}: validator still passed")
                ok = False
            elif expect not in out:
                print(f"  BROKEN  {label}: refused, but not for the stated reason "
                      f"(wanted {expect!r})")
                ok = False
            else:
                print(f"  ok      {label}")
    print()
    if not ok:
        print("FAIL: a planted defect survived — this validator is decoration")
        return 1
    print(f"self-test OK — {len(PLANTS)} planted defects, every one refused")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    for fn in CHECKS:
        fn()
    for n in _notes:
        print(f"  unlooked: {n}")
    if _problems:
        print("FAIL: telegram-dev structure invalid")
        for p in _problems:
            print(f" - {p}")
        return 1
    print(f"OK: telegram-dev structurally valid ({len(CHECKS)} checks, "
          f"{len(skill_dirs)} skills, v{version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
