# Windows manual acceptance checklist — LEED Studio 0.11.1

Complete this on a real Windows desktop after downloading artifacts from a successful GitHub Actions run. Record Windows version, display scaling, artifact filenames, workflow run URL, and outcome for each check.

## Installation and launch
- [ ] Portable ZIP extracts without errors.
- [ ] Portable application launches and shows a usable window.
- [ ] Installer completes without unexpected prompts or errors.
- [ ] Installed application launches from its installed location.
- [ ] Application can be uninstalled; note whether user project files remain as expected.

## GUI usability
- [ ] Window is legible at the normal display scale.
- [ ] Window remains usable at 125% or 150% scaling if available.
- [ ] Dock panels can be hidden, shown, moved, and restored.
- [ ] Restart behavior for saved window/dock layout is sensible.
- [ ] No blocking error dialog appears during normal navigation.

## Sample-data workflow
- [ ] Open bundled sample TIFF / use the example workflow.
- [ ] Navigate between frames.
- [ ] Select a bright spot and run the documented fit/measurement operation.
- [ ] Review fit validity, residuals, and flagged frames.
- [ ] Save a project, close the app, reopen the project, and check that the expected data and settings return.
- [ ] Export CSV and verify that it exists, opens, and has sensible headers/row counts.

## Evidence
- [ ] Record screenshots of the main window, a measurement result, reopened project, and exported CSV (remove private paths/data).
- [ ] Record bugs with reproduction steps and logs in GitHub Issues.

## Interpretation
Passing this checklist establishes basic desktop usability only. It does not establish scientific accuracy. Real experimental validation remains a separate release requirement.
