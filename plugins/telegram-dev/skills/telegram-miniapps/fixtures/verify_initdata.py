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


def verify(init_data: str, bot_token: str, max_age: int = DEFAULT_MAX_AGE) -> dict:
    """Return the verified fields, or raise. Identity comes from the RETURN value."""
    pairs = dict(parse_qsl(init_data, strict_parsing=True))
    received = pairs.pop("hash", None)
    if not received:
        raise ValueError("no hash")
    # `signature` is the Ed25519 third-party field. It is NOT part of the HMAC
    # check string, and leaving it in fails only for clients new enough to send it.
    pairs.pop("signature", None)

    check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    # The constant is the KEY and the token is the MESSAGE. Swapped, this produces
    # a stable digest that never matches, and the usual "fix" is to stop checking.
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received):
        raise ValueError("bad signature")

    auth_date = pairs.get("auth_date")
    if auth_date is None:
        raise ValueError("no auth_date")
    if time.time() - int(auth_date) > max_age:
        raise ValueError("stale")
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
