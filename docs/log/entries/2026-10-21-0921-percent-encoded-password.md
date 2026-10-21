---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T09:21
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# proves_viewer apply: password in .env is percent-encoded, script decodes it now

## What was done

- Second operator run of the fixed `apply_proves_viewer.py` still failed auth on
  port 6543, now with the password passed raw as a keyword argument. Probed
  `PROVES_LIBRARY/.env` again without printing secrets: listed variable names,
  counted `%XX` escape sequences in the stored password, and compared raw vs
  percent-decoded lengths.
- Updated the apply script (session scratchpad): `raw_password()` now returns
  `unquote(raw)` — the password as libpq would see it after URI decoding.
- Wrote a correction memory (`proves-db-password-is-percent-encoded`)
  superseding the earlier "literal %" diagnosis.

## What was found / decided

- The DB password in the `.env` URLs is **percent-encoded**: 21 characters
  stored containing 3 valid `%XX` escapes, 15 characters real. libpq decodes
  URI passwords, which is why the PROVES app connects with these URLs while the
  raw keyword-argument form failed.
- The earlier "literal %" conclusion rested on a bad probe: Python's
  `urlparse().password` does not percent-decode, so `raw == u.password` being
  True proved nothing about encoding.
- Decided to decode with `unquote()` in the script rather than ask the operator
  for the plaintext password. If auth still fails, the credential is stale and
  the fallback is the Supabase dashboard (Project Settings → Database).

## Lessons

When auth fails with a secret extracted from a URI, test both the raw and the
percent-decoded form before concluding the secret is wrong — and know your
parser: `urlparse` leaves userinfo encoded, libpq decodes it. A probe that
cannot distinguish the two hypotheses is not evidence for either.
