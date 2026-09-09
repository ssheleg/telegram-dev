#!/usr/bin/env python3
"""FIX-TG-03.02 — strict input boundaries (sherlock audit, TG-03, second leaf).

The contract under test, in the shipped verifier: duplicate fields and
unparseable blobs are refused BEFORE any signature math (dict() keeps the last
duplicate silently); auth_date carries an upper window beside the lower one
(a future timestamp only ever gets fresher); and the exact boundary
timestamps pass — the windows are strict inequalities.

Standard library only; drives the fixture module and both its run modes.
"""
import importlib.util
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MINI = os.path.join(ROOT, "plugins", "telegram-dev", "skills", "telegram-miniapps")
FIXTURE = os.path.join(MINI, "fixtures", "verify_initdata.py")

_spec = importlib.util.spec_from_file_location("verify_initdata", FIXTURE)
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_duplicates_fail_before_signature_math():
    good = V.sign(V.fresh_fields())
    try:
        V.verify(good + "&user=%7B%22id%22%3A99%7D", V.BOT_TOKEN)
        raise AssertionError("a duplicated user field verified")
    except ValueError as e:
        assert "duplicate field" in str(e) and "user" in str(e), \
            f"the refusal does not name the duplicate: {e}"


def t_unparseable_fails_cleanly():
    for blob in ("just words", "=broken&x", ""):
        try:
            V.verify(blob, V.BOT_TOKEN)
            raise AssertionError(f"accepted {blob!r}")
        except ValueError:
            pass


def t_future_and_stale_fail_boundary_passes():
    real = time.time
    frozen = float(int(real()))
    V.time.time = lambda: frozen
    try:
        now = int(frozen)
        ok_edge = V.sign(V.fresh_fields(auth_date=str(now - V.DEFAULT_MAX_AGE)))
        assert V.verify(ok_edge, V.BOT_TOKEN), "the exact age boundary was refused"
        skew_edge = V.sign(V.fresh_fields(auth_date=str(now + V.DEFAULT_MAX_SKEW)))
        assert V.verify(skew_edge, V.BOT_TOKEN), "the exact skew boundary was refused"
        for delta, why in ((-(V.DEFAULT_MAX_AGE + 1), "stale"),
                           (V.DEFAULT_MAX_SKEW + 1, "future")):
            blob = V.sign(V.fresh_fields(auth_date=str(now + delta)))
            try:
                V.verify(blob, V.BOT_TOKEN)
                raise AssertionError(f"{why} auth_date verified")
            except ValueError as e:
                assert ("stale" in str(e)) or ("future" in str(e)), f"wrong refusal: {e}"
    finally:
        V.time.time = real


def t_fixture_passes_and_docs_agree():
    r = subprocess.run([sys.executable, FIXTURE], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"the fixture fails:\n{(r.stderr or r.stdout)[-300:]}"
    skill = " ".join(open(os.path.join(MINI, "SKILL.md"), encoding="utf-8").read().split())
    for needle in ("Duplicates and garbage are refused before any math",
                   "a future timestamp only ever gets fresher"):
        assert needle in skill, f"SKILL.md no longer states {needle!r}"


def main():
    case("a duplicate field fails before signature math", t_duplicates_fail_before_signature_math)
    case("an unparseable blob fails cleanly", t_unparseable_fails_cleanly)
    case("future and stale fail; the exact boundaries pass",
         t_future_and_stale_fail_boundary_passes)
    case("the fixture runs green and the docs agree", t_fixture_passes_and_docs_agree)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
