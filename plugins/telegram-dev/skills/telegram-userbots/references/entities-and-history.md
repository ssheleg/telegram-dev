# Entities, peers, and reading history

**Load this when** resolving users or chats, iterating messages, or downloading
media at scale.

*Read against Telethon 1.44.0 on 2026-08-25.*

## Resolution costs a request; ids do not

`get_entity("@someone")` may hit the network. In a loop over ten thousand
usernames it is ten thousand requests and a certain FloodWait.

- **Keep the ids you are given.** Every update carries peer ids; store them with
  your rows the first time you see them.
- **`get_input_entity` is the cheap one** — it can answer from the local cache
  where `get_entity` wants the full object.
- **A username is a lookup, an id is an address.** Resolve once, store, and use
  the id afterwards.

## `PeerIdInvalidError` usually means "never seen"

MTProto clients can only address peers the account has encountered — through a
dialog, a message, a member list. An id copied from another account's logs is
valid and still unusable here. The fix is to make the account meet the peer
(open the dialog, fetch the message that mentions it), not to retry.

This is the sharpest behavioural difference from the Bot API, where a `chat_id`
works as long as the bot is in the chat.

## Iterate with the library's iterators

```python
async for message in client.iter_messages(peer, limit=None):
    ...
```

`iter_messages`, `iter_dialogs`, `iter_participants` page correctly, respect the
server's cursors and stop when the server says stop. Hand-rolled `offset_id`
arithmetic re-requests pages, which costs quota and produces duplicates that look
like a bug in your deduplication.

`limit=None` means "all", and "all" on a large channel is a long job — give it the
same queue, resume point and flood handling as any other long job.

## Media

- **`client.download_media` handles the chunking**; a manual implementation is
  where people rediscover flood limits.
- **Download to a temporary path and move on success.** A partial file that looks
  complete is worse than none, and this is a job that will be interrupted.
- **Deduplicate on the file's own id before downloading**, not after. The
  cheapest download is the one you skip.
- The 20 MB Bot API ceiling does not apply here — which is the single most common
  reason a project reaches for a user account. Weigh it against a local Bot API
  server first; `SKILL.md` states why.

## What to write down

| Fact | Why |
|---|---|
| peer id ↔ your own row | so you never resolve a username twice |
| the last message id processed per peer | resume without re-reading |
| the file id already downloaded | the skipped download |
| the session's account id | so an alert can name which account died |
