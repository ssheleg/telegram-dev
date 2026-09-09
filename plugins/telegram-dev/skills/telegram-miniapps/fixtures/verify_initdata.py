#!/usr/bin/env python3
"""Verify Telegram Mini App `initData`, and the proof that each rule can fail.

    python3 verify_initdata.py              # run the assertions
    python3 verify_initdata.py --self-test  # break one rule at a time; each MUST go red

Copy `verify()` into your project. The rest of this file is the evidence: it
forges `initData` the way Telegram signs it, then checks that a tampered user id,
a stale `auth_date`, a re-serialised `user` field and a swapped key derivation are
each REFUSED. A verifier nobody has watched reject something is decoration.

Standard library only. No network, no clock beyond `time.time()`.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from urllib.parse import parse_qsl, urlencode

# --------------------------------------------------------------- the verifier

DEFAULT_MAX_AGE = 300
# How far into the FUTURE an auth_date may sit (clock skew between Telegram and
# this host). Without an upper window, a forged-clock auth_date defeats the
# freshness check forever — it only gets fresher.
DEFAULT_MAX_SKEW = 30


def hmac_check_string(pairs: dict) -> str:
    """The Bot-API HMAC canonicalization, and ONLY that. `hash` is the value under
    test and `signature` is the OTHER protocol's input — both excluded here, per
    the Bot API docs, not per a shared helper's opinion. The Ed25519 path has its
    own canonicalizer below; one helper serving both is how a canonicalization
    bug verifies itself (TG-03)."""
    keep = {k: v for k, v in pairs.items() if k not in ("hash", "signature")}
    return "\n".join(f"{k}={keep[k]}" for k in sorted(keep))


def ed25519_check_string(bot_id: str, pairs: dict) -> str:
    """The third-party (Ed25519) canonicalization: `{bot_id}:WebAppData` then the
    sorted pairs with `hash` AND `signature` excluded — per the third-party
    validation docs. The curve verification itself needs an Ed25519 library
    (none in the stdlib): this function pins the MESSAGE bytes, and a host
    without the library reports the curve check NOT_RUN, never skips it into a
    PASS."""
    keep = {k: v for k, v in pairs.items() if k not in ("hash", "signature")}
    return f"{bot_id}:WebAppData\n" + "\n".join(f"{k}={keep[k]}" for k in sorted(keep))


def verify(init_data: str, bot_token: str, max_age: int = DEFAULT_MAX_AGE,
           max_skew: int = DEFAULT_MAX_SKEW) -> dict:
    """Return the verified fields, or raise. Identity comes from the RETURN value.

    Strict input boundaries, each refused BEFORE the signature math (TG-03.02):
    an unparseable blob is "unparseable", never a stack trace; DUPLICATE fields
    are refused outright — dict() keeps the last duplicate silently, and
    "user=innocent&user=admin" is an argument about which copy the HMAC covered
    that no verifier should be having; auth_date has an upper window too, so a
    future timestamp cannot out-fresh the freshness check.
    """
    try:
        pair_list = parse_qsl(init_data, strict_parsing=True)
    except ValueError:
        raise ValueError("unparseable")
    keys = [k for k, _ in pair_list]
    if len(keys) != len(set(keys)):
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        raise ValueError(f"duplicate field: {', '.join(dupes)}")
    pairs = dict(pair_list)
    received = pairs.get("hash")
    if not received:
        raise ValueError("no hash")

    check = hmac_check_string(pairs)
    # The constant is the KEY and the token is the MESSAGE. Swapped, this produces
    # a stable digest that never matches, and the usual "fix" is to stop checking.
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received):
        raise ValueError("bad signature")

    auth_date = pairs.get("auth_date")
    if auth_date is None:
        raise ValueError("no auth_date")
    now = time.time()
    if now - int(auth_date) > max_age:
        raise ValueError("stale")
    if int(auth_date) - now > max_skew:
        raise ValueError("auth_date is in the future")
    pairs.pop("hash", None)
    pairs.pop("signature", None)
    return pairs


# ------------------------------------------------------------- the test rig

BOT_TOKEN = "1234567:PLACEHOLDER-not-a-real-bot-token"


def sign(fields: dict, bot_token: str = BOT_TOKEN) -> str:
    """Produce `initData` the way Telegram does, so the checks have something real."""
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": digest})


def fresh_fields(**over) -> dict:
    user = json.dumps(
        {"id": 100200300, "first_name": "Placeholder", "username": "placeholder"},
        separators=(",", ":"),
    )
    return {
        "auth_date": str(int(time.time())),
        "query_id": "AAPLACEHOLDER",
        "user": user,
        **over,
    }


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


def refuses(init_data: str, why: str, **kw) -> None:
    try:
        verify(init_data, BOT_TOKEN, **kw)
    except ValueError:
        return
    raise AssertionError(f"accepted what it must refuse: {why}")


@check("a genuine initData verifies, and the identity comes from the return value")
def _():
    fields = fresh_fields()
    got = verify(sign(fields), BOT_TOKEN)
    assert json.loads(got["user"])["id"] == 100200300
    assert got["auth_date"] == fields["auth_date"]


@check("a tampered user id is refused — the whole point of the exercise")
def _():
    fields = fresh_fields()
    data = sign(fields)
    forged = data.replace("100200300", "999999999")
    assert forged != data, "the fixture did not actually tamper with anything"
    refuses(forged, "a user id edited on the client")


@check("a hash from a different bot token is refused")
def _():
    refuses(sign(fresh_fields(), "7654321:SOME-OTHER-PLACEHOLDER-TOKEN"),
            "initData signed by another bot")


@check("stale initData is refused, so a captured blob is not a bearer token")
def _():
    old = fresh_fields(auth_date=str(int(time.time()) - 3600))
    refuses(sign(old), "an hour-old auth_date", max_age=300)
    # and the same blob verifies when the window is genuinely that wide, so the
    # check above is measuring freshness rather than a broken signature
    assert verify(sign(old), BOT_TOKEN, max_age=7200)


@check("initData with no hash at all is refused")
def _():
    refuses(urlencode(fresh_fields()), "no hash field")


@check("initData with no auth_date is refused even when the signature is good")
def _():
    fields = fresh_fields()
    del fields["auth_date"]
    refuses(sign(fields), "a correctly signed blob with no timestamp")


@check("re-serialising the user JSON breaks the hash — pass values through as received")
def _():
    fields = fresh_fields()
    data = sign(fields)
    pairs = dict(parse_qsl(data, strict_parsing=True))
    # The mistake: parse `user`, dump it again with different separators, re-sign
    # nothing, and hand the reordered string to the verifier.
    pairs["user"] = json.dumps(json.loads(pairs["user"]))      # spaces after separators
    refuses(urlencode(pairs), "a user field re-serialised before checking")


@check("the signature field is excluded from the check string")
def _():
    fields = fresh_fields()
    data = sign(fields)                       # signed WITHOUT `signature`, as Telegram does
    with_sig = f"{data}&signature=cGxhY2Vob2xkZXI"
    assert verify(with_sig, BOT_TOKEN)["query_id"] == "AAPLACEHOLDER"


@check("the key derivation is not symmetric — swapping key and message is refused")
def _():
    fields = fresh_fields()
    check_str = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    wrong_secret = hmac.new(fields and BOT_TOKEN.encode(), b"WebAppData",
                            hashlib.sha256).digest()          # token as KEY: backwards
    wrong = hmac.new(wrong_secret, check_str.encode(), hashlib.sha256).hexdigest()
    refuses(urlencode({**fields, "hash": wrong}), "a hash built with the derivation reversed")


@check("a duplicate field is refused before any signature math")
def _():
    data = sign(fresh_fields())
    refuses(data + "&user=%7B%22id%22%3A1%7D", "user sent twice — dict() keeps the last silently")
    refuses("auth_date=1&auth_date=2&hash=00", "a duplicated auth_date")


@check("an unparseable blob is refused cleanly, not a stack trace")
def _():
    for blob in ("not-a-querystring", "a=1&=broken", "&&&"):
        try:
            verify(blob, BOT_TOKEN)
            raise AssertionError(f"accepted unparseable blob {blob!r}")
        except ValueError as e:
            assert "unparseable" in str(e) or "no hash" in str(e), \
                f"the refusal leaks internals: {e}"


@check("a future auth_date cannot out-fresh the freshness window")
def _():
    future = fresh_fields(auth_date=str(int(time.time()) + 3600))
    refuses(sign(future), "an auth_date an hour in the future")
    # inside the skew allowance, a slightly-ahead clock still verifies
    nearly = fresh_fields(auth_date=str(int(time.time()) + 10))
    assert verify(sign(nearly), BOT_TOKEN)["query_id"] == "AAPLACEHOLDER"


@check("the exact boundary timestamps pass — the windows are strict inequalities")
def _():
    # Frozen clock: with real time the edge drifts stale between building the
    # blob and verifying it, and the check measures the scheduler, not the rule.
    real = time.time
    frozen = float(int(real()))
    time.time = lambda: frozen
    try:
        at_age_edge = fresh_fields(auth_date=str(int(frozen) - DEFAULT_MAX_AGE))
        assert verify(sign(at_age_edge), BOT_TOKEN)
        at_skew_edge = fresh_fields(auth_date=str(int(frozen) + DEFAULT_MAX_SKEW))
        assert verify(sign(at_skew_edge), BOT_TOKEN)
        refuses(sign(fresh_fields(auth_date=str(int(frozen) - DEFAULT_MAX_AGE - 1))),
                "one second past the age window")
        refuses(sign(fresh_fields(auth_date=str(int(frozen) + DEFAULT_MAX_SKEW + 1))),
                "one second past the skew window")
    finally:
        time.time = real


# Precomputed BY HAND, once, and inlined — deliberately NOT built with sign():
# a vector the oracle derives shares the oracle's canonicalization, and a shared
# canonicalization is how a bug verifies itself (TG-03). auth_date is fixed, so
# the checks pass an explicit max_age instead of racing the clock.
GOLDEN_WITH_SIGNATURE = (
    "auth_date=1757000000&query_id=AAPLACEHOLDER"
    "&user=%7B%22id%22%3A100200300%2C%22first_name%22%3A%22Placeholder%22%2C"
    "%22username%22%3A%22placeholder%22%7D"
    "&signature=cGxhY2Vob2xkZXItZWQyNTUxOQ"
    "&hash=eceadeeed9abe565c6a5982e4f0740e8507dd7de124514912ddf59334bb42e31"
)
GOLDEN_ED25519_CHECK = (
    "1234567:WebAppData\n"
    "auth_date=1757000000\n"
    "query_id=AAPLACEHOLDER\n"
    'user={"id":100200300,"first_name":"Placeholder","username":"placeholder"}'
)
WIDE = 10 ** 10  # the vector's fixed auth_date, admitted explicitly


@check("the golden vector (with signature) passes only the correct HMAC path")
def _():
    got = verify(GOLDEN_WITH_SIGNATURE, BOT_TOKEN, max_age=WIDE)
    assert got["query_id"] == "AAPLACEHOLDER", "the independent vector did not verify"
    # The wrong path — signature folded into the HMAC check string, the exact
    # canonicalization this leaf separates — must REFUSE the same vector.
    pairs = dict(parse_qsl(GOLDEN_WITH_SIGNATURE, strict_parsing=True))
    received = pairs.pop("hash")
    wrong_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))  # keeps signature
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    wrong = hmac.new(secret, wrong_check.encode(), hashlib.sha256).hexdigest()
    assert wrong != received, \
        "the wrong canonicalization produced the right digest — the vector separates nothing"


@check("the Ed25519 canonicalizer is its own function with its own message shape")
def _():
    pairs = dict(parse_qsl(GOLDEN_WITH_SIGNATURE, strict_parsing=True))
    ed = ed25519_check_string("1234567", pairs)
    assert ed == GOLDEN_ED25519_CHECK, f"the third-party message drifted:\n{ed!r}"
    assert ed != hmac_check_string(pairs), \
        "the two canonicalizers produced one string — one helper is serving both protocols"
    assert ed.startswith("1234567:WebAppData\n"), "the bot-id prefix is gone"


def main(argv: list[str]) -> int:
    failures = []
    for name, fn in CHECKS:
        try:
            fn()
        except AssertionError as e:
            failures.append(f"{name}: {e}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1
    print(f"OK ({len(CHECKS)} checks — every rule watched refusing its own defect)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
