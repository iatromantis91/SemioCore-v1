## Summary

Describe the change in one or two sentences.

## Contract discipline checklist

- [ ] Contracts validated: `python -m semioc contracts validate`
- [ ] Tests green: `pytest -q`
- [ ] If artifacts changed: goldens regenerated under `expected/` and change documented
- [ ] Docs updated where applicable (`docs/contract/*`)
- [ ] No non-deterministic fields introduced (timestamps, hostnames, random IDs)

## Notes

Link to issue/discussion if available.
