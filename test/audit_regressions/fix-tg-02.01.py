#!/usr/bin/env python3
"""FIX-TG-02.01 — omit is not empty, and update_id is identity (sherlock
audit, TG-02).

The finding: the skill said omitting allowed_updates and passing [] behave the
same — the official API keeps the PREVIOUS subscription on omission and RESETS
on []. And it claimed update_id is "sequential" without the caveat that after
~a week idle the counter restarts from a new random base.

The fix under test: a unset/[]/explicit table with getWebhookInfo as the
evidence and the desired subscription stored separately; update_id used as
identity, not a perpetual monotonicity guarantee. Documented in both files,
and the subscription and dedup rules are run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BOTS = os.path.join(ROOT, "plugins", "telegram-dev", "skills", "telegram-bots")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def read(rel):
    return open(os.path.join(BOTS, rel), encoding="utf-8").read()


def t_doctrine_states_omit_vs_empty():
    ref = " ".join(read("references/updates-and-delivery.md").split())
    for needle in ("Omitting the parameter and passing `[]` are NOT the same",
                   "keeps the PREVIOUS subscription",
                   "`[]` (empty list) | **resets**",
                   "getWebhookInfo` reports `allowed_updates`",
                   "the desired\nsubscription is stored on YOUR side".replace("\n", " ")):
        assert needle in ref, f"updates-and-delivery.md no longer states {needle!r}"
    assert "Passing nothing, or an empty list, subscribes to" not in ref, \
        "the omit==[] claim survived"


def t_doctrine_states_update_id_identity():
    ref = " ".join(read("references/updates-and-delivery.md").split())
    assert "it is IDENTITY, not a\nperpetual monotonicity guarantee".replace("\n", " ") in ref \
        or "IDENTITY, not a perpetual monotonicity guarantee" in ref, \
        "the ordering section does not caveat update_id monotonicity"
    assert "restart from a new random base" in ref
    sk = " ".join(read("SKILL.md").split())
    assert "it is IDENTITY, not a forever\nguarantee of monotonicity".replace("\n", " ") in sk \
        or "IDENTITY, not a forever guarantee of monotonicity" in sk, \
        "SKILL.md still calls update_id simply sequential"


# ---------------- the subscription + dedup rules, executed


class Engine:
    """A getUpdates/setWebhook mock that REMEMBERS the last allowed_updates,
    as the real API does."""

    DEFAULT_RESET = ["message", "edited_message", "callback_query"]  # sample: not the 3

    def __init__(self):
        self.subscription = None

    def configure(self, allowed_updates="__unset__"):
        if allowed_updates == "__unset__":
            pass                                  # omission: keep previous
        elif allowed_updates == []:
            self.subscription = list(self.DEFAULT_RESET)   # [] resets
        else:
            self.subscription = list(allowed_updates)
        return self.subscription

    def get_webhook_info(self):
        return {"allowed_updates": self.subscription}


def t_omit_keeps_empty_resets():
    e = Engine()
    e.configure(["chat_member", "message"])       # explicit
    assert e.get_webhook_info()["allowed_updates"] == ["chat_member", "message"]
    e.configure()                                 # omit: unchanged
    assert e.get_webhook_info()["allowed_updates"] == ["chat_member", "message"], \
        "omitting the parameter changed the subscription — the finding itself"
    e.configure([])                               # []: reset
    assert "chat_member" not in e.get_webhook_info()["allowed_updates"], \
        "an empty list did not reset the subscription"


class Inbox:
    def __init__(self):
        self.rows = set()

    def put(self, update_id):
        if update_id in self.rows:
            return "duplicate"
        self.rows.add(update_id)
        return "stored"


def t_update_id_dedups_across_a_random_restart():
    inbox = Inbox()
    # a normal run, ascending ids
    assert inbox.put(1005) == "stored"
    assert inbox.put(1006) == "stored"
    assert inbox.put(1006) == "duplicate"         # a redelivery
    # a week idle → the counter restarts from a SMALLER random base; a
    # monotonicity assumption would DROP it, identity-dedup keeps it.
    assert inbox.put(42) == "stored", \
        "a post-idle lower update_id was dropped — monotonicity was assumed"
    assert inbox.put(42) == "duplicate"           # its own redelivery still dedups


def main():
    case("the doctrine states omit != empty with getWebhookInfo evidence",
         t_doctrine_states_omit_vs_empty)
    case("the doctrine caveats update_id as identity, not perpetual monotonicity",
         t_doctrine_states_update_id_identity)
    case("omit keeps the previous subscription; [] resets it",
         t_omit_keeps_empty_resets)
    case("update_id dedups by identity across a random restart",
         t_update_id_dedups_across_a_random_restart)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
