# GitHub handoff from a mobile phone

This handoff is designed for preparing the repository while away from the Windows test computer. Mobile GitHub upload screens vary, so treat these steps as a guide rather than a guaranteed exact UI sequence.

## 1. Keep the source archive safe
- Keep the original handover ZIP and Stage 7 source ZIP unchanged.
- Use `LEED_Studio_0_11_1_Stage7_Source.zip` as the source snapshot; Stage 8 adds review templates and release documents, not application features.
- Do not upload backups, logs containing private paths, credentials, or generated Windows artifacts to the public repository.

## 2. Create the repository
- Sign in to GitHub using the account that should receive credit for the project.
- Create a repository named `leed-studio` (or your chosen name).
- Decide whether it should initially be private while you review the contents.
- For a clean Git history and usable issue templates, upload the extracted project files and folders, not just a ZIP as the only repository file. If mobile upload is cumbersome, wait until a computer is available rather than publishing an incomplete repository.

## 3. Before making it public
- Review `CREDITS.md`, `LICENSE`, and `THIRD_PARTY_NOTICES.md`.
- Confirm the README clearly says Windows acceptance and experimental validation are pending.
- Check that `.github/workflows/windows-build.yml` and `.github/ISSUE_TEMPLATE/` are included.
- Do not create a `v0.11.1` release tag or claim a verified installer until the Windows workflow passes.

## 4. When at home on Wi-Fi / computer
1. Push the repository to GitHub.
2. Open Actions and run **Windows application build and executable acceptance tests**.
3. Download and inspect the portable ZIP, installer, and `WINDOWS_ACCEPTANCE_TESTS.txt`.
4. Complete `WINDOWS_MANUAL_ACCEPTANCE_CHECKLIST.md` on Windows.
5. Separately download the TU Wien Fe₂O₃ LEED-I(V) dataset and matching reference Spot Tracker results; record checksums and run `tools/benchmark_tuwien_fe2o3.py` before making scientific accuracy claims.

## Status vocabulary
- **Configured:** a workflow or test exists in the source.
- **Automated pass:** a named workflow completed successfully and logs/artifacts were inspected.
- **Manual pass:** a person completed the desktop checklist.
- **Scientifically validated:** the real experimental reference benchmark ran and its metrics were reviewed.
