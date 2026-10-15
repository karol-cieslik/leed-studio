"""Generate a small synthetic TIFF stack with a drifting LEED-like spot."""
from pathlib import Path
import numpy as np
import tifffile


def main():
    rng = np.random.default_rng(41)
    height, width = 160, 180
    yy, xx = np.mgrid[0:height, 0:width]
    frames = []
    amplitudes = [100, 160, 240, 330, 220, 130, 190, 270]
    for i, amplitude in enumerate(amplitudes):
        x0, y0 = 82 + 1.1*i, 77 + 0.55*i
        frame = 12 + 0.015*xx + 0.01*yy
        frame += amplitude*np.exp(-0.5*(((xx-x0)/2.8)**2 + ((yy-y0)/3.1)**2))
        # A nearby weak spot tests whether the tracker is overly sensitive to neighbours.
        frame += 30*np.exp(-0.5*(((xx-(x0+13))/3.5)**2 + ((yy-(y0-3))/3.5)**2))
        frame += rng.normal(0, 0.8, frame.shape)
        frames.append(np.clip(frame, 0, 65535).astype(np.uint16))
    out = Path(__file__).resolve().parent / "sample_drifting_stack.tif"
    tifffile.imwrite(out, np.stack(frames), photometric="minisblack")
    print(f"Wrote {out} ({len(frames)} frames). Use energy start 80 eV and step 5 eV for this synthetic example.")


if __name__ == "__main__":
    main()
