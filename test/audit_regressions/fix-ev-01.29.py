#!/usr/bin/env python3
"""FIX-EV-01.27 — the outcome corpus for telegram-userbots (sherlock audit,
parent FIX-EV-01; depends on the family harness of FIX-EV-01.01).

The corpus (evals/cases/telegram-userbots.json) holds a positive
(restart+replay exactly-once, TG-01), a negative (routing), the
omit-vs-empty allowed_updates case (TG-02), the one-call alert no-op (the
router's own NOT-through-it boundary) and a live getMe gated on a bot token
— judged on ARTIFACTS through the family's outcome-case contract, so
telegram-userbots can no longer pass an eval by its name being picked.

Checked here, stdlib only.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASES = os.path.join(ROOT, "evals", "cases", "telegram-userbots.json")
HARNESS = os.path.expanduser("~/DATA/sshlg-skills/test/outcome_harness.py")

failures = []
not_run = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def manifest():
    with open(CASES, encoding="utf-8") as fh:
        return json.load(fh)


def t_cases_are_structurally_valid():
    m = manifest()
    ids = [c["id"] for c in m["cases"]]
    assert len(ids) == len(set(ids)) and len(ids) >= 5
    for c in m["cases"]:
        assert c["schema_version"] == "outcome-case/1"
        assert c["skill"] == "telegram-userbots"
        assert c["environment"]["case_digest"] == \
            hashlib.sha256(c["prompt"]["text"].encode()).hexdigest(), \
            f"{c['id']}: case_digest does not pin the frozen prompt"
        assert c["checks"]["outcome"], \
            f"{c['id']}: no outcome checks — the name-picking eval again"


def t_floodwait_case_is_bounded():
    c = next(x for x in manifest()["cases"] if "floodwait" in x["id"])
    assert "100 consecutive" in c["prompt"]["text"]
    assert any("bounded" in (o.get("expect") or "") for o in c["checks"]["outcome"]), \
        "the FloodWait case does not pin a bounded retry sequence (TG-05)"


def t_negative_and_noop_hold_the_boundary():
    m = manifest()
    neg = next(c for c in m["cases"] if "negative" in c["id"])
    assert "telegram-userbots" in neg["checks"]["load_trace"]["expect_not_loaded"]
    noop = next(c for c in m["cases"] if "self-alert" in c["id"])
    assert "telegram-userbots" in noop["checks"]["load_trace"]["expect_not_loaded"], \
        "the self-alert loaded the skill — the transport boundary fails"


def t_revoked_session_stops_and_alerts_once():
    c = next(x for x in manifest()["cases"] if "revoked-session" in x["id"])
    expects = {o.get("expect") for o in c["checks"]["outcome"]}
    assert "work stopped" in expects and "one alert" in expects, \
        "the revoked-session case does not pin stop + single-alert (DV-16)"


def t_live_case_gated_on_credentials():
    c = next(x for x in manifest()["cases"] if "live" in x["id"])
    assert "TELEGRAM_SESSION" in c["checks"]["tool"][0]["command"], \
        "the live case has no session-string probe"
    flat = " ".join(json.dumps(manifest(), ensure_ascii=False).split())
    for needle in ("actual output oracle", "raw result", "with/without-skill",
                   "NOT_RUN", "grader convenience"):
        assert needle in flat, f"the manifest no longer records {needle!r}"


def t_family_harness_validates_each_case_where_present():
    if not os.path.isfile(HARNESS):
        not_run.append("family harness absent — case validation NOT_RUN (never PASS)")
        return
    for c in manifest()["cases"]:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(c, fh)
            path = fh.name
        try:
            r = subprocess.run([sys.executable, HARNESS, path],
                               capture_output=True, text=True, timeout=60)
            assert r.returncode == 0, \
                f"{c['id']} rejected by the family harness:\n{r.stdout}"
        finally:
            os.unlink(path)


def main():
    case("every case is structurally valid, none is name-picking",
         t_cases_are_structurally_valid)
    case("the FloodWait case pins a bounded retry sequence",
         t_floodwait_case_is_bounded)
    case("the negative and self-alert both refuse to load the skill",
         t_negative_and_noop_hold_the_boundary)
    case("the revoked-session case stops work and alerts once",
         t_revoked_session_stops_and_alerts_once)
    case("the live case is gated on a session string; rules recorded",
         t_live_case_gated_on_credentials)
    case("the family harness validates each case (where present)",
         t_family_harness_validates_each_case_where_present)
    for n in not_run:
        print(f"  NOT_RUN  {n}")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
