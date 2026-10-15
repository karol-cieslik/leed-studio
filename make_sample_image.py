"""Generate a synthetic LEED-like spot pattern for testing without experimental data."""
from pathlib import Path
import numpy as np
from PIL import Image

def main():
    rng = np.random.default_rng(7)
    h, w = 512, 512
    yy, xx = np.mgrid[0:h, 0:w]
    image = np.full((h, w), 18.0)
    spots = [
        (256, 256, 1800, 4.5, 4.5),
        (256, 145, 900, 3.5, 4.2),
        (256, 367, 1000, 4.1, 3.7),
        (145, 256, 1100, 4.0, 4.0),
        (367, 256, 950, 3.7, 4.3),
        (178, 178, 550, 3.5, 3.8),
        (334, 178, 620, 4.2, 3.5),
        (178, 334, 580, 3.7, 4.2),
        (334, 334, 500, 3.8, 3.6),
    ]
    for x0, y0, amp, sx, sy in spots:
        image += amp * np.exp(-0.5 * (((xx-x0)/sx)**2 + ((yy-y0)/sy)**2))
    image += rng.normal(0, 3.0, image.shape)
    image = np.clip(image, 0, 65535).astype(np.uint16)
    out = Path(__file__).resolve().parent / "sample_leed_like_pattern.tif"
    Image.fromarray(image).save(out)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
