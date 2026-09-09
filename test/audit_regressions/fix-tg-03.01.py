#!/usr/bin/env python3
"""FIX-TG-03.01 — separate canonicalizers (sherlock audit, finding TG-03).

The finding: the HMAC verifier dropped the `signature` field through the same
canonicalization helper its own oracle used — so a canonicalization bug
verified itself, and the Ed25519 path had no canonicalizer of its own at all.

The fix under test: `hmac_check_string` and `ed25519_check_string` are two
functions with two field policies (both exclude hash+signature; only the
Ed25519 message carries the `{bot_id}:WebAppData` prefix), and HAND-COMPUTED
golden vectors — never derived via the oracle — pass only the correct
verification path.

Standard library only.
"""
import importlib.util
import hashlib
import hmac
import os
import subprocess
import sys
from urllib.parse import parse_qsl

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


def t_two_canonicalizers_exist_and_differ():
    pairs = dict(parse_qsl(V.GOLDEN_WITH_SIGNATURE, strict_parsing=True))
    h = V.hmac_check_string(pairs)
    e = V.ed25519_check_string("1234567", pairs)
    assert "signature=" not in h and "hash=" not in h, f"the HMAC string kept a meta field:\n{h}"
    assert "signature=" not in e and "hash=" not in e, f"the Ed25519 message kept a meta field:\n{e}"
    assert e.startswith("1234567:WebAppData\n"), "the Ed25519 prefix is gone"
    assert e != h, "one helper is serving both protocols"
    assert e == V.GOLDEN_ED25519_CHECK, "the third-party message drifted from the golden literal"


def t_golden_vector_passes_only_the_correct_path():
    got = V.verify(V.GOLDEN_WITH_SIGNATURE, V.BOT_TOKEN, max_age=V.WIDE)
    assert got["query_id"] == "AAPLACEHOLDER"
    # the wrong canonicalization (signature folded into the HMAC) must refuse it
    pairs = dict(parse_qsl(V.GOLDEN_WITH_SIGNATURE, strict_parsing=True))
    received = pairs.pop("hash")
    wrong_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", V.BOT_TOKEN.encode(), hashlib.sha256).digest()
    wrong = hmac.new(secret, wrong_check.encode(), hashlib.sha256).hexdigest()
    assert wrong != received, "the wrong path reproduced the golden digest"


def t_vector_is_independent_of_the_oracle():
    """The golden vector is a literal, not a sign() product: re-deriving it via
    the oracle and getting the same bytes would be fine, but the SOURCE is the
    file's literal — assert the literal exists as bytes in the file."""
    src = open(FIXTURE, encoding="utf-8").read()
    assert "eceadeeed9abe565c6a5982e4f0740e8507dd7de124514912ddf59334bb42e31" in src, \
        "the golden digest is not inlined — it is being derived at runtime"
    assert 'GOLDEN_WITH_SIGNATURE = (' in src


def t_fixture_and_docs_agree():
    r = subprocess.run([sys.executable, FIXTURE], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"the fixture fails:\n{(r.stderr or r.stdout)[-300:]}"
    skill = " ".join(open(os.path.join(MINI, "SKILL.md"), encoding="utf-8").read().split())
    for needle in ("a SEPARATE protocol with a SEPARATE canonicalization",
                   "hmac_check_string", "ed25519_check_string",
                   "golden vectors (hand-computed, never derived by the oracle)"):
        assert needle in skill, f"SKILL.md no longer states {needle!r}"


def main():
    case("two canonicalizers, two field policies, one prefix", t_two_canonicalizers_exist_and_differ)
    case("the golden vector passes only the correct path", t_golden_vector_passes_only_the_correct_path)
    case("the vector is independent of the oracle", t_vector_is_independent_of_the_oracle)
    case("the fixture runs green and the docs agree", t_fixture_and_docs_agree)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
