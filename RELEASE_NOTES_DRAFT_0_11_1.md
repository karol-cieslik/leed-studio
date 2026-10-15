# LEED Studio 0.11.1 — Draft release notes

**Status: pre-release prototype; not yet accepted as a verified Windows release.**

## Highlights
- Gwyddion-inspired dockable scientific workspace.
- Image-stack viewing, spot fitting/tracking and I(E) exploration workflows.
- Project save/reopen and CSV export workflows documented in the user manual.
- Windows packaging and automated acceptance workflow are configured.

## Validation status
- Linux regression baseline: 47 passed, 1 skipped in the available environment; the optional GUI smoke test was skipped because Qt dependencies were unavailable.
- Core self-test and Python compilation passed.
- Windows executable and installer have not yet been verified on a Windows runner.
- Real experimental tracking accuracy has not yet been validated against the TU Wien Fe₂O₃ dataset and reference Spot Tracker results.

## Important limitations
This is exploratory research software, not a validated replacement for ViPErLEED Spot Tracker. Synthetic tests do not establish real-data measurement accuracy. Check outputs against independent reference data before using them in scientific conclusions or publications.

## Before publishing a GitHub Release
- [ ] Windows GitHub Actions workflow passes.
- [ ] Portable ZIP and installer are downloaded and checked.
- [ ] Manual Windows GUI acceptance checklist is completed.
- [ ] Experimental benchmark requirement is completed or the release is explicitly labelled as not scientifically validated.
- [ ] Maintainer identity, attribution, licence, and third-party notices are reviewed.
