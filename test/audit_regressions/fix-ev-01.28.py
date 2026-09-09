#!/usr/bin/env python3
"""FIX-EV-01.27 — the outcome corpus for telegram-miniapps (sherlock audit,
parent FIX-EV-01; depends on the family harness of FIX-EV-01.01).

The corpus (evals/cases/telegram-miniapps.json) holds the golden
signature-field case (TG-03), a negative (routing), the future-auth_date
boundary case, the launch-surface matrix (TG-04) and a differential case
gated on an independent verifier
— judged on ARTIFACTS through the family's outcome-case contract, so
telegram-miniapps can no longer pass an eval by its name being picked.

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
CASES = os.path.join(ROOT, "evals", "cases", "telegram-miniapps.json")
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
        assert c["skill"] == "telegram-miniapps"
        assert c["environment"]["case_digest"] == \
            hashlib.sha256(c["prompt"]["text"].encode()).hexdigest(), \
            f"{c['id']}: case_digest does not pin the frozen prompt"
        assert c["checks"]["outcome"], \
            f"{c['id']}: no outcome checks — the name-picking eval again"


def t_hmac_case_pins_the_signature_field():
    c = next(x for x in manifest()["cases"] if "hmac-signature" in x["id"])
    p = c["prompt"]["text"]
    assert "BOTH hash and signature" in p and "Ed25519" in p, \
        "the golden case no longer covers the signature-field defect (TG-03)"


def t_negative_forbids_loading():
    neg = next(c for c in manifest()["cases"] if "negative" in c["id"])
    assert "telegram-miniapps" in neg["checks"]["load_trace"]["expect_not_loaded"]
    assert not neg["checks"]["load_trace"]["expect_loaded"]


def t_skew_case_pins_both_sides():
    c = next(x for x in manifest()["cases"] if "future-auth-date" in x["id"])
    expects = {o.get("expect") for o in c["checks"]["outcome"]}
    assert "future" in expects and "boundary" in expects, \
        "the skew case does not pin refusal AND boundary pass"


def t_surface_matrix_covers_menu_and_degradation():
    c = next(x for x in manifest()["cases"] if "launch-surface" in x["id"])
    expects = {o.get("expect") for o in c["checks"]["outcome"]}
    assert "menu" in expects and "degrad" in expects, \
        "the matrix case lost the TG-04 menu row or graceful degradation"


def t_differential_gated_on_independent_verifier():
    c = next(x for x in manifest()["cases"] if "differential" in x["id"])
    assert "init_data_py" in c["checks"]["tool"][0]["command"], \
        "the differential case has no independent-verifier probe"
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
    case("the golden case pins the signature-field defect",
         t_hmac_case_pins_the_signature_field)
    case("the negative case forbids the skill from loading", t_negative_forbids_loading)
    case("the skew case pins refusal and boundary", t_skew_case_pins_both_sides)
    case("the surface matrix covers the menu row and degradation",
         t_surface_matrix_covers_menu_and_degradation)
    case("the differential case is probe-gated; rules recorded",
         t_differential_gated_on_independent_verifier)
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
