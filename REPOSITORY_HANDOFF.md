# Repository handoff — LEED Studio 0.11.1

## Suggested public repository description

A Python desktop prototype for exploratory Low-Energy Electron Diffraction (LEED) image-stack analysis and I(E) inspection. Built with PySide6, pyqtgraph, NumPy and SciPy; inspired by Gwyddion's dockable scientific workspace.

## Recommended initial GitHub setup

- Repository name: `leed-studio`
- Keep the repository public only if you are comfortable releasing the GPL-3.0-or-later source and attribution documents.
- Use `README.md` as the landing page and `RELEASE_READINESS_CHECKLIST.md` as the maintainer gate.
- Do not upload the generated wheel, build tree, egg-info directory, or unverified Windows executables as source files. Publish verified binaries as release assets after Windows CI passes.
- Run the Windows Actions workflow before attaching binary downloads.
- Preserve `CREDITS.md`, `LICENSE`, and `THIRD_PARTY_NOTICES.md`.

## Current status to disclose

The Linux regression baseline passes (47 passed, 1 skipped due to missing PySide6). The Windows workflow is configured but has not been verified by a successful run in this audit. Real experimental coordinate validation against the TU Wien dataset is pending because the dataset and matching reference files are not currently available locally. The reported 0.0054-pixel RMSE is synthetic and must not be described as experimental accuracy.

## Versioning caution

The current source metadata is 0.11.1, but some historical validation/audit documents describe earlier versions. Keep those clearly labelled as historical or update them only after checking the claims against this source snapshot.
