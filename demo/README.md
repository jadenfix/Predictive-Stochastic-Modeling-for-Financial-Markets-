# Evaluation mechanics demo

`evaluation-correction.gif` and `evaluation-correction.mp4` show the temporal
direction, purged multi-step split, and MSPE arithmetic checked by
`test_forecast_evaluation.R`. They use the same synthetic, hand-calculable
values as the test.

The footer pins the archived source to main commit
`bc503584d827e19004501a219edfdb92db902bf1` and pins the checked helper by its
SHA-256 digest. The MP4 also records both pins in its comment metadata.

Regenerate from the repository root with Pillow and FFmpeg installed:

```bash
python demo/generate_evaluation_demo.py
```

The demo establishes only forward date direction, a training-label boundary at
or before the first test predictor origin, and correct mean-squared-error
arithmetic. It does not demonstrate regime accuracy, forecast skill,
calibration, optimizer convergence, or trading performance.
