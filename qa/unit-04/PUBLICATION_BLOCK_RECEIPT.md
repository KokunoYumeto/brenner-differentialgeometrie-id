# Unit 4 GitHub publication attempt

Attempted: 2026-08-22T16:00:31Z

## Exact local boundary

- Repository destination: `https://github.com/KokunoYumeto/brenner-differentialgeometrie-id`
- Branch: `main`
- Unit 4 content commit: `f04e23367a6b11dbe9cd375150f5333944061910`
- Intended cumulative tag: `v0.4.0-unit-04`
- Pending predecessor tag: `v0.3.0-unit-03` at commit `5fb8d2716f0f4b0a1596178f0ab69a5cb22bbd93`

## Bounded attempts and external state

The ordinary HTTPS push and one explicit credential-backed retry using the first supplied GitHub credential both reached GitHub and returned HTTP 403 with the exact account-state reason `Your account is suspended`. The second supplied credential was checked only against GitHub's authenticated `/user` endpoint and returned HTTP 401 `Bad credentials`; it was not used for another push. No credential value was printed, copied into a URL, retained in this receipt, committed, or sent to another service.

At 2026-08-22T16:00:46Z, anonymous GitHub API reads for the repository and its historically verified Unit 2 release both returned HTTP 404. At 2026-08-22T16:00:56Z, GitHub's official status endpoint reported indicator `none` and `All Systems Operational`. The evidence therefore identifies an account/repository availability block, not a general GitHub outage and not a defect in the verified Unit 4 content.

## Disposition

No Unit 3 or Unit 4 public tag or release is claimed. Unit 2 remains the most recent release that was previously published and anonymously verified byte-for-byte, but the suspended account currently makes even that repository lineage anonymously unreachable. The exact local commits remain preserved; retry once at the next substantial verified boundary rather than looping on the same external rejection.
