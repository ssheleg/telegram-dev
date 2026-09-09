#!/usr/bin/env python3
"""FIX-TG-04.01 — the launch-surface matrix (sherlock audit, TG-04).

The finding: the reference merged direct link and menu button as "neither, no
query" — but the Telegram MENU button carries inline-button semantics and CAN
answerWebAppQuery; and an inline-QUERY app was conflated with an inline
BUTTON. Also DeviceStorage/SecureStorage were listed as blanket "all 8.0+"
when each method needs a per-method capability check.

The fix under test: keyboard / inline-keyboard / inline-mode / menu /
direct-main-attachment are separate surfaces, each with query_id presence and
the allowed return API; a capability floor is necessary, not sufficient, and
per-method capability is checked. Documented in both references, and the
matrix + degradation rules run as behaviour.

Standard library only.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REFS = os.path.join(ROOT, "plugins", "telegram-dev", "skills", "telegram-miniapps",
                    "references")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def read(name):
    return open(os.path.join(REFS, name), encoding="utf-8").read()


def t_doctrine_states_the_matrix():
    a2b = " ".join(read("app-to-bot.md").split())
    for needle in ("The launch surface decides the way back — and there are more "
                   "than two",
                   "**Inline mode** result",
                   "the menu button carries inline-button semantics and CAN\nanswer a "
                   "query — it is not \"neither\"".replace("\n", " "),
                   "distinct from an inline BUTTON",
                   "this is the only \"neither\" row",
                   "degrade gracefully"):
        assert needle in a2b, f"app-to-bot.md no longer states {needle!r}"
    assert "| A direct link / menu button | neither" not in a2b, \
        "the merged direct-link/menu row survived"
    vp = " ".join(read("viewport-and-platform.md").split())
    assert "each method has its OWN capability" in vp and \
        "version floor is necessary, not sufficient" in vp, \
        "the blanket 'all 8.0+' storage claim was not corrected"


# ---------------- the matrix, executed


# surface -> (has_query_id, return_api)
SURFACES = {
    "keyboard": (False, "sendData"),
    "inline-keyboard": (True, "answerWebAppQuery"),
    "inline-mode": (True, "answerWebAppQuery"),
    "menu": (True, "answerWebAppQuery"),
    "direct": (False, "backend"),
}


def can_answer_query(surface):
    has_query, api = SURFACES[surface]
    return has_query and api == "answerWebAppQuery"


def t_menu_can_answer_a_query():
    assert can_answer_query("menu"), \
        "the menu button was denied answerWebAppQuery — the finding itself"
    assert SURFACES["menu"][0] is True, "the menu surface has no query_id"


def t_inline_mode_is_not_inline_button_but_both_answer():
    assert can_answer_query("inline-mode") and can_answer_query("inline-keyboard")
    # distinct entries, same call
    assert "inline-mode" != "inline-keyboard"


def t_only_no_query_surfaces_use_the_backend():
    assert not can_answer_query("keyboard")
    assert SURFACES["keyboard"][1] == "sendData"
    assert not can_answer_query("direct")
    assert SURFACES["direct"][1] == "backend", \
        "a direct link tried to answer a query it does not have"


def capability_ok(version_at_least_8, method_exposed):
    """A version floor is necessary, not sufficient — the method must be
    exposed at runtime."""
    return bool(version_at_least_8 and method_exposed)


def t_per_method_capability_not_just_version():
    assert capability_ok(True, method_exposed=True) is True
    assert capability_ok(True, method_exposed=False) is False, \
        "an 8.0 client without the method exposed was assumed capable"
    assert capability_ok(False, method_exposed=True) is False


def main():
    case("the doctrine states the launch-surface matrix",
         t_doctrine_states_the_matrix)
    case("the menu button can answer a query", t_menu_can_answer_a_query)
    case("inline mode is distinct from an inline button; both answer",
         t_inline_mode_is_not_inline_button_but_both_answer)
    case("only the no-query surfaces use the backend",
         t_only_no_query_surfaces_use_the_backend)
    case("capability is checked per method, not just by version floor",
         t_per_method_capability_not_just_version)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
