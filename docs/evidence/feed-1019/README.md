# v0.3.0 source packet (2026-10-19)

Candidate content came from a private review of field reports. Field reports
are leads, not sources: a sentence entered a skill only when a primary source
fetched on 2026-10-19 said it. This packet lists those sources and the leads
that stayed out.

## Primary sources read

| Claim area | Source | Lands in |
|---|---|---|
| `auth.logOut`, `future_auth_token`, `logout_tokens`, Fragment code type | `https://core.telegram.org/api/auth`, `https://core.telegram.org/method/auth.logOut` | `telegram-userbots/references/sessions-and-auth.md` |
| Session listing and termination, the 24-hour refusal | `https://core.telegram.org/method/account.getAuthorizations`, `.../method/account.resetAuthorization`, `.../method/auth.resetAuthorizations`, `.../constructor/authorization` | same |
| New-login notice, unconfirmed sessions, autoconfirm period | `https://core.telegram.org/api/auth` (Confirming login), `.../constructor/updateNewAuthorization`, `https://core.telegram.org/api/config` | same |
| QR login token and the login code link | `https://core.telegram.org/api/qr-login`, `.../method/auth.acceptLoginToken`, `https://core.telegram.org/api/links` | same |
| Terminating a session from *Settings > Devices* | `https://telegram.org/faq` | same |
| `+888` codes on Fragment, behind the wallet | `https://fragment.com/about` | same |
| Telethon class names; the client keeps no future auth tokens | `telethon==1.44.0` wheel from PyPI, `telethon/tl/functions/{account,auth}.py`, `telethon/tl/types/__init__.py`, `telethon/client/` | userbots skill and reference |
| Super-app host capabilities | Priyanka, Ortwein, Reardon, Specter, Sharma, Ensafi, *Don't Trust the Super-App: A Case Study of Russia's Max*, arXiv:2609.11814 (2026-09-10) | `telegram-miniapps/SKILL.md` |
| Mini App client storage findings | Ciccotelli, Zappone, Di Pietro, *TENET: Telegram Mini App (in)security*, arXiv:2608.17538 (2026-08-18) | same |
| `SecureStorage`, `DeviceStorage`, Bot API 9.0 | `https://core.telegram.org/bots/webapps` | same |
| TON Connect 3.1.0, 5.0.0, 5.0.1 | `ton-connect/sdk` repository, `packages/ui/CHANGELOG.md`; npm registry versions of `@tonconnect/ui`, `@tonconnect/ui-react`, `@tonconnect/sdk` | same |
| Bot API 10.3 still the latest | `https://core.telegram.org/bots/api-changelog` | `telegram-bots/SKILL.md` |
| Official Markdown docs | `https://core.telegram.org/bots/api.md`, `.../bots/api/methods/getupdates.md`, `.../bots/api/types.md` (all `text/markdown`) | same |
| Gift purchase offers | `https://telegram.org/blog/passkeys-and-gift-offers` (2025-12-12); Bot API 9.3 changelog entry for `UniqueGiftInfo.origin` | `telegram-bots/references/payments-stars.md` |

The second-channel note in `telegram-bots` is stated as practice and makes no
factual claim about any country.

## Leads left out (no primary source found)

| Lead | Why it stayed out |
|---|---|
| A client's stored auth key keeps working after Log Out | No Telegram document says what `auth.logOut` does to the auth key. The documented, adjacent fact (the future auth token) went in instead. |
| `+888` numbers flooded with login codes, and a Fragment switch that stops code reception | Fragment's public pages describe code reception, not a switch to disable it, and no first-party report of the flood was found. |
| Gift scam tells: a left-aligned message, a long press showing a gift-sending link | No first-party description. Only the native offer's guarantees went in. |
| Debug-menu logs on iOS, police linking a web client, gift-trace doxxing | Field reports with no primary source. |
| A wallet rename, a default wallet change, a feed tab in a desktop beta | The Telegram blog has no post after 2026-08-25. Only what the TON Connect changelog states (a Gram Wallet button) went in. |
| Stars losses through instant refunds | Rumour by its own account; nothing primary. |
| Telegram blocking figures for any country | Practice note only, no figures. |

Each lead is a row on the [board](../backlog.md) so a later wave can pick it up
when a primary source appears.
