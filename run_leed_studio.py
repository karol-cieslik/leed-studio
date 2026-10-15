"""Top-level script used by PyInstaller so package-relative imports work."""
from leed_studio.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
