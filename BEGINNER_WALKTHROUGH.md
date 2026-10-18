# Beginner walkthrough

This walkthrough uses the small simulated stack included with LEED Studio. It is safe to explore and can be loaded again from **File → Try example data**. It is not a real experiment, and its numbers must not be used as scientific results.

## 1. Look through the stack

On the first launch, the practice stack loads automatically. Use the slider below the image to move between frames. The spot shifts slightly from frame to frame. You can also use the left and right arrow keys.

## 2. Select a bright spot

Click close to the centre of the bright spot in the image. A marker appears and the measurement buttons become available. If you click the wrong place, click again on the spot.

## 3. Fit one spot

Choose **Measure spot profile**. Review the fitted centre, width, and fit residual. The fit is a model of the selected spot in the current frame; a successful fit does not prove the model is scientifically correct.

## 4. Make an intensity-versus-energy curve

The practice stack has a known demo axis: it starts at 80 eV and advances by 5 eV per frame. The first-launch example fills and confirms these demo values for you. After selecting a spot, choose **Measure intensity vs energy**. The curve and table show the result for each frame.

For your own experiment, replace the demo values with the energy of frame 1 and the step recorded by your instrument. Confirm the axis only after checking those records. LEED Studio assumes one constant step between frames.

## 5. Review and save

Select a row in the table or a point on the curve to inspect that frame. Use the previous/next flagged-frame buttons if the analysis reports warnings. Save with **Save project…** to keep the stack and settings together. You can also try the fit CSV or I(E) CSV export buttons.

## When you are ready for real data

Choose **Open data…** and select a grayscale image or multipage TIFF. Keep a copy of the original data. Check the energy mapping, image orientation, selected spot, correction inputs, and quality flags before using exported values.

The public TU Wien Fe₂O₃ dataset is a separate research benchmark, not the bundled practice example. Its record is at <https://doi.org/10.48436/hgg42-xss85>. LEED Studio has not yet been shown to reproduce its published reference results.

## If the layout gets confusing

- **F1** opens the short guide inside the app.
- **View → Beginner mode** hides advanced settings.
- **View → Reset workspace layout** restores the default panel arrangement.
